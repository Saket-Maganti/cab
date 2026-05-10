# CausalAgentBench

**When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents**

CausalAgentBench is a Python research package for studying tool-using language agents under controlled interventions. The motivation is that final task success can hide why an agent succeeded or failed: planning, tool selection, tool arguments, observation interpretation, memory use, contradiction handling, recovery, stopping behavior, and final answer quality are different skills. The benchmark pairs clean task instances with targeted intervention variants so those skills can be measured more explicitly.

This repository is an initial research scaffold and deterministic prototype. It is not a completed benchmark, and smoke/dev outputs are engineering checks rather than scientific results.

## Installation

Requires Python 3.11+.

```bash
cd causal-agent-bench
pip install -e ".[dev]"
```

If your shell's `python` points to a missing pyenv version, either install the local version or use `python3`:

```bash
pyenv install 3.11.9
pyenv local 3.11.9
# or
python3 -m pip install -e ".[dev]"
```

For source-only use without installation:

```bash
export PYTHONPATH=src
```

## Smoke Run

```bash
python -m causal_agent_bench --help
python -m causal_agent_bench validate data/sample/instances.jsonl --schema instances
python -m causal_agent_bench run --config configs/smoke.yaml
```

The smoke run creates a timestamped directory such as `results/<timestamp>_smoke/`.

## Benchmark Generation

```bash
python -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python -m causal_agent_bench validate data/processed/dev_20/instances.jsonl --schema instances
```

The generator writes `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`, `generation_report.json`, and `quality_report.md`.

## Experiment Run

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml
```

This creates `results/<timestamp>_dev_20/` with config, config hash, metadata, trajectories, errors, scores, aggregate tables, and a score report.

## Scoring

Runs score automatically by default. To re-score:

```bash
python -m causal_agent_bench score --run-dir results/<timestamp>_dev_20
```

## Analysis

```bash
python -m causal_agent_bench analyze --run-dir results/<timestamp>_dev_20
python -m causal_agent_bench export-paper-assets --run-dir results/<timestamp>_dev_20
```

Analysis exports paper-oriented figures, tables, statistical summaries, and error cases.

## Repository Structure

```text
src/causal_agent_bench/   Python package
tests/                    Pytest suite
configs/                  YAML configs
data/raw/                 Raw or source data placeholders
data/processed/           Generated benchmark JSONL
data/sample/              Small sample task files and mock data
benchmark_specs/          Benchmark version specs
docs/                     Benchmark cards, metrics, interventions, reproducibility, ethics
paper/                    Paper scaffold and LaTeX source
reviews/                  Internal review and fix logs
results/                  Local run outputs, ignored except .gitkeep
figures/                  Generated paper figure templates
tables/                   Generated paper table templates
```

## Current Status

Implemented:

- Pydantic schemas and validation utilities.
- Deterministic synthetic task/intervention generation.
- Deterministic simulated tool environment.
- Baseline deterministic agents and LLM adapter interfaces.
- Metrics, scoring, experiment runner, resume checks, and analysis assets.
- Benchmark card, dataset card, metrics docs, intervention docs, claim ledger, reproducibility docs, and paper scaffold.

Not yet complete:

- Real LLM-backed agent runs.
- Human validation.
- Filled related-work citations.
- Final NeurIPS-scale experiments.

## Citation

Citation metadata is not final. Use this placeholder until a release DOI or paper exists:

```bibtex
@misc{causalagentbench2027,
  title = {When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents},
  author = {CausalAgentBench Contributors},
  year = {2027},
  note = {Research scaffold; citation metadata to be updated before publication}
}
```

## Limitations

- Default tasks are synthetic and template-generated.
- Default scoring is deterministic and heuristic.
- Oracle baselines are sanity checks, not realistic agents.
- Smoke/dev runs should not be cited as scientific evidence.
- Controlled interventions require human or expert audit before strong causal claims.

The claim ledger in [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md) is the source of truth for which claims are planned, engineering-only, supported, or weakened.
