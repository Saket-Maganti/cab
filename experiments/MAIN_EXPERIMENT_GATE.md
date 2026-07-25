# Main Experiment Gate

**Do not start the main paid/provider experiment until this gate returns GO.**

## Prerequisites checklist

| # | Requirement | Verification command / artifact |
|---|---|---|
| 1 | Dataset frozen | `data/frozen/<version>/freeze_manifest.json` exists |
| 2 | Intervention audit passed | `python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/<version>` |
| 3 | Isolation audit passed | `python3 scripts/audit_intervention_isolation.py --dataset data/frozen/<version>/instances.jsonl` |
| 4 | Provider pilot completed | Complete run in `results/` with `commercial_api_pilot_unvalidated` or approved pilot scope |
| 5 | Provider/model list frozen | `configs/providers.yaml` + experiment config committed; model IDs pinned |
| 6 | Prompt templates frozen | Agent prompt files hashed in config metadata |
| 7 | Run budget approved | Budget block in config; `allow_paid_calls: true` only with explicit approval |
| 8 | Human validation sample plan | `docs/HUMAN_VALIDATION_GUIDELINES.md` + export config ready |
| 9 | Scoring/analysis locked | Scorer version tagged; `make fast-check` green |
| 10 | Claim ledger clean | `python3 scripts/check_claim_ledger.py --mode submission` |
| 11 | Paper placeholders known | `python3 scripts/check_paper_placeholders.py --mode submission` |
| 12 | CI / fast-check passing | `make fast-check` |
| 13 | Security/privacy clean | `make security-check` |
| 14 | Expected runtime approved | `plan-run` output reviewed for trajectory count × cost |

## Decision criteria

### GO

All of:

- Items 1–3 pass with zero `fail`-level isolation issues (warnings documented)
- At least one **complete** provider pilot run on frozen pilot split
- Claim ledger has **no** `supported` claims without evidence (or all downgraded to `planned`)
- Budget sign-off recorded in experiment registry
- Human validation export dry-run succeeds

### NO-GO

Any of:

- Frozen dataset missing or differs from audited processed build
- Intervention audit failures unresolved
- Mock/stub/local interrupted runs cited as evidence
- `allow_paid_calls: true` without budget approval
- Claim ledger C1–C8/C10 marked `supported` prematurely
- `check_submission_readiness.py` blockers unresolved for target venue

### DEFER

- Pilot complete but human validation not started → defer main until annotation plan ready
- Provider pilot shows &gt;50% infrastructure failures → defer until runner stable
- Scorer version change pending → defer until mock diagnostic + human calibration rerun

## Current status (engineering snapshot)

- **Gate status:** NO-GO (deterministic prototype; no provider pilot; human validation pending)
- **Safe parallel work:** mock diagnostics, docs, audits, stub runs—**not** main experiment

## Commands before GO

```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
python3 -m causal_agent_bench plan-run --config configs/main_500_multi_provider.yaml
python3 scripts/check_claim_ledger.py --mode submission
```

## Related

- [experiments/MAIN_EXPERIMENT_READINESS_CHECKLIST.md](MAIN_EXPERIMENT_READINESS_CHECKLIST.md)
- [experiments/EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md)
- [docs/EVIDENCE_LEVEL_POLICY.md](../docs/EVIDENCE_LEVEL_POLICY.md)
