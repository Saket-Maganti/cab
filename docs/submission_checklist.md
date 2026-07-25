# Camera-Ready Submission Checklist

Use this checklist before claiming NeurIPS Evaluations & Datasets (ED) submission readiness.  
Automated helpers: `make submission-precheck` (draft) · `make submission-check` (strict) · `make release-dry-run`

| # | Item | Script / command | Draft OK? | Submission |
| --- | --- | --- | --- | --- |
| 1 | Paper source present (`paper/main.tex`) | `check_repo_packaging.py` | ✓ | Required |
| 2 | Paper compiles to PDF | `make paper` or `camera_ready_precheck.py --compile-paper` | Optional | Required |
| 3 | No bracketed result placeholders | `check_paper_placeholders.py --mode submission` | ✗ | Required |
| 4 | No unsupported `supported` claims in ledger | `check_claim_ledger.py` + `check_paper_claims.py` | ✗ | Required |
| 5 | No broken citations / citation TODOs | `check_citation_todos.py` | ✓ | Required |
| 6 | No `\todo{}` / TODO markers in paper | `check_todos.py` | ✗ | Required |
| 7 | Figures/tables exist; inputs resolve | `check_paper_assets.py` | ✓ | Required |
| 8 | Figures/tables linked to verified run | `docs/PAPER_EVIDENCE_MAPPING.json` + `fill-paper-from-run` | Warn | Required |
| 9 | Code imports from clean path | `check_package_import.py` | ✓ | Required |
| 10 | `pip install -e ".[dev]"` + smoke CLI | `make smoke` | ✓ | Required |
| 11 | Dataset freeze manifest exists | `check_repo_packaging.py` | ✓ | Required |
| 12 | README quickstart (install + smoke) | `check_repo_packaging.py` | ✓ | Required |
| 13 | LICENSE present | `check_repo_packaging.py` | ✓ | Required |
| 14 | Ethics/limitations doc present | `check_repo_packaging.py` | ✓ | Required |
| 15 | Release manifest + cards valid | `make release-check` | ✓ | Required |
| 16 | Reviewer attack matrix maintained | `check_reviewer_proofing.py` | ✓ | Required |
| 17 | Oracle excluded from main rankings | table exporters + §6 | ✓ | Required |
| 18 | Human validation complete (if claimed) | §8 + Table 5 | ✗ | Required |
| 19 | Non-oracle LLM runs with metadata | `fill-paper-from-run` | ✗ | Required |
| 20 | Cost/latency reported for LLM runs | `docs/COST_LATENCY.md` | ✗ | Required |

## Quick commands

```bash
# Draft iteration (expected to pass on scaffold with warnings)
make submission-precheck

# Strict gate (expected to fail until results + validation are complete)
make submission-check

# Release bundle + packaging + tests
make release-dry-run
```

## Current scaffold status (honest)

- Items **3, 6, 8, 18, 19, 20** are **not** submission-ready today.
- Stub/smoke runs must **not** satisfy rows 8 or 19 (`scientific_evidence_from_stub_runs: forbidden`).
- See `reviews/reviewer_attack_response_matrix.md` for reviewer-facing mitigations.

## Related docs

- `docs/REVIEWER_PROOFING.md`
- `docs/PAPER_RESULTS_FILL.md`
- `docs/claim_ledger.json`
- `release/release_manifest.json`
