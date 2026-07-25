# Dataset Freeze Process

`freeze-dataset` creates a release-style benchmark bundle for planned `v0.1`, `v0.5`, and `v1.0` datasets. A frozen bundle is a reproducibility artifact, not scientific evidence by itself.

```bash
python -m causal_agent_bench freeze-dataset \
  --source-dir data/processed/pilot_v0_1 \
  --version v0.1 \
  --output-dir data/frozen
```

The command:

- validates `base_tasks.jsonl`, `interventions.jsonl`, and `instances.jsonl`;
- runs intervention quality filters and fails if the audit fails;
- writes disjoint release splits: `dev`, `pilot`, `validation`, `test`, and `heldout_templates`;
- checks split leakage for repeated base tasks, identical instructions across splits, duplicate ground-truth objects across splits, and repeated held-out template keys when avoidable;
- computes per-file SHA-256 hashes and one deterministic `dataset_hash`;
- writes `freeze_manifest.json`;
- writes `benchmark_card_snapshot.md`;
- preserves generated cards, quality reports, and human-audit samples when present.

The manifest records dataset version, generation config hash, source benchmark version, git commit, timestamp, task counts, intervention counts, schema validation summaries, quality audit summary, leakage report, split policy, file hashes, dataset hash, and known limitations.

Split semantics:

- `dev`: small pipeline/debugging split.
- `pilot`: early experiments and failure analysis; not final evidence.
- `validation`: method and prompt selection.
- `test`: final held-back evaluation.
- `heldout_templates`: later template variants reserved where possible to reduce template leakage.

Known limitations remain in force for all frozen bundles: tasks are synthetic, human validation is still required before strong claims, deterministic or local-stub runs are engineering checks only, and oracle agents are sanity-check upper bounds rather than realistic agents.

For leaderboard reporting rules and split semantics used in exports, see [LEADERBOARD_PROTOCOL.md](LEADERBOARD_PROTOCOL.md) and [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md).

Freeze also injects hidden-split canary metadata, runs `contamination_audit_report.{json,md}`, and records `contamination_audit_summary` in `freeze_manifest.json`. See [MODEL_CONTAMINATION.md](MODEL_CONTAMINATION.md).
