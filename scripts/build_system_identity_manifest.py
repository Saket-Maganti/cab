#!/usr/bin/env python3
"""Freeze hashed system components and emit the strict identity schema."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.runners.system_identity import (
    PRIMARY_ADAPTER_LANE,
    CompatibilityRow,
    DecodingConfiguration,
    EvaluatedSystemIdentity,
    assert_compatible_lane,
    content_sha256,
    system_identity_hash,
)


def build(
    *,
    contract_path: Path,
    matrix_path: Path,
    ablation_path: Path,
    output_path: Path,
    schema_path: Path,
) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
    rows = [CompatibilityRow.model_validate(row) for row in matrix["rows"]]
    smoke = {
        row.model_category: bool(
            assert_compatible_lane(
                rows,
                model_category=row.model_category,
                adapter_lane=PRIMARY_ADAPTER_LANE,
            )
        )
        for row in rows
    }
    components = {
        "chat_template": content_sha256(contract["chat_template"]["content"]),
        "system_prompt": content_sha256(contract["system_prompt"]["content"]),
        "tool_adapter_source": _sha256_file(ROOT / contract["tool_adapter"]["source"]),
        "parser_source": _sha256_file(ROOT / contract["parser"]["source"]),
        "tool_protocol": system_identity_hash(contract["tool_protocol"]),
        "decoding": system_identity_hash(contract["decoding"]),
        "context_limit": content_sha256(str(contract["context_limit"])),
        "stop_conditions": system_identity_hash(
            {"stop_conditions": contract["stop_conditions"]}
        ),
        "compatibility_matrix": _sha256_file(matrix_path),
        "adapter_ablation_plan": _sha256_file(ablation_path),
        "identity_schema_source": _sha256_file(
            ROOT / "src/causal_agent_bench/runners/system_identity.py"
        ),
    }
    fixture = EvaluatedSystemIdentity(
        model_id="fixture-model",
        model_revision="fixture-revision-1",
        quantization="none",
        tokenizer_id="fixture-tokenizer",
        tokenizer_revision="fixture-tokenizer-revision-1",
        tokenizer_hash=content_sha256("fixture-tokenizer-bytes"),
        chat_template_id=contract["chat_template"]["id"],
        chat_template_hash=components["chat_template"],
        system_prompt_id=contract["system_prompt"]["id"],
        system_prompt_hash=components["system_prompt"],
        tool_adapter_id=contract["tool_adapter"]["id"],
        tool_adapter_version=contract["tool_adapter"]["version"],
        tool_adapter_hash=components["tool_adapter_source"],
        parser_id=contract["parser"]["id"],
        parser_version=contract["parser"]["version"],
        parser_hash=components["parser_source"],
        tool_protocol_id=contract["tool_protocol"]["id"],
        tool_protocol_hash=components["tool_protocol"],
        decoding=DecodingConfiguration.model_validate(contract["decoding"]),
        context_limit=contract["context_limit"],
        stop_conditions=contract["stop_conditions"],
        adapter_lane=PRIMARY_ADAPTER_LANE,
    )
    payload: dict[str, Any] = {
        "schema_version": "cab_evaluated_system_manifest_frozen_v1",
        "contract": contract,
        "component_hashes": components,
        "compatibility_matrix": matrix,
        "adapter_ablation_plan": ablation,
        "primary_lane_compatibility_smoke": smoke,
        "primary_lane_is_uniform": len(
            {row.primary_adapter for row in rows if row.primary_lane_supported}
        )
        == 1,
        "fixture_binding_demonstration": {
            "evidence_class": "FIXTURE_ONLY",
            "scientific_evidence": False,
            "system_identity_hash": fixture.system_identity_hash,
        },
        "model_revision_binding_pending": True,
        "scientific_execution_allowed_before_binding": False,
        "comparisons_with_adapter_difference_label": "system_comparison",
    }
    payload["frozen_contract_hash"] = system_identity_hash(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(
            EvaluatedSystemIdentity.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "output": str(output_path),
        "schema": str(schema_path),
        "frozen_contract_hash": payload["frozen_contract_hash"],
        "primary_lane_is_uniform": payload["primary_lane_is_uniform"],
        "model_revision_binding_pending": True,
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "configs/pre_run/evaluated_system_manifest.json",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=ROOT / "configs/pre_run/system_compatibility_matrix.json",
    )
    parser.add_argument(
        "--ablation",
        type=Path,
        default=ROOT / "configs/pre_run/adapter_ablation_plan.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "reports/pre_run_scientific_hardening/evaluated_system_identity_frozen.json"
        ),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=ROOT / "configs/pre_run/evaluated_system_identity.schema.json",
    )
    args = parser.parse_args(argv)
    print(
        json.dumps(
            build(
                contract_path=args.contract.resolve(),
                matrix_path=args.matrix.resolve(),
                ablation_path=args.ablation.resolve(),
                output_path=args.output.resolve(),
                schema_path=args.schema.resolve(),
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
