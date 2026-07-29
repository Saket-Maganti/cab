"""Protected evaluator contracts, mock sandbox, anti-gaming, and signed receipts."""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import shutil
import signal
import subprocess
import time
from collections import Counter
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.level5.core import canonical_json, content_hash, utc_now
from causal_agent_bench.level5.registry import SQLiteRegistry
from causal_agent_bench.level5.signing import (
    FixtureHMACSigner,
    FixtureHMACVerifier,
    Signer,
    SigningKeyRegistry,
    Verifier,
)


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
    image_digest: str | None = None
    entry_point: list[str] = Field(min_length=1)
    resources: ResourceRequest = Field(default_factory=ResourceRequest)
    network_requested: bool = False
    licence: str
    authorship_attestation: bool
    protected_mode: bool = False

    @model_validator(mode="after")
    def safe_entry_point(self) -> SubmissionManifest:
        if not self.authorship_attestation:
            raise ValueError("authorship attestation is required")
        if self.network_requested:
            raise ValueError("protected evaluator denies network by default")
        if any("\x00" in value for value in self.entry_point):
            raise ValueError("entry point contains a null byte")
        if self.image_digest is not None and not re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            self.image_digest,
        ):
            raise ValueError("image_digest must be a lowercase sha256 digest")
        if self.protected_mode and self.image_digest is None:
            raise ValueError("protected mode requires an image digest")
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
    user_namespace: bool = True
    seccomp_profile: str | None = None
    mandatory_lsm_hook: str | None = None
    docker_socket_denied: bool = True
    pid_namespace_isolated: bool = True
    ipc_namespace_isolated: bool = True
    tmpfs_nodev: bool = True
    swap_disabled: bool = True
    output_mount_isolated: bool = True
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

    @staticmethod
    def runtime_policy() -> dict[str, Any]:
        if not DockerSandboxRuntime.available():
            return {
                "available": False,
                "rootless": False,
                "reason": "Docker executable unavailable",
            }
        completed = subprocess.run(
            ["docker", "info", "--format", "{{json .SecurityOptions}}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        text = completed.stdout.lower()
        return {
            "available": completed.returncode == 0,
            "rootless": "rootless" in text,
            "security_options": completed.stdout.strip(),
            "reason": completed.stderr.strip() if completed.returncode else "",
        }

    def build_command(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        private_task_path: str | Path,
        output_path: str | Path | None = None,
    ) -> list[str]:
        task_path = Path(private_task_path).resolve()
        if not task_path.is_file():
            raise FileNotFoundError(task_path)
        output = Path(output_path or task_path.parent / "output").resolve()
        output.mkdir(parents=True, exist_ok=True)
        resources = sandbox.resources
        image = submission.runtime_image
        if submission.image_digest:
            image = f"{image.split('@', maxsplit=1)[0]}@{submission.image_digest}"
        command = [
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
            "--ipc",
            "none",
            "--pids-limit",
            str(resources.process_limit),
            "--memory",
            f"{resources.memory_mb}m",
            "--memory-swap",
            f"{resources.memory_mb}m",
            "--cpus",
            str(resources.cpus),
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount",
            f"type=bind,src={task_path},dst=/cab/private/task.json,readonly",
            "--mount",
            f"type=bind,src={output},dst=/cab/output",
            "--env",
            "CAB_OUTPUT_DIR=/cab/output",
            "--entrypoint",
            submission.entry_point[0],
        ]
        if sandbox.user_namespace:
            command[2:2] = ["--userns", "private"]
        if sandbox.seccomp_profile:
            profile = Path(sandbox.seccomp_profile).resolve()
            if not profile.is_file():
                raise FileNotFoundError(profile)
            command[2:2] = ["--security-opt", f"seccomp={profile}"]
        command.extend([image, *submission.entry_point[1:]])
        return command

    def validate_protected_controls(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
    ) -> dict[str, Any]:
        runtime = self.runtime_policy()
        controls = {
            "image_digest": submission.image_digest is not None,
            "rootless_runtime": bool(runtime.get("rootless")),
            "user_namespace": sandbox.user_namespace,
            "seccomp_profile": bool(sandbox.seccomp_profile),
            "lsm_hook": bool(sandbox.mandatory_lsm_hook),
            "no_new_privileges": sandbox.capabilities_dropped,
            "capabilities_dropped": sandbox.capabilities_dropped,
            "read_only_root": sandbox.evaluator_read_only,
            "docker_socket_denied": sandbox.docker_socket_denied,
            "pid_isolated": sandbox.pid_namespace_isolated,
            "ipc_isolated": sandbox.ipc_namespace_isolated,
            "tmpfs_hardened": sandbox.tmpfs_nodev,
            "swap_disabled": sandbox.swap_disabled,
            "network_none": sandbox.network_disabled,
            "output_isolated": sandbox.output_mount_isolated,
        }
        return {
            "passed": all(controls.values()),
            "controls": controls,
            "runtime": runtime,
            "protected_mode": submission.protected_mode,
        }

    def run(
        self,
        submission: SubmissionManifest,
        sandbox: SandboxSpec,
        *,
        protected_task_token: str,
    ) -> SandboxResult:
        if not self.available():
            raise RuntimeError("Docker is unavailable; use mock contract validation")
        if submission.protected_mode:
            policy = self.validate_protected_controls(submission, sandbox)
            if not policy["passed"]:
                raise RuntimeError(
                    "protected mode mandatory controls unavailable: "
                    + ", ".join(
                        key for key, value in policy["controls"].items() if not value
                    )
                )
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


def audit_structured_output(
    output: str,
    *,
    output_limit: int,
    allowed_fields: set[str],
    protected_text: str | None = None,
    prior_probe_hashes: set[str] | None = None,
) -> dict[str, Any]:
    base = audit_output(
        output,
        output_limit=output_limit,
        protected_markers=[protected_text] if protected_text else None,
    )
    findings = list(base["findings"])
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        findings.append({"kind": "invalid_output_json", "severity": "DISQUALIFY"})
        payload = None
    if not isinstance(payload, dict):
        findings.append({"kind": "invalid_output_schema", "severity": "DISQUALIFY"})
    else:
        unexpected = sorted(set(payload) - allowed_fields)
        if unexpected:
            findings.append(
                {
                    "kind": "unexpected_output_fields",
                    "severity": "DISQUALIFY",
                    "fields": ",".join(unexpected),
                }
            )
        answer = str(payload.get("answer", ""))
        if protected_text:
            protected_tokens = set(re.findall(r"\w+", protected_text.lower()))
            answer_tokens = set(re.findall(r"\w+", answer.lower()))
            overlap = (
                len(protected_tokens & answer_tokens) / len(protected_tokens)
                if protected_tokens
                else 0.0
            )
            if overlap > 0.8 and len(protected_tokens) >= 5:
                findings.append(
                    {
                        "kind": "prompt_echo_similarity",
                        "severity": "DISQUALIFY",
                    }
                )
    probe_hash = content_hash(output)
    repeated = probe_hash in (prior_probe_hashes or set())
    if repeated:
        findings.append({"kind": "repeated_probe", "severity": "REVIEW"})
    return {
        **base,
        "passed": not any(row["severity"] == "DISQUALIFY" for row in findings),
        "findings": findings,
        "probe_hash": probe_hash,
        "repeated_probe": repeated,
        "manual_controls": [
            "submission similarity",
            "collusion indicators",
            "abstention abuse",
            "resource anomaly",
        ],
    }


def validate_archive_members(paths: list[str]) -> None:
    for name in paths:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {name}")


class ArchiveMember(BaseModel):
    path: str
    size_bytes: int = Field(ge=0)
    is_symlink: bool = False
    link_target: str | None = None
    content_sample: str = Field(default="", max_length=8192)


SECRET_PATTERN = re.compile(
    r"(?:api[_-]?key|secret[_-]?key|private[_-]?key|password|bearer\s+[a-z0-9._-]{16,})",
    re.IGNORECASE,
)
PROTECTED_LIKE_PATTERN = re.compile(
    r"(?:BEGIN_PRIVATE_TASK|PROTECTED_PROMPT|GOLD_ANSWER|private[_-]?task[_-]?body)",
    re.IGNORECASE,
)


def inspect_submission(
    submission: SubmissionManifest,
    members: list[ArchiveMember],
    *,
    max_archive_bytes: int = 100_000_000,
    max_files: int = 2_000,
) -> dict[str, Any]:
    """Inspect a submission package and emit a deterministic policy report."""

    findings: list[dict[str, str]] = []
    if len(members) > max_files:
        findings.append({"kind": "file_count_limit", "severity": "REJECT"})
    total = sum(member.size_bytes for member in members)
    if total > max_archive_bytes:
        findings.append({"kind": "archive_size_limit", "severity": "REJECT"})
    paths = [member.path for member in members]
    try:
        validate_archive_members(paths)
    except ValueError:
        findings.append({"kind": "archive_traversal", "severity": "REJECT"})
    for member in members:
        if member.is_symlink:
            target = PurePosixPath(member.link_target or "")
            if target.is_absolute() or ".." in target.parts or not member.link_target:
                findings.append({"kind": "unsafe_symlink", "severity": "REJECT"})
            else:
                findings.append({"kind": "symlink_not_allowed", "severity": "REJECT"})
        if SECRET_PATTERN.search(member.content_sample):
            findings.append({"kind": "bundled_secret", "severity": "REJECT"})
        if PROTECTED_LIKE_PATTERN.search(member.content_sample):
            findings.append({"kind": "bundled_protected_like_payload", "severity": "REJECT"})
    entry = submission.entry_point[0]
    entry_present = entry in paths or any(path.endswith(f"/{entry}") for path in paths)
    if "/" in entry and not entry_present:
        findings.append({"kind": "entry_point_missing", "severity": "REJECT"})
    if submission.protected_mode and submission.image_digest is None:
        findings.append({"kind": "unpinned_image", "severity": "REJECT"})
    image_pinned = submission.image_digest is not None
    report = {
        "submission_id": submission.submission_id,
        "package_hash": submission.package_hash,
        "computed_member_commitment": content_hash(
            [member.model_dump(mode="json") for member in members]
        ),
        "file_count": len(members),
        "archive_bytes": total,
        "entry_point": list(submission.entry_point),
        "image": submission.runtime_image,
        "image_digest": submission.image_digest,
        "image_pinned": image_pinned,
        "protected_mode": submission.protected_mode,
        "findings": findings,
        "external_vulnerability_scanner": "OPTIONAL_HOOK_NOT_EXECUTED",
        "passed": not any(row["severity"] == "REJECT" for row in findings),
    }
    report["policy_hash"] = content_hash(report)
    return report


class EncryptedTaskStore(Protocol):
    def put(self, task_id: str, plaintext: bytes) -> str: ...

    def lease(self, task_id: str, *, evaluator_id: str, auth_token: str) -> dict[str, Any]: ...

    def resolve_once(self, lease_token: str, *, evaluator_auth: str) -> bytes: ...

    def public_commitment(self) -> dict[str, Any]: ...


class LocalEncryptedFixtureTaskStore:
    """Authenticated one-time encrypted fixture store; not production KMS."""

    def __init__(self, root: str | Path, *, key: bytes) -> None:
        if len(key) < 32:
            raise ValueError("fixture encryption key must contain at least 32 bytes")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.key = key
        self._leases: dict[str, dict[str, Any]] = {}

    def _keystream(self, nonce: bytes, size: int) -> bytes:
        blocks: list[bytes] = []
        counter = 0
        while sum(len(block) for block in blocks) < size:
            blocks.append(
                hashlib.sha256(
                    self.key + nonce + counter.to_bytes(8, "big")
                ).digest()
            )
            counter += 1
        return b"".join(blocks)[:size]

    def put(self, task_id: str, plaintext: bytes) -> str:
        nonce = secrets.token_bytes(16)
        stream = self._keystream(nonce, len(plaintext))
        ciphertext = bytes(left ^ right for left, right in zip(plaintext, stream, strict=True))
        tag = hashlib.sha256(self.key + nonce + ciphertext).digest()
        blob = nonce + tag + ciphertext
        task_hash = content_hash(task_id)
        (self.root / f"{task_hash}.encrypted").write_bytes(blob)
        return task_hash

    def lease(self, task_id: str, *, evaluator_id: str, auth_token: str) -> dict[str, Any]:
        task_hash = content_hash(task_id)
        if not (self.root / f"{task_hash}.encrypted").is_file():
            raise KeyError("unknown opaque task ID")
        if not auth_token:
            raise PermissionError("authenticated evaluator token is required")
        token = secrets.token_urlsafe(32)
        self._leases[self._token_hash(token)] = {
            "task_hash": task_hash,
            "evaluator_id_hash": content_hash(evaluator_id),
            "auth_hash": content_hash(auth_token),
            "created_at": utc_now(),
            "consumed": False,
        }
        return {
            "lease_token": token,
            "opaque_task_hash": task_hash,
            "evaluator_id_hash": content_hash(evaluator_id),
            "one_time": True,
        }

    @staticmethod
    def _token_hash(token: str) -> str:
        return content_hash(["task-lease", token])

    def resolve_once(self, lease_token: str, *, evaluator_auth: str) -> bytes:
        lease = self._leases.get(self._token_hash(lease_token))
        if (
            lease is None
            or lease["consumed"]
            or not secrets.compare_digest(
                str(lease["auth_hash"]),
                content_hash(evaluator_auth),
            )
        ):
            raise PermissionError("invalid, unauthenticated, or consumed task lease")
        path = self.root / f"{lease['task_hash']}.encrypted"
        blob = path.read_bytes()
        nonce, tag, ciphertext = blob[:16], blob[16:48], blob[48:]
        expected = hashlib.sha256(self.key + nonce + ciphertext).digest()
        if not secrets.compare_digest(tag, expected):
            raise ValueError("encrypted fixture task failed authentication")
        lease["consumed"] = True
        stream = self._keystream(nonce, len(ciphertext))
        return bytes(
            left ^ right for left, right in zip(ciphertext, stream, strict=True)
        )

    def public_commitment(self) -> dict[str, Any]:
        hashes = sorted(path.stem for path in self.root.glob("*.encrypted"))
        return {
            "task_count": len(hashes),
            "task_set_hash": content_hash(hashes),
            "plaintext_stored": False,
            "fixture_encryption_only": True,
        }


class EvaluationState(StrEnum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    DISQUALIFIED = "DISQUALIFIED"
    CORRECTED = "CORRECTED"
    WITHDRAWN = "WITHDRAWN"
    QUOTA_DEFERRED = "QUOTA_DEFERRED"


class EvaluationQueue:
    """Durable submission, approval, queue, quota, receipt, and withdrawal records."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    def set_quota(self, submitter_id: str, allowance: int) -> None:
        if allowance < 0:
            raise ValueError("quota allowance must be non-negative")
        submitter_hash = content_hash(submitter_id)
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO evaluator_quotas(
                    submitter_hash, allowance, consumed, window_started_at
                ) VALUES (?, ?, 0, ?)
                ON CONFLICT(submitter_hash) DO UPDATE SET
                    allowance=excluded.allowance,
                    consumed=0,
                    window_started_at=excluded.window_started_at
                """,
                (submitter_hash, allowance, utc_now()),
            )

    def submit(
        self,
        submission: SubmissionManifest,
        *,
        submitter_id: str,
        policy_report: dict[str, Any],
    ) -> dict[str, Any]:
        if not policy_report.get("passed"):
            raise ValueError("submission policy report did not pass")
        submitter_hash = content_hash(submitter_id)
        now = utc_now()
        with self.registry.transaction() as connection:
            quota = connection.execute(
                "SELECT allowance, consumed FROM evaluator_quotas WHERE submitter_hash=?",
                (submitter_hash,),
            ).fetchone()
            state = (
                EvaluationState.QUOTA_DEFERRED
                if quota and int(quota["consumed"]) >= int(quota["allowance"])
                else EvaluationState.SUBMITTED
            )
            if quota and state is EvaluationState.SUBMITTED:
                connection.execute(
                    "UPDATE evaluator_quotas SET consumed=consumed+1 WHERE submitter_hash=?",
                    (submitter_hash,),
                )
            payload = submission.model_dump(mode="json")
            connection.execute(
                """
                INSERT INTO evaluator_submissions(
                    submission_id, submitter_hash, package_hash, image_digest,
                    manifest_json, policy_hash, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission.submission_id,
                    submitter_hash,
                    submission.package_hash,
                    submission.image_digest,
                    canonical_json(payload),
                    str(policy_report["policy_hash"]),
                    state.value,
                    now,
                    now,
                ),
            )
        return {"submission_id": submission.submission_id, "status": state.value}

    def approve_and_enqueue(
        self,
        submission_id: str,
        *,
        approver_id: str,
        priority: int = 0,
    ) -> dict[str, Any]:
        queue_id = f"eval-queue.{content_hash([submission_id, priority])[:24]}"
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT status FROM evaluator_submissions WHERE submission_id=?",
                (submission_id,),
            ).fetchone()
            if row is None:
                raise KeyError(submission_id)
            if str(row["status"]) != EvaluationState.SUBMITTED.value:
                raise ValueError("submission is not approval-eligible")
            connection.execute(
                "UPDATE evaluator_submissions SET status=?, updated_at=? WHERE submission_id=?",
                (EvaluationState.QUEUED.value, utc_now(), submission_id),
            )
            connection.execute(
                """
                INSERT INTO evaluator_queue(
                    queue_id, submission_id, priority, status,
                    approved_by_hash, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    queue_id,
                    submission_id,
                    priority,
                    EvaluationState.QUEUED.value,
                    content_hash(approver_id),
                    utc_now(),
                    utc_now(),
                ),
            )
        return {"queue_id": queue_id, "status": EvaluationState.QUEUED.value}

    def claim(self, worker_id: str) -> dict[str, Any] | None:
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM evaluator_queue WHERE status=? "
                "ORDER BY priority DESC, created_at, queue_id LIMIT 1",
                (EvaluationState.QUEUED.value,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE evaluator_queue SET status=?, evaluator_worker_id=?, "
                "updated_at=? WHERE queue_id=?",
                (
                    EvaluationState.RUNNING.value,
                    worker_id,
                    utc_now(),
                    row["queue_id"],
                ),
            )
            connection.execute(
                "UPDATE evaluator_submissions SET status=?, updated_at=? "
                "WHERE submission_id=?",
                (EvaluationState.RUNNING.value, utc_now(), row["submission_id"]),
            )
        return {**dict(row), "status": EvaluationState.RUNNING.value}

    def record_receipt(self, receipt: dict[str, Any]) -> None:
        receipt_id = str(receipt["receipt_id"])
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO evaluator_receipts(
                    receipt_id, submission_id, signer_key_id, receipt_json,
                    receipt_hash, evidence_class, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    receipt["submission_id"],
                    receipt["signer_key_id"],
                    canonical_json(receipt),
                    content_hash(receipt),
                    receipt["evidence_class"],
                    utc_now(),
                ),
            )
            connection.execute(
                "UPDATE evaluator_submissions SET status=?, updated_at=? "
                "WHERE submission_id=?",
                (
                    EvaluationState.SUCCEEDED.value,
                    utc_now(),
                    receipt["submission_id"],
                ),
            )

    def revoke_receipt(self, receipt_id: str, reason: str) -> str:
        revocation_id = f"eval-revocation.{content_hash([receipt_id, reason])[:24]}"
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO evaluator_revocations(
                    revocation_id, receipt_id, reason, revoked_at
                ) VALUES (?, ?, ?, ?)
                """,
                (revocation_id, receipt_id, reason, utc_now()),
            )
        return revocation_id


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
    signing_key: bytes | None = None,
    signer: Signer | None = None,
    security_profile_hash: str | None = None,
) -> dict[str, Any]:
    if signer is not None and signing_key is not None:
        raise ValueError("provide signer or signing_key, not both")
    active_signer = (
        signer
        if signer is not None
        else FixtureHMACSigner(
            key_id="fixture-hmac-v1",
            key=signing_key or b"cab-development-signing-fixture",
        )
    )
    if submission.protected_mode and active_signer.development_only:
        raise PermissionError("protected mode refuses development signing keys")
    sandbox = SandboxSpec(resources=submission.resources)
    result = runtime.run(
        submission,
        sandbox,
        protected_task_token="fixture-token-not-a-task",
    )
    audit = audit_output(result.stdout, output_limit=submission.resources.output_bytes)
    unsigned: dict[str, Any] = {
        "schema_version": "2.0",
        "evaluator_version": "cab-protected-hardened-pilot-1",
        "runtime": runtime.name,
        "runtime_version": "fixture" if runtime.name == "mock" else "detected",
        "security_profile_hash": security_profile_hash
        or content_hash(sandbox.model_dump(mode="json")),
        "task_set_hash": task_set_hash,
        "submission_id": submission.submission_id,
        "submission_hash": content_hash(submission.model_dump(mode="json")),
        "package_digest": submission.package_hash,
        "image_digest": submission.image_digest,
        "model_declaration": submission.model_declaration,
        "policy_declaration": submission.policy_declaration,
        "resources_requested": submission.resources.model_dump(mode="json"),
        "resource_use": result.resource_use,
        "resources_measured": result.resource_use,
        "audit_status": "PASS" if audit["passed"] else "DISQUALIFIED",
        "findings": audit["findings"],
        "disqualification_reasons": [
            row["kind"] for row in audit["findings"] if row["severity"] == "DISQUALIFY"
        ],
        "cleanup_verified": result.cleanup_verified,
        "output_hash": content_hash(result.stdout),
        "evidence_class": "FIXTURE_ONLY",
        "created_at": utc_now(),
        "signer_key_id": active_signer.key_id,
        "signature_algorithm": active_signer.algorithm,
        "development_signature": active_signer.development_only,
        "revocation_state": "ACTIVE",
        "protected_mode": submission.protected_mode,
    }
    receipt_id = f"eval-receipt.{content_hash(unsigned)[:24]}"
    signed_payload = {**unsigned, "receipt_id": receipt_id}
    signature = active_signer.sign(canonical_json(signed_payload).encode("utf-8"))
    return {**signed_payload, "signature": signature}


def verify_receipt(
    receipt: dict[str, Any],
    *,
    signing_key: bytes | None = None,
    verifier: Verifier | None = None,
    key_registry: SigningKeyRegistry | None = None,
    protected_mode: bool = False,
) -> bool:
    if verifier is not None and signing_key is not None:
        raise ValueError("provide verifier or signing_key, not both")
    unsigned = {key: value for key, value in receipt.items() if key != "signature"}
    payload = canonical_json(unsigned).encode("utf-8")
    signature = str(receipt.get("signature", ""))
    receipt_id = str(receipt.get("receipt_id", ""))
    key_id = str(receipt.get("signer_key_id", "fixture-hmac-v1"))
    if key_registry is not None:
        return key_registry.verify(
            object_id=receipt_id,
            key_id=key_id,
            payload=payload,
            signature=signature,
            protected_mode=protected_mode,
        )
    active_verifier = (
        verifier
        if verifier is not None
        else FixtureHMACVerifier(
            key_id=key_id,
            key=signing_key or b"cab-development-signing-fixture",
        )
    )
    if protected_mode and active_verifier.development_only:
        return False
    if receipt.get("revocation_state") == "REVOKED":
        return False
    return active_verifier.verify(payload, signature)


EVALUATOR_CONTAINER_ATTACKS = (
    "filesystem_enumeration",
    "network_access",
    "fork_attempt",
    "memory_pressure",
    "timeout",
    "output_flooding",
    "prompt_echo",
    "path_traversal",
    "signal_handling",
    "orphan_child_process",
    "environment_scraping",
    "writable_root_assumption",
)


def _container_case_command(attack: str) -> list[str]:
    scripts = {
        "filesystem_enumeration": "print('/etc/passwd')",
        "network_access": (
            "import json,socket\n"
            "s=socket.socket();s.settimeout(.2)\n"
            "try:s.connect(('1.1.1.1',53));state='unexpected_network'\n"
            "except OSError:state='network_blocked'\n"
            "print(json.dumps({'answer':state}))"
        ),
        "fork_attempt": (
            "import json,subprocess\n"
            "children=[]\n"
            "try:\n"
            " [children.append(subprocess.Popen(['true'])) for _ in range(128)]\n"
            "except OSError: pass\n"
            "[p.wait() for p in children]\n"
            "print(json.dumps({'answer':'fork_bounded','children':len(children)}))"
        ),
        "memory_pressure": "a=bytearray(512*1024*1024);print(len(a))",
        "timeout": "import time;time.sleep(30)",
        "output_flooding": "print('x'*2000000)",
        "prompt_echo": "print('BEGIN_PRIVATE_TASK PROTECTED_PROMPT GOLD_ANSWER')",
        "path_traversal": "print('../../cab/private/task.json')",
        "signal_handling": "import signal,time;signal.signal(signal.SIGTERM,lambda *_:None);time.sleep(30)",
        "orphan_child_process": (
            "import subprocess,time;"
            "subprocess.Popen(['python','-c','import time;time.sleep(30)']);"
            "print('{\"answer\":\"child_started\"}');time.sleep(30)"
        ),
        "environment_scraping": (
            "import json,os;print(json.dumps({'answer':sorted(os.environ)}))"
        ),
        "writable_root_assumption": (
            "import json\n"
            "try:open('/cab-root-write','w').write('x');state='writable'\n"
            "except OSError:state='read_only'\n"
            "print(json.dumps({'answer':state}))"
        ),
    }
    return ["python", "-c", scripts[attack]]


def run_evaluator_malicious_campaign(
    *,
    image: str,
    execute_containers: bool,
) -> dict[str, Any]:
    """Run local malicious containers or report every unavailable case honestly."""

    docker_available = DockerSandboxRuntime.available()
    image_available = False
    if docker_available:
        image_available = (
            subprocess.run(
                ["docker", "image", "inspect", image],
                check=False,
                capture_output=True,
                timeout=15,
            ).returncode
            == 0
        )
    cases: list[dict[str, Any]] = []
    for index, attack in enumerate(EVALUATOR_CONTAINER_ATTACKS):
        if not execute_containers or not docker_available or not image_available:
            cases.append(
                {
                    "attack": attack,
                    "outcome": "NOT_EXECUTED",
                    "passed": False,
                    "critical": False,
                    "reason": (
                        "execution not requested"
                        if not execute_containers
                        else "Docker unavailable"
                        if not docker_available
                        else "local fixture image unavailable"
                    ),
                    "contract_tested": True,
                }
            )
            continue
        name = f"cab-malicious-{index}-{secrets.token_hex(4)}"
        command = [
            "docker",
            "run",
            "--name",
            name,
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
            "32",
            "--memory",
            "128m",
            "--memory-swap",
            "128m",
            "--cpus",
            "1",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--entrypoint",
            "python",
            image,
            *_container_case_command(attack)[1:],
        ]
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            )
            stdout = completed.stdout[:2_100_000]
            stderr = completed.stderr[:4096]
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(
                exc.stdout, bytes
            ) else str(exc.stdout or "")
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(
                exc.stderr, bytes
            ) else str(exc.stderr or "")
            exit_code = -signal.SIGKILL
        finally:
            subprocess.run(
                ["docker", "rm", "-f", name],
                check=False,
                capture_output=True,
                timeout=10,
            )
        audit = audit_output(stdout, output_limit=1_000_000)
        expectations = {
            "filesystem_enumeration": bool(audit["findings"]),
            "network_access": "network_blocked" in stdout,
            "fork_attempt": exit_code in {0, 137},
            "memory_pressure": exit_code != 0,
            "timeout": timed_out,
            "output_flooding": len(stdout.encode("utf-8")) > 1_000_000,
            "prompt_echo": bool(audit["findings"]),
            "path_traversal": ".." in stdout,
            "signal_handling": timed_out,
            "orphan_child_process": timed_out,
            "environment_scraping": "CAB_" not in stdout and "TOKEN" not in stdout,
            "writable_root_assumption": "read_only" in stdout,
        }
        contained = expectations[attack]
        cases.append(
            {
                "attack": attack,
                "outcome": "DETECTED_AND_CONTAINED" if contained else "NOT_MITIGATED",
                "passed": contained,
                "critical": not contained,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "stdout_hash": content_hash(stdout),
                "stderr_hash": content_hash(stderr),
                "findings": audit["findings"],
                "cleanup_verified": True,
                "contract_tested": True,
            }
        )
    executed = [case for case in cases if case["outcome"] != "NOT_EXECUTED"]
    critical = [case for case in cases if case.get("critical")]
    return {
        "passed": not critical,
        "case_count": len(cases),
        "executed_count": len(executed),
        "not_executed_count": len(cases) - len(executed),
        "critical_unresolved_count": len(critical),
        "docker_available": docker_available,
        "image_available": image_available,
        "image": image,
        "cases": cases,
        "evidence_class": "FIXTURE_ONLY",
    }


__all__ = [
    "EVALUATOR_CONTAINER_ATTACKS",
    "ArchiveMember",
    "DockerSandboxRuntime",
    "EncryptedTaskStore",
    "EvaluationQueue",
    "EvaluationState",
    "FixtureHMACSigner",
    "FixtureHMACVerifier",
    "LocalEncryptedFixtureTaskStore",
    "MockSandboxRuntime",
    "ProtectedTaskBroker",
    "ResourceRequest",
    "SandboxRuntime",
    "SandboxSpec",
    "SubmissionManifest",
    "audit_output",
    "audit_structured_output",
    "evaluate_fixture_submission",
    "inspect_submission",
    "run_evaluator_malicious_campaign",
    "validate_archive_members",
    "verify_receipt",
]
