"""Plan a future public reproducibility bundle without zipping large artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.release.build_manifest import build_release_manifest
from causal_agent_bench.utils.io import write_json

EXCLUDED_PATTERNS = [
    ".env",
    ".env.*",
    "**/secrets/**",
    "results/**/trajectories.jsonl",
    "results/**/INCOMPLETE_RUN.json",
    "audits/full_verification/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/*.pyc",
]

SENSITIVE_EXCLUDED = [
    ".env",
    "credentials.json",
    "**/*api_key*",
    "**/*secret*",
]

LARGE_EXCLUDED = [
    "results/**",
    "figures/*.png",
    "figures/*.pdf",
    "data/processed/main_v0_1_500/**",
]


def plan_repro_bundle(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd()).resolve()
    manifest = build_release_manifest(root)

    include = {
        "source_code": ["src/causal_agent_bench/", "pyproject.toml", "Makefile"],
        "configs": manifest.get("configs", []),
        "synthetic_datasets": [
            "data/frozen/pilot_v0.1/",
            "data/sample/",
        ],
        "benchmark_specs": manifest.get("benchmark_specs", []),
        "docs": manifest.get("docs", [])[:40],
        "paper": [p for p in manifest.get("paper_files", []) if not p.endswith(".aux")],
        "analysis_scripts": [
            "scripts/reproduce_artifact.py",
            "scripts/run_fast_checks.py",
            "scripts/check_submission_readiness.py",
        ],
        "release_metadata": ["release/release_manifest.json", "CITATION.cff", "LICENSE"],
    }

    commands = [
        "pip install -e '.[dev]'",
        "make fast-check",
        "python3 scripts/reproduce_artifact.py --all-deterministic",
        "python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1",
        "python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl",
    ]

    plan: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "bundle_name": f"causal-agent-bench-repro-{manifest['package_version']}",
        "include": include,
        "exclude_patterns": EXCLUDED_PATTERNS,
        "sensitive_excluded": SENSITIVE_EXCLUDED,
        "large_artifacts_excluded": LARGE_EXCLUDED,
        "incomplete_runs_excluded": True,
        "environment_instructions": {
            "python": ">=3.11",
            "install": "pip install -e '.[dev]'",
            "env_file": "Copy .env.example to .env (gitignored); never commit keys.",
            "no_paid_calls_default": True,
        },
        "repro_commands": commands,
        "required_future_artifacts": [
            "Complete provider pilot run metadata (not trajectories in bundle)",
            "Human validation annotation export",
            "Frozen main_v0.1 dataset manifest",
            "Updated claim ledger with supported claims only after main experiment",
        ],
        "secrets_policy": "No API keys, credentials, or .env contents in bundle.",
        "zip_policy": "Do not zip results/ or large PNG/PDF assets by default.",
    }

    out_dir = root / "release"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "repro_bundle_plan.json", plan)
    (out_dir / "REPRO_BUNDLE_PLAN.md").write_text(_plan_markdown(plan), encoding="utf-8")
    return plan


def _plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Reproducibility Bundle Plan",
        "",
        f"Generated: `{plan['generated_at']}`",
        "",
        "## Included (future public release)",
        "",
    ]
    for category, items in plan["include"].items():
        lines.append(f"### {category}")
        for item in items[:15]:
            lines.append(f"- `{item}`")
        if len(items) > 15:
            lines.append(f"- ... {len(items) - 15} more")
        lines.append("")

    lines.extend(["## Excluded", ""])
    for label, items in [
        ("Sensitive", plan["sensitive_excluded"]),
        ("Large", plan["large_artifacts_excluded"]),
        ("General patterns", plan["exclude_patterns"]),
    ]:
        lines.append(f"### {label}")
        for item in items:
            lines.append(f"- `{item}`")
        lines.append("")

    lines.extend(["## Repro commands", ""])
    for cmd in plan["repro_commands"]:
        lines.append(f"```bash\n{cmd}\n```")

    lines.extend(["", "## Required future artifacts", ""])
    for item in plan["required_future_artifacts"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def scan_plan_for_secrets(plan: dict[str, Any]) -> list[str]:
    text = json.dumps(plan)
    hits = []
    for token in ("sk-", "api_key=", "secret=", "password="):
        if token.lower() in text.lower():
            hits.append(token)
    return hits
