# Paper Status

**Last refreshed:** 2026-05-20 (safe paper refresh after build phases 2–9; LaTeX moved to `latexpaper/`)

## Layout

- **`latexpaper/`** — self-contained LaTeX bundle for Overleaf/local build
- **Coordination docs** — status, sync map, contribution/evidence maps, reviewer packet

## What changed

- **Abstract:** Added framework/artifact language; preserved all numeric placeholders
- **Introduction:** Repository status paragraph; updated evidence doc pointers
- **Benchmark Design:** Task registry, freeze policy, evidence labels, mock diagnostic E2E note, isolation audit
- **Interventional Framework:** Automated isolation audit paragraph
- **Metrics:** Mock/stub/incomplete run caveats
- **Experimental Setup:** Run pipeline, governance, stages, Phase 9 demo reference
- **Results:** Stronger placeholder status note
- **Human Validation:** Export protocol refs; explicit not-complete status
- **Ablations:** Planned matrix content (was empty)
- **Limitations:** Mock/stub and build-vs-science paragraphs
- **Ethics/Repro:** Evidence enforcement, release manifest, pre-experiment gates
- **Checklist:** Updated honest statuses
- **Conclusion:** Hypothesis vs result framing; next milestones
- **Related Work:** Artifact/repro practice paragraph

## What remains placeholder

- Numeric placeholders (N, M, K, X, rho, domains) in abstract and stats table
- All Results RQ subsections (Tables 2–5, Figures 2–6)
- Human validation Table 5
- Ablation Table 4
- Mini-study comparison table `[todo]` rows

## Unsupported claims (unchanged)

- C1–C8, C10: **planned**
- C9: **engineering_only** (pipeline reproducibility only)

## Section readiness

| Section | Ready for draft? | Blocked for submission? |
|---|---|---|
| Abstract | Yes (with placeholders) | Yes — numbers |
| Introduction | Yes | Partial |
| Related Work | Yes | Citation pass ongoing |
| Benchmark Design | Yes | Needs final N/M counts |
| Interventional Framework | Yes | C10 human audit |
| Metrics | Yes | Validation studies |
| Experimental Setup | Yes | — |
| Results | Placeholder only | **Yes** |
| Human Validation | Scaffold only | **Yes** |
| Ablations | Planned only | **Yes** |
| Limitations | Yes | — |
| Ethics/Repro | Yes | Final release tag |
| Conclusion | Yes | Results pending |

## Evidence required before submission

1. Completed provider pilot on frozen split
2. Human validation annotations + agreement
3. Main experiment (if claiming main-scale)
4. `fill-paper-from-run` from verified runs only
5. Claim ledger updates with linked artifact paths

## Status sources used

- `MASTER_STATUS.md`, `PROJECT_HEALTH.md`, `NEXT_DECISION.md`
- `paper/EVIDENCE_GAP_MAP.md`, `paper/CONTRIBUTION_MAP.md`
- `paper/paper_section_contract.json`, `paper/PAPER_SECTION_CONTRACT.md`
- `docs/EVIDENCE_LEVEL_POLICY.md`, `demo/ENGINEERING_DEMO_BUNDLE.md`
- `audits/paper_refresh/PAPER_REFRESH_START_SNAPSHOT.md`
- Pre-edit validator outputs (claim ledger, placeholders, lint, assets)

## Sync commands

```bash
python3 scripts/check_paper_placeholders.py --mode draft
python3 scripts/check_paper_section_contract.py --mode draft
python3 scripts/check_claim_ledger.py
python3 scripts/lint_paper_claims.py --mode draft
python3 scripts/validate_paper_assets.py --mode draft
```
