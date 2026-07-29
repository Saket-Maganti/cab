"""Explicit signer, verifier, rotation, and revocation interfaces."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from causal_agent_bench.level5.core import content_hash, file_sha256, utc_now


class Signer(Protocol):
    @property
    def key_id(self) -> str: ...

    @property
    def algorithm(self) -> str: ...

    @property
    def development_only(self) -> bool: ...

    def sign(self, payload: bytes) -> str: ...

    def public_material(self) -> dict[str, str]: ...


class Verifier(Protocol):
    @property
    def key_id(self) -> str: ...

    @property
    def algorithm(self) -> str: ...

    @property
    def development_only(self) -> bool: ...

    def verify(self, payload: bytes, signature: str) -> bool: ...

    def public_material(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class FixtureHMACSigner:
    """Fixture-only signer. It is rejected by every protected-mode path."""

    key_id: str
    key: bytes
    algorithm: str = "HMAC-SHA256"
    development_only: bool = True

    @classmethod
    def development(cls, key_id: str = "fixture-hmac-v1") -> FixtureHMACSigner:
        return cls(key_id=key_id, key=b"cab-development-signing-fixture")

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, signature: str) -> bool:
        return hmac.compare_digest(self.sign(payload), signature)

    def public_material(self) -> dict[str, str]:
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "development_only": "true",
            "key_commitment": content_hash(self.key.hex()),
        }


@dataclass(frozen=True)
class FixtureHMACVerifier:
    key_id: str
    key: bytes
    algorithm: str = "HMAC-SHA256"
    development_only: bool = True

    @classmethod
    def development(cls, key_id: str = "fixture-hmac-v1") -> FixtureHMACVerifier:
        return cls(key_id=key_id, key=b"cab-development-signing-fixture")

    def verify(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(self.key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def public_material(self) -> dict[str, str]:
        return FixtureHMACSigner(self.key_id, self.key).public_material()


class Ed25519Signer:
    """Optional production-capable signer loaded only from an explicit path."""

    algorithm = "Ed25519"
    development_only = False

    def __init__(self, key_id: str, private_key_path: str | Path) -> None:
        path = Path(private_key_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_mode & 0o077:
            raise PermissionError("Ed25519 private-key path must not be group/world accessible")
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Ed25519 support requires the optional cryptography package") from exc
        raw = path.read_bytes()
        loaded = serialization.load_pem_private_key(raw, password=None)
        if not isinstance(loaded, Ed25519PrivateKey):
            raise ValueError("private key is not Ed25519")
        self.key_id = key_id
        self._private_key = loaded
        self._serialization = serialization
        self._source_hash = file_sha256(path)

    def sign(self, payload: bytes) -> str:
        return base64.b64encode(self._private_key.sign(payload)).decode("ascii")

    def public_material(self) -> dict[str, str]:
        public = self._private_key.public_key().public_bytes(
            encoding=self._serialization.Encoding.Raw,
            format=self._serialization.PublicFormat.Raw,
        )
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "development_only": "false",
            "public_key_base64": base64.b64encode(public).decode("ascii"),
            "private_source_hash": self._source_hash,
        }


class Ed25519Verifier:
    algorithm = "Ed25519"
    development_only = False

    def __init__(self, key_id: str, public_key_base64: str) -> None:
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Ed25519 support requires the optional cryptography package") from exc
        self.key_id = key_id
        self._public_text = public_key_base64
        self._public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(public_key_base64, validate=True)
        )
        self._invalid_signature = InvalidSignature

    def verify(self, payload: bytes, signature: str) -> bool:
        try:
            self._public_key.verify(base64.b64decode(signature, validate=True), payload)
        except (ValueError, self._invalid_signature):
            return False
        return True

    def public_material(self) -> dict[str, str]:
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "development_only": "false",
            "public_key_base64": self._public_text,
        }


class SigningKeyRegistry:
    """In-memory public key registry with auditable rotation and revocation."""

    def __init__(self) -> None:
        self._verifiers: dict[str, Verifier] = {}
        self._active_key_id: str | None = None
        self._revoked_keys: dict[str, str] = {}
        self._revoked_objects: dict[str, str] = {}
        self._audit: list[dict[str, str]] = []

    def add(self, verifier: Verifier, *, activate: bool = False) -> None:
        existing = self._verifiers.get(verifier.key_id)
        if existing and existing.public_material() != verifier.public_material():
            raise ValueError("signing key ID conflict")
        self._verifiers[verifier.key_id] = verifier
        if activate or self._active_key_id is None:
            self.rotate(verifier.key_id)

    def rotate(self, key_id: str) -> None:
        if key_id not in self._verifiers:
            raise KeyError(key_id)
        if key_id in self._revoked_keys:
            raise ValueError("cannot activate a revoked signing key")
        previous = self._active_key_id or ""
        self._active_key_id = key_id
        self._audit.append(
            {
                "event": "KEY_ROTATED",
                "previous_key_id": previous,
                "key_id": key_id,
                "created_at": utc_now(),
            }
        )

    def revoke_key(self, key_id: str, reason: str) -> None:
        if key_id not in self._verifiers:
            raise KeyError(key_id)
        self._revoked_keys[key_id] = reason
        self._audit.append(
            {
                "event": "KEY_REVOKED",
                "key_id": key_id,
                "reason": reason,
                "created_at": utc_now(),
            }
        )
        if self._active_key_id == key_id:
            self._active_key_id = None

    def revoke_object(self, object_id: str, reason: str) -> None:
        self._revoked_objects[object_id] = reason
        self._audit.append(
            {
                "event": "SIGNED_OBJECT_REVOKED",
                "object_id": object_id,
                "reason": reason,
                "created_at": utc_now(),
            }
        )

    def verify(
        self,
        *,
        object_id: str,
        key_id: str,
        payload: bytes,
        signature: str,
        protected_mode: bool = False,
    ) -> bool:
        verifier = self._verifiers.get(key_id)
        if (
            verifier is None
            or key_id in self._revoked_keys
            or object_id in self._revoked_objects
            or (protected_mode and verifier.development_only)
        ):
            return False
        return verifier.verify(payload, signature)

    @property
    def active_key_id(self) -> str | None:
        return self._active_key_id

    def status(self) -> dict[str, object]:
        return {
            "active_key_id": self._active_key_id,
            "keys": [
                self._verifiers[key].public_material() for key in sorted(self._verifiers)
            ],
            "revoked_keys": dict(sorted(self._revoked_keys.items())),
            "revoked_objects": dict(sorted(self._revoked_objects.items())),
            "audit": list(self._audit),
            "production_secrets_stored": False,
        }


def explicit_private_key_environment(variable: str) -> Path:
    """Resolve an explicitly named private-key path without exposing its value."""

    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"required private-key path environment variable is missing: {variable}")
    return Path(value)


__all__ = [
    "Ed25519Signer",
    "Ed25519Verifier",
    "FixtureHMACSigner",
    "FixtureHMACVerifier",
    "Signer",
    "SigningKeyRegistry",
    "Verifier",
    "explicit_private_key_environment",
]
