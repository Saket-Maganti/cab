# CAB public Level-5 fixture

This CC0 fixture demonstrates the benchmark-authoring, compilation, review-packet,
planning, interruption, resume, artifact, evaluator, evidence-graph and
certification contracts. It is deliberately trivial and is always
`FIXTURE_ONLY`; it is not CAB scientific evidence.

```bash
cab benchmark validate --spec examples/level5/public_fixture/authoring.yaml
cab benchmark compile --spec examples/level5/public_fixture/authoring.yaml
cab run --dry-run
cab reproduce --workdir /tmp/cab_level5_reproduction
```
