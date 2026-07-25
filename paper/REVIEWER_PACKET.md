# Reviewer Packet (CausalAgentBench)

**Status:** Pre-submission scaffold. **No empirical results are claimed here.**

## What the benchmark tests

CausalAgentBench evaluates **tool-using agents** on paired clean/intervention instances across synthetic domains. It measures:

- Final task success under clean vs intervened conditions
- Trajectory-level skills (tool use, recovery, memory verification, contradiction handling, stopping)
- Agent Causal Robustness Score (ACRS)—a composite emphasizing intervention performance

## What the benchmark does **not** test

- Real-world web browsing, live APIs, or human users in the loop
- Open-ended creative tasks without machine-checkable success criteria
- Security exploits, multi-agent negotiation, or long-horizon production deployments
- General intelligence beyond the defined synthetic tool environments

## Why paired interventions matter

Comparing clean vs intervention instances on the **same base task** holds the user goal stable while changing one designed factor (tool availability, memory, observations, etc.). This supports **bounded causal language**: we study sensitivity to controlled perturbations, not unrestricted “causal discovery” in the wild.

## Why synthetic tools are used

Synthetic tools provide:

- Deterministic ground truth and reproducibility without paid APIs
- Safe workflows (draft-only email, booking stub, no live sending)
- Controlled corruption/conflict injection with auditable patches

Tradeoff: external validity is limited; mini-study / web-shadow tracks are planned separately.

## How causal language is bounded

We claim **controlled intervention effects** on benchmark-defined skills—not causal effects in real user deployments. Wording like “isolates skill components” applies to **designed factors in synthetic tasks**, subject to intervention audit and human validation (C10).

## What ACRS is and is not

**ACRS (Agent Causal Robustness Score)** combines clean and intervention performance with trajectory diagnostics. It is:

- A **benchmark-specific** composite for ranking agents on this suite
- Not a universal “agent IQ” or real-world readiness score
- Sensitive to intervention family weighting and scorer version (`deterministic_heuristic_v1`)

## How trajectory diagnostics are validated

1. **Mock diagnostic agents** (`mock_behavior_agent`) emit known failure patterns without LLM calls.
2. **Engineering tests** assert metric signals (e.g., high unnecessary tool rate for `mock_tool_overuser`).
3. **Human validation** (planned) will measure agreement on a stratified sample—required before C3/C10 `supported`.

Mock/stub outputs are labeled `engineering_only` / `not_real_llm_behavior`.

## How human validation will work

- Stratified sample across domains and intervention families
- Annotators tag failure modes ([docs/FAILURE_TAXONOMY.md](../docs/FAILURE_TAXONOMY.md))
- Agreement metrics exported to `tables/table5_human_validation_agreement.csv`
- Protocol: [docs/HUMAN_VALIDATION_GUIDELINES.md](../docs/HUMAN_VALIDATION_GUIDELINES.md)

## What counts as evidence

See [docs/EVIDENCE_LEVEL_POLICY.md](../docs/EVIDENCE_LEVEL_POLICY.md). Summary:

| Level | Paper-ready? |
|---|---|
| dry_run / stub / mock | No |
| local preliminary | No (limitations only) |
| provider pilot | Pilot wording only |
| main_experiment + human_validated | Yes, per claim ledger |

Claim ledger: [docs/claim_ledger.json](../docs/claim_ledger.json). **C1–C8, C10 are planned—not supported.**

## Reproducibility checklist

- [ ] Frozen dataset manifest (`data/frozen/.../freeze_manifest.json`)
- [ ] Config hash in run metadata
- [ ] `make fast-check` passes
- [ ] Intervention + isolation audits pass
- [ ] Complete run dirs (no `INCOMPLETE_RUN.json` for cited runs)
- [ ] Scorer version recorded in scores
- [ ] Claim ledger links runs → tables/figures

Commands: [docs/REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md), [artifact/README.md](../artifact/README.md)

## Known limitations

- Synthetic tools and templated tasks limit ecological validity
- Heuristic trajectory metrics may disagree with human judgment
- Provider/model churn requires frozen model IDs and dated snapshots
- Interrupted local pilots are **not** scientific evidence

## Expected reviewer concerns → responses

| Concern | Response |
|---|---|
| “Interventions change more than one thing.” | `audit-interventions` + `audit_intervention_isolation.py`; family audit guide; human audit sample |
| “Metrics are hand-crafted.” | Mock diagnostic suite + planned human agreement (C3) |
| “Synthetic isn’t realistic.” | Acknowledged; mini-study/web-shadow tracks; claims bounded to benchmark |
| “ACRS hides failures.” | Trajectory vs final-success disagreement figures; failure gallery |
| “No strong model results yet.” | Correct—paper scaffold; claim ledger gates prevent overclaim |
| “Data contamination?” | `audit-contamination`, frozen splits, held-out templates |

## Related documents

- [docs/BENCHMARK_TAXONOMY.md](../docs/BENCHMARK_TAXONOMY.md)
- [docs/FAILURE_TAXONOMY.md](../docs/FAILURE_TAXONOMY.md)
- [experiments/MAIN_EXPERIMENT_GATE.md](../experiments/MAIN_EXPERIMENT_GATE.md)
- [docs/NEURIPS_ARTIFACT_CHECKLIST.md](../docs/NEURIPS_ARTIFACT_CHECKLIST.md)
- [reviews/REVIEWER_ATTACK_MATRIX.md](../reviews/REVIEWER_ATTACK_MATRIX.md)
