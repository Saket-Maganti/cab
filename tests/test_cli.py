import os
import subprocess
import sys


def test_module_help_runs():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "validate" in result.stdout
    assert "export-paper-assets" in result.stdout


def test_placeholder_validate_runs_without_explicit_path():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "validate"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "validated" in result.stdout or "No task file found" in result.stdout
