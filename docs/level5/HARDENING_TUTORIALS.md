# Hardened operations tutorials

These tutorials are public-safe and provider-free.

## 1. Benchmark authoring

```bash
cab benchmark init --spec /tmp/cab-authoring.yaml
cab benchmark validate --spec /tmp/cab-authoring.yaml
cab benchmark compile --spec /tmp/cab-authoring.yaml --output-dir /tmp/cab-benchmark
```

Review the target commitment, manipulation-check ID, tool schema, scorer,
provenance, privacy class and public/private outputs.

## 2. Registry migration

```bash
cab registry init --path /tmp/cab.sqlite3
cab registry migrate --path /tmp/cab.sqlite3 --dry-run
cab registry migrate --path /tmp/cab.sqlite3
cab registry doctor --path /tmp/cab.sqlite3
```

## 3. Concurrent fixture run

Compile a plan and use `ConcurrentScheduler` with four workers. Inspect state
counts, throughput, contention, duplicate commits and deterministic hash.

## 4. Interruption and resume

```bash
cab resume --run-dir /tmp/cab-fixture
cab status --run-dir /tmp/cab-fixture
```

The manifest must match and completed objects must verify.

## 5. Reliability campaign

```bash
cab reliability campaign --fault worker_kill --fault disk_full \
  --output /tmp/cab-faults.json
```

Read observations and invariants, not only the summary.

## 6. Fixture review

```bash
cab review serve --data-dir /tmp/cab-review
```

Qualify two fixture reviewers, assign, submit a disagreement, adjudicate and
amend. Public export must report zero genuine rows and C10 remains blocked.

## 7. Evaluator fixture

```bash
cab evaluator validate-submission
cab evaluator run-fixture --output /tmp/cab-evaluator-receipt.json
```

The receipt is development-signed. Protected mode rejects that key.

## 8. Evidence tracing

```bash
cab evidence verify --graph reports/level5/evidence_graph.fixture.json
cab evidence trace --graph reports/level5/evidence_graph.fixture.json \
  --node-id node.run.public_fixture.v1
```

Also verify certificate status and the transparency chain in persistent use.

## 9. Clean-checkout reproduction

Run `run_cleanroom_reproduction()` against a commit. Require both internal
classes, no discrepancies, and `EXTERNAL_INDEPENDENT` as `NOT_EXECUTED`.
