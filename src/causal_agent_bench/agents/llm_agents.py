from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.agent_payload import build_agent_task_context
from causal_agent_bench.agents.base import BaseAgent
from causal_agent_bench.agents.llm_clients import (
    CachingLLMClient,
    LLMClient,
    LLMResponse,
    LocalStubLLMClient,
    Message,
    ModelConfig,
    ProviderConfigurationError,
    ProviderError,
    TokenUsage,
    cache_key_parts,
    estimate_cost_usd,
    get_llm_client,
    response_hash,
)
from causal_agent_bench.agents.tool_protocol import parse_tool_action
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import (
    AgentAction,
    BenchmarkInstance,
    BenchmarkTask,
    ToolCall,
    ToolCallParseResult,
    ToolSpec,
)

PROMPT_ROOT = Path(__file__).resolve().parents[3] / "prompts" / "agents"


class LLMAgentBase(BaseAgent):
    name = "llm_agent"
    prompt_file = "direct_tool_agent.md"
    provider_default = "local_stub"
    model_default = "local-stub"

    def __init__(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        retry_count: int = 2,
        timeout: float = 60.0,
        pricing: dict[str, float] | None = None,
        base_url: str | None = None,
        api_key_env: str | tuple[str, ...] | None = None,
        cache_dir: str | None = None,
        client: LLMClient | None = None,
        seed: int = 0,
        prompt_file: str | None = None,
        prompt_addendum_file: str | None = None,
        prompt_addendum: str | None = None,
        system_safety_file: str = "system_safety.md",
        tool_protocol_file: str | None = None,
        action_protocol: str = "json_only",
        tool_description_mode: str = "detailed",
        step_budget_reminder: bool = False,
        ablation: dict[str, Any] | None = None,
        max_cost_per_task_usd: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(seed=seed, **kwargs)
        if action_protocol not in {"json_only", "flexible_text"}:
            raise ValueError("action_protocol must be 'json_only' or 'flexible_text'")
        if tool_description_mode not in {"detailed", "short"}:
            raise ValueError("tool_description_mode must be 'detailed' or 'short'")
        self.provider = provider or self.provider_default
        self.model = model or self.model_default
        if self.provider != "local_stub" and not self.model:
            raise ProviderConfigurationError(
                f"model is not configured for provider {self.provider!r}; set the model in the run config or environment"
            )
        self.client = client or get_llm_client(self.provider)
        if cache_dir:
            self.client = CachingLLMClient(self.client, cache_dir)
        self.model_config = ModelConfig(
            provider=self.provider,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            retry_count=retry_count,
            seed=seed,
            pricing=pricing or {},
            base_url=base_url,
            api_key_env=api_key_env,
            cache_dir=cache_dir,
            extra=dict(kwargs),
        )
        if prompt_file is not None:
            self.prompt_file = prompt_file
        self.prompt_addendum_file = prompt_addendum_file
        self.system_safety_file = system_safety_file
        self.action_protocol = action_protocol
        self.tool_description_mode = tool_description_mode
        self.step_budget_reminder = bool(step_budget_reminder)
        self.ablation = dict(ablation or {})
        self.max_cost_per_task_usd = max_cost_per_task_usd
        self.tool_protocol_file = (
            tool_protocol_file
            or ("tool_protocol_flexible_text.md" if action_protocol == "flexible_text" else "tool_protocol.md")
        )
        self._prompt = _load_prompt(self.prompt_file)
        self._prompt_addendum = prompt_addendum or (
            _load_prompt(prompt_addendum_file) if prompt_addendum_file else ""
        )
        self._safety_prompt = _load_prompt(self.system_safety_file)
        self._tool_protocol_prompt = _load_prompt(self.tool_protocol_file)
        self.prompt_version_hash = stable_hash(
            {
                "agent": self.name,
                "prompt_file": self.prompt_file,
                "prompt": self._prompt,
                "prompt_addendum_file": self.prompt_addendum_file,
                "prompt_addendum": self._prompt_addendum,
                "system_safety_file": self.system_safety_file,
                "safety": self._safety_prompt,
                "tool_protocol_file": self.tool_protocol_file,
                "tool_protocol": self._tool_protocol_prompt,
                "action_protocol": self.action_protocol,
                "tool_description_mode": self.tool_description_mode,
                "step_budget_reminder": self.step_budget_reminder,
                "ablation": self.ablation,
            }
        )
        self.prompt_template_hash = stable_hash(
            {
                "prompt_file": self.prompt_file,
                "prompt": self._prompt,
                "prompt_addendum_file": self.prompt_addendum_file,
                "prompt_addendum": self._prompt_addendum,
            }
        )
        self.prompt_files = {
            "agent": self.prompt_file,
            "prompt_addendum": self.prompt_addendum_file,
            "system_safety": self.system_safety_file,
            "tool_protocol": self.tool_protocol_file,
        }
        self.llm_calls: list[dict[str, Any]] = []
        self.total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.total_estimated_cost_usd: float | None = 0.0
        self.total_latency_s = 0.0

    def reset(self, instance: BenchmarkInstance | BenchmarkTask, seed: int | None = None) -> None:
        super().reset(instance, seed=seed)
        if seed is not None:
            self.model_config = ModelConfig(
                provider=self.model_config.provider,
                model=self.model_config.model,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                timeout=self.model_config.timeout,
                retry_count=self.model_config.retry_count,
                seed=seed,
                json_mode=self.model_config.json_mode,
                pricing=self.model_config.pricing,
                base_url=self.model_config.base_url,
                api_key_env=self.model_config.api_key_env,
                cache_dir=self.model_config.cache_dir,
                extra=self.model_config.extra,
            )
        self.llm_calls = []
        self.total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.total_estimated_cost_usd = 0.0
        self.total_latency_s = 0.0

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        messages = self._messages(observation_history, available_tools)
        response = self._complete(messages, available_tools, phase="act")
        return self._response_to_action(
            response,
            messages,
            phase="act",
            available_tools=available_tools,
            observation_history=observation_history,
        )

    @property
    def model_name(self) -> str:
        return self.model_config.model

    def run_metadata(self) -> dict[str, Any]:
        prompt_hashes = sorted(
            {
                str(value)
                for call in self.llm_calls
                for value in [
                    call.get("prompt_hash"),
                    call.get("prompt_version_hash"),
                ]
                if value
            }
        )
        return {
            "provider": self.provider,
            "model": self.model,
            "model_id": self.model,
            "api_version": self.model_config.extra.get("api_version")
            or self.model_config.extra.get("anthropic_version"),
            "run_date": datetime.now(UTC).date().isoformat(),
            "agent_type": self.name,
            "prompt_version_hash": self.prompt_version_hash,
            "prompt_template_hash": self.prompt_template_hash,
            "prompt_hash": self.prompt_version_hash,
            "prompt_hashes": prompt_hashes,
            "prompt_files": dict(self.prompt_files),
            "action_protocol": self.action_protocol,
            "tool_description_mode": self.tool_description_mode,
            "step_budget_reminder": self.step_budget_reminder,
            "ablation": dict(self.ablation),
            "sampling_parameters": {
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens,
                "retry_count": self.model_config.retry_count,
            },
            "llm_calls": self.llm_calls,
            "token_usage": dict(self.total_usage),
            "prompt_tokens": self.total_usage["input_tokens"],
            "completion_tokens": self.total_usage["output_tokens"],
            "total_tokens": self.total_usage["total_tokens"],
            "latency_s": round(self.total_latency_s, 6),
            "estimated_cost_usd": self.total_estimated_cost_usd,
            "actual_estimated_cost_usd": self.total_estimated_cost_usd,
            "model_call_count": sum(1 for call in self.llm_calls if call.get("provider_call_made", True)),
            "llm_call_count": len(self.llm_calls),
            "total_retries": sum(int(call.get("retries") or 0) for call in self.llm_calls),
            "max_cost_per_task_usd": self.max_cost_per_task_usd,
        }

    def _messages(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
        *,
        extra_instruction: str | None = None,
    ) -> list[Message]:
        task_context = self._task_context()
        tool_context = [self._tool_payload(tool) for tool in available_tools if tool.is_available]
        user_payload = {
            "task": task_context,
            "available_tools": tool_context,
            "observation_history": _jsonable_history(observation_history),
            "response_contract": self._response_contract(),
        }
        if extra_instruction:
            user_payload["extra_instruction"] = extra_instruction
        if self.step_budget_reminder:
            user_payload["step_budget_reminder"] = (
                "Track remaining steps. Prefer the fewest sufficient tool calls, and stop with "
                "uncertainty rather than exceeding the budget."
            )
        if self.ablation:
            user_payload["ablation"] = self.ablation
        system_parts = [self._safety_prompt, self._tool_protocol_prompt, self._prompt]
        if self._prompt_addendum:
            system_parts.append(self._prompt_addendum)
        return [
            Message(
                role="system",
                content="\n\n".join(part for part in system_parts if part),
            ),
            Message(role="user", content=json.dumps(user_payload, indent=2, sort_keys=True)),
        ]

    def _tool_payload(self, tool: ToolSpec) -> dict[str, Any]:
        if self.tool_description_mode == "short":
            return {
                "name": tool.name,
                "description": tool.description,
                "is_available": tool.is_available,
            }
        return tool.model_dump(mode="json")

    def _response_contract(self) -> dict[str, Any]:
        contract = {
            "tool_call": {
                "action": "tool_call",
                "thought": "short rationale",
                "tool_name": "name",
                "arguments": {},
            },
            "final_answer": {
                "action": "final_answer",
                "thought": "short rationale",
                "final_answer": "answer text",
                "evidence": ["observation id, observed fact, or limitation"],
                "stop": True,
            },
            "clarification": {
                "action": "clarification",
                "thought": "why the task is underspecified",
                "clarification": "question or uncertainty statement",
                "stop": True,
            },
        }
        if self.action_protocol == "flexible_text":
            return {
                "mode": "flexible_text",
                "instruction": (
                    "Short prose is allowed, but include exactly one parseable JSON action object "
                    "matching one of these schemas."
                ),
                "schemas": contract,
            }
        return {"mode": "json_only", "schemas": contract}

    def _task_context(self) -> dict[str, Any]:
        if self.instance is not None:
            return build_agent_task_context(self.instance)
        return {
            "user_instruction": self.user_instruction(),
            "instruction_patch": None,
            "success_criteria": [],
            "required_information": [],
            "forbidden_assumptions": [],
            "initial_memory": {},
            "max_steps": None,
        }

    def _complete(
        self,
        messages: list[Message],
        available_tools: list[ToolSpec],
        *,
        phase: str,
    ) -> LLMResponse:
        if self._task_cost_budget_exhausted():
            response = _budget_exceeded_response(self.model, self.provider, self.max_cost_per_task_usd)
            call_record = _llm_call_record(
                phase=phase,
                messages=messages,
                response=response,
                prompt_hash=self.prompt_version_hash,
                available_tools=available_tools,
                config=self.model_config,
            )
            self.llm_calls.append(call_record)
            return response
        try:
            response = self.client.complete(messages, available_tools, self.model_config)
        except ProviderError as exc:
            response = LLMResponse(
                content=json.dumps(
                    {
                        "thought": "The configured model provider failed before returning a usable response.",
                        "final_answer": (
                            "Unable to complete because the configured model provider failed. "
                            "No scientific result should be inferred from this trajectory."
                        ),
                        "stop": True,
                    }
                ),
                usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
                model_name=self.model,
                provider_name=self.provider,
                latency_s=0.0,
                estimated_cost_usd=0.0,
                retries=self.model_config.retry_count,
                metadata={
                    "provider_error_class": type(exc).__name__,
                    "provider_error_message": _safe_error_message(exc),
                },
            )
        response = _with_estimated_cost(response, self.model_config)
        call_record = _llm_call_record(
            phase=phase,
            messages=messages,
            response=response,
            prompt_hash=self.prompt_version_hash,
            available_tools=available_tools,
            config=self.model_config,
        )
        self.llm_calls.append(call_record)
        _accumulate_usage(self.total_usage, response)
        if response.estimated_cost_usd is None:
            self.total_estimated_cost_usd = None
        elif self.total_estimated_cost_usd is not None:
            self.total_estimated_cost_usd = round(
                self.total_estimated_cost_usd + response.estimated_cost_usd,
                8,
            )
        self.total_latency_s += response.latency_s or 0.0
        return response

    def _task_cost_budget_exhausted(self) -> bool:
        if self.max_cost_per_task_usd is None:
            return False
        if self.total_estimated_cost_usd is None:
            return False
        return self.total_estimated_cost_usd >= self.max_cost_per_task_usd

    def _response_to_action(
        self,
        response: LLMResponse,
        messages: list[Message],
        *,
        phase: str,
        available_tools: list[ToolSpec],
        observation_history: list[dict[str, Any]],
    ) -> AgentAction:
        metadata = {
            "agent_type": self.name,
            "provider": self.provider,
            "model": self.model,
            "prompt_version_hash": self.prompt_version_hash,
            "prompt_template_hash": self.prompt_template_hash,
            "prompt_file": self.prompt_file,
            "prompt_addendum_file": self.prompt_addendum_file,
            "system_safety_file": self.system_safety_file,
            "tool_protocol_file": self.tool_protocol_file,
            "action_protocol": self.action_protocol,
            "tool_description_mode": self.tool_description_mode,
            "step_budget_reminder": self.step_budget_reminder,
            "ablation": dict(self.ablation),
            "llm_phase": phase,
            "token_usage": response.usage.as_dict(),
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
            "latency_s": response.latency_s,
            "estimated_cost_usd": response.estimated_cost_usd,
            "retries": response.retries,
            "llm_calls": [
                _llm_call_record(
                    phase,
                    messages,
                    response,
                    self.prompt_version_hash,
                    available_tools=available_tools,
                    config=self.model_config,
                )
            ],
        }
        parse_result = _parse_response_action(
            response,
            available_tools=available_tools,
            observation_history=observation_history,
            required_information=self._required_information(),
        )
        parse_payload = parse_result.model_dump(mode="json")
        metadata.update(
            {
                "raw_model_output": response.content,
                "parsed_action": parse_payload,
                "parser_outcome": parse_result.outcome,
                "parser_valid": parse_result.is_valid,
            }
        )
        if parse_result.action_type == "tool_call" and parse_result.tool_name:
            return AgentAction(
                thought=parse_result.explanation,
                tool_call=ToolCall(
                    tool_name=parse_result.tool_name,
                    arguments=parse_result.arguments,
                    call_id=parse_result.metadata.get("call_id"),
                ),
                metadata={**metadata, "invalid_action": not parse_result.is_valid},
            )
        if parse_result.action_type in {"final_answer", "clarification"}:
            return AgentAction(
                thought=parse_result.explanation,
                final_answer=parse_result.final_answer,
                stop=True,
                metadata={**metadata, "invalid_action": not parse_result.is_valid},
            )
        return AgentAction(
            thought="The model did not return a valid action.",
            final_answer="Unable to complete: model response did not match the required action schema.",
            stop=True,
            metadata={
                **metadata,
                "parse_error": True,
                "invalid_action": True,
                "raw_content": response.content,
            },
        )

    def _required_information(self) -> list[str]:
        if self.instance is not None:
            return list(self.instance.base_task.goal.required_information)
        if self.legacy_task is not None:
            return list(self.legacy_task.expected_behavior.required_tools)
        return []


class DirectToolAgent(LLMAgentBase):
    name = "direct_tool_agent"
    prompt_file = "direct_tool_agent.md"


class DirectLLMToolAgent(DirectToolAgent):
    name = "direct_llm_tool_agent"
    prompt_file = "direct_llm_tool_agent.md"


class ReActStyleLLMAgent(LLMAgentBase):
    name = "react_style_llm_agent"
    prompt_file = "react_style_llm_agent.md"


class PlannerExecutorAgent(LLMAgentBase):
    name = "planner_executor_agent"
    prompt_file = "planner_executor_agent.md"

    def reset(self, instance: BenchmarkInstance | BenchmarkTask, seed: int | None = None) -> None:
        super().reset(instance, seed=seed)
        self.plan: str | None = None

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        if self.plan is None:
            plan_messages = self._messages(
                observation_history,
                available_tools,
                extra_instruction="First produce a compact plan as JSON: {\"plan\": [\"...\"]}. Do not call tools in this planning response.",
            )
            plan_response = self._complete(plan_messages, available_tools, phase="plan")
            self.plan = plan_response.content or ""
        messages = self._messages(
            observation_history,
            available_tools,
            extra_instruction=f"Current plan: {self.plan}\nExecute the next step or revise if a tool failed.",
        )
        response = self._complete(messages, available_tools, phase="execute")
        return self._response_to_action(
            response,
            messages,
            phase="execute",
            available_tools=available_tools,
            observation_history=observation_history,
        )


class PlannerExecutorLLMAgent(PlannerExecutorAgent):
    name = "planner_executor_llm_agent"
    prompt_file = "planner_executor_llm_agent.md"


class SelfCheckAgent(LLMAgentBase):
    name = "self_check_agent"
    prompt_file = "self_check_agent.md"

    def reset(self, instance: BenchmarkInstance | BenchmarkTask, seed: int | None = None) -> None:
        super().reset(instance, seed=seed)
        self.checked_once = False

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        messages = self._messages(observation_history, available_tools)
        response = self._complete(messages, available_tools, phase="act")
        action = self._response_to_action(
            response,
            messages,
            phase="act",
            available_tools=available_tools,
            observation_history=observation_history,
        )
        if action.final_answer is None or self.checked_once:
            return action
        self.checked_once = True
        check_messages = self._messages(
            observation_history,
            available_tools,
            extra_instruction=(
                "Before finalizing, verify that the final answer is supported by observations. "
                "If evidence is missing or conflicting, call a verification tool or state uncertainty. "
                f"Candidate final answer: {action.final_answer}"
            ),
        )
        check_response = self._complete(check_messages, available_tools, phase="self_check")
        checked_action = self._response_to_action(
            check_response,
            check_messages,
            phase="self_check",
            available_tools=available_tools,
            observation_history=observation_history,
        )
        checked_action.metadata["candidate_final_answer"] = action.final_answer
        return checked_action


class SelfCheckingLLMAgent(SelfCheckAgent):
    name = "self_checking_llm_agent"
    prompt_file = "self_checking_llm_agent.md"


class MemoryVerifyingLLMAgent(LLMAgentBase):
    name = "memory_verifying_llm_agent"
    prompt_file = "memory_verifying_llm_agent.md"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        extra_instruction = None
        memory = self._task_context().get("initial_memory") or {}
        if memory and "verify_fact" not in self.called_tools(observation_history):
            extra_instruction = (
                "Initial memory is present. Before relying on it in a final answer, verify the "
                "task-relevant claim with an available verification or evidence tool. If no such "
                "tool is available, state the limitation instead of treating memory as ground truth."
            )
        messages = self._messages(
            observation_history,
            available_tools,
            extra_instruction=extra_instruction,
        )
        response = self._complete(messages, available_tools, phase="memory_verify")
        return self._response_to_action(
            response,
            messages,
            phase="memory_verify",
            available_tools=available_tools,
            observation_history=observation_history,
        )


class RecoveryPromptLLMAgent(LLMAgentBase):
    name = "recovery_prompt_llm_agent"
    prompt_file = "recovery_prompt_llm_agent.md"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        extra_instruction = None
        if self.has_error(observation_history):
            extra_instruction = (
                "A prior tool observation failed, was corrupted, or returned incomplete evidence. "
                "Do not repeat the same failed call unchanged. Repair arguments, choose another "
                "relevant tool, or answer with calibrated uncertainty if recovery is impossible."
            )
        messages = self._messages(
            observation_history,
            available_tools,
            extra_instruction=extra_instruction,
        )
        response = self._complete(messages, available_tools, phase="recovery")
        return self._response_to_action(
            response,
            messages,
            phase="recovery",
            available_tools=available_tools,
            observation_history=observation_history,
        )


class ToolConservativeLLMAgent(LLMAgentBase):
    name = "tool_conservative_llm_agent"
    prompt_file = "tool_conservative_llm_agent.md"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = self.called_tools(observation_history)
        extra_instruction = (
            "Use a tool only if it is necessary for an unmet success criterion. "
            f"Tools already called: {called}. If enough evidence is present, finalize. "
            "If evidence is impossible to obtain with the remaining tools, state uncertainty."
        )
        messages = self._messages(
            observation_history,
            available_tools,
            extra_instruction=extra_instruction,
        )
        response = self._complete(messages, available_tools, phase="conservative_act")
        return self._response_to_action(
            response,
            messages,
            phase="conservative_act",
            available_tools=available_tools,
            observation_history=observation_history,
        )


def _load_prompt(name: str) -> str:
    path = PROMPT_ROOT / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_response_action(
    response: LLMResponse,
    *,
    available_tools: list[ToolSpec],
    observation_history: list[dict[str, Any]],
    required_information: list[str],
) -> ToolCallParseResult:
    if response.tool_calls:
        if len(response.tool_calls) == 1:
            tool_call = response.tool_calls[0]
            payload: dict[str, Any] = {
                "action": "tool_call",
                "thought": _thought_from_content(response.content),
                "tool_name": tool_call.name,
                "arguments": tool_call.arguments,
                "call_id": tool_call.call_id,
            }
        else:
            payload = {
                "tool_calls": [
                    {
                        "tool_name": tool_call.name,
                        "arguments": tool_call.arguments,
                        "call_id": tool_call.call_id,
                    }
                    for tool_call in response.tool_calls
                ]
            }
        result = parse_tool_action(
            json.dumps(payload, sort_keys=True),
            available_tools=available_tools,
            observation_history=observation_history,
            required_information=required_information,
        )
        result.metadata["native_tool_calls"] = True
        return result
    return parse_tool_action(
        response.content,
        available_tools=available_tools,
        observation_history=observation_history,
        required_information=required_information,
    )


def _thought_from_content(content: str | None) -> str | None:
    if not content:
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict) and parsed.get("thought") is not None:
        return str(parsed["thought"])
    return None


