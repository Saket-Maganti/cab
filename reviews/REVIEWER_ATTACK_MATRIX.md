# Reviewer attack matrix (infrastructure-focused)

| Attack | Response | Status |
|--------|----------|--------|
| "Results from stub runs" | `evidence_scope` + export guards; stub/mock labeled engineering-only | Mitigated |
| "Incomplete run scored as final" | `score/analyze/export` refuse incomplete by default | Mitigated |
| "Resume corrupted config" | Config-hash check; `--force-resume` explicit | Mitigated |
| "Oracle in main table" | Oracle excluded from leaderboard/main tables | Existing |
| "No reproducibility metadata" | `run_metadata.json`, config hash, git commit | Existing |
| "Long local runs without warning" | `plan-run` + limits + docs | Mitigated |
| "Paid calls without approval" | `allow_paid_calls` gate + budget preflight | Existing |
| "Human validation claimed without data" | Claim ledger stays planned; sampling infra only | Partial |
| "NeurIPS-scale claims from pilot" | C1–C8/C10 not auto-supported; Prompt 67 blocked | Policy |

See also: `reviews/reviewer_attack_response_matrix.md`, `scripts/check_evidence_safety.py`
