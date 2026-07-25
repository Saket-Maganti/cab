# Experiment State Machine

Maps run directories and experiment stages to allowed actions and claims.

## States

| State | Entry criteria | Allowed commands | Forbidden commands | Allowed claims | Required artifacts | Next state | Failure recovery |
|---|---|---|---|---|---|---|---|
| **not_started** | No run dir | `plan-run`, `dry-run`, `validate-config` | `run`, `score`, `export-paper-assets` | None | Config YAML | `planned` | N/A |
| **planned** | Config validated | `plan-run`, `dry-run`, readiness scripts | `run` without approval for heavy configs | Engineering planning only | `validate-config` pass | `dry_run_ready` | Fix config |
| **dry_run_ready** | Dry-run report exists | `dry-run`, `plan-run` | Treat dry-run as evidence | Dry-run wording only | `dry_run_report.json` | `zero_cost_ready` | Re-run dry-run |
| **zero_cost_ready** | Zero-cost checks pass | stub/mock `run`, audits | Paid/local without approval | `engineering_only` | `check_zero_cost_readiness` | `running` / `complete_engineering` | Fix config/budget |
| **running** | Checkpoint in progress | `monitor`, `run-status` | `score` as final evidence | None | `checkpoint.json` | `complete_*` / `interrupted` | `mark-interrupted` |
| **interrupted** | `INCOMPLETE_RUN.json` or partial checkpoint | `mark-interrupted`, `run-status` | `score/export` without `--allow-incomplete` | None | Interruption record | `running` (resume) or discard | Document reason; do not cite |
| **complete_engineering** | Complete stub/mock run | `generate-report`, `failure-gallery` | Promote claims to `supported` | `engineering_only`, mock diagnostic | `run_metadata.json`, scores | `provider_pilot_complete` (different run) | Re-run mock diagnostic |
| **complete_preliminary** | Complete local run | `generate-report` with preliminary label | Main-scale claims | `local_preliminary` wording | Model ID in metadata | `provider_pilot_complete` | Do not merge with provider tables |
| **provider_pilot_complete** | Complete provider pilot | `analyze`, `export-paper-assets` (pilot) | C1–C8 `supported` without main | Pilot wording | Complete run + config hash | `human_validation_ready` | Extend pilot if infra failures |
| **human_validation_ready** | Annotation export exists | `summarize-human-validation` | Full-benchmark human claims | Validation subset | Annotation files | `main_experiment_ready` | Expand sample |
| **main_experiment_ready** | Main gate GO + complete main run | Full analysis pipeline | Claims beyond ledger | Per-claim `supported` | Frozen data + main run | `submission_ready` | Lock scorer version |
| **submission_ready** | All submission checks pass | Release manifest, camera-ready | Placeholder numbers | Ledger-approved only | Full artifact set | Release | Fix blockers from readiness script |
| **blocked** | Policy violation or unknown status | Diagnostics only | All evidence export | None | Issue log | Prior safe state | `check_experiment_state.py` |

## Validator

```bash
python3 scripts/check_experiment_state.py --run-dir results/<run_dir>
```

## Related

- [docs/EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md)
- [experiments/MAIN_EXPERIMENT_GATE.md](../experiments/MAIN_EXPERIMENT_GATE.md)
- [experiments/COMMAND_PLANS.md](../experiments/COMMAND_PLANS.md)
