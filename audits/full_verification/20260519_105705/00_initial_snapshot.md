# 00 Initial Snapshot

Audit timestamp: `20260519_105705`

Repository root: `/Users/saketmaganti/codexprojects/causal-agent-bench`

## Commands recorded

- `pwd`: initial shell was `/Users/saketmaganti/codexprojects`; the correct repository root is `/Users/saketmaganti/codexprojects/causal-agent-bench`.
- `git branch --show-current`: `main`
- `git log -1 --oneline`: `dea8e25 Initialize CausalAgentBench research benchmark scaffold`
- `git status --short`: dirty before audit; many tracked modifications and many untracked project files were already present.
- `git diff --stat`: 99 tracked files changed, 8436 insertions, 720 deletions at snapshot time.

## Top-level structure observed

Important areas present: `src/`, `tests/`, `configs/`, `data/`, `docs/`, `paper/`, `figures/`, `tables/`, `results/`, `scripts/`, `reviews/`, `release/`, `.github/`, `artifact/`.

The repository appears to be the intended CausalAgentBench root because it contains `pyproject.toml`, `src/causal_agent_bench/`, benchmark configs, data, paper scaffold, and test suite.

## Obvious initial risks

- Bare `python` is broken through pyenv, while `python3` works.
- The working tree was dirty before this audit; audit changes must not be interpreted as a clean diff from `main`.
- Existing results are mostly smoke, oracle, or local-stub runs; none are real provider-backed scientific evidence.
- The paper contains planned placeholders and must not be treated as result-bearing text.

