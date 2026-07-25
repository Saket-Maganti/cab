"""Build release/release_manifest.json and release/release_manifest.md."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.utils.io import git_commit, write_json

# Reuse release_check hashing for CI compatibility
_REPO_FOR_IMPORT = Path(__file__).resolve().parents[3]
if str(_REPO_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_IMPORT))
from scripts.release_check import (  # noqa: E402
    _collect_manifest_paths,
    _release_bundle_hash,
)

PACKAGE_INIT = Path("src/causal_agent_bench/__init__.py")
DEFAULT_MANIFEST = Path("release/release_manifest.json")
SECRET_PATTERNS = (
    r"sk-[a-zA-Z0-9]{20,}",
    r"OPENAI_API_KEY\s*=\s*\S+",
    r"ANTHROPIC_API_KEY\s*=\s*\S+",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compute_bundle_hash(repo_root: Path, manifest: dict[str, Any]) -> str:
    inventory = _collect_manifest_paths(manifest)
    resolved = [repo_root / rel for rel in inventory if (repo_root / rel).exists()]
    return _release_bundle_hash(resolved, repo_root)


def _inventory_path_strings(manifest: dict[str, Any]) -> list[str]:
    return _collect_manifest_paths(manifest)


def _package_version(repo_root: Path) -> str:
    text = (repo_root / PACKAGE_INIT).read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else "unknown"


def _git_dirty(repo_root: Path) -> bool | None:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        return bool(proc.stdout.strip())
    except OSError:
        return None


def _hash_dependency_files(repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in ("pyproject.toml", "requirements.txt", "requirements-dev.txt"):
        path = repo_root / rel
        if path.exists():
            hashes[rel] = _file_sha256(path)
    return hashes


def _glob_inventory(
    repo_root: Path,
    pattern: str,
    *,
    limit: int | None = None,
) -> list[str]:
    """Return a deterministic file-only inventory.

    Release inventories must not silently omit files merely because a category
    grew beyond an arbitrary cap.  ``limit`` remains available only for
    explicitly non-canonical display inventories.
    """

    paths = sorted(
        path.relative_to(repo_root).as_posix()
        for path in repo_root.glob(pattern)
        if path.is_file()
    )
    return paths if limit is None else paths[:limit]


def _claim_ledger_status(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs/claim_ledger.json"
    if not path.exists():
        return {"present": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for claim in payload.get("claims", []):
        status = str(claim.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return {
        "present": True,
        "schema_version": payload.get("schema_version"),
        "status_counts": counts,
        "supported_claims": [c["claim_id"] for c in payload.get("claims", []) if c.get("status") == "supported"],
    }


def _security_status(repo_root: Path) -> dict[str, Any]:
    env_example = repo_root / ".env.example"
    gitignore = repo_root / ".gitignore"
    return {
        "env_example_present": env_example.exists(),
        "gitignore_present": gitignore.exists(),
        "secrets_in_manifest_forbidden": True,
    }


def _scan_for_secrets(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            hits.append(pattern)
    return hits


def build_release_manifest(
    repo_root: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd()).resolve()
    out_dir = Path(output_dir or root / "release")
    out_dir.mkdir(parents=True, exist_ok=True)

    configs = sorted(
        {
            *_glob_inventory(root, "configs/**/*.yaml"),
            *_glob_inventory(root, "configs/**/*.yml"),
            *_glob_inventory(root, "configs/**/*.json"),
        }
    )
    docs = sorted(
        {
            *_glob_inventory(root, "docs/**/*.md"),
            *_glob_inventory(root, "docs/**/*.json"),
        }
    )
    paper_files = _glob_inventory(root, "paper/**/*", limit=100)
    scripts = _glob_inventory(root, "scripts/*.py")
    notebooks = _glob_inventory(root, "notebooks/kaggle/*.ipynb")
    data_manifests = _glob_inventory(root, "data/manifests/*.json")
    benchmark_specs = _glob_inventory(root, "benchmark_specs/**/*")
    datasets = [
        p.relative_to(root).as_posix()
        for p in (root / "data/frozen").glob("**/freeze_manifest.json")
    ]

    # Content cards must contain every entry of ``required_card_sections``.
    section_validated_cards = [
        "docs/BENCHMARK_CARD.md",
        "docs/DATASET_CARD.md",
        "docs/METRIC_CARD_ACRS.md",
        "docs/INTERVENTION_CARD.md",
    ]
    # REPRODUCIBILITY / ETHICS are bundled and hashed as cards but are not
    # expected to carry the dataset-card section headings; they are validated for
    # existence only (and remain in ``docs`` for inventory hashing).
    cards = [
        *section_validated_cards,
        "docs/REPRODUCIBILITY.md",
        "docs/ETHICS_AND_LIMITATIONS.md",
    ]
    cards = [c for c in cards if (root / c).exists()]
    section_validated_cards = [c for c in section_validated_cards if (root / c).exists()]

    important_paths = sorted(
        set(cards + configs[:30] + scripts[:20] + ["LICENSE", "README.md", "CITATION.cff"])
    )
    file_hashes = {
        rel: _file_sha256(root / rel) for rel in important_paths if (root / rel).exists()
    }

    claim_status = _claim_ledger_status(root)
    missing_assets = []
    for rel in cards:
        if not (root / rel).exists():
            missing_assets.append(rel)
    if not datasets:
        missing_assets.append("data/frozen/*/freeze_manifest.json")

    manifest: dict[str, Any] = {
        "release_id": f"causal-agent-bench-{_package_version(root)}",
        "release_version": f"{_package_version(root)}-dev",
        "package_version": _package_version(root),
        "benchmark_status": "research_scaffold",
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_metadata": {
            "repo_root": str(root),
            "git_commit": git_commit(root),
            "git_dirty": _git_dirty(root),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "dependency_hashes": _hash_dependency_files(root),
        "cards": cards,
        "section_validated_cards": section_validated_cards,
        "configs": configs,
        "dataset_versions": datasets,
        "docs": sorted({d for d in docs if (root / d).exists()}),
        "paper_files": [p for p in paper_files if p.endswith((".tex", ".md", ".bib", ".csv"))][:60],
        "scripts": scripts,
        "benchmark_specs": benchmark_specs,
        "source_packages": _glob_inventory(root, "src/causal_agent_bench/**/*.py"),
        "notebooks": notebooks,
        "data_manifests": data_manifests,
        "root_documents": [
            path
            for path in ("README.md", "CITATION.cff", "DATA_LICENSE.md")
            if (root / path).is_file()
        ],
        "license_files": [
            path for path in ("LICENSE", "DATA_LICENSE.md") if (root / path).is_file()
        ],
        "inventory_policy": {
            "completeness_enforced": True,
            "categories": {
                "docs": ["docs/**/*.md", "docs/**/*.json"],
                "configs": ["configs/**/*.yaml", "configs/**/*.yml", "configs/**/*.json"],
                "scripts": ["scripts/*.py"],
                "source_packages": ["src/causal_agent_bench/**/*.py"],
                "notebooks": ["notebooks/kaggle/*.ipynb"],
                "data_manifests": ["data/manifests/*.json"],
            },
            "note": (
                "Canonical documentation, script, and Python-package inventories "
                "are file-only, sorted, uncapped, and covered by the release hash."
            ),
        },
        "run_artifacts_policy": {
            "included": "none_by_default",
            "excluded": ["results/*/trajectories.jsonl", "results/*/INCOMPLETE_RUN.json"],
            "note": "Run directories are not bundled; cite run_metadata.json paths instead.",
        },
        "evidence_levels": {
            "stub_engineering": "allowed_in_repo",
            "mock_diagnostic": "allowed_in_repo",
            "local_preliminary": "excluded_from_release_bundle",
            "provider_pilot": "requires_explicit_approval",
            "main_experiment": "not_started",
        },
        "known_missing_assets": missing_assets,
        "claim_ledger_status": claim_status,
        "security_privacy_status": _security_status(root),
        "validation_status": {
            "automated_quality_checks": "implemented",
            "human_validation_annotations": "not_complete",
            "intervention_audit_tooling": "implemented",
            "paper_empirical_claims": "not_submitted",
            "scientific_evidence_from_stub_runs": "forbidden",
            "validated_llm_agent_runs": "not_complete",
        },
        "license": "MIT",
        "license_file": "LICENSE",
        "default_frozen_dataset": "data/frozen/pilot_v0.1",
        "default_frozen_manifest": "data/frozen/pilot_v0.1/freeze_manifest.json",
        "required_card_sections": [
            "Intended Use",
            "Out-of-Scope Use",
            "Data Construction",
            "Synthetic Data Policy",
            "Intervention Families",
            "Scoring Methodology",
            "Validation Status",
            "Known Failure Modes",
            "Contamination Risk",
            "Maintenance Plan",
            "License",
        ],
        "file_hashes": file_hashes,
        "inventory_file_count": len(file_hashes),
    }

    manifest["release_bundle_hash"] = _compute_bundle_hash(root, manifest)
    manifest["inventory_file_count"] = len(_inventory_path_strings(manifest))

    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    if _scan_for_secrets(manifest_text):
        raise ValueError("manifest generation detected secret-like patterns; aborting")

    write_json(out_dir / "release_manifest.json", manifest)
    (out_dir / "release_manifest.md").write_text(
        _manifest_markdown(manifest),
        encoding="utf-8",
    )
    return manifest


def _manifest_markdown(manifest: dict[str, Any]) -> str:
    meta = manifest["repo_metadata"]
    lines = [
        "# Release Manifest",
        "",
        f"- **Release ID:** `{manifest['release_id']}`",
        f"- **Package version:** `{manifest['package_version']}`",
        f"- **Generated:** `{manifest['generated_at']}`",
        f"- **Git commit:** `{meta.get('git_commit')}` (dirty={meta.get('git_dirty')})",
        f"- **Python:** `{meta.get('python_version')}`",
        f"- **Bundle hash:** `{manifest['release_bundle_hash']}`",
        "",
        "## Inventory counts",
        "",
        f"- Configs: {len(manifest.get('configs', []))}",
        f"- Docs: {len(manifest.get('docs', []))}",
        f"- Scripts: {len(manifest.get('scripts', []))}",
        f"- Source modules: {len(manifest.get('source_packages', []))}",
        f"- Kaggle notebooks: {len(manifest.get('notebooks', []))}",
        f"- Data manifests: {len(manifest.get('data_manifests', []))}",
        f"- Dataset versions: {len(manifest.get('dataset_versions', []))}",
        f"- Paper files: {len(manifest.get('paper_files', []))}",
        "",
        "## Claim ledger",
        "",
        f"- Status counts: `{manifest.get('claim_ledger_status', {}).get('status_counts', {})}`",
        "",
        "## Known missing assets",
        "",
    ]
    missing = manifest.get("known_missing_assets") or []
    lines.extend(f"- `{item}`" for item in missing) if missing else lines.append("- None.")
    lines.extend(["", "## Evidence levels", ""])
    for level, note in (manifest.get("evidence_levels") or {}).items():
        lines.append(f"- `{level}`: {note}")
    lines.append("")
    return "\n".join(lines)
