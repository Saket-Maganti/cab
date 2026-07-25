# NeurIPS Submission Gate

**Current verdict: NOT READY**

This gate defines **necessary** conditions for empirical NeurIPS submission. Passing is **not sufficient** for acceptance.

---

## Gates (all must pass)

| # | Gate | Current status | Requirement |
|---|------|----------------|-------------|
| 1 | Dataset leakage clear | **pass** (static) | `blocker_cluster_count == 0` |
| 2 | Main dataset ready | **fail** | `main_200` / `main_v0_1_500` frozen |
| 3 | Provider runs complete | **fail** | `paper_eligible_runs > 0` |
| 4 | Paper assets eligible | **fail** | `eligible_empirical_assets > 0` |
| 5 | Human validation complete | **fail** | Completed annotations + agreement |
| 6 | Claim ledger supported | **fail** | C1–C8, C10 = `supported` |
| 7 | Release artifact packaged | **fail** | Public v1.0 bundle shipped |
| 8 | Reproducibility passed | **partial** | C9 engineering_only only |
| 9 | Paper no-overclaim check | **pass** (vacuous) | No empirical tables filled |
| 10 | Advisor/coauthor signoff | **fail** | Signed approval + completed runs |

**Gates passed:** ~3/10 with current evidence (leakage clear, C9 engineering reproducibility, no-overclaim vacuous pass)  
**Submission ready:** **false**  
**NeurIPS ready:** **false**

Regenerate: `python3 -m causal_agent_bench neurips-submission-gate`

---

## Generate gate report

```bash
python3 -m causal_agent_bench neurips-submission-gate --output-dir reports/neurips_submission_gate
```

Or inspect after `all-no-run-reports` (if integrated).

---

## What tiny pilot does NOT satisfy

- Gates 3, 4, 6 (headline claims)
- Gate 5 (human validation)
- Gate 7 (release)
- Gate 10 (signoff on empirical package)

Stage B is **debug only**.

---

## Submission checklist (future)

- [ ] Stage F main_500 complete and audited
- [ ] Stage G human validation complete
- [ ] Stage H paper assets eligible
- [ ] `make paper-submission-check` passes
- [ ] `check_claim_ledger.py --mode submission` passes
- [ ] `check_evidence_safety.py` submission mode passes
- [ ] Advisor approval on final claim-evidence matrix
- [ ] Coauthor sign-off on abstract (no placeholder numbers)

---

## Explicit non-claims

This repository **does not** claim:

- NeurIPS readiness
- Camera-ready empirical paper
- Validated benchmark results
- Public v1.0 release

---

See `paper/NEURIPS_PAPER_BLUEPRINT.md`, `docs/NEURIPS_CLAIM_EVIDENCE_UPGRADE_MAP.md`.
