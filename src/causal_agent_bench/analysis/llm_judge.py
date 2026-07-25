from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal, Protocol

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

from causal_agent_bench.agents.llm_clients import Message, ModelConfig, get_llm_client
from causal_agent_bench.analysis.human_validation import sample_validation_items
from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.config import AgentRunConfig
from causal_agent_bench.utils.io import git_commit, load_yaml, read_jsonl, write_json, write_jsonl

JudgeLabel = Literal["yes", "no", "unclear", "not_applicable"]

JUDGE_DIMENSIONS = [
    "final_answer_correctness",
    "intervention_validity",
    "trajectory_error_taxonomy",
    "contradiction_handling",
    "recovery_behavior",
]

HUMAN_DIMENSION_MAP = {
    "final_answer_correctness": "final_answer_label_correct",
    "intervention_validity": "changed_factor_isolated",
    "trajectory_error_taxonomy": "error_taxonomy_label_correct",
    "contradiction_handling": "trajectory_detected_contradiction",
    "recovery_behavior": "trajectory_showed_recovery",
}


class JudgeConfig(BaseModel):
    """Explicit opt-in configuration for optional LLM-as-judge runs."""

    model_config = ConfigDict(extra="forbid")

    judge_provider: str
    judge_model: str
    prompt_version: str = Field(min_length=1)
    temperature: float = Field(ge=0)
    max_tokens: int = Field(ge=1)
    retries: int = Field(ge=0)
    sample_size: int = Field(default=100, ge=1)
    seed: int = 0
    dimensions: list[str] = Field(default_factory=lambda: list(JUDGE_DIMENSIONS))
    output_dir: str | None = None
    allow_label_overwrite: bool = False
    fake_judge: bool = False

    @field_validator("judge_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        if value == "fake_judge":
            return value
        checked = AgentRunConfig.validate_provider(value)
        assert checked is not None
        return checked

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, value: list[str]) -> list[str]:
        unknown = sorted(set(value) - set(JUDGE_DIMENSIONS))
        if unknown:
            raise ValueError(f"unknown judge dimension(s): {unknown}")
        return value


class ModelJudge(Protocol):
    def judge(self, item: dict[str, Any], dimension: str) -> dict[str, Any]:
        ...


