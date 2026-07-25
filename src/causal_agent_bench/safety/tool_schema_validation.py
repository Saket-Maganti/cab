"""Static validator for simulated tool schemas and task-tool references."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import section_markdown, write_dual_report

TOOL_INTERVENTION_MARKERS = ("tool", "web")


@lru_cache(maxsize=1)
def load_code_registry_tool_specs() -> tuple[dict[str, Any], ...]:
    """Load tool schemas from the code-level simulated tool registry.

    This benchmark's tools live as Python classes (the deterministic simulated
    tool environment), not as per-dataset schema files. Treating that registry
    as the repo-default tool environment is what lets static validation resolve
    task tool references without re-declaring every schema in each dataset.
    Returns an empty tuple if the registry cannot be imported, so validation
    degrades gracefully rather than crashing or executing any tool.
    """
    try:
        from causal_agent_bench.tools.simulated import build_simulated_tools

        specs: list[dict[str, Any]] = []
        for tool in build_simulated_tools():
            spec = tool.spec()
            specs.append(
                {
                    "name": spec.name,
                    "description": spec.description,
                    "input_schema": spec.input_schema,
                    "output_schema": spec.output_schema,
                    "deterministic": True,
                    "source": "code_registry",
                }
            )
        return tuple(specs)
    except Exception:  # pragma: no cover - defensive: never let validation crash
        return ()


def build_tool_schema_validation(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    output_dir: str | Path = "reports/tool_schemas",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    dataset_reports = [
        validate_tool_schemas_for_dataset(path if path.is_absolute() else root / path, repo_root=root)
        for path in dataset_dirs
    ]
    issues = [issue for report in dataset_reports for issue in report["issues"]]
    root_causes = _root_cause_summary(issues)
    summary = {
        "dataset_count": len(dataset_reports),
        "issue_count": len(issues),
        "blockers": sum(1 for issue in issues if issue["severity"] == "blocker"),
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "root_cause_count": len(root_causes),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static tool-schema validation only; no tools are executed and no providers are called.",
        "summary": summary,
        "datasets": dataset_reports,
        "issues": sorted(issues, key=lambda row: (row["severity"], row["dataset"], row["issue_id"])),
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
    }
    md = tool_schema_validation_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="tool_schema_validation",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_tool_schemas_for_dataset(
    dataset_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = root / path
    base_tasks = _read_jsonl(path / "base_tasks.jsonl")
    instances = _read_jsonl(path / "instances.jsonl")
    rows = instances or [{"instance_id": _task_id(task), "condition": "base_task", "base_task": task} for task in base_tasks]
    issues: list[dict[str, Any]] = []
    tool_defs = _collect_tool_definitions(path, base_tasks, instances)
    code_registry_names = {str(spec.get("name")) for spec in load_code_registry_tool_specs()}
    code_registry_present = bool(code_registry_names)
    dataset_tool_manifest_present = any(
        (path / filename).exists()
        for filename in ("tools.json", "tool_schemas.json", "tools.yaml", "tool_schemas.yaml")
    )
    names = [tool["name"] for tool in tool_defs if tool.get("name")]
    for name, count in Counter(names).items():
        if count > 1:
            issues.append(_issue(path, root, "blocker", "duplicate_tool_name", name, f"Duplicate tool name `{name}` appears {count} times."))
    tools_by_name = {tool["name"]: tool for tool in tool_defs if tool.get("name")}

    referenced_by_tool: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        entity = _instance_id(row) or _base_task_id(row)
        refs = _referenced_tools(row)
        for ref in refs:
            referenced_by_tool[ref].append(entity)
    for tool in tool_defs:
        _validate_tool_definition(path, root, tool, issues, sorted(set(referenced_by_tool.get(str(tool.get("name")), []))))
    for tool_name, entities in sorted(referenced_by_tool.items()):
        if tool_name not in tools_by_name:
            issues.append(
                _issue(
                    path,
                    root,
                    "blocker",
                    "tool_not_found",
                    tool_name,
                    f"Tool `{tool_name}` is referenced by {len(set(entities))} task(s) but no schema definition was found.",
                    affected_tasks=sorted(set(entities)),
                    affected_tool=tool_name,
                )
            )
    for row in rows:
        entity = _instance_id(row) or _base_task_id(row)
        refs = _referenced_tools(row)
        for call in _tool_calls(row):
            _validate_call(path, root, entity, call, tools_by_name, issues)
        # Only warn about a missing tool environment when references cannot be
        # resolved at all. A repo-default code registry that covers every
        # referenced tool *is* the environment, so re-declaring it per dataset is
        # unnecessary noise (unresolved tools are still flagged as tool_not_found).
        refs_resolved = all(ref in tools_by_name for ref in refs)
        environment_known = (
            dataset_tool_manifest_present
            or _tool_environment_present(row)
            or (code_registry_present and refs_resolved)
        )
        if refs and not environment_known:
            issues.append(_issue(path, root, "warning", "missing_tool_environment_reference", entity, "Task references tools but does not name a tool environment."))

    _check_tool_drift(path, root, rows, issues)
    blockers = sum(1 for issue in issues if issue["severity"] == "blocker")
    root_causes = _root_cause_summary(issues)
    referenced_names = {tool for row in rows for tool in _referenced_tools(row)}
    return {
        "dataset": _rel(path, root),
        "tool_definition_count": len(tool_defs),
        "referenced_tool_count": len(referenced_names),
        "tool_schema_sources": {
            "dataset_manifest": dataset_tool_manifest_present,
            "code_registry": code_registry_present,
            "code_registry_tool_count": len(code_registry_names),
        },
        "unresolved_referenced_tools": sorted(referenced_names - set(tools_by_name)),
        "issue_count": len(issues),
        "blockers": blockers,
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "passed": blockers == 0,
        "issues": issues,
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
    }


def tool_schema_validation_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Tool Schema Validation",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Datasets scanned: {summary['dataset_count']}",
                f"- Issues: {summary['issue_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
            ],
        ),
        "## Root Cause Summary",
        "",
    ]
    root_causes = list(payload.get("root_causes") or [])
    if not root_causes:
        lines.append("- (none)")
    for row in root_causes[:50]:
        lines.append(
            f"- `{row['issue_type']}` tool=`{row['affected_tool']}` tasks={row['affected_task_count']}: {row['suggested_fix']}"
        )
    lines.extend(
        [
            "",
        "## Issues",
        "",
        ]
    )
    if not payload["issues"]:
        lines.append("- (none)")
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['dataset']}` `{issue['entity_id']}` `{issue['issue_type']}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def _collect_tool_definitions(
    path: Path,
    base_tasks: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    *,
    include_code_registry: bool = True,
) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    for filename in ("tools.json", "tool_schemas.json", "tools.yaml", "tool_schemas.yaml"):
        definitions.extend(_read_tool_file(path / filename))
    for row in [*base_tasks, *instances]:
        task = _task_from_row(row)
        for key in ("tools", "tool_specs", "available_tool_specs", "tool_schemas"):
            value = task.get(key) or row.get(key)
            definitions.extend(_normalize_tool_specs(value))
    if include_code_registry:
        # Dataset/inline schemas take precedence; the code registry fills the gaps
        # for the repo-default tool environment without creating false duplicates.
        existing = {str(spec.get("name")) for spec in definitions if spec.get("name")}
        for spec in load_code_registry_tool_specs():
            if str(spec.get("name")) not in existing:
                definitions.append(dict(spec))
    return definitions


def _read_tool_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, yaml.YAMLError):
        return []
    if isinstance(payload, dict):
        payload = payload.get("tools") or payload.get("tool_schemas") or payload.get("schemas") or payload
    return _normalize_tool_specs(payload)


def _normalize_tool_specs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        if any(key in value for key in ("name", "description", "input_schema", "parameters")):
            values = [value]
        else:
            values = [dict(spec, name=name) if isinstance(spec, dict) else {"name": name} for name, spec in value.items()]
    elif isinstance(value, list):
        values = [item for item in value if isinstance(item, dict)]
    else:
        return []
    out = []
    for spec in values:
        name = spec.get("name") or spec.get("tool_name")
        if not name:
            continue
        row = dict(spec)
        row["name"] = str(name)
        out.append(row)
    return out


def _validate_tool_definition(
    path: Path,
    root: Path,
    tool: dict[str, Any],
    issues: list[dict[str, Any]],
    referenced_tasks: list[str],
) -> None:
    name = str(tool.get("name") or "unknown")
    if not tool.get("description"):
        issues.append(_issue(path, root, "warning", "tool_missing_description", name, "Tool is missing a description."))
    input_schema = _input_schema(tool)
    output_schema = _output_schema(tool)
    if not input_schema:
        severity = "blocker" if referenced_tasks else "warning"
        issues.append(
            _issue(
                path,
                root,
                severity,
                "missing_input_schema",
                name,
                "Referenced tool is missing input schema." if referenced_tasks else "Unused tool is missing input schema.",
                affected_tasks=referenced_tasks,
                affected_tool=name,
            )
        )
    else:
        # Code-registry tools enforce argument requirements in code (including
        # conditional "one of A or B" rules that a flat `required` list cannot
        # express), so a missing static `required` list is not an authoring gap
        # for them. Only flag dataset-authored schemas, and accept anyOf/oneOf as
        # an explicit conditional-requirement surface.
        from_code_registry = tool.get("source") == "code_registry"
        has_conditional = bool(input_schema.get("anyOf") or input_schema.get("oneOf"))
        if (
            isinstance(input_schema, dict)
            and input_schema.get("properties")
            and "required" not in input_schema
            and not from_code_registry
            and not has_conditional
        ):
            issues.append(_issue(path, root, "warning", "tool_required_fields_missing", name, "Input schema has properties but no required field list."))
    if not output_schema:
        issues.append(
            _issue(
                path,
                root,
                "warning",
                "missing_output_schema",
                name,
                "Tool is missing output schema.",
                affected_tasks=referenced_tasks,
                affected_tool=name,
            )
        )
    if _has_simulated_outputs(tool) and "deterministic" not in tool and "determinism" not in tool:
        issues.append(_issue(path, root, "warning", "non_deterministic_tool_unmarked", name, "Simulated tool outputs are not marked deterministic or otherwise.", affected_tasks=referenced_tasks, affected_tool=name))


def _validate_call(
    path: Path,
    root: Path,
    entity: str,
    call: dict[str, Any],
    tools_by_name: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    name = str(call.get("tool") or call.get("tool_name") or call.get("name") or "")
    if not name:
        return
    tool = tools_by_name.get(name)
    if not tool:
        return
    args = call.get("arguments") or call.get("args") or call.get("input") or {}
    if not isinstance(args, dict):
        issues.append(_issue(path, root, "warning", "tool_call_args_not_mapping", entity, f"Arguments for `{name}` are not a mapping."))
        return
    schema = _input_schema(tool)
    properties = schema.get("properties") if isinstance(schema, dict) and isinstance(schema.get("properties"), dict) else {}
    required = schema.get("required") if isinstance(schema, dict) and isinstance(schema.get("required"), list) else []
    unknown_args = sorted(arg for arg in args if properties and arg not in properties)
    missing_required = sorted(arg for arg in required if arg not in args)
    if unknown_args:
        issues.append(_issue(path, root, "blocker", "argument_mismatch", entity, f"Call to `{name}` uses unknown arguments: {', '.join(unknown_args)}.", affected_tasks=[entity], affected_tool=name))
    if missing_required:
        issues.append(_issue(path, root, "warning", "tool_required_argument_missing", entity, f"Call to `{name}` omits required arguments: {', '.join(missing_required)}."))


def _check_tool_drift(path: Path, root: Path, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    pairs: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        pairs[_base_task_id(row)][_condition(row)].append(row)
    for base_id, grouped in pairs.items():
        clean_items = grouped.get("clean") or []
        if not clean_items:
            continue
        clean_tools = set(_referenced_tools(clean_items[0]))
        for intervention in grouped.get("intervention") or []:
            intervention_tools = set(_referenced_tools(intervention))
            if clean_tools == intervention_tools:
                continue
            intervention_obj = intervention.get("intervention") if isinstance(intervention.get("intervention"), dict) else {}
            kind = str(intervention_obj.get("family") or intervention_obj.get("type") or intervention_obj.get("intervention_type") or "")
            if not any(marker in kind for marker in TOOL_INTERVENTION_MARKERS):
                entity = _instance_id(intervention) or base_id
                issues.append(
                    _issue(
                        path,
                        root,
                        "blocker",
                        "clean_intervention_tool_drift",
                        entity,
                        "Tool references drift across clean/intervention pair for a non-tool intervention.",
                        affected_tasks=[entity],
                    )
                )


def _referenced_tools(row: dict[str, Any]) -> list[str]:
    task = _task_from_row(row)
    refs: list[str] = []
    for container in (task, row):
        for key in ("available_tools", "required_tools", "optional_tools", "gold_tool_sequence", "tools"):
            value = container.get(key)
            if isinstance(value, list):
                refs.extend(str(item.get("name") if isinstance(item, dict) else item) for item in value)
    for call in _tool_calls(row):
        name = call.get("tool") or call.get("tool_name") or call.get("name")
        if name:
            refs.append(str(name))
    return sorted({ref for ref in refs if ref and ref != "None"})


def _tool_calls(row: dict[str, Any]) -> list[dict[str, Any]]:
    task = _task_from_row(row)
    calls: list[dict[str, Any]] = []
    for container in (task, row):
        for key in ("tool_calls", "expected_tool_calls", "gold_tool_calls", "simulated_tool_calls"):
            value = container.get(key)
            if isinstance(value, list):
                calls.extend(item for item in value if isinstance(item, dict))
    return calls


def _tool_environment_present(row: dict[str, Any]) -> bool:
    task = _task_from_row(row)
    for container in (task, row):
        if any(container.get(key) for key in ("tool_environment", "tool_env", "environment", "simulated_environment")):
            return True
    return bool(_collect_inline_tool_specs(row))


def _collect_inline_tool_specs(row: dict[str, Any]) -> list[dict[str, Any]]:
    task = _task_from_row(row)
    out = []
    for key in ("tools", "tool_specs", "available_tool_specs", "tool_schemas"):
        out.extend(_normalize_tool_specs(task.get(key) or row.get(key)))
    return out


def _input_schema(tool: dict[str, Any]) -> dict[str, Any]:
    value = (
        tool.get("input_schema")
        or tool.get("inputSchema")
        or tool.get("parameters")
        or tool.get("args_schema")
        or tool.get("argsSchema")
        or tool.get("schema")
        or tool.get("json_schema")
    )
    return value if isinstance(value, dict) else {}


def _output_schema(tool: dict[str, Any]) -> dict[str, Any]:
    value = tool.get("output_schema") or tool.get("outputSchema") or tool.get("returns") or tool.get("response_schema") or tool.get("responseSchema")
    return value if isinstance(value, dict) else {}


def _has_simulated_outputs(tool: dict[str, Any]) -> bool:
    return any(key in tool for key in ("outputs", "responses", "fixtures", "simulated_outputs"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _task_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("base_task") if isinstance(row.get("base_task"), dict) else row


def _condition(row: dict[str, Any]) -> str:
    return str(row.get("condition") or ("intervention" if row.get("intervention") else "clean"))


def _base_task_id(row: dict[str, Any]) -> str:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    task = _task_from_row(row)
    value = intervention.get("base_task_id") or row.get("base_task_id") or task.get("task_id")
    if value:
        return str(value)
    instance_id = _instance_id(row)
    return instance_id.split(".", 1)[0] if instance_id and "." in instance_id else instance_id or "unknown"


def _task_id(task: dict[str, Any]) -> str | None:
    value = task.get("task_id") or task.get("id")
    return str(value) if value else None


def _instance_id(row: dict[str, Any]) -> str | None:
    value = row.get("instance_id") or row.get("id")
    return str(value) if value else None


def _issue(
    path: Path,
    root: Path,
    severity: str,
    issue_type: str,
    entity_id: str,
    message: str,
    *,
    affected_tasks: list[str] | None = None,
    affected_tool: str | None = None,
) -> dict[str, Any]:
    dataset = _rel(path, root)
    stable = hashlib.sha1(f"{dataset}|{issue_type}|{entity_id}|{message}".encode()).hexdigest()[:12]
    return {
        "issue_id": f"tool_{stable}",
        "severity": severity,
        "issue_type": issue_type,
        "dataset": dataset,
        "entity_id": entity_id,
        "affected_tool": affected_tool or _tool_from_message_or_entity(message, entity_id),
        "affected_tasks": affected_tasks or ([entity_id] if entity_id and entity_id != affected_tool else []),
        "affected_task_count": len(set(affected_tasks or ([] if entity_id == affected_tool else [entity_id]))),
        "message": message,
        "recommended_fix": _fix(issue_type),
    }


def _fix(issue_type: str) -> str:
    fixes = {
        "tool_not_found": "Add one schema definition for the referenced tool or remove the references.",
        "missing_input_schema": "Add a required input schema for referenced tools.",
        "missing_output_schema": "Add an output schema when provider-pilot scoring depends on tool outputs.",
        "duplicate_tool_name": "Rename or merge duplicate tool definitions.",
        "argument_mismatch": "Align task tool-call arguments with the input schema.",
        "clean_intervention_tool_drift": "Keep tool references invariant or mark the intervention as tool-related.",
    }
    return fixes.get(issue_type, "Review tool schema metadata.")


def _root_cause_summary(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        grouped[(str(issue.get("issue_type")), str(issue.get("affected_tool") or issue.get("entity_id")))].append(issue)
    rows = []
    for (issue_type, tool), items in grouped.items():
        tasks = sorted({task for item in items for task in item.get("affected_tasks", []) if task})
        severity = "blocker" if any(item.get("severity") == "blocker" for item in items) else "warning"
        rows.append(
            {
                "issue_type": issue_type,
                "affected_tool": tool,
                "severity": severity,
                "affected_task_count": len(tasks),
                "representative_tasks": tasks[:5],
                "symptom_count": len(items),
                "suggested_fix": _fix(issue_type),
            }
        )
    return sorted(rows, key=lambda row: (0 if row["severity"] == "blocker" else 1, -row["affected_task_count"], row["issue_type"], row["affected_tool"]))


def _tool_from_message_or_entity(message: str, entity_id: str) -> str:
    if "`" in message:
        parts = message.split("`")
        if len(parts) >= 3:
            return parts[1]
    return entity_id


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
