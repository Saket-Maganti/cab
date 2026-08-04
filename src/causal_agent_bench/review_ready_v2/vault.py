"""Encrypted Stage-2 vault with a mandatory external key.

Stage-2 plaintext is never written next to its key, and never persisted at all.
The key lives outside the repository at a path supplied through
``CAB_STAGE2_KEY_PATH``; if that variable is unset the vault fails closed rather
than silently creating a key inside the working tree.
"""

from __future__ import annotations

import os
import secrets
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from causal_agent_bench.review_ready_v2.common import canonical_bytes, sha256_bytes

KEY_ENV = "CAB_STAGE2_KEY_PATH"
VAULT_ASSOCIATED_DATA = b"cab-review-ready-v2-stage2"
KEY_BYTES = 32
NONCE_BYTES = 12


class VaultError(RuntimeError):
    """The Stage-2 vault refused to operate."""


def resolve_key_path(repo_root: Path) -> Path:
    raw = os.environ.get(KEY_ENV, "").strip()
    if not raw:
        raise VaultError(
            f"{KEY_ENV} is not set. Point it at an owner-only key file OUTSIDE the repository, "
            f"for example: export {KEY_ENV}=$HOME/.cab/keys/stage2_review_ready_v2.key"
        )
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise VaultError(f"{KEY_ENV} must be an absolute path")
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path
    raise VaultError(f"{KEY_ENV} must point outside the repository root {repo_root}")


def load_or_create_key(repo_root: Path) -> tuple[Path, bytes]:
    path = resolve_key_path(repo_root)
    if path.is_file():
        key = path.read_bytes()
        if len(key) != KEY_BYTES:
            raise VaultError(f"the Stage-2 key at {KEY_ENV} must be exactly {KEY_BYTES} bytes")
        return path, key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    key = secrets.token_bytes(KEY_BYTES)
    path.write_bytes(key)
    path.chmod(0o600)
    return path, key


def load_key(repo_root: Path) -> tuple[Path, bytes]:
    path = resolve_key_path(repo_root)
    if not path.is_file():
        raise VaultError(f"no Stage-2 key at the path given by {KEY_ENV}")
    key = path.read_bytes()
    if len(key) != KEY_BYTES:
        raise VaultError(f"the Stage-2 key at {KEY_ENV} must be exactly {KEY_BYTES} bytes")
    return path, key


def key_permissions_owner_only(path: Path) -> bool:
    mode = stat.S_IMODE(path.stat().st_mode)
    return not mode & 0o077


def seal(records: list[dict[str, Any]], key: bytes) -> bytes:
    plaintext = canonical_bytes({"schema_version": "cab_stage2_records_v2", "records": records})
    nonce = secrets.token_bytes(NONCE_BYTES)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, VAULT_ASSOCIATED_DATA)


def unseal(ciphertext: bytes, key: bytes) -> list[dict[str, Any]]:
    if len(ciphertext) <= NONCE_BYTES:
        raise VaultError("the Stage-2 vault is truncated")
    try:
        plaintext = AESGCM(key).decrypt(
            ciphertext[:NONCE_BYTES], ciphertext[NONCE_BYTES:], VAULT_ASSOCIATED_DATA
        )
    except InvalidTag as error:
        raise VaultError("the Stage-2 vault failed authentication with this key") from error
    import json

    payload = json.loads(plaintext)
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise VaultError("the Stage-2 vault does not contain a record list")
    return records


def write_vault(vault_path: Path, records: list[dict[str, Any]], key: bytes) -> dict[str, Any]:
    ciphertext = seal(records, key)
    vault_path.parent.mkdir(parents=True, exist_ok=True)
    vault_path.parent.chmod(0o700)
    vault_path.write_bytes(ciphertext)
    vault_path.chmod(0o600)
    leftovers = sorted(
        path.name
        for path in vault_path.parent.iterdir()
        if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".key"}
    )
    if leftovers:
        raise VaultError(f"plaintext or key material found beside the vault: {leftovers}")
    return {
        "vault_path": str(vault_path),
        "vault_sha256": sha256_bytes(ciphertext),
        "record_count": len(records),
        "plaintext_persisted": False,
        "key_stored_beside_vault": False,
    }


@contextmanager
def unlocked_workspace(prefix: str = "cab-stage2-") -> Iterator[Path]:
    """Owner-only scratch directory that is wiped on exit and then verified."""

    directory = Path(tempfile.mkdtemp(prefix=prefix))
    directory.chmod(0o700)
    try:
        yield directory
    finally:
        for path in sorted(directory.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        directory.rmdir()
        if directory.exists():
            raise VaultError("the Stage-2 scratch directory could not be removed")


def vault_status(vault_path: Path, repo_root: Path) -> dict[str, Any]:
    """Public-safe status. Never reports plaintext, key bytes, or record content."""

    try:
        key_path = resolve_key_path(repo_root)
        key_configured = True
        key_present = key_path.is_file()
        key_outside_repo = True
        key_owner_only = key_present and key_permissions_owner_only(key_path)
    except VaultError:
        key_configured = key_present = key_outside_repo = key_owner_only = False
    plaintext_neighbours = (
        sorted(
            path.name
            for path in vault_path.parent.iterdir()
            if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".key"}
        )
        if vault_path.parent.is_dir()
        else []
    )
    checks = {
        "vault_present": vault_path.is_file(),
        "external_key_environment_variable_configured": key_configured,
        "key_outside_repository": key_outside_repo,
        "key_owner_only_permissions": key_owner_only,
        "no_stage2_plaintext_beside_vault": not plaintext_neighbours,
    }
    return {
        "vault_sha256": sha256_bytes(vault_path.read_bytes()) if vault_path.is_file() else None,
        "key_environment_variable": KEY_ENV,
        "key_path_recorded": False,
        "checks": checks,
        "passed": all(checks.values()),
    }


__all__ = [
    "KEY_ENV",
    "VaultError",
    "key_permissions_owner_only",
    "load_key",
    "load_or_create_key",
    "resolve_key_path",
    "seal",
    "unlocked_workspace",
    "unseal",
    "vault_status",
    "write_vault",
]
