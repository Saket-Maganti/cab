#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --constraint constraints.txt -e ".[dev,docs]"
python -m causal_agent_bench env doctor
