# Recovery-Aware Agent Control

Status: `DESIGN_ONLY` / `ENGINEERING_ONLY`. The deterministic fixtures are
`FIXTURE_ONLY`. No RAAC effectiveness claim is supported until approved real
model execution, audit, and evidence promotion are complete.

Recovery-Aware Agent Control (RAAC) is a model-agnostic controller for bounded
recovery, verification, clarification, and abstention in tool-using agents. It
operates only on information available in the interaction: tool errors,
timeouts, parsed outputs, public schemas, timestamps, repeated observations,
the agent's own success claim, and remaining budgets. It does not receive the
benchmark condition, intervention family or ID, expected behavior, gold
answer, hidden ground truth, answer key, scorer state, or evaluator metadata.

## Public implementation

The canonical implementation is `src/causal_agent_bench/raac/`:

| Module | Contract |
|---|---|
| `types.py` | Typed states, signals, decisions, reasons, budgets, and variants |
| `state_machine.py` | One fail-closed transition graph |
| `signals.py` | Observable-only envelope, hidden-metadata scrubber, anomaly detector |
| `contracts.py` | Compute ceilings and realized overhead accounting |
| `policy.py` | LIGHT, FULL, ablations, and baseline policies |
| `controller.py` | Deterministic policy execution, loop bound, checkpoint/resume |
| `adapters.py` | Canonical agent, provider, and open-model extension points |
| `fixtures.py` | Model-free deterministic scenarios |
| `opportunities.py` | Evaluator-side opportunity flags from public RAAC traces |

## State machine

The typed states are:

`PLAN`, `ACT`, `VALIDATE_OBSERVATION`, `DETECT_ANOMALY`, `RETRY`,
`ALTERNATE_ROUTE`, `CROSS_CHECK`, `CLARIFY`, `ABSTAIN`, `FINAL_VERIFY`,
`ANSWER`, and `TERMINATE`.

All legal edges live in the single `LEGAL_TRANSITIONS` registry. Unknown or
illegal edges raise an error. `TERMINATE` has no outgoing edge. Every decision
path has a hard bound derived from the compute contract, so a zero-cost action
cannot create an infinite loop.

The common path is:

```text
PLAN -> ACT -> VALIDATE_OBSERVATION -> DETECT_ANOMALY
```

From anomaly detection, the controller either returns to `ACT`, enters one
bounded recovery state, answers, abstains, or terminates an infrastructure
failure. `ANSWER` and `ABSTAIN` transition only to `TERMINATE`.

## Observable signals

RAAC recognizes the following typed signals:

- tool error and timeout;
- malformed output, missing required field, and schema mismatch;
- contradictory observation and inconsistent repeated result;
- stale timestamp, partial output, and impossible value;
- insufficient evidence and unverifiable success signal;
- exhausted token, tool, or retry budget;
- infrastructure failure.

`ObservationEnvelope.from_payload` uses a public allow-list. Nested hidden
fields are scrubbed before policy evaluation. Direct construction rejects extra
fields. Tests change hidden labels and gold values while holding public
observations fixed and require identical decisions.

## Typed decision record

Each decision contains:

- the decision and reason code;
- current and next state;
- triggering signal, if any;
- remaining budget snapshot after the action;
- an explicit action instruction;
- a deterministic trace index;
- the unchanged evidence class.

Decisions are: continue, retry same tool, use alternate tool, cross-check
source, verify current evidence, request clarification, qualified answer,
abstain, final verification, answer, and terminate infrastructure failure.

## Paper-ready pseudocode

```text
procedure RAAC(observation o, policy p, budget b, state s):
    require s is non-terminal
    s <- enter_validation_path(s)
    x <- sanitize_to_public_observables(o)
    signals <- detect_typed_anomalies(x, b)

    if infrastructure_failure in signals:
        d <- TERMINATE_INFRASTRUCTURE_FAILURE
    else if a declared budget is exhausted:
        d <- QUALIFIED_ANSWER if supported_candidate(x) else ABSTAIN
    else if no signals:
        d <- ANSWER if verifiable_success(x) else CONTINUE
    else:
        d <- policy_choice(signals, p)

    if cost(d) exceeds b:
        d <- bounded_fallback(d, p, x)
    consume(cost(d), b)
    s <- legal_transition(s, target_state(d))
    append_auditable_trace(d, signals, b, evidence_class)
    return d
```

The policy never branches on benchmark labels or gold. The evaluator may use
labels later when scoring treatment effects, but those fields are not in the
controller input type.

## Variants

`RAAC_LIGHT` permits one retry, one optional alternate route, one verification,
three extra model/tool calls in total, 384 tokens, and 30 seconds. It is the
default constrained-compute treatment.

`RAAC_FULL` permits two retries, two alternate routes, three verifications, one
clarification, eight extra model calls, six extra tool calls, 1,536 tokens, and
90 seconds.

The frozen ablations are `VERIFY_ONLY`, `RETRY_ONLY`, `ABSTAIN_ONLY`,
`NO_CROSS_CHECK`, `NO_ALTERNATE_ROUTE`, and `NO_FINAL_VERIFY`. Baseline
wrappers are direct answer, standard tool use, ReAct-style, self-check, and an
oracle engineering-only control. The oracle control is prevented from carrying
an evidence class above `FIXTURE_ONLY` or `ENGINEERING_ONLY`.

## Integration and traces

Runner configuration accepts a run-level `raac` block and a per-agent override.
When enabled, the canonical runner wraps `BaseAgent` with `RAACAgentWrapper`.
Same-tool retry and safe terminal actions are generic. Provider-specific and
open-model-specific actions use `ProviderRAACAdapter`,
`OpenModelRAACAdapter`, or the `RAACDirectiveConsumer` protocol.

Run metadata records the policy, policy hash, comparison mode, compute
contract, realized overhead, public trace, and evidence class. Trajectory v2
has root `raac_metadata` and step-level state, decision, signal, and trace index
fields. The run manifest has optional policy, comparison-mode, and overhead
fields; old manifests remain valid.

The scorer emits opportunity flags only. It does not infer effectiveness:
recovery, verification, clarification, and abstention opportunities are
reported with explicit denominators for later paired analysis.

## Deterministic fixtures

The fixture suite covers clean success, transient and persistent tool failure,
conflicting observations, stale memory, malformed and partial output,
premature success, insufficient evidence, clarification, correct and false
abstention, and alternate-route recovery. Fixtures exercise wiring and policy
invariants only. They are never scientific or paper-eligible evidence.
