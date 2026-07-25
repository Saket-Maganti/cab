# Reproducibility Commands Without Providers

Status: safe static commands.

```bash
python3 -m pytest -q tests/test_claim_ledger.py tests/test_human_validation_protocol.py tests/test_provider_pilot_preflight.py
python3 scripts/check_evidence_safety.py
python3 scripts/check_claim_ledger.py
python3 -m pytest -q tests/test_acrs_v2_fixture_only.py tests/test_scorer_robustness_fixture_only.py tests/test_cab_v3_no_execution_upgrade.py
```

These commands must not call providers or local LLMs.
