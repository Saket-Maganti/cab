# M4 Low-Memory Workflow

This is the canonical CPU-only workflow for a 16 GB Apple-silicon laptop. It
does not authorize scientific model execution.

## Safe operating modes

| Mode | Worker cap | Intended use |
|---|---:|---|
| `serial` | 1 | debugging, schema repair, lowest memory |
| `low_memory` | 2 | default validation and streaming analysis |
| `four_worker` | 4 | bounded test/analysis work with memory headroom |
| `adaptive` | 4 maximum | caps workers by CPU and approximately 3 GiB per worker |

Never use unbounded `-n auto` for the full suite on this machine. Use
`python3 -m pytest -n0` for serial work or `python3 -m pytest -n4` only after
checking memory pressure.

## Read-only preflight

```bash
PYTHONPATH=src python3 scripts/cab_resource_preflight.py \
  --worker-mode low_memory \
  --memory-gib 16 \
  --bootstrap-mode pilot \
  --output /tmp/cab_resource_preflight.json
```

All runtime and storage figures emitted by this command are
`ESTIMATE_NOT_MEASURED`. They are formulas over explicit assumptions, not
benchmarks.

## Streaming and disk policy

- Read JSONL in bounded chunks; never load the full Main candidate or trajectory
  archive unless the measured size is safe.
- Pilot bootstraps use 1,000 deterministic replicates; final analysis uses
  10,000, sharded in resumable batches and clustered by base task.
- Compress completed shards with deterministic gzip and retain integrity
  hashes.
- Keep raw evidence. Cleanup tooling may report caches and duplicates but must
  never delete raw evidence automatically.
- Use a bounded temporary directory and export completed chunks incrementally.
- Regenerate intermediates only when the producing command, input hashes, and
  code revision are recorded.

## Failure recovery

If memory pressure rises, stop after the current atomic shard, keep its
checkpoint, switch to `serial`, halve the JSONL chunk size, and resume. If disk
headroom becomes small, compress completed shards and move reviewed duplicates
only after explicit human confirmation. Do not delete raw run material.
