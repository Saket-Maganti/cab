import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

V3_FILES = [
    "docs/BENCHMARK_THEORY_OF_CHANGE.md",
    "docs/CONTROLLED_INTERVENTION_ASSUMPTIONS.md",
    "docs/ACRS_FORMALIZATION_AND_LIMITATIONS.md",
    "docs/INTERVENTION_TAXONOMY_V2.md",
    "docs/INTERVENTION_FAMILY_VALIDITY_CHECKLIST.md",
    "data/compact20_reviewed/compact20_candidate_quality_schema.json",
    "experiments/STATISTICAL_ANALYSIS_PLAN.md",
    "docs/SCORER_ROBUSTNESS_POLICY.md",
    "paper/CLAIM_SAFE_ABSTRACT_TEMPLATES.md",
    "release/REPRODUCIBILITY_COMMANDS_NO_PROVIDER.md",
    "reports/CAB_V3_NO_EXECUTION_UPGRADE_FINAL_REPORT.md",
]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v3_required_files_exist_fixture_only_not_evidence():
    missing = [path for path in V3_FILES if not (ROOT / path).is_file()]
    assert missing == []


def test_claim_safe_abstract_templates_keep_result_placeholders_fixture_only_not_evidence():
    text = _read("paper/CLAIM_SAFE_ABSTRACT_TEMPLATES.md")
    assert "RESULT_REQUIRED" in text
    forbidden = ["we find that", "we show that", "outperforms", "achieves 0.", "achieves 1."]
    lowered = text.lower()
    assert not any(phrase in lowered for phrase in forbidden)


def test_no_proxy_review_counted_as_human_fixture_only_not_evidence():
    status = _read("data/human_validation/compact20_real_review/HUMAN_REVIEW_PACKET_STATUS.md")
    final = _read("reports/CAB_V3_NO_EXECUTION_UPGRADE_FINAL_REPORT.md")
    assert "AI proxy reviews counted as human: `false`" in status
    assert "human validation: `0`" in final
    assert "C10: blocked" in final


def test_no_api_keys_or_paid_calls_in_v3_docs_fixture_only_not_evidence():
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9]{12,}"),
        re.compile(r"api_key:\s*['\"]?[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
        re.compile(r"OPENAI_API_KEY=[A-Za-z0-9_\-]{8,}"),
        re.compile(r"allow_paid_calls:\s*true", re.IGNORECASE),
    ]
    checked = [ROOT / path for path in V3_FILES]
    checked.extend(
        [
            ROOT / "release/REPRODUCIBILITY_COMMANDS_WITH_PROVIDER_TEMPLATE.md",
            ROOT / "configs/ablations/README_V3_NO_EXECUTION.md",
        ]
    )
    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert not any(pattern.search(text) for pattern in secret_patterns), path


def test_intervention_taxonomy_has_validity_checks_fixture_only_not_evidence():
    text = _read("docs/INTERVENTION_TAXONOMY_V2.md")
    required = [
        "intended factor changed",
        "invariants",
        "expected failure mode",
        "valid examples",
        "invalid/confounded examples",
        "scorer risks",
        "human-review questions",
        "exclusion criteria",
        "abstention_required_ambiguity",
    ]
    for phrase in required:
        assert phrase in text


def test_release_and_final_gate_stay_blocked_fixture_only_not_evidence():
    assert (ROOT / "release" / "MANIFEST.json").exists()
    release_text = _read("release/RELEASE_READINESS_V2.md")
    gate_text = _read("reports/CAB_V3_NEXT_EXECUTION_GATE.md")
    final_text = _read("reports/CAB_V3_NO_EXECUTION_UPGRADE_FINAL_REPORT.md")
    assert "blocked" in release_text.lower()
    assert "Do Not Run Yet" in gate_text
    assert "provider calls: none" in final_text
    assert "CAB_V3_NO_EXECUTION_UPGRADE_COMPLETE" in final_text
