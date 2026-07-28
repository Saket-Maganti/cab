# C10 Intervention-Isolation Validation Contract

The canonical operational protocol is
`docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`; the machine-readable contract is
`configs/human_validation/c10_contract_v1.json`.

C10 is the claim that controlled interventions isolate intended skill
components. Static taxonomy audits and deterministic marker checks prepare the
claim but do not validate it.

The contract requires genuine human rows, at least two independent qualified
reviewers for every candidate, a separate adjudicator, no AI/proxy assistance,
model-output and model-identity blinding, full candidate coverage, raw
agreement of at least 0.80 overall and per dimension, resolved disagreements,
valid final labels, a passing leakage report, a passing answer-contract report,
deterministic manipulation linkage, and a matching frozen review-slice hash.

Empty, header-only, partial, invalid, placeholder, duplicated, synthetic,
fixture, proxy, and AI-labelled data fail closed. Fixture-only tests may verify
the software contract but always retain zero genuine human rows and
`C10_PENDING`.

Run:

```bash
python3 scripts/build_c10_review_packet.py
python3 scripts/validate_cab_human_reviews.py
```

The first command writes blank assignments only and refuses to overwrite
completed inputs. The second exits nonzero until every genuine prerequisite is
present. Current C10 evidence remains unsupported.
