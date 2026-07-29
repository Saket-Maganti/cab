# CAB Level-5 hardening handoff

## Current state

`CAB_LEVEL5_HARDENED_FOUNDATION_READY`.

The operational hardening pass is implemented and validated at fixture and
internal-cleanroom scope. It does not complete scientific Level 5.

## Resume safely

Read:

- `reports/level5_hardening/CAB_LEVEL5_HARDENING_BASELINE.md`
- `reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json`
- `reports/level5_hardening/CAB_LEVEL5_HARDENING_LEDGER.md`
- `reports/level5_hardening/CAB_LEVEL5_HARDENING_DECISIONS.md`

Remain on `main`. Preserve the three user-owned untracked paths listed in the
baseline. Do not run providers or promote fixture evidence.

## Scientific boundary

```text
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

All genuine evidence counters are zero. The evaluator state is
`PROTECTED_EVALUATOR_HARDENED_PILOT_READY`, not production-ready.

## Operational notes

- Canonical schema version is 3; run `cab registry migrate --dry-run` before
  any future upgrade.
- Stress leases are conservative by design; do not reduce them without
  re-running the eight-worker campaign.
- Fixture HMAC keys are rejected by protected mode. Supply a production signer
  explicitly; never add a secret to this repository.
- Container evaluator and clean-room modes must stay `NOT_EXECUTED` when a
  usable local runtime/image is unavailable.
- The durable review database is private. Only privacy-filtered exports belong
  in public artifacts.

## Exact next action

Recruit and onboard genuine qualified Compact-20 reviewers using the hardened
human-review operating system.