def _jsonable_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return json.loads(json.dumps(history, sort_keys=True, default=str))


def _with_estimated_cost(response: LLMResponse, config: ModelConfig) -> LLMResponse:
    if response.estimated_cost_usd is not None or not config.pricing:
        return response
    cost = estimate_cost_usd(response.usage, config.pricing)
    if cost is None:
        return response
    return LLMResponse(
        content=response.content,
        tool_calls=response.tool_calls,
        usage=response.usage,
        model_name=response.model_name or config.model,
        provider_name=response.provider_name or config.provider,
        latency_s=response.latency_s,
        estimated_cost_usd=cost,
        retries=response.retries,
        response_id=response.response_id,
        metadata={**response.metadata, "cost_estimated_from_config": True},
    )


def _budget_exceeded_response(
    model: str,
    provider: str,
    cap: float | None,
) -> LLMResponse:
    return LLMResponse(
        content=json.dumps(
            {
                "thought": "The configured per-task cost budget has been reached.",
                "final_answer": (
                    "Unable to continue because the configured per-task cost budget was reached. "
                    "No scientific result should be inferred from this trajectory."
                ),
                "stop": True,
            }
        ),
        usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
        model_name=model,
        provider_name=provider,
        latency_s=0.0,
        estimated_cost_usd=0.0,
        retries=0,
        metadata={
            "budget_exceeded": True,
            "budget_scope": "task",
            "budget_cap_usd": cap,
            "provider_call_made": False,
        },
    )


