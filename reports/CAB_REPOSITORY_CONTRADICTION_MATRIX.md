# CAB Repository Contradiction Matrix

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

The machine-readable current state is canonical. Historical files are preserved but cannot override live validators.

| Artifact A | Artifact B | Conflicting field | Repository-derived truth | Resolution | Canonical replacement | Deprecation action |
|---|---|---|---|---|---|---|
| `PROJECT_STATUS.json` | `MASTER_STATUS.json` | completed/indexed run counts and readiness label | 80 live indexed directories; zero real provider/open-model trajectories | Treat legacy counts as snapshots and do not infer scientific evidence. | `reports/CAB_CURRENT_STATE_VERIFIED.json` | Mark both legacy status files historical/noncanonical. |
| `MASTER_STATUS.json` | `reports/CAB_V3_NO_EXECUTION_UPGRADE_FINAL_REPORT.md` | next action (mock/provider planning versus human-first gate) | Human review is incomplete and C10 is pending; live runs are forbidden. | Use the stricter dependency order. | `reports/CAB_EXECUTION_ENTRY_GATE.md` | Supersede old next-action blocks; preserve files for history. |
| `cabv1.md` | master prompt historical handoff requirement | source availability | `cabv1.md` is not present in the live checkout. | Classify its major assertions `NOT_FOUND`/`UNVERIFIABLE`; do not reconstruct it. | `cabv2.md` | Record absence explicitly. |
| legacy scorer docs | production scorer/export code | scorer identity | `cab_typed_final_answer` version `2.0.0` is production identity. | Legacy `deterministic_heuristic_v1` references are stale. | `reports/CAB_SCORER_VALIDITY_AUDIT.md` | Deprecate legacy name; retain migration note. |
| fixture/stub run artifacts | paper/result surfaces | scientific and paper eligibility | Fixtures/stubs are ENGINEERING_ONLY/FIXTURE_ONLY; paper-eligible assets are 0. | Reject any empirical promotion. | `docs/claim_ledger.json` + entry gate | Keep placeholders and eligibility sidecars fail-closed. |
| static intervention-isolation score | human C10 state | validity interpretation | Static `likely_isolated` findings are not genuine judgments; C10 is pending. | Require two independent reviewers and adjudication. | `reports/CAB_HUMAN_REVIEW_AND_C10_GATE.json` | Never count proxy/template rows. |
| existing approved provider config | maximum-ceiling study gate | approval scope | No current `CAB_KAGGLE_T4X2_LIVE_APPROVAL.md` marker exists. | Historical/tiny approval cannot authorize a new study. | `reports/CAB_EXECUTION_ENTRY_GATE.md` | Require run-specific approval after slice lock. |
| V3 implementation claims | live code/tests | currentness | Core V3 engineering exists but is superseded by typed scorer, paired metrics, manifest v2, and nine notebooks. | Classify `VERIFIED_BUT_STALE` where code exists. | `cabv2.md` | Retain V3 report as archive evidence. |
| V4 implementation claim | live repository | existence of a canonical V4 handoff | No canonical V4 implementation report or `cabv1.md` was found. | Classify `NOT_FOUND`; do not infer completion from filenames. | `cabv2.md` | Resolve V4 as unverified historical context. |

## `cabv1.md` classification

| Major assertion | Classification | Basis |
|---|---|---|
| V3 implementation | `VERIFIED_BUT_STALE` | Independent live code and V3 report exist. |
| V4 implementation | `NOT_FOUND` | No canonical V4 report/handoff found. |
| Historical test count | `UNVERIFIABLE` | Source handoff absent; use current collection ledger. |
| Provider evidence count | `CONTRADICTED` if nonzero | Live real provider trajectories are zero. |
| Human-review count | `CONTRADICTED` if nonzero | Genuine human rows are zero. |
| C1–C8 empirical claims | `PLANNED_ONLY` | Claim ledger has no eligible evidence. |
| C9 engineering claim | `VERIFIED_CURRENT` | Provider-free fixtures/tests exist. |
| C10 | `PLANNED_ONLY` | Fail-closed validator reports pending. |
| Compact-20 | `PARTIALLY_VERIFIED` | Candidate manifest exists; review/run do not. |
| Paper state | `VERIFIED_BUT_STALE` | Scaffold exists; empirical assets remain ineligible. |
| Release state | `PARTIALLY_VERIFIED` | Engineering package checks exist; public empirical release is blocked. |
| Publication ceiling | `UNVERIFIABLE` | A venue outcome cannot be guaranteed pre-execution. |