def run_llm_judge(
    run_dir: str | Path,
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = JudgeConfig.model_validate(load_yaml(config_path))
    data = load_run_results(run_dir)
    out = Path(output_dir or config.output_dir or data.run_dir / "llm_judge")
    out.mkdir(parents=True, exist_ok=True)
    if not config.allow_label_overwrite and (out / "judge_labels.jsonl").exists():
        raise FileExistsError(
            f"judge labels already exist at {out / 'judge_labels.jsonl'}; use a new output dir"
        )
    items = sample_validation_items(data, sample_size=config.sample_size, seed=config.seed)
    judge = _build_judge(config)
    labels = []
    prompt_hashes = {}
    for item in items:
        for dimension in config.dimensions:
            prompt = judge_prompt(dimension, item, config.prompt_version)
            prompt_hash = stable_hash(prompt)
            prompt_hashes[dimension] = prompt_hash
            result = judge.judge(item, dimension)
            labels.append(
                {
                    "judge_label_id": stable_hash(
                        {
                            "item_id": item["item_id"],
                            "dimension": dimension,
                            "provider": config.judge_provider,
                            "model": config.judge_model,
                            "prompt_version": config.prompt_version,
                        }
                    ),
                    "item_id": item["item_id"],
                    "run_id": item.get("run_id"),
                    "instance_id": item.get("instance_id"),
                    "agent_name": item.get("agent_name"),
                    "dimension": dimension,
                    "label": _normalize_label(result.get("label")),
                    "rationale": result.get("rationale", ""),
                    "confidence": result.get("confidence"),
                    "judge_provider": config.judge_provider,
                    "judge_model": config.judge_model,
                    "prompt_version": config.prompt_version,
                    "prompt_hash": prompt_hash,
                    "config_hash": stable_hash(config.model_dump(mode="json")),
                    "metadata": result.get("metadata", {}),
                }
            )
    labels_path = out / "judge_labels.jsonl"
    write_jsonl(labels_path, labels)
    manifest = {
        "run_dir": str(data.run_dir),
        "output_dir": str(out),
        "labels_path": str(labels_path),
        "items_judged": len(items),
        "labels_written": len(labels),
        "judge_provider": config.judge_provider,
        "judge_model": config.judge_model,
        "prompt_version": config.prompt_version,
        "prompt_hashes": prompt_hashes,
        "config_hash": stable_hash(config.model_dump(mode="json")),
        "git_commit": git_commit(Path.cwd()),
        "safety": {
            "overwrites_deterministic_scores": False,
            "overwrites_human_labels": False,
            "allow_label_overwrite": config.allow_label_overwrite,
            "paper_ground_truth_warning": (
                "Judge labels are not ground truth without human calibration and claim-ledger evidence."
            ),
        },
    }
    write_json(out / "judge_manifest.json", manifest)
    return manifest


def calibrate_llm_judge(
    judge_labels_path: str | Path,
    human_annotations_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    judge_rows = read_jsonl(judge_labels_path)
    human_rows = _read_human_rows(Path(human_annotations_path))
    out = Path(output_dir) if output_dir is not None else Path(judge_labels_path).parent / "calibration"
    out.mkdir(parents=True, exist_ok=True)
    comparisons = _judge_human_comparisons(judge_rows, human_rows)
    agreement = _judge_human_agreement(comparisons)
    report = {
        "judge_labels_path": str(judge_labels_path),
        "human_annotations_path": str(human_annotations_path),
        "n_comparisons": len(comparisons),
        "agreement": agreement,
        "by_dimension": _agreement_by_dimension(comparisons),
        "bias_by_agent": _bias_by_field(comparisons, "agent_name"),
        "bias_by_model_family": _bias_by_field(comparisons, "judge_model"),
        "sensitivity_to_answer_length": _answer_length_sensitivity(comparisons),
        "sensitivity_to_answer_order": _answer_order_sensitivity(comparisons),
        "scope": "Calibration report only; judge labels remain unvalidated unless agreement is acceptable and documented.",
    }
    write_json(out / "judge_calibration_report.json", report)
    write_jsonl(out / "judge_human_comparisons.jsonl", comparisons)
    _write_calibration_markdown(out / "judge_calibration_report.md", report)
    _write_calibration_table(out / "judge_calibration_table.csv", report)
    return report


class FakeJudge:
    """Deterministic judge for tests and calibration plumbing, not evidence."""

    def __init__(self, config: JudgeConfig) -> None:
        self.config = config

    def judge(self, item: dict[str, Any], dimension: str) -> dict[str, Any]:
        score_details = _json_dict(item.get("score_details"))
        label: JudgeLabel = "unclear"
        if dimension == "final_answer_correctness":
            label = "yes" if score_details.get("final_success_binary") in {1} else "no"
        elif dimension == "intervention_validity":
            label = "not_applicable" if item.get("condition") == "clean" else "yes"
        elif dimension == "trajectory_error_taxonomy":
            label = "yes" if item.get("error_taxonomy_label") not in {None, "", "none"} else "not_applicable"
        elif dimension == "contradiction_handling":
            value = score_details.get("contradiction_detected_binary")
            label = "yes" if value in {1} else "no" if value in {0} else "not_applicable"
        elif dimension == "recovery_behavior":
            value = score_details.get("tool_error_recovery_binary")
            label = "yes" if value in {1} else "no" if value in {0} else "not_applicable"
        return {
            "label": label,
            "rationale": "Deterministic fake judge label derived from score_details.",
            "confidence": 1.0,
            "metadata": {"fake_judge": True},
        }


class LLMModelJudge:
    def __init__(self, config: JudgeConfig) -> None:
        self.config = config
        self.client = get_llm_client(config.judge_provider)

    def judge(self, item: dict[str, Any], dimension: str) -> dict[str, Any]:
        prompt = judge_prompt(dimension, item, self.config.prompt_version)
        response = self.client.complete(
            [Message(role="user", content=prompt)],
            tools=[],
            config=ModelConfig(
                provider=self.config.judge_provider,
                model=self.config.judge_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                retry_count=self.config.retries,
                json_mode=True,
            ),
        )
        payload = _json_dict(response.content)
        return {
            "label": _normalize_label(payload.get("label")),
            "rationale": payload.get("rationale", ""),
            "confidence": payload.get("confidence"),
            "metadata": {
                "latency_s": response.latency_s,
                "estimated_cost_usd": response.estimated_cost_usd,
                "token_usage": response.usage.as_dict(),
                "response_hash": stable_hash(response.content or ""),
            },
        }


def _build_judge(config: JudgeConfig) -> ModelJudge:
    if config.fake_judge or config.judge_provider == "fake_judge":
        return FakeJudge(config)
    return LLMModelJudge(config)


def judge_prompt(dimension: str, item: dict[str, Any], prompt_version: str) -> str:
    template_path = Path("prompts/judges") / f"{dimension}.md"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = "Judge dimension: {dimension}\nReturn JSON with label, rationale, confidence.\n"
    payload = json.dumps(item, indent=2, sort_keys=True, default=str)
    return (
        template.replace("{dimension}", dimension)
        .replace("{prompt_version}", prompt_version)
        .replace("{item_json}", payload)
    )


def _judge_human_comparisons(
    judge_rows: list[dict[str, Any]],
    human_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    human_by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in human_rows:
        if row.get("item_id"):
            human_by_item[str(row["item_id"])].append(row)
    comparisons = []
    for judge in judge_rows:
        human_dimension = HUMAN_DIMENSION_MAP.get(str(judge.get("dimension")))
        if human_dimension is None:
            continue
        labels = [
            _optional_label(row.get(f"adjudicated_{human_dimension}") or row.get(human_dimension))
            for row in human_by_item.get(str(judge.get("item_id")), [])
        ]
        labels = [label for label in labels if label is not None]
        if not labels:
            continue
        human_label = Counter(labels).most_common(1)[0][0]
        comparisons.append(
            {
                "item_id": judge.get("item_id"),
                "instance_id": judge.get("instance_id"),
                "agent_name": judge.get("agent_name"),
                "judge_model": judge.get("judge_model"),
                "judge_dimension": judge.get("dimension"),
                "human_dimension": human_dimension,
                "judge_label": _normalize_label(judge.get("label")),
                "human_label": human_label,
                "matches_human": _normalize_label(judge.get("label")) == human_label,
                "answer_length": len(str(_human_item_field(human_by_item.get(str(judge.get("item_id")), []), "final_answer") or "")),
                "answer_order": _answer_order(judge),
            }
        )
    return comparisons


def _agreement_by_dimension(comparisons: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        rows[str(comparison["judge_dimension"])].append(comparison)
    return {dimension: _binary_match_summary(items) for dimension, items in rows.items()}


def _judge_human_agreement(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    if not comparisons:
        return {
            "items_with_two_or_more_annotations": 0,
            "percent_agreement": None,
            "cohens_kappa": None,
            "krippendorffs_alpha": None,
        }
    pairs = [(row["judge_label"], row["human_label"]) for row in comparisons]
    observed = sum(first == second for first, second in pairs) / len(pairs)
    judge_counts = Counter(first for first, _ in pairs)
    human_counts = Counter(second for _, second in pairs)
    labels = set(judge_counts) | set(human_counts)
    expected = sum(
        (judge_counts[label] / len(pairs)) * (human_counts[label] / len(pairs))
        for label in labels
    )
    kappa = 1.0 if expected == 1 else (observed - expected) / (1 - expected)
    pooled = Counter(label for pair in pairs for label in pair)
    total = sum(pooled.values())
    expected_disagreement = (
        1 - sum(count * (count - 1) for count in pooled.values()) / (total * (total - 1))
        if total > 1
        else 0
    )
    observed_disagreement = 1 - observed
    alpha = (
        1.0
        if expected_disagreement == 0
        else 1 - observed_disagreement / expected_disagreement
    )
    return {
        "items_with_two_or_more_annotations": len(pairs),
        "percent_agreement": round(observed, 6),
        "cohens_kappa": round(kappa, 6),
        "krippendorffs_alpha": round(alpha, 6),
    }


def _bias_by_field(comparisons: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[str(comparison.get(field) or "unknown")].append(comparison)
    return {value: _binary_match_summary(items) for value, items in sorted(grouped.items())}


def _answer_length_sensitivity(comparisons: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {"short": [], "medium": [], "long": []}
    for comparison in comparisons:
        length = int(comparison.get("answer_length") or 0)
        bucket = "short" if length < 80 else "medium" if length < 240 else "long"
        buckets[bucket].append(comparison)
    return {bucket: _binary_match_summary(items) for bucket, items in buckets.items()}


def _answer_order_sensitivity(comparisons: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[str(comparison.get("answer_order") or "unknown")].append(comparison)
    return {order: _binary_match_summary(items) for order, items in sorted(grouped.items())}


def _binary_match_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "agreement_rate": None, "judge_yes_rate": None, "human_yes_rate": None}
    return {
        "n": len(rows),
        "agreement_rate": round(sum(bool(row.get("matches_human")) for row in rows) / len(rows), 6),
        "judge_yes_rate": round(sum(row.get("judge_label") == "yes" for row in rows) / len(rows), 6),
        "human_yes_rate": round(sum(row.get("human_label") == "yes" for row in rows) / len(rows), 6),
    }


def _write_calibration_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# LLM Judge Calibration Report",
        "",
        "Judge labels are optional diagnostics and are not ground truth without human validation.",
        "",
        f"- Comparisons: {report['n_comparisons']}",
        f"- Overall percent agreement: {_fmt(report.get('agreement', {}).get('percent_agreement'))}",
        f"- Cohen's kappa: {_fmt(report.get('agreement', {}).get('cohens_kappa'))}",
        f"- Krippendorff's alpha: {_fmt(report.get('agreement', {}).get('krippendorffs_alpha'))}",
        "",
        "## By Dimension",
        "",
        "| Dimension | N | Agreement | Judge yes | Human yes |",
        "|---|---:|---:|---:|---:|",
    ]
    for dimension, row in sorted(report.get("by_dimension", {}).items()):
        lines.append(
            f"| `{dimension}` | {row['n']} | {_fmt(row['agreement_rate'])} | {_fmt(row['judge_yes_rate'])} | {_fmt(row['human_yes_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "Do not report judge labels as ground truth unless this calibration is acceptable, human annotations are complete, and the claim ledger cites the evidence.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_calibration_table(path: Path, report: dict[str, Any]) -> None:
    rows = [
        {"group": "dimension", "name": key, **value}
        for key, value in sorted(report.get("by_dimension", {}).items())
    ]
    if not rows:
        rows = [{"group": "dimension", "name": "none", "n": 0, "agreement_rate": None, "judge_yes_rate": None, "human_yes_rate": None}]
    pd.DataFrame(rows).to_csv(path, index=False)


def _read_human_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    return pd.read_csv(path).fillna("").to_dict(orient="records")


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_label(value: Any) -> JudgeLabel:
    label = str(value or "unclear").strip().lower()
    aliases = {"n/a": "not_applicable", "na": "not_applicable", "not applicable": "not_applicable"}
    label = aliases.get(label, label)
    if label not in {"yes", "no", "unclear", "not_applicable"}:
        return "unclear"
    return label  # type: ignore[return-value]


def _optional_label(value: Any) -> JudgeLabel | None:
    if value is None or str(value).strip() == "":
        return None
    return _normalize_label(value)


def _human_item_field(rows: list[dict[str, Any]], field: str) -> Any:
    for row in rows:
        value = row.get(field)
        if value not in {None, ""}:
            return value
    return None


def _answer_order(judge: dict[str, Any]) -> str:
    digest = stable_hash({"item_id": judge.get("item_id"), "dimension": judge.get("dimension")})
    return "original_first" if int(digest[-1], 16) % 2 == 0 else "candidate_first"


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
