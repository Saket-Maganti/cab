"""Protected evaluator contracts, mock sandbox, anti-gaming, and signed receipts."""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.level5.core import canonical_json, content_hash, utc_now


class ResourceRequest(BaseModel):
    cpus: int = Field(default=1, ge=1, le=8)
    memory_mb: int = Field(default=1024, ge=128, le=32768)
    process_limit: int = Field(default=32, ge=1, le=256)
    wall_seconds: int = Field(default=300, ge=1, le=3600)
    output_bytes: int = Field(default=1_000_000, ge=128, le=10_000_000)


class SubmissionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    submission_id: str
    package_hash: str = Field(min_length=32)
    model_declaration: str
    policy_declaration: str
    runtime_image: str
    entry_point: list[str] = Field(min_length=1)
    resources: ResourceRequest = Field(default_factory=ResourceRequest)
    network_requested: bool = False
    licence: str
    authorship_attestation: bool

    @model_validator(mode="after")
    def safe_entry_point(self) -> SubmissionManifest:
        if not self.authorship_attestation:
            raise ValueError("authorship attestation is required")
        if self.network_requested:
            raise ValueError("protected evaluator denies network by default")
        if any("\x00" in value for value in self.entry_point):
            raise ValueError("entry point contains a null byte")
        return self


class SandboxSpec(BaseModel):
    ephemeral_workspace: bool = True
    evaluator_read_only: bool = True
    private_mount_at_runtime_only: bool = True
    network_disabled: bool = True
    non_root: bool = True
    capabilities_dropped: bool = True
    secret_free_environment: bool = True
    cleanup_verified: bool = True
    resources: ResourceRequest


class SandboxResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    resource_use: dict[str, float]
    cleanup_verified: bool


class SandboxRuntime(Protocol):
    name: str

    def run(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        protected_task_token: str,
    ) -> SandboxResult: ...


class MockSandboxRuntime:
    """Contract fixture; it never mounts real private tasks or starts a process."""

    name = "mock"

    def __init__(self, output: str = '{"answer":"fixture"}') -> None:
        self.output = output

    def run(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        protected_task_token: str,
    ) -> SandboxResult:
        del submission, protected_task_token
        return SandboxResult(
            exit_code=0,
            stdout=self.output,
            stderr="",
            resource_use={"cpu_seconds": 0.0, "peak_memory_mb": 0.0, "wall_seconds": 0.0},
            cleanup_verified=sandbox.cleanup_verified,
        )


class DockerSandboxRuntime:
    """Hardened Docker fixture runtime; private input is mounted read-only."""

    name = "docker"

    @staticmethod
    def available() -> bool:
        return shutil.which("docker") is not None

    def build_command(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        private_task_path: str | Path,
    ) -> list[str]:
        task_path = Path(private_task_path).resolve()
        if not task_path.is_file():
            raise FileNotFoundError(task_path)
        resources = sandbox.resources
        return [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--user",
            "65532:65532",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(resources.process_limit),
            "--memory",
            f"{resources.memory_mb}m",
            "--cpus",
            str(resources.cpus),
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--mount",
            f"type=bind,src={task_path},dst=/cab/private/task.json,readonly",
            "--entrypoint",
            submission.entry_point[0],
            submission.runtime_image,
            *submission.entry_point[1:],
        ]

    def run(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        protected_task_token: str,
    ) -> SandboxResult:
        if not self.available():
            raise RuntimeError("Docker is unavailable; use mock contract validation")
        command = self.build_command(
            submission,
            sandbox,
            private_task_path=protected_task_token,
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=sandbox.resources.wall_seconds,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
        )
        wall = time.monotonic() - started
        return SandboxResult(
            exit_code=completed.returncode,
            stdout=completed.stdout[: sandbox.resources.output_bytes],
            stderr=completed.stderr[: sandbox.resources.output_bytes],
            resource_use={"wall_seconds": wall},
            cleanup_verified=True,
        )


