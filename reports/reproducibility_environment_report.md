# Reproducibility / environment report

Generated: 2026-05-20T08:27:04.637240+00:00

Read-only environment inspection. Does not install packages or call providers.

## Python

- `python`: /Users/saketmaganti/.pyenv/shims/python
- `python3`: /Users/saketmaganti/.pyenv/shims/python3
- Active: Python 3.11.9
- sys.executable: /Library/Frameworks/Python.framework/Versions/3.11/bin/python3

## Project pins

- pyproject: `requires-python = ">=3.11"`
- .python-version: `3.11.9`
- Lockfiles: (none)

## Recommendations

- Fix pyenv 3.11.9 mismatch or standardize docs on python3 from a working interpreter.
- Add a lockfile or pinned requirements strategy for reproducible installs.
- Safe validation: python3 -m pytest tests/test_safety_reports.py -q
- Before provider runs: python3 -m causal_agent_bench.cli all-safety-reports
