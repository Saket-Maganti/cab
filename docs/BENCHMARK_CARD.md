# Benchmark Card: CausalAgentBench

**Release:** `0.1.0-rc1` (research scaffold)
**Package version:** `0.1.0`
**Default frozen dataset:** `data/frozen/pilot_v0.1` (`freeze_manifest.json`)

## Intended Use

CausalAgentBench evaluates tool-using LLM agents on **paired clean and intervened** tasks in a deterministic simulated environment. It is intended for:

- controlled research on whether final task success survives perturbations to tools, observations, memory, instructions, and stopping signals;
- debugging agent scaffolds, tool protocols, and recovery behavior;
- reproducible metric and intervention-audit development before large-scale model runs.

## Out-of-Scope Use

- Public leaderboards or product readiness claims from scaffold/stub runs.
- Real-world deployment certification (email, calendar, payments, live web, enterprise systems).
- Training on benchmark instances and reporting uncontaminated test performance.
- Treating **oracle / scripted agents** as realistic model baselines (they are sanity-check upper bounds only).
- Strong causal claims about isolated skills without human or expert intervention audit.

## Data Construction

1. **Template generation** (`task_style: template`): deterministic domain templates across travel, calendar/email, file/spreadsheet QA, shopping, research, policy, coding, and operations planning.
2. **Optional extensions**: naturalistic mock-artifact tasks (`task_style: naturalistic`), static web snapshot tasks (`task_style: web_shadow`) — see `docs/MINI_STUDY_EXTERNAL_VALIDITY.md` and `docs/WEB_SHADOW_STUDY.md`.
3. **Interventions**: one targeted patch per intervention family when possible (`tool_availability_patch`, `memory_patch`, `tool_output_patch`, or `instruction_patch`).
4. **Instances**: each base task yields one clean `BenchmarkInstance` plus one instance per applied intervention.
5. **Freeze**: `freeze-dataset` validates schemas, reruns quality filters, writes disjoint splits, checks leakage, hashes files, and emits `freeze_manifest.json`.

Primary generator: `src/causal_agent_bench/generation/`. Configs under `configs/generate_*.yaml`.

## Synthetic Data Policy

- **All default benchmark content is synthetic.** No live web crawl, private user data, or paid API outputs are embedded in generated tasks.
- Mock tools (`send_email_draft`, `book_stub`, `web_*` snapshot tools) **never perform real side effects**.
- Human-authored or enterprise data requires a separate privacy review and dataset card update before inclusion.
- Synthetic repetition and template structure are expected; diversity audits and held-out templates are planned maintenance items.

## Intervention Families

Core families (see `docs/INTERVENTION_CARD.md`):

`tool_removal`, `tool_failure`, `tool_corruption`, `irrelevant_tools`, `memory_corruption`, `observation_conflict`, `ambiguous_instruction`, `long_horizon_dependency`, `premature_success_signal`, `distractor_evidence`.

Optional web-shadow families: `web_broken_link`, `web_stale_page`, `web_conflicting_page`, `web_irrelevant_search_result`, `web_hidden_evidence`.

## Scoring Methodology

Default scorer: `deterministic_heuristic_v1` (`src/causal_agent_bench/scoring.py`).

Reports per trajectory: final success, tool-use quality, recovery, contradiction handling, memory verification, stopping behavior, trajectory faithfulness, ACRS, per-family robustness, ranking instability. Expanded exports: Metrics v2 and statistical summaries (`docs/METRICS.md`, `docs/METRIC_CARD_ACRS.md`).

Every published result must cite: run config, run directory, seeds, model IDs, prompt hashes, scorer version, and git commit when available.

## Validation Status

| Layer | Status |
|-------|--------|
| Schema validation (JSONL) | Implemented |
| Automated quality checks | Implemented |
| Intervention audit tooling | Implemented (pilot) |
| Frozen pilot dataset (`pilot_v0.1`) | Available |
| Human validation annotations | **Not complete** |
| Validated commercial/open-weight LLM runs | **Not complete** |
| Paper empirical claims | **Not submitted** |
| Stub/smoke runs as scientific evidence | **Forbidden** |

See `docs/claim_ledger.json` for claim-level status.

## Known Failure Modes

- Template repetition and shallow lexical overlap with expected answers.
- Heuristic final-answer scoring (misses paraphrases; may accept shallow keyword matches).
- Single-factor interventions may still leak secondary difficulty changes (tracked in Claim C10).
- Oracle agents can inflate clean success; do not compare to realistic agents on the same leaderboard.
- Optional LLM-judge scores are unstable without calibration and human agreement checks.
- Small clean-success denominators make ACRS undefined or noisy.

## Contamination Risk

- **High** if agents are trained or prompt-tuned on public `instances.jsonl` / frozen splits and evaluated on the same tasks.
- **Mitigation**: use disjoint `heldout_templates` and unreleased generation configs for final evaluation; report training-data exposure; freeze dataset hash and split policy (`docs/DATASET_FREEZE.md`).
- **Stub results** in `results/` are local engineering artifacts and must not be treated as benchmark leaderboards.

## Maintenance Plan

- Versioned releases via `release/release_manifest.json` and `make release-check`.
- Dataset freezes with `dataset_hash` and file-level SHA-256 in `freeze_manifest.json`.
- Schema migrations documented in `docs/TRAJECTORY_SCHEMA_V2.md` and changelog.
- Intervention family changes require audit guide updates and claim-ledger review.
- Post-paper: held-out templates, human validation completion, pinned lockfiles/containers (see `docs/REPRODUCIBILITY.md`).

## License

Code and documentation: **MIT** (`LICENSE`). Generated synthetic datasets distributed with the repository are MIT-licensed unless a separate dataset license is added in a future release. Cite the repository version and frozen `dataset_hash` when using a frozen bundle.
