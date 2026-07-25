# Model Contamination and Memorization Tests

Causal Agent Bench includes **pre-release contamination audits** to prepare for future concerns about training-data overlap, split leakage, and benchmark gaming. These checks are heuristic guardrails, not proof that a model has not memorized tasks.

## What the audit covers

| Check | Purpose |
| --- | --- |
| **Template fingerprinting** | Stable hash per task template (domain, tools, instruction skeleton) to detect cross-split template collisions |
| **Canary strings** | Deterministic `CAB-CANARY-<version>-<hash>` tokens on hidden splits (`test`, `heldout_templates`) |
| **Near-duplicate detection** | Token Jaccard similarity of instructions across splits (default threshold 0.85) |
| **Prompt leakage** | Whether hidden ground truth, intervention metadata, or tool catalog text appears in agent-visible context |

## Public vs hidden splits

See [PUBLIC_VS_HIDDEN_SPLITS.md](PUBLIC_VS_HIDDEN_SPLITS.md) and [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md).

- **Public / disclosed:** `dev`, `pilot`, `validation`, and alias `public_dev`
- **Hidden / held-out:** `test` (headline evaluation), `heldout_templates` (reserved templates)

Canary strings are assigned only to hidden-split base tasks (`metadata.contamination_canary`). The audit fails if any canary appears in public-split text.

## Running the audit

```bash
python -m causal_agent_bench audit-contamination \
  --benchmark-dir data/frozen/pilot_v0.1

python scripts/audit_contamination.py --benchmark-dir data/processed/pilot_v0_1
```

`freeze-dataset` now:

1. writes release splits;
2. injects canary metadata on hidden base tasks;
3. emits `contamination_audit_report.json` and `.md` beside the frozen bundle.

Freeze does **not** fail solely on contamination warnings; inspect the report before claims.

## Agent-visible context model

Leakage checks mirror the JSON payload exposed to LLM tool agents (`llm_agents._task_context`): user instruction, success criteria, intervention family, and `intervention_expected_behavior`.

**Known scaffold exposure:** `expected_behavior` is intentionally included for diagnostic agents. The audit records a **warning**, not an error. Do not use this scaffold for blind model ranking without ablation.

## Contamination risks

1. Public instructions and tool schemas may exist in pretraining corpora.
2. Method development on `pilot` can overfit template families before `test` evaluation.
3. Repeated `test` submissions enable adaptive overfitting.
4. Oracle or hidden-metadata exposure inflates scores.
5. Near-duplicate instructions shrink effective held-out size.

## Mitigations

1. Version datasets with `dataset_hash` and frozen manifests.
2. Report `eval_split` on every leaderboard export.
3. Exclude oracle agents from rankings.
4. Run contamination audits before freeze and before headline claims.
5. Disclose prompts, model versions, cost, and retries (see [LEADERBOARD_PROTOCOL.md](LEADERBOARD_PROTOCOL.md)).

## Remaining limitations

- Synthetic tasks are not live web or enterprise environments.
- Canary and near-duplicate checks are necessary but not sufficient.
- Shared tool catalogs may correlate with public API documentation.
- Human validation is still required before strong robustness claims.
- **Stub/smoke runs** validate engineering only; they are not memorization evidence.

## Report artifacts

Each audit writes:

- `contamination_audit_report.json` — machine-readable findings with provenance
- `contamination_audit_report.md` — reviewer-facing summary

Link these paths in the claim ledger when citing contamination posture.
