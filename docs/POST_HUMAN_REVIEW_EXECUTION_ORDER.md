# Post-human-review execution order

The order the Compact-20 pilot must follow, and what each step is allowed to
conclude.

```text
import completed genuine review
  -> C10
  -> reviewed slice lock
  -> local CPU verification
  -> Kaggle CPU reproducibility checks
  -> Compact-20 T4x2 pilot
  -> post-run CPU audit
  -> blinded scorer audit
  -> conditional escalation
```

## 1. Import the completed offline review

The Compact-20 reviewers completed the substantive Stage-1 and Stage-2 forms
through simplified offline HTML pages, not through the production
issue-declare-submit sequence. The import path says so rather than pretending
otherwise.

```bash
python3 scripts/cab_manual_offline_review_import.py discover
python3 scripts/cab_manual_offline_review_import.py import \
  --manual-offline-import --coordinator-declaration-waiver
python3 scripts/cab_manual_offline_review_import.py verify
```

Evidence is classified by content — column layout, opaque item-id namespace and
decision dimension vocabulary — so filenames are irrelevant and an A/B filename
swap changes nothing.

Everything is sealed under the `MANUAL_OFFLINE_REVIEW_IMPORT_V1` origin. A
manual-import receipt can never authenticate against a production gate, and a
production receipt can never authenticate against an import gate. The normal
strict production commands are unchanged.

## 2. What the coordinator waived

Two waivers are sealed and disclosed, never hidden:

- `COORDINATOR_DECLARATION_WAIVER_RECORDED` — no separate reviewer declaration
  files were collected.
- `COORDINATOR_QUALIFICATION_EVIDENCE_WAIVER_RECORDED` — no qualification
  submission was imported, so **no qualification rate is claimed, re-derived or
  implied anywhere in this chain**.

The chain never emits `REVIEWER_DECLARATIONS_CONFIRMED`, and never asserts a
qualification pass. Both waivers travel by hash into C10, the exclusion
register, the slice lock and the execution authorization, so a reader of the
authorization alone can see them.

## 3. C10 and the reviewed slice

```bash
python3 scripts/cab_manual_offline_review_import.py gates
python3 scripts/cab_manual_offline_review_import.py report
```

C10 recomputes the agreement tables from the frozen judgements and refuses a
sealed agreement report that does not reproduce. Agreement is always computed
from the two independent pre-adjudication submissions; adjudicated values decide
eligibility and never enter an agreement statistic.

Status on success is `C10_MECHANICS_PASS_WITH_COORDINATOR_WAIVERS`, carrying
`c10_state: PASS`, `declaration_mode: COORDINATOR_WAIVER` and
`declaration_files_collected: false`.

## 4. Local CPU verification

```bash
PYTHONPATH=src python3 scripts/cab_resource_preflight.py \
  --worker-mode low_memory --memory-gib 16 --bootstrap-mode pilot \
  --output reports/post_human_review/cab_resource_preflight_post_c10.json

PYTHONPATH=src:. python3 -m pytest -q -n4
python3 -m ruff check . && python3 -m mypy && codespell
PYTHONPATH=src:. python3 scripts/security_check.py
PYTHONPATH=src:. python3 scripts/cab_leakage_gate.py
PYTHONPATH=src:. python3 scripts/release_check.py
python3 scripts/validate_kaggle_cpu_notebooks.py --execute-offline
PYTHONPATH=src:. python3 scripts/validate_kaggle_notebooks.py --execute-offline
```

Use bounded workers (2 by default, at most 4 when memory is healthy). Never
`-n auto`.

## 5. Kaggle CPU reproducibility checks

See [KAGGLE_CPU_OPERATIONS.md](KAGGLE_CPU_OPERATIONS.md).

## 6. Compact-20 T4x2 pilot

See [KAGGLE_T4X2_OPERATIONS.md](KAGGLE_T4X2_OPERATIONS.md). The committed
default is `RUN_LIVE = False`, and the notebook verifies the sealed execution
authorization rather than trusting that boolean.

The authorized pilot is fixed before results are seen:

```text
20 pairs x 2 conditions x 3 open-model categories x 1 repeat = 120 trajectories
```

Repeats are not added after seeing results. The model panel is not changed after
seeing benchmark outcomes.

## 7. What is *not* authorized

The execution authorization names exactly one study,
`compact20_reviewed_pilot`, and explicitly withholds:

- `scale100_confirmatory`
- `main500_confirmatory`
- `naturalistic_transfer`
- `raac_ablation`

Each needs its own reviewed material, its own validity gates and its own
authorization. None is implied by this pilot passing.

## 8. Paper eligibility

Not established by C10, and not established by a model run. It requires the
post-run audit **and** the blinded scorer audit. Before a genuine T4 run,
`GENUINE_MODEL_TRAJECTORIES = 0`; retries and failed attempts are never counted
as successful trajectories.
