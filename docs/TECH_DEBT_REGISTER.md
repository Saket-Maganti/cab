# Tech Debt Register

Track non-blocking issues to burn down between experiment phases. Updated: 2026-05-20 (Phase 7).

| Debt ID | Area | Issue | Impact | Priority | Suggested Fix | Status |
|---|---|---|---|---|---|---|
| TD-001 | Experiments | No completed provider-backed pilot | Blocks C1–C8 evidence | P0 | Run bounded pilot with budget approval | open |
| TD-002 | Validation | Human validation annotations missing | Blocks C3, C10 | P0 | Export sample + annotate per protocol | open |
| TD-003 | Paper | Placeholders `[N]`, `[M]`, `[K]`, `[X]`, `[rho]` unfilled | Submission blocked | P0 | Fill from verified main/pilot only | open |
| TD-004 | Runs | Long local Ollama runs slow / interrupted | Misleading partial artifacts | P1 | Mark interrupted; do not score as evidence | mitigated |
| TD-005 | Environment | pyenv vs system `python3` confusion | Install friction | P2 | README + doctor check; document in ONBOARDING | partial |
| TD-006 | Docs | Docs sprawl (~65 markdown files) | Navigation overhead | P2 | docs/README hub + DOC_STATUS_BOARD | mitigated |
| TD-007 | Artifacts | Root `figures/` may contain pre-pilot exports | Overclaim risk | P1 | GENERATED_FILES_POLICY; don't commit new exports | mitigated |
| TD-008 | Evidence | Mock/stub vs real LLM separation | Reviewer confusion | P1 | Evidence policy + safety scripts | mitigated |
| TD-009 | Configs | Some paid configs lack `description` field | Audit warnings | P3 | `audit_configs.py --apply-safe-fixes` | open |
| TD-010 | Configs | Inconsistent budget block shapes | Cost guard drift | P2 | Standardize on `budget.max_total_usd` | open |
| TD-011 | CI | Clean-checkout proof not automated | Reproducibility gap | P2 | artifact-deterministic in CI optional job | open |
| TD-012 | Bibliography | Related-work relevance final pass | Paper weakness | P2 | RELATED_WORK_RELEVANCE_CHECKLIST | open |
| TD-013 | Release | Release manifest must be regenerated on hash drift | Release friction | P3 | `make release-check` in precommit optional | mitigated |
| TD-014 | Testing | Full pytest suite slower than fast-check | Dev velocity | P3 | Keep fast-check subset; mark slow tests | mitigated |
| TD-015 | Terminology | `docs/TERMINOLOGY.md` overlaps GLOSSARY | Duplication | P3 | Point TERMINOLOGY → GLOSSARY | open |
| TD-016 | Status | Multiple status docs (NEXT_STEPS, MILESTONES) | Stale copies | P2 | `generate_project_status.py` as canonical | mitigated |
| TD-017 | Incomplete runs | Interrupted runs in results index | Index noise | P2 | mark-interrupted + index warnings | mitigated |
| TD-018 | Matplotlib | Fontconfig cache warnings in sandbox | Noisy logs | P4 | Document MPLCONFIGDIR in figure README | mitigated |
| TD-019 | Makefile | `smoke` target runs `run` | Accidental model run | P2 | Document as unsafe in CLI_REFERENCE | mitigated |
| TD-020 | Claims | Legacy table/figure paths in claim ledger | Broken links pre-pilot | P2 | Update after first verified export | open |

**Priority:** P0 = blocks claims; P1 = evidence integrity; P2 = polish; P3 = convenience; P4 = cosmetic.

Review after each build phase or pilot milestone.
