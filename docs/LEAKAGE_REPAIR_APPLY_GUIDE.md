# Leakage Repair Apply Guide

This guide describes how to use `apply-leakage-patch` and the static leakage
suppression registry safely. Neither command runs benchmarks, calls providers,
promotes claims, or modifies `results/`, the claim ledger, or run metadata.

## When to use it

Use the applier only after:

1. Running `all-no-run-reports` and reading the cluster-level summaries.
2. Reviewing `leakage_repair_plan.md` and `proposed_patch_manifest.md`.
3. Running `validate-leakage-patch-manifest` and confirming
   `manifest_valid=true`.
4. Picking a specific subset of operation IDs by hand. The applier refuses to
   apply all operations by default.

## Preview mode (default)

```
python3 -m causal_agent_bench apply-leakage-patch \
  --manifest reports/no_run/leakage_repair_plan/proposed_patch_manifest.json \
  --selected-op leak_patch_<hash> \
  --output-dir reports/leakage_repair_apply
```

Preview mode does not touch any file. It writes
`reports/leakage_repair_apply/leakage_patch_apply_report.{json,md}` containing:

- The set of operations the user selected,
- For each operation, whether it would be `applied`, `preview_only`, or
  `refused`, plus the reason,
- Any manifest-level refusals (forbidden paths, evidence promotion, etc.).

## Apply mode

Apply mode is restricted to deterministic `rename_instance_id` operations that
the manifest already marked `safe_to_auto_patch=true` and that are listed in a
reviewed-ops file. Everything else stays preview-only, including:

- `remove_prompt_answer_leakage` (content edits)
- `update_split_assignment`, `correct_split_metadata` (split movement)
- `mark_false_positive` (must go through the YAML suppression registry)

```
python3 -m causal_agent_bench apply-leakage-patch \
  --manifest reports/no_run/leakage_repair_plan/proposed_patch_manifest.json \
  --selected-op leak_patch_<hash> \
  --reviewed-ops reviewed_ops.txt \
  --reviewed-by "advisor-name" \
  --approval-note "approved deterministic rename of duplicate IDs after advisor review" \
  --apply \
  --output-dir reports/leakage_repair_apply
```

The `reviewed-ops` file may be a JSON list, a JSON object with
`reviewed_operation_ids`, or a plain newline-separated text file (lines starting
with `#` are ignored).

### Refusals you can expect

The applier hard-refuses (no file changes) when any of the following are true:

- The selected operation is not present in the reviewed-ops file.
- The operation is not a deterministic ID rename.
- The operation touches `results/`, `claim_ledger`, `claim_evidence`, `paper/`,
  or `release/`.
- The manifest contains `scientific_evidence: true`, `allow_paid_calls: true`,
  `paper_eligible: true`, or `promote_to_supported: true` anywhere.
- The renamed file is outside the `data/` directory.
- The `new_id` already exists in the target file (collision).
- The `old_id` is not found in the target file.

Every applied change is recorded with SHA-1 hashes of the pre- and post-patch
file contents and the operator's name and approval note.

## Suppression registry

`configs/static_leakage_suppressions.yaml` documents reviewed false-positive
clusters so they no longer appear as active blockers. Each entry requires:

- `reviewer`
- `reason`
- `scope` (one of the `static_leakage_*` values listed in the file's header)
- `date`
- One of `classifications`, `cluster_ids`, or `root_cause_ids`

Hard rules enforced by the loader:

- `answer_leakage`, `duplicate_id_leakage`, `hidden_metadata_visible`, and
  `intervention_label_leakage` clusters are never suppressible.
- Blocker-risk clusters are never suppressible.
- Forbidden keys (`scientific_evidence`, `allow_paid_calls`, `paper_eligible`,
  `promote_to_supported`) are rejected outright.
- `review_after` dates that have passed flip the entry to `expired`, which
  causes the cluster to reappear in the active blocker list with an
  `expired_suppression` warning.

Validate the registry with:

```
python3 -m causal_agent_bench leakage-suppression-registry \
  --output-dir reports/leakage_suppressions
```

## What this guide does not do

- It does not run benchmarks.
- It does not call providers.
- It does not promote claims or fill paper assets.
- It does not authorize a provider pilot.
- It does not turn no-run reports into empirical evidence.

Provider runs remain blocked until the provider-pilot preflight gate reaches
`ready_for_dry_run` or `ready_for_live_run` on a separately approved config.
