#!/usr/bin/env python3
"""Scan repository for secrets, unsafe defaults, and release security requirements."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SCAN_EXTENSIONS = {
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".md",
    ".tex",
    ".bib",
    ".sh",
    ".env",
    ".toml",
    ".cff",
}
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".ipynb_checkpoints",
    "build",
    "dist",
    "*.egg-info",
}
SKIP_PATH_PREFIXES = (
    "audits/",
    "results/",
)
SECRET_SCAN_SKIP_PREFIXES = (
    "results/",
    "tests/",
)

SECRET_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("hardcoded_bearer", re.compile(r"Bearer\s+[A-Za-z0-9._-]{24,}")),
    (
        "yaml_inline_secret",
        re.compile(r"(?i)(api[_-]?key|secret|password)\s*:\s*['\"]?sk-[A-Za-z0-9_-]{8,}"),
    ),
)

ALLOWLIST_SUBSTRINGS = (
    "sk-test-",
    "sk-live-should-not",
    "<redacted>",
    "[REDACTED]",
    "sk-...",
    "export OPENAI_API_KEY=...",
    "export OPENAI_API_KEY=sk-...",
    "${OPENAI_API_KEY",
)

PERSONAL_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)"
    r"(?:gmail|yahoo|hotmail|outlook|icloud|proton|edu|ac\.uk)\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

LIVE_ACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("smtp_send", re.compile(r"\bsmtplib\b|\bsendmail\s*\(")),
    ("requests_live", re.compile(r"\brequests\.(get|post|put|delete)\s*\(\s*['\"]https?://")),
)

GITIGNORE_REQUIRED = (
    ".env",
    ".venv/",
    "results/*/",
    ".cache/",
    "__pycache__/",
    "*.pem",
    "credentials.json",
    "secrets.json",
)

REQUIRED_FILES = (
    "LICENSE",
    "DATA_LICENSE.md",
    "CITATION.cff",
    ".env.example",
    "docs/SECURITY_AND_PRIVACY.md",
)

MOCK_TOOL_SAFETY_SNIPPETS = (
    ('"sent": False', "src/causal_agent_bench/tools/mock_tools.py"),
    ("def send_email_draft", "src/causal_agent_bench/tools/mock_tools.py"),
    ("def book_stub", "src/causal_agent_bench/tools/mock_tools.py"),
)


@dataclass(frozen=True)
class Finding:
    severity: str  # error | warning
    kind: str
    path: str
    detail: str

    def format(self) -> str:
        return f"[{self.severity}] {self.kind}: {self.path}: {self.detail}"


def _should_scan(path: Path, repo_root: Path | None = None) -> bool:
    if path.suffix.lower() not in SCAN_EXTENSIONS and path.name not in {".env", ".env.example"}:
        return False
    try:
        rel = path.relative_to(repo_root).as_posix() if repo_root is not None else path.as_posix()
    except ValueError:
        rel = path.as_posix()
    for prefix in SKIP_PATH_PREFIXES:
        if rel.startswith(prefix):
            return False
    return all(
        part not in SKIP_DIR_NAMES and not part.endswith(".egg-info")
        for part in path.parts
    )


def _is_allowlisted(line: str) -> bool:
    return any(token in line for token in ALLOWLIST_SUBSTRINGS)


def scan_file(path: Path, repo_root: Path) -> list[Finding]:
    rel = path.relative_to(repo_root).as_posix()
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Finding("warning", "unreadable", rel, str(exc))]

    skip_secrets = any(rel.startswith(prefix) for prefix in SECRET_SCAN_SKIP_PREFIXES)

    for line_number, line in enumerate(text.splitlines(), 1):
        if _is_allowlisted(line):
            continue
        if not skip_secrets:
            for kind, pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            "error",
                            kind,
                            f"{rel}:{line_number}",
                            line.strip()[:120],
                        )
                    )
        if PERSONAL_EMAIL_PATTERN.search(line) and "tests/" not in rel:
            findings.append(
                Finding(
                    "warning",
                    "personal_email",
                    f"{rel}:{line_number}",
                    "possible non-synthetic email address",
                )
            )
        if rel.startswith("src/"):
            for kind, pattern in LIVE_ACTION_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            "error",
                            kind,
                            f"{rel}:{line_number}",
                            "live network/send pattern in tool code",
                        )
                    )
    return findings


def scan_repository(repo_root: Path = REPO_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if not _should_scan(path, repo_root):
            continue
        findings.extend(scan_file(path, repo_root))
    return findings


def check_gitignore(repo_root: Path = REPO_ROOT) -> list[Finding]:
    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        return [Finding("error", "gitignore_missing", ".gitignore", "file not found")]
    text = gitignore.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for required in GITIGNORE_REQUIRED:
        if required.rstrip("/") not in text.replace("\n", " "):
            findings.append(
                Finding("error", "gitignore_entry", ".gitignore", f"missing pattern: {required}")
            )
    if ".env.*" in text and "!.env.example" not in text:
        findings.append(
            Finding(
                "warning",
                "gitignore_env_example",
                ".gitignore",
                ".env.* may ignore .env.example; add !.env.example",
            )
        )
    return findings


def check_required_files(repo_root: Path = REPO_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            findings.append(Finding("error", "missing_file", rel, "required for release"))
    return findings


def check_mock_tool_safety(repo_root: Path = REPO_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    mock_tools = repo_root / "src/causal_agent_bench/tools/mock_tools.py"
    if not mock_tools.exists():
        return [Finding("error", "mock_tools_missing", str(mock_tools), "not found")]
    text = mock_tools.read_text(encoding="utf-8")
    for snippet, label in MOCK_TOOL_SAFETY_SNIPPETS:
        if snippet not in text:
            findings.append(
                Finding("error", "mock_tool_safety", label, f"missing expected snippet: {snippet!r}")
            )
    if '"sent": False' not in text:
        findings.append(
            Finding(
                "error",
                "email_not_draft_only",
                "src/causal_agent_bench/tools/mock_tools.py",
                "send_email_draft must not set sent=True by default",
            )
        )
    return findings


def run_security_check(repo_root: Path = REPO_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_required_files(repo_root))
    findings.extend(check_gitignore(repo_root))
    findings.extend(check_mock_tool_safety(repo_root))
    findings.extend(scan_repository(repo_root))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--warnings-only", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = run_security_check(repo_root)
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]

    for finding in warnings:
        print(finding.format())
    for finding in errors:
        print(finding.format())

    if errors:
        print(f"\nsecurity-check: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    if warnings:
        print(f"\nsecurity-check: PASS with {len(warnings)} warning(s)")
    else:
        print("\nsecurity-check: PASS")
    return 0 if not args.warnings_only or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
