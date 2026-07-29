"""Typed CAB plugin metadata, compatibility checks, and isolated discovery."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import entry_points
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level5.core import canonical_json, content_hash, utc_now
from causal_agent_bench.level5.registry import SQLiteRegistry


class PluginType(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    BACKEND = "backend"
    SCORER = "scorer"
    INTERVENTION_FAMILY = "intervention_family"
    ANALYSIS = "analysis"
    EXPORTER = "exporter"
    EVALUATOR_RUNTIME = "evaluator_runtime"


class PluginPermission(StrEnum):
    READ_PUBLIC_ARTIFACTS = "read_public_artifacts"
    WRITE_NAMESPACED_ARTIFACTS = "write_namespaced_artifacts"
    EXECUTE_FIXTURE_SUBPROCESS = "execute_fixture_subprocess"
    NETWORK = "network"
    READ_PRIVATE_EVIDENCE = "read_private_evidence"
    PROTECTED_EVALUATOR = "protected_evaluator"


FORBIDDEN_CAPABILITIES = frozenset(
    {
        "gate_override",
        "certificate_issue",
        "claim_promotion",
        "review_impersonation",
        "protected_task_export",
    }
)


class PluginMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    plugin_type: PluginType
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    api_version: str = Field(pattern=r"^\d+\.\d+$")
    capabilities: list[str] = Field(default_factory=list)
    permissions: list[PluginPermission] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)
    diagnostic_timeout_seconds: float = Field(default=5.0, ge=0.1, le=30.0)
    description: str

    @property
    def metadata_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class CABPlugin(Protocol):
    metadata: PluginMetadata

    def validate(self) -> list[str]: ...


@dataclass(frozen=True)
class PluginLoadResult:
    name: str
    loaded: bool
    metadata: dict[str, Any] | None
    error: str | None
    metadata_hash: str | None = None
    duration_limit_seconds: float | None = None


class PluginRepository:
    """Durable plugin metadata and provenance without persisting plugin secrets."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        registry.initialize()

    def record(
        self,
        metadata: PluginMetadata,
        *,
        status: str,
        provenance: dict[str, Any],
    ) -> str:
        metadata_json = canonical_json(metadata.model_dump(mode="json"))
        plugin_id = f"plugin.{content_hash([metadata.name, metadata.version, metadata.metadata_hash])[:24]}"
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO plugin_records(
                    plugin_id, metadata_json, metadata_hash, permissions_json,
                    provenance_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plugin_id,
                    metadata_json,
                    metadata.metadata_hash,
                    canonical_json([permission.value for permission in metadata.permissions]),
                    canonical_json(provenance),
                    status,
                    utc_now(),
                ),
            )
            row = connection.execute(
                "SELECT metadata_hash FROM plugin_records WHERE plugin_id = ?",
                (plugin_id,),
            ).fetchone()
            if row is None or row["metadata_hash"] != metadata.metadata_hash:
                raise RuntimeError("plugin metadata idempotency collision")
        return plugin_id

    def records(self) -> list[dict[str, Any]]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM plugin_records ORDER BY created_at, plugin_id"
            ).fetchall()
        return [
            {
                **dict(row),
                "metadata": json.loads(str(row["metadata_json"])),
                "permissions": json.loads(str(row["permissions_json"])),
                "provenance": json.loads(str(row["provenance_json"])),
            }
            for row in rows
        ]


