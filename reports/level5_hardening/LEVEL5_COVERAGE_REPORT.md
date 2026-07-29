# Level-5 coverage report

Command:

```text
pytest -n0 -q tests/test_level5_*.py --cov=causal_agent_bench.level5
```

Result: 79 passed in 25.19 seconds. The line-only gate passed at 87.68% overall
against an 85% floor. Critical line coverage passed the 90% floor:

| Module | Line coverage |
|---|---:|
| evaluator.py | 91.17% |
| evidence.py | 91.18% |
| execution.py | 91.12% |
| registry.py | 92.86% |
| review.py | 91.84% |

Coverage.py's branch-aware combined display was 84.8%; this is reported
separately and is not mislabeled as line coverage. Coverage JSON SHA-256:
`0532cb7597c4d6fd68f9596e9130add3b8597bb8ef8611465d0ef8a0a8245490`.
