# CAB ICLR Pre-Execution Handoff

## Current gate

```text
HUMAN_VALIDATION_REQUIRED
build_complete: true
```

Run from the repository root:

```bash
PYTHONPATH=src:. python3 scripts/check_iclr_preexecution_readiness.py
```

Exit code `2` is expected while human/C10/evidence prerequisites remain.
Exit code `1` indicates a build defect and must be repaired before review or
execution.

## Exact next action

Complete the blank Compact-20 review packet with two independent, qualified
human reviewers; do not run models.

The canonical packet is:

`data/human_validation/compact20_real_review/`

Start with:

- `README.md`
- `reviewer_instructions.md`
- `REVIEWER_QUALIFICATION_EXAMPLES.md`
- `review_items.jsonl`
- `reviewer_registry.csv`
- `review_judgments.csv`
- `adjudication.csv`

Use genuine privacy-safe reviewer IDs and the registered disclosures,
qualification, consent, blinding, and timestamp rules. Do not use proxy, AI, or
synthetic review. Do not modify the candidate membership during review.

## After genuine review

Validate without executing models:

```bash
PYTHONPATH=src:. python3 scripts/validate_cab_human_reviews.py
```

If and only if review coverage, agreement, adjudication, manipulation checks,
leakage, answer contracts, and the slice hash all pass, C10 may promote and
the slice may be locked. Follow the strict order in
`CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md`.

## Evidence boundary

Current genuine counts are all zero:

- human rows: 0
- real trajectories: 0
- audited runs: 0
- paper-eligible assets: 0
- supported empirical claims: 0

Do not execute Compact-20, Scale-100, naturalistic transfer, Main expansion,
provider calls, local models, or Kaggle live cells before the handbook's
prerequisites and an explicit approval are satisfied.

## Protected data

Complete v2 payloads stay under ignored `private_data/`. Public Git may contain
only schemas, generators, aggregates, and cryptographic commitments. The
public v1 candidates are permanently development-only/contaminated and cannot
be reused for confirmatory or paper evidence.

## Revalidation

Before any future stage transition:

```bash
PYTHONPATH=src:. python3 scripts/generate_cab_split_registry.py --check
PYTHONPATH=src:. python3 scripts/security_check.py
PYTHONPATH=src:. python3 scripts/release_check.py
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

The full build report is
`CAB_ICLR_ULTIMATE_ONESHOT_BUILD_REPORT.md`.
