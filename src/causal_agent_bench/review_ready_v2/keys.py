"""External key material: resolution, permissions, and fail-closed loading.

Every secret this package needs — the Stage-2 vault key, the qualification
answer key, the coordinator acceptance key — lives outside the repository at a
path named by an environment variable.  Nothing here ever creates a key inside
the working tree, and no key value is returned to a report, a log, or a hash.
"""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path

KEY_BYTES = 32


class ExternalKeyError(RuntimeError):
    """A required external key is missing, misplaced, or unusable."""


def resolve_external_key_path(env_var: str, repo_root: Path) -> Path:
    """Resolve ``env_var`` to an absolute path that is outside ``repo_root``."""

    raw = os.environ.get(env_var, "").strip()
    if not raw:
        raise ExternalKeyError(
            f"{env_var} is not set. Point it at an owner-only key file OUTSIDE the repository, "
            f"for example: export {env_var}=$HOME/.cab/keys/<name>.key"
        )
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ExternalKeyError(f"{env_var} must be an absolute path")
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path
    raise ExternalKeyError(f"{env_var} must point outside the repository root {repo_root}")


def key_permissions_owner_only(path: Path) -> bool:
    return not stat.S_IMODE(path.stat().st_mode) & 0o077


def load_external_key(env_var: str, repo_root: Path, *, require_owner_only: bool = True) -> bytes:
    """Load an external key, failing closed on every deviation."""

    path = resolve_external_key_path(env_var, repo_root)
    if not path.is_file():
        raise ExternalKeyError(f"no key file at the path given by {env_var}")
    if require_owner_only and not key_permissions_owner_only(path):
        raise ExternalKeyError(
            f"the key at {env_var} must be owner-readable only; run: chmod 600 <path>"
        )
    key = path.read_bytes()
    if len(key) != KEY_BYTES:
        raise ExternalKeyError(f"the key at {env_var} must be exactly {KEY_BYTES} bytes")
    return key


def create_external_key(env_var: str, repo_root: Path) -> Path:
    """Create the key named by ``env_var`` if it does not exist yet."""

    path = resolve_external_key_path(env_var, repo_root)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_bytes(secrets.token_bytes(KEY_BYTES))
    path.chmod(0o600)
    return path


def external_key_available(env_var: str, repo_root: Path) -> bool:
    try:
        load_external_key(env_var, repo_root)
    except ExternalKeyError:
        return False
    return True


__all__ = [
    "KEY_BYTES",
    "ExternalKeyError",
    "create_external_key",
    "external_key_available",
    "key_permissions_owner_only",
    "load_external_key",
    "resolve_external_key_path",
]