class PluginManager:
    ENTRY_POINT_GROUP = "causal_agent_bench.plugins"

    def __init__(
        self,
        *,
        supported_api: str = "1.0",
        repository: PluginRepository | None = None,
    ) -> None:
        self.supported_api = supported_api
        self.repository = repository
        self._plugins: dict[str, CABPlugin] = {}
        self._errors: list[PluginLoadResult] = []

    def register(self, plugin: CABPlugin) -> None:
        metadata = plugin.metadata
        supported_major, supported_minor = self._api_tuple(self.supported_api)
        plugin_major, plugin_minor = self._api_tuple(metadata.api_version)
        if plugin_major != supported_major or plugin_minor > supported_minor:
            raise ValueError(
                f"plugin {metadata.name} API {metadata.api_version} is incompatible "
                f"with CAB API {self.supported_api}"
            )
        if metadata.name in self._plugins:
            raise ValueError(f"plugin already registered: {metadata.name}")
        forbidden = sorted(FORBIDDEN_CAPABILITIES.intersection(metadata.capabilities))
        if forbidden:
            raise ValueError(f"plugins cannot request governance capabilities: {forbidden}")
        if (
            PluginPermission.READ_PRIVATE_EVIDENCE in metadata.permissions
            or PluginPermission.PROTECTED_EVALUATOR in metadata.permissions
        ):
            raise ValueError("sensitive plugin permissions require an external approval service")
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="cab-plugin-check") as pool:
            future = pool.submit(plugin.validate)
            try:
                errors = future.result(timeout=metadata.diagnostic_timeout_seconds)
            except TimeoutError as exc:
                future.cancel()
                raise ValueError("plugin validation exceeded its declared timeout") from exc
        if errors:
            raise ValueError(f"plugin validation failed: {errors}")
        self._plugins[metadata.name] = plugin
        if self.repository is not None:
            self.repository.record(
                metadata,
                status="VALIDATED",
                provenance={
                    **metadata.provenance,
                    "api_supported": self.supported_api,
                    "validation": "PASSED",
                },
            )

    @staticmethod
    def _api_tuple(value: str) -> tuple[int, int]:
        major, minor = value.split(".", maxsplit=1)
        return int(major), int(minor)

    def discover(self) -> list[PluginLoadResult]:
        results: list[PluginLoadResult] = []
        for entry_point in entry_points(group=self.ENTRY_POINT_GROUP):
            try:
                loaded = entry_point.load()
                plugin = loaded() if isinstance(loaded, type) else loaded
                self.register(plugin)
            except Exception as exc:
                result = PluginLoadResult(
                    name=entry_point.name,
                    loaded=False,
                    metadata=None,
                    error=f"{type(exc).__name__}: {exc}",
                    metadata_hash=None,
                )
                self._errors.append(result)
                results.append(result)
                continue
            results.append(
                PluginLoadResult(
                    name=plugin.metadata.name,
                    loaded=True,
                    metadata=plugin.metadata.model_dump(mode="json"),
                    error=None,
                    metadata_hash=plugin.metadata.metadata_hash,
                    duration_limit_seconds=plugin.metadata.diagnostic_timeout_seconds,
                )
            )
        return results

    def capabilities(self) -> dict[str, list[str]]:
        return {
            name: sorted(plugin.metadata.capabilities)
            for name, plugin in sorted(self._plugins.items())
        }

    def get(self, name: str) -> CABPlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise KeyError(f"plugin not found: {name}") from exc

    @property
    def errors(self) -> list[PluginLoadResult]:
        return list(self._errors)


class ExampleScorerPlugin:
    metadata = PluginMetadata(
        name="cab.example_exact_scorer",
        plugin_type=PluginType.SCORER,
        version="1.0.0",
        api_version="1.0",
        capabilities=["exact_match", "fixture_safe"],
        permissions=[PluginPermission.READ_PUBLIC_ARTIFACTS],
        provenance={"distribution": "causal-agent-bench", "fixture_only": "true"},
        description="Provider-free example scorer plugin.",
    )

    def validate(self) -> list[str]:
        return []

    def score(self, expected: str, observed: str) -> float:
        return float(expected.strip() == observed.strip())


__all__ = [
    "CABPlugin",
    "ExampleScorerPlugin",
    "PluginLoadResult",
    "PluginManager",
    "PluginMetadata",
    "PluginPermission",
    "PluginRepository",
    "PluginType",
]
