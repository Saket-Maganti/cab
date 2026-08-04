# ICLR Prompt 1 Post-Fix Baseline

**Recorded:** 2026-07-28 (Asia/Kolkata)  
**Scope:** Provider-free reproduction before repair  
**Branch:** `main`  
**Commit:** `d3469045a78de3a20b37783b29167805e7417e04`  
**Initial worktree:** clean

## Commands and exit codes

| Command | Exit | Observed result |
|---|---:|---|
| `git branch --show-current` | 0 | `main` |
| `git rev-parse HEAD` | 0 | `d3469045a78de3a20b37783b29167805e7417e04` |
| `git status --short` | 0 | No output before the suite |
| `python3 -m pytest -q` | 1 | 4 failed, 1,010 passed, 1 skipped in 108.96 seconds |

No provider, model, Kaggle, or scientific execution occurred. The suite
regenerated tracked status/report artifacts; those incidental changes were
restored to `HEAD` before repair work began.

## Reproduced failures

### 1. Protected held-out payloads are tracked

```text
tests/test_cab_phase2_phase3_gate.py::
test_live_heldout_release_policy_is_fail_closed
```

Failing assertion:

```python
assert report["passed"] is True, report["issues"]
```

Observed issue code:

```text
protected_payload_git_tracked
```

The live Git index contains protected payload files under multiple
`data/processed/**/heldout_*.jsonl` paths. The policy correctly treats this as
a blocker. The test expects the repository to have repaired the exposure.

**Predates Prompt 1:** yes. The protected files and the failing policy test are
present in parent commit `ca9c13b`.

### 2. Stale workflow-state assertion

```text
tests/test_max_ceiling_gate.py::
test_unified_gate_separates_build_and_external_blockers
```

Failing assertion:

```python
assert gate["current_state"] in {
    "HUMAN_REVIEW_PENDING",
    "HUMAN_REVIEW_INCOMPLETE",
    "ADJUDICATION_PENDING",
    "C10_PENDING",
}
```

Observed state:

```text
METHODOLOGY_READY
```

The canonical state engine already returned `METHODOLOGY_READY` when local build
blockers remained, but the test copied an older incomplete state list.

**Predates Prompt 1:** yes. Both the canonical return value and stale test are
present in parent commit `ca9c13b`.

### 3. Draft camera-ready precheck inherits the release failure

```text
tests/test_camera_ready_precheck.py::
test_draft_precheck_passes_on_scaffold
```

Failing assertion:

```python
assert failed == []
```

Observed failed step:

```text
release_check
```

The release inventory and bundle hash do not include the five Prompt 1
methodology documents and the new intervention-validity source module.

**Predates Prompt 1:** no. This is a Prompt 1 release-manifest refresh omission.

### 4. Release dry run inherits the stale inventory and hash

```text
tests/test_camera_ready_precheck.py::test_release_dry_run_cli
```

Failing assertion:

```python
assert proc.returncode == 0
```

Observed release errors:

- five omitted ICLR methodology documents;
- omitted
  `src/causal_agent_bench/safety/intervention_validity_profile.py`; and
- `release_bundle_hash` mismatch.

**Predates Prompt 1:** no. The manifest in Prompt 1 commit `d346904` retained
the parent commit's bundle hash and inventory.

## Files directly implicated

- `data/processed/**/heldout_base_tasks.jsonl`
- `data/processed/**/heldout_instances.jsonl`
- `src/causal_agent_bench/safety/heldout_release.py`
- `src/causal_agent_bench/safety/max_ceiling_gate.py`
- `tests/test_cab_phase2_phase3_gate.py`
- `tests/test_max_ceiling_gate.py`
- `release/release_manifest.json`
- `release/release_manifest.md`
- `scripts/release_check.py`
- the six Prompt 1 implementation files omitted from the release inventory

## Minimal repair plan

1. Inventory every protected or answer-bearing artifact in the current tree and
   Git history.
2. Permanently classify publicly exposed payloads as non-confirmatory and remove
   full protected payloads from the tracked public tree without erasing the
   scientific audit record.
3. Generate a deterministic replacement candidate into an ignored private path;
   publish only non-reversible hashes and aggregate metadata.
4. Make split, release, and leakage gates reject contaminated roles and unsafe
   public manifests.
5. Centralize workflow states and replace the duplicated state-list assertion
   with semantic fail-closed assertions.
6. Regenerate canonical registries, state/handoff artifacts, and the release
   inventory.
7. Run focused checks, static validation, and the complete provider-free suite.
