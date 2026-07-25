# Dataset Release Readiness

**Scope:** CAB dataset bundles from processed generation through frozen public release.  
**Current verdict:** **Pilot frozen and inspectable; main-scale and public v1.0 blocked.**

---

## Leakage status

| Check | Status | Notes |
|-------|--------|-------|
| True answer-leakage blocker clusters | **0** | Re-verify via latest `all-no-run-reports` → `static_leakage_report` |
| Static leakage scan tooling | **Ready** | `static-leakage-report` CLI |
| Answer-leakage repair history | **Applied** | Webshadow docs-hub repair (2026-06-04); see `PROVIDER_PILOT_PREPARATION_STATUS.md` |
| Contamination audit on freeze | **Ready (pilot)** | `freeze_manifest.json` → `contamination_audit_summary` |
| Template held-out keys | **Policy ready** | `heldout_templates` split in `splits.json` |

**Answer leakage cleared:** Static scans report 0 blocker clusters for true answer leakage on current pilot bundle. This is necessary but **not sufficient** for public release (human audit + main freeze still required).

---

## Frozen vs processed distinction

| Type | Path | Authority | Mutable? |
|------|------|-----------|----------|
| **Processed** | `data/processed/<bundle>/` | Regeneration output | Yes — regenerate with `generate-*` configs |
| **Frozen** | `data/frozen/<version>/` | Release authority | **No** — edit only via documented repair workflow |

**Rule:** Leaderboards, paper claims, and external release must cite **frozen** manifests (`freeze_manifest.json`, `dataset_hash`), not processed paths alone.

**Current frozen bundle:**

- `data/frozen/pilot_v0.1/` — pilot-scale release candidate
- Manifest: `data/frozen/pilot_v0.1/freeze_manifest.json`
- Splits: `data/frozen/pilot_v0.1/splits.json`

---

## Split policy

Policy name: `release_disjoint_v1` (see [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md)).

| Split | Role | Public? | Paper headline use |
|-------|------|---------|-------------------|
| `dev` | Pipeline debug | Disclosed | Engineering only |
| `pilot` | Early analysis | Disclosed | Engineering / pilot reports |
| `validation` | Method selection | Disclosed | Not headline ranking |
| `test` | Held-back eval | **Hidden IDs** | Official when release rules met |
| `heldout_templates` | Template reserve | Policy disclosed | Not for public ranking |

---

## Repair history

| Date | Action | Scope |
|------|--------|-------|
| 2026-06-04 | Webshadow docs-hub answer-leakage repair | Pilot static scans → 0 blocker clusters |
| Ongoing | `docs/LEAKAGE_REPAIR_APPLY_GUIDE.md` workflow | Manual review queue for new findings |

Repairs to frozen data require: documented issue → repair plan → re-freeze or patched manifest with changelog entry.

---

## Remaining manual-review queues

| Queue | Status |
|-------|--------|
| Human audit sample review | Protocol ready; annotations **not complete** |
| Main-scale generation QA | `main_200` / `main_v0.1_500` not frozen |
| Intervention isolation expert review | Static audit pass; C10 human validity **blocked** |
| Template naturalistic mini-study | 40-task configs exist; not release-frozen |

---

## Main_200 / main_v0.1_500 blockers

| Blocker | Detail |
|---------|--------|
| Not frozen | Only generation configs: `configs/generate_main_v0_1_500.yaml`, `configs/main_200_*.yaml` |
| No provider main run | 0 paper-eligible runs on main split |
| Human validation | Required before strong main-scale claims |
| Release policy | `docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md` gates v1.0 |
| Leaderboard | Cannot publish headline `test` split results without frozen main + eligible runs |

**Pilot dataset readiness:** `pilot_v0.1` is suitable for **infrastructure review** and **provider pilot template** (`pilot_20_instances.jsonl`), not for final NeurIPS headline benchmark claims alone.

---

## Pilot dataset readiness

| Item | Status |
|------|--------|
| Schema validation | Pass (freeze pipeline) |
| Intervention quality audit | Tooling implemented |
| Disjoint splits | Recorded in `splits.json` |
| File hashes / `dataset_hash` | In `freeze_manifest.json` |
| Dataset card | [DATASET_CARD.md](DATASET_CARD.md) |
| Paper-eligible runs on pilot | **0** |

---

## Release license / data license checklist

| Item | Status | Path |
|------|--------|------|
| Code license (MIT) | Ready | `LICENSE` |
| Synthetic data license | Ready | `DATA_LICENSE.md` |
| Citation metadata | Ready | `CITATION.cff` |
| Third-party API terms acknowledged | Ready | `docs/ETHICS_AND_LIMITATIONS.md` |
| Zenodo / Hugging Face upload | **Blocked** | No public v1.0 bundle |
| Benchmark card snapshot in freeze | Ready (pilot) | `benchmark_card_snapshot.md` in frozen dir |

---

## Versioning / changelog requirement

Before any public dataset release:

1. Bump version in `CITATION.cff` and `release/release_manifest.json`
2. Append entry to `CHANGELOG.md` with `dataset_hash` and split policy
3. Run `freeze-dataset` and archive `freeze_manifest.json`
4. Run `audit-contamination` on release candidate
5. Update `docs/DATASET_CARD.md` validation status
6. Confirm `reports/claim_evidence_matrix.md` still shows 0 eligible runs until provider audit completes

**Do not** auto-edit frozen files or promote release readiness without human sign-off.

---

See [DATASET_FREEZE.md](DATASET_FREEZE.md), [DATASET_VERSIONING_AND_RELEASE_POLICY.md](DATASET_VERSIONING_AND_RELEASE_POLICY.md), [NEURIPS_ARTIFACT_READINESS_CHECKLIST.md](NEURIPS_ARTIFACT_READINESS_CHECKLIST.md).