def _llm_call_record(
    phase: str,
    messages: list[Message],
    response: LLMResponse,
    prompt_hash: str,
    *,
    available_tools: list[ToolSpec] | None = None,
    config: ModelConfig | None = None,
) -> dict[str, Any]:
    request_hashes = (
        cache_key_parts(messages, available_tools, config)
        if available_tools is not None and config is not None
        else {}
    )
    return {
        "phase": phase,
        "provider": response.provider_name or (config.provider if config else None),
        "model": response.model_name or (config.model if config else None),
        "prompt_version_hash": prompt_hash,
        "prompt_hash": request_hashes.get("prompt_hash"),
        "response_hash": response_hash(response),
        "tool_state_hash": request_hashes.get("tool_state_hash"),
        "config_hash": request_hashes.get("config_hash"),
        "cache_key": response.metadata.get("cache_key") or request_hashes.get("cache_key"),
        "cache_hit": response.metadata.get("cache_hit", False),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "name": message.name,
                "tool_call_id": message.tool_call_id,
            }
            for message in messages
        ],
        "response": {
            "content": response.content,
            "tool_calls": [
                {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                    "call_id": tool_call.call_id,
                }
                for tool_call in response.tool_calls
            ],
            "provider": response.provider_name,
            "model": response.model_name,
            "response_id": response.response_id,
        },
        "usage": response.usage.as_dict(),
        "prompt_tokens": response.usage.input_tokens,
        "completion_tokens": response.usage.output_tokens,
        "total_tokens": response.usage.total_tokens,
        "latency_s": response.latency_s,
        "estimated_cost_usd": response.estimated_cost_usd,
        "retries": response.retries,
        "provider_call_made": response.metadata.get("provider_call_made", True),
        "provider_error_class": response.metadata.get("provider_error_class"),
        "metadata": response.metadata,
    }


def _accumulate_usage(total: dict[str, int], response: LLMResponse) -> None:
    usage = response.usage
    total["input_tokens"] += int(usage.input_tokens or 0)
    total["output_tokens"] += int(usage.output_tokens or 0)
    total["total_tokens"] += int(usage.total_tokens or 0)


def _safe_error_message(exc: Exception) -> str:
    message = str(exc)
    return message if len(message) <= 500 else f"{message[:500]}..."


def local_stub_agent_for_tests(responses: list[dict[str, Any]]) -> DirectToolAgent:
    return DirectToolAgent(client=LocalStubLLMClient(responses))
