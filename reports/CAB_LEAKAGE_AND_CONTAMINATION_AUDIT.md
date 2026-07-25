# CAB Leakage and Contamination Audit

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

## Verdict

Static reports present: 4/4. Blocker clusters: 0. Manual-review clusters: 88. Static clearance does not replace human review.

## Threat model

| Class | Threat | Implemented boundary |
|---|---|---|
| A | Gold-answer leakage | visible answer/fragment/path/debug payload scans; hidden evaluator context remains isolated |
| B | Intervention-label leakage | namespaces do not expose family in task IDs; visible payload linter blocks label cues |
| C | Cross-condition leakage | fresh conversations/tools/memory/workspaces/cache namespaces required per condition |
| D | Split/selection leakage | six immutable hashed roles; cross-role base-task overlap is blocked |
| E | Scorer leakage | typed preregistered policies; immutable raw trajectories; no model-specific tolerance |
| F | Tool/environment leakage | agent-visible schema checks and guarded fixture paths |
| G | Prompt injection | task/artifact/notebook strings, code, path, formula, and serialization surfaces scanned |
| H | Provider/adapter leakage | equivalent budgets/retries/context required; run-specific approval absent |
| I | Human-review leakage | model identity/output separation; proxy/template rows rejected |
| J | Public-release contamination | development/harness/hidden/post-study release tiers |
| K | Pretraining contamination | fresh namespacing, delayed challenge pack, provenance; mitigation only, never elimination |

## Pack-level static audits

| Study | Blocker clusters | Needs review | Warning clusters | Report |
|---|---:|---:|---:|---|
| `compact20_pilot` | 0 | 40 | 62 | `audits/max_ceiling/compact20_source/leakage/static_leakage_report.json` |
| `scale100_confirmatory` | 0 | 0 | 26 | `audits/max_ceiling/scale100_confirmatory_v1_candidate/leakage/static_leakage_report.json` |
| `naturalistic_transfer` | 0 | 9 | 27 | `audits/max_ceiling/naturalistic_transfer_v1_candidate/leakage/static_leakage_report.json` |
| `main500_confirmatory` | 0 | 39 | 58 | `audits/max_ceiling/main500_confirmatory_v1_candidate/leakage/static_leakage_report.json` |

## Finding contract

Each canonical gate finding carries file/path, task or instance ID where available, visible field, severity, leakage class, suggested repair, automatic-repair state, and unresolved human-review state. Repeated raw symptoms are clustered so count volume is not mistaken for independent defects.

## Split and freeze result

- Registry: `data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json`
- Roles: 6
- Cross-role base-task overlaps: 0
- Recorded/live hash issues: 0
- Any membership/hash change requires a new version and review before execution.
- Held-out answer keys and complete payloads remain delayed/hidden until the post-study release tier.

## Residual blockers

- Resolve all human-review queues before slice lock.
- Perform two-reviewer intervention-isolation review and adjudication.
- Treat public/pretraining contamination as a limitation, not a solved property.
- Rerun the leakage gate after any prompt, task, tool, notebook, or scorer change.