FORBIDDEN_OUTPUT_PATTERNS = {
    "filesystem_enumeration": re.compile(r"(?:/etc/passwd|/proc/self|find\s+/|ls\s+-R)"),
    "prompt_echo": re.compile(r"(?:BEGIN_PRIVATE_TASK|PROTECTED_PROMPT|GOLD_ANSWER)"),
    "score_oracle": re.compile(r"(?:score[_ -]?oracle|query[_ -]?score)", re.IGNORECASE),
    "encoded_dump": re.compile(r"(?:base64|hex_dump|private_payload)", re.IGNORECASE),
    "task_hardcoding": re.compile(r"(?:task[_-]?id\s*==|hardcod(?:e|ed))", re.IGNORECASE),
}


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    return -sum(
        (count / len(text)) * math.log2(count / len(text)) for count in counts.values()
    )


def audit_output(
    output: str,
    *,
    output_limit: int,
    protected_markers: list[str] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    encoded = output.encode("utf-8")
    if len(encoded) > output_limit:
        findings.append({"kind": "oversized_output", "severity": "DISQUALIFY"})
    for kind, pattern in FORBIDDEN_OUTPUT_PATTERNS.items():
        if pattern.search(output):
            findings.append({"kind": kind, "severity": "DISQUALIFY"})
    for marker in protected_markers or []:
        if marker and marker in output:
            findings.append({"kind": "protected_marker_echo", "severity": "DISQUALIFY"})
    entropy = _entropy(output)
    if len(output) > 4096 and entropy > 5.8:
        findings.append({"kind": "suspicious_entropy_volume", "severity": "REVIEW"})
    return {
        "passed": not any(row["severity"] == "DISQUALIFY" for row in findings),
        "findings": findings,
        "output_bytes": len(encoded),
        "entropy_bits_per_character": entropy,
        "heuristic_limitations": True,
    }


def validate_archive_members(paths: list[str]) -> None:
    for name in paths:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {name}")


class ProtectedTaskBroker:
    """Resolves opaque task IDs only inside a caller-supplied trusted boundary."""

    def __init__(self, tasks: dict[str, str]) -> None:
        self._tasks = dict(tasks)

    def resolve(self, task_id: str, *, trusted: bool) -> str:
        if not trusted:
            raise PermissionError("protected task resolution denied outside trusted boundary")
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError("unknown protected task ID") from exc

    def public_manifest(self) -> dict[str, Any]:
        ids = sorted(self._tasks)
        return {
            "task_count": len(ids),
            "task_set_hash": content_hash(
                [{"task_id_hash": content_hash(task_id)} for task_id in ids]
            ),
        }


def evaluate_fixture_submission(
    submission: SubmissionManifest,
    runtime: SandboxRuntime,
    *,
    task_set_hash: str,
    signing_key: bytes = b"cab-development-signing-fixture",
) -> dict[str, Any]:
    sandbox = SandboxSpec(resources=submission.resources)
    result = runtime.run(
        submission,
        sandbox,
        protected_task_token="fixture-token-not-a-task",
    )
    audit = audit_output(result.stdout, output_limit=submission.resources.output_bytes)
    unsigned = {
        "schema_version": "1.0",
        "evaluator_version": "cab-protected-fixture-1",
        "runtime": runtime.name,
        "task_set_hash": task_set_hash,
        "submission_hash": content_hash(submission.model_dump(mode="json")),
        "model_declaration": submission.model_declaration,
        "policy_declaration": submission.policy_declaration,
        "resource_use": result.resource_use,
        "audit_status": "PASS" if audit["passed"] else "DISQUALIFIED",
        "disqualification_reasons": [
            row["kind"] for row in audit["findings"] if row["severity"] == "DISQUALIFY"
        ],
        "cleanup_verified": result.cleanup_verified,
        "evidence_class": "FIXTURE_ONLY",
        "created_at": utc_now(),
        "development_signature": True,
    }
    signature = hmac.new(
        signing_key, canonical_json(unsigned).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return {**unsigned, "signature": signature}


def verify_receipt(
    receipt: dict[str, Any],
    *,
    signing_key: bytes = b"cab-development-signing-fixture",
) -> bool:
    unsigned = {key: value for key, value in receipt.items() if key != "signature"}
    expected = hmac.new(
        signing_key, canonical_json(unsigned).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(str(receipt.get("signature", "")), expected)


__all__ = [
    "DockerSandboxRuntime",
    "MockSandboxRuntime",
    "ProtectedTaskBroker",
    "ResourceRequest",
    "SandboxRuntime",
    "SandboxSpec",
    "SubmissionManifest",
    "audit_output",
    "evaluate_fixture_submission",
    "validate_archive_members",
    "verify_receipt",
]
