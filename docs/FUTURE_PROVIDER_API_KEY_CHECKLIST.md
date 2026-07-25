# Future Provider API Key Checklist

Purpose: prepare for a future tiny provider pilot without changing the current evidence state.

Current state remains no-API:

- `allow_paid_calls: false`
- provider-backed evidence: `0`
- human annotations: `0`
- C1-C8/C10: unsupported

## 1. Store The Key Only In The Environment

Use a shell/session environment variable. Do not write provider secrets into YAML, Markdown, JSON, notebooks, shell scripts, logs, or committed files.

Allowed pattern:

```bash
export OPENAI_API_KEY="<set in shell only>"
```

Do not add the value to:

- `configs/*.yaml`
- `.env` files committed to the repo
- reports
- notebooks
- run metadata
- command transcripts

## 2. Verify Presence Without Printing The Key

Use a presence check only:

```bash
if [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY_PRESENT"
else
  echo "OPENAI_API_KEY_MISSING"
fi
```

Never run commands that echo the key value.

## 3. Re-Run No-Provider Gates First

Before enabling paid calls:

```bash
python3 scripts/check_evidence_safety.py
PYTHONPATH=src python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_cost
PYTHONPATH=src python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_prerun_dryrun
PYTHONPATH=src python3 -m causal_agent_bench provider-pilot-preflight --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_preflight
```

Required results:

- leakage blockers: `0`
- trajectory cap: `<= 5`
- estimated cost: `<= USD 5.00`
- no API key values in YAML or reports
- `scientific_evidence: false`
- `evidence_scope: provider_pilot_debug_or_preliminary`

## 4. Keep Paid Calls Disabled Until The Final Moment

`configs/provider_pilot_tiny_APPROVED.yaml` must remain locked while gates are being checked:

```yaml
allow_paid_calls: false
approval:
  approved_for_live_run: false
```

Only after every live gate passes may the approved config be changed for the single tiny run:

```yaml
allow_paid_calls: true
approval:
  approved_for_live_run: true
```

Do not change trajectory caps, budget caps, evidence scope, or scientific claim settings.

## 5. Run Only The Tiny Approved Config

The only live provider command allowed for this lane is:

```bash
PYTHONPATH=src python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml
```

Still forbidden:

- `main_200`
- `main_500`
- Compact-20 or Compact-50
- broad sweeps
- local LLMs
- claim-promotion commands
- paper asset eligibility marking

## 6. Lock The Config Immediately After The Run

Whether the run succeeds, fails, times out, or is interrupted, immediately restore:

```yaml
allow_paid_calls: false
```

Then verify:

```bash
PYTHONPATH=src python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
```

## 7. Complete Post-Run Review Before Using Outputs

Required reports after any live tiny pilot:

- `reports/TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md`
- `reports/TINY_PROVIDER_PILOT_TRAJECTORY_REVIEW.csv`
- `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.md`
- `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.csv`

Every trajectory must be manually inspected. Incomplete provider runs are blocked from evidence.

## 8. Evidence Reminder

The tiny provider pilot can support only:

- provider integration sanity,
- pipeline sanity,
- scorer sanity inspection,
- preliminary debugging observations.

It cannot support:

- C1-C8 final claims,
- C10,
- NeurIPS readiness,
- definitive model rankings,
- human-validation claims,
- eligible paper assets.
