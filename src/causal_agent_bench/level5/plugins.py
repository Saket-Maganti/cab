"""Typed CAB plugin metadata, compatibility checks, and isolated discovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import entry_points
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class PluginType(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    BACKEND = "backend"
    SCORER = "scorer"
    INTERVENTION_FAMILY = "intervention_family"
    ANALYSIS = "analysis"
    EXPORTER = "exporter"
    EVALUATOR_RUNTIME = "evaluator_runtime"


class PluginMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    plugin_type: PluginType
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    api_version: str = Field(pattern=r"^\d+\.\d+$")
    capabilities: list[str] = Field(default_factory=list)
    description: str


class CABPlugin(Protocol):
    metadata: PluginMetadata

    def validate(self) -> list[str]: ...


@dataclass(frozen=True)
class PluginLoadResult:
    name: str
    loaded: bool
    metadata: dict[str, Any] | None
    error: str | None


class PluginManager:
    ENTRY_POINT_GROUP = "causal_agent_bench.plugins"

    def __init__(self, *, supported_api: str = "1.0") -> None:
        self.supported_api = supported_api
        self._plugins: dict[str, CABPlugin] = {}
        self._errors: list[PluginLoadResult] = []

    def register(self, plugin: CABPlugin) -> None:
        metadata = plugin.metadata
        if metadata.api_version != self.supported_api:
            raise ValueError(
                f"plugin {metadata.name} API {metadata.api_version} is incompatible "
                f"with CAB API {self.supported_api}"
            )
        if metadata.name in self._plugins:
            raise ValueError(f"plugin already registered: {metadata.name}")
        errors = plugin.validate()
        if errors:
            raise ValueError(f"plugin validation failed: {errors}")
        self._plugins[metadata.name] = plugin

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
    "PluginType",
]
