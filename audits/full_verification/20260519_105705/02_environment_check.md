# 02 Environment Check

## Python and install

- `python --version`: failed because pyenv points `python` at unavailable `3.11.9`.
- `python3 --version`: `Python 3.11.9`.
- `python -m pip --version`: failed for the same pyenv reason.
- `python3 -m pip --version`: pip `26.0.1`.
- Install command used: `python3 -m pip install -e ".[dev]"`.
- Editable install status: success, installed/imported `causal-agent-bench==0.1.0`.

## CLI and doctor

- `python3 -m causal_agent_bench --help`: success.
- `python3 -m causal_agent_bench doctor`: success.

Doctor summary:

- Python version: `3.11.9`
- Expected directories: 9 present
- Required docs: 9 present
- Sample schema validation: 9 valid instances
- Config load: 37 YAML configs loaded
- Test modules: 43 discoverable
- Optional provider credentials: 0 external paid-provider credentials configured; local stub available

## Fixes

No environment code fix was needed. Use `python3` in commands until `.python-version`/pyenv is repaired.

