# Dataset Repair Workflow

This guide describes how to triage and fix the leakage and dataset-quality
clusters surfaced by the no-run reports. No step here runs benchmarks, calls
providers, mutates `results/`, or promotes claims.

## 1. Generate the reports

```
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run
```

This produces (among others):

- `static_leakage/static_leakage_report.{json,md}` — clustered leakage
- `leakage_repair_plan/leakage_repair_plan.{json,md}` — repair-cluster ranking
- `leakage_repair_plan/proposed_patch_manifest.{json,md}` — manifest of safe
  proposed operations
- `leakage_repair_apply/reviewed_ops_template.{json,md}` and
  `reviewed_ops_blank.txt` — advisor worksheet
- `manual_repair_preview/manual_repair_preview.{json,md}` — checklist for
  content/split clusters
- `evidence_dashboard/index.{json,md}` — overall readiness state
- `report_quality/report_quality_check.{json,md}` — meta-quality of the bundle

## 2. Subset-family false positives

`pilot_20 ⊂ pilot_100 ⊂ pilot` and `dev ⊂ pilot` are *intentional* subset
relations. The static-leakage classifier now recognizes these and labels the
duplicates as `expected_subset_overlap` (informational, gate `nice_to_have`).
No repair is required.

If you add a new family with subset relations, declare it explicitly in
`splits.json`:

```json
{
  "subset_families": [["pilot", "pilot_20", "pilot_100", "dev"]],
  "splits": { ... }
}
```

## 2b. Same-family protected-split overlap

Near-duplicate prompts across heldout/pilot where both sides belong to the
*same task family* (e.g., `research_assistant_hard_003` in heldout vs
`research_assistant_hard_025` in pilot) are now classified as
`same_family_protected_split_overlap` (needs_review, gate
`must_fix_before_main_benchmark`) rather than `true_split_leakage` (blocker,
gate `must_fix_before_provider_pilot`). These are typically shared scaffolding,
not cross-family leakage.

Reviewer decision per cluster:

- Confirm overlap is scaffolding → document via `configs/static_leakage_suppressions.yaml`.
- Confirm overlap is real heldout↔pilot content overlap → rewrite or remove
  one side before the main benchmark.

Cross-family protected-split overlap (different task families) still blocks
the provider pilot as `true_split_leakage`.

## 2c. Pair-link consistency

The new `validate-pair-links` command catches real dataset bugs that
static-leakage cannot:

- Orphaned interventions (no matching clean baseline)
- Orphaned clean instances (no intervention variants)
- Mismatched `base_task_id` (declared ID does not match instance ID prefix)
- Intervention referencing missing base task
- Pair crossing task family
- Pair crossing protected split boundary (excluding declared subset families)
- Duplicate intervention variants

Run as part of `all-no-run-reports` or standalone:

```
python3 -m causal_agent_bench validate-pair-links --output-dir reports/pair_link_validator
```

## 3. Triage the true blockers

After subset-family calibration, the only real duplicate-ID blockers are
duplicates that cross protected boundaries (e.g. `heldout ↔ pilot`).

The proposed patch manifest contains `rename_instance_id` operations for these
cases. Each operation is preview-only by default — the applier will not modify
files without explicit reviewer approval.

## 4. Build the reviewed-ops worksheet

```
python3 -m causal_agent_bench reviewed-ops-template \
  --manifest /tmp/cab_no_run/leakage_repair_plan/proposed_patch_manifest.json \
  --output-dir /tmp/cab_no_run/leakage_repair_apply
```

This produces a worksheet (no IDs pre-approved) and a blank reviewed-ops file.

## 5. Preview the patches

```
python3 -m causal_agent_bench apply-leakage-patch \
  --manifest /tmp/cab_no_run/leakage_repair_plan/proposed_patch_manifest.json \
  --selected-op leak_patch_<hash> \
  --output-dir /tmp/cab_no_run/leakage_repair_apply
```

Default mode is preview-only. The output report lists what would be applied,
what stays preview-only, and what is refused.

## 6. Apply only the reviewed, deterministic renames

Add approved operation_ids to the blank reviewed-ops file (one per line, lines
starting with `#` ignored), then:

```
python3 -m causal_agent_bench apply-leakage-patch \
  --manifest /tmp/cab_no_run/leakage_repair_plan/proposed_patch_manifest.json \
  --selected-op leak_patch_<hash> \
  --reviewed-ops /tmp/cab_no_run/leakage_repair_apply/reviewed_ops_blank.txt \
  --reviewed-by "advisor-name" \
  --approval-note "approved deterministic rename of duplicate IDs across protected boundary" \
  --apply \
  --output-dir /tmp/cab_no_run/leakage_repair_apply
```

Hard refusals (applier never modifies any file when any of these is true):

- Manifest contains `scientific_evidence=true`, `allow_paid_calls=true`,
  `paper_eligible=true`, or `promote_to_supported=true` anywhere.
- Manifest touches `results/`, `claim_ledger`, `claim_evidence`, `paper/`, or
  `release/`.
- Operation is not `rename_instance_id`.
- Operation is not listed in `--reviewed-ops`.
- Operation is not marked `safe_to_auto_patch=true`.
- Target file is outside `data/` or inside `data/frozen/`.
- `new_id` already appears anywhere under `data/` (global collision check).
- `old_id` is not found, or `old_id == new_id`, or IDs contain unsafe
  characters.

## 7. Address content/split repairs manually

`manual_repair_preview/manual_repair_preview.md` provides per-type checklists
for:

- **Answer leakage** — rewrite the visible prompt/context manually.
- **True split leakage** — manually move, rewrite, or remove one side of the
  protected overlap.
- **Split metadata issue** — manually fix the split label or pair linkage.
- **False-positive cluster** — document in
  `configs/static_leakage_suppressions.yaml` (never for blocker-class
  clusters).

## 8. Document reviewed false positives

For clusters that are genuinely shared scaffolding (e.g.
`shared_tool_description`), add an entry to
`configs/static_leakage_suppressions.yaml` with reviewer, reason, scope, date.
Validate with:

```
python3 -m causal_agent_bench leakage-suppression-registry
```

Suppressions never hide answer-leakage, duplicate-ID, hidden-metadata, or
intervention-label clusters; the loader refuses such entries.

## 9. Re-run the bundle

```
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run
```

Confirm in `evidence_dashboard/index.md` that the blocker count dropped and
the readiness state moved closer to `ready_for_dry_run`.

## 10. Provider pilot still blocked

These steps do not approve a provider pilot. The provider-pilot gate also
requires:

- An approved (non-template) config copy.
- Advisor + budget approval recorded in the config.
- Tiny trajectory and budget caps.
- Stop conditions.
- A separate dry-run pass before any live run.

See `docs/PROVIDER_PILOT_READINESS_PACKET.md` and
`docs/LEAKAGE_REPAIR_APPLY_GUIDE.md` for details.
