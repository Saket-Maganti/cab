# CausalAgentBench

**When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents.**

CausalAgentBench studies tool-using language agents under controlled interventions.
It pairs clean task instances with targeted intervention variants so that distinct
agent skills — planning, tool selection, observation interpretation, contradiction
handling, recovery, stopping behaviour, and final-answer quality — can be measured
explicitly, rather than hidden behind a single end-task success number.

!!! note "Research scaffold"
    This site is generated from the repository's Markdown docs. The project is a
    deterministic research scaffold; smoke/dev outputs are engineering checks, not
    scientific results. See the evidence policy before citing anything.

## Start here

- [Active surface index](CAB_FOCUSED_PROJECT_SURFACE.md) — canonical code,
  data, notebook, gate, and governance paths.
- [Quickstart](QUICKSTART.md) — install → smoke → reproduce.
- [Benchmark card](BENCHMARK_CARD.md) and [Dataset card](DATASET_CARD.md).
- [Metrics](METRICS.md) — ACRS (Agent Causal Robustness Score) and component scores.
- [Interventions](INTERVENTIONS.md) — the intervention families and how pairs are built.
- [Reproducibility](REPRODUCIBILITY.md) — determinism, the pinned lockfile, and manifests.
- [Held-out release governance](HELDOUT_RELEASE_GOVERNANCE.md) — protected
  confirmatory and challenge material.

## Safety & evidence

Default tools are **simulated** and **no paid or network calls** run without explicit
opt-in. Read the [evidence level policy](EVIDENCE_LEVEL_POLICY.md) and
[ethics & limitations](ETHICS_AND_LIMITATIONS.md) before treating any output as a result.

## Developing

```bash
pip install -e ".[dev]"
make fast-check     # ruff + mypy + a fast pytest subset, no model runs
make test           # full suite, parallel (pytest-xdist)
make coverage       # branch coverage with a ratchet floor
make lock           # refresh the pinned dependency lockfile (constraints.txt)
make audit          # scan pinned deps for known CVEs (pip-audit)
```
