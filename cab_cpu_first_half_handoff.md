# CAB CPU First-Half Handoff

Current state:

```text
CAB_CPU_FIRST_HALF_PARTIAL_GENUINE_INPUTS_MISSING
HUMAN_VALIDATION_REQUIRED
```

CPU-H1 is complete and healthy. CPU-H2 audited every configured input location
and found zero genuine human rows. CPU-H3 through CPU-H10 remain scientifically
blocked; no placeholder evidence was created.

Start with:

1. `reports/cpu_first_half/CPU_H2_HUMAN_REVIEW_ONBOARDING.md`
2. `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`
3. `configs/human_validation/c10_contract_v1.json`

After genuine review and separate adjudication are complete, run exactly:

```bash
python3 scripts/validate_cab_human_reviews.py
```

Do not proceed to Compact slice lock until that command returns genuine C10
`PASS` with 20/20 coverage. The private input audit remains ignored under
`private_data/cpu_first_half/` and must never be committed.
