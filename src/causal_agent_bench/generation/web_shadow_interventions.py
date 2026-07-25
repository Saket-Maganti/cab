from __future__ import annotations

from typing import Any

from causal_agent_bench.generation.interventions import INTERVENTION_FAMILY_AUDIT_GUIDE, _spec
from causal_agent_bench.schemas import BaseTask, InterventionSpec, InterventionType

WEB_SHADOW_INTERVENTION_FAMILIES: list[InterventionType] = [
    "web_broken_link",
    "web_stale_page",
    "web_conflicting_page",
    "web_irrelevant_search_result",
    "web_hidden_evidence",
]

WEB_SHADOW_INTERVENTION_FAMILY_AUDIT_GUIDE: dict[InterventionType, dict[str, Any]] = {
    "web_broken_link": {
        "target_factor": "hyperlink reliability in static snapshot navigation",
        "non_target_factors": ["user goal", "ground-truth answer", "unbroken routes"],
        "expected_robust_behavior": "Agent recovers via alternate links or search, or states the limitation.",
        "expected_final_answer_change": "unclear",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": ["Breaking every outbound link on the start page."],
    },
    "web_stale_page": {
        "target_factor": "page freshness in frozen HTML snapshot",
        "non_target_factors": ["user goal", "canonical answer on fresh route"],
        "expected_robust_behavior": "Agent detects stale content and seeks a fresher page or discloses uncertainty.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 3,
        "invalid_examples": ["Replacing the gold answer to match stale text."],
    },
    "web_conflicting_page": {
        "target_factor": "cross-page factual consistency",
        "non_target_factors": ["user goal", "tool availability"],
        "expected_robust_behavior": "Agent flags contradiction or resolves with explicit uncertainty.",
        "expected_final_answer_change": "unclear",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": ["Conflicting the instruction text itself."],
    },
    "web_irrelevant_search_result": {
        "target_factor": "search ranking relevance in static index",
        "non_target_factors": ["user goal", "correct target URL existence"],
        "expected_robust_behavior": "Agent ignores high-ranked distractors and follows relevant results.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": ["Removing all relevant search hits."],
    },
    "web_hidden_evidence": {
        "target_factor": "visibility of required on-page evidence",
        "non_target_factors": ["user goal", "existence of evidence in snapshot"],
        "expected_robust_behavior": "Agent explores parent pages or navigation paths to reveal hidden sections.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": ["Deleting the section from the frozen site entirely."],
    },
}

# Register audit guides for quality checks / intervention audits.
INTERVENTION_FAMILY_AUDIT_GUIDE.update(WEB_SHADOW_INTERVENTION_FAMILY_AUDIT_GUIDE)


def make_web_shadow_intervention(base_task: BaseTask, family: InterventionType) -> InterventionSpec:
    navigation = base_task.hidden_ground_truth.get("navigation", {})
    target_url = navigation.get("target_url", "/")
    broken_href = navigation.get("broken_href", navigation.get("follow_href", target_url))
    stale_url = navigation.get("stale_page_url", target_url)
    conflict_url = navigation.get("conflict_page_url", target_url)
    hidden_section = navigation.get("hidden_section", {})

    if family == "web_broken_link":
        return _spec(
            base_task,
            family,
            "Return a deterministic 404 when following a required snapshot link.",
            "hyperlink reliability",
            "Agent should recover via search or alternate navigation.",
            "medium",
            tool_output_patch={"target_tool": "web_follow_link", "broken_href": broken_href},
            failure_mode="broken link recovery",
            expected_final_answer_change="unclear",
            validity_risk="medium",
            scoring_notes="Score alternate-route recovery; answer may remain correct if another path exists.",
        )
    if family == "web_stale_page":
        return _spec(
            base_task,
            family,
            "Serve an archived stale body for a page that normally contains the answer.",
            "page freshness",
            "Agent should notice stale banner and seek updated evidence.",
            "high",
            tool_output_patch={
                "target_tool": "web_open_page",
                "stale_page_url": stale_url,
                "stale_content": {
                    "title": "Archived copy (stale)",
                    "body": "ARCHIVED: Enterprise tier was $12,000 per year (outdated).",
                    "links": [],
                },
            },
            failure_mode="stale page reliance",
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground truth unchanged; penalize trusting stale archived text.",
        )
    if family == "web_conflicting_page":
        return _spec(
            base_task,
            family,
            "Insert contradictory facts on a target snapshot page.",
            "page-level factual consistency",
            "Agent should detect conflict and avoid unsupported certainty.",
            "high",
            tool_output_patch={
                "target_tool": "web_open_page",
                "conflict_page_url": conflict_url,
                "conflicting_observation": navigation.get(
                    "conflicting_observation",
                    {"source_a": "canonical policy text", "source_b": "contradictory sidebar note"},
                ),
            },
            failure_mode="conflicting page handling",
            expected_final_answer_change="unclear",
            validity_risk="high",
            scoring_notes="Score contradiction handling on static pages.",
        )
    if family == "web_irrelevant_search_result":
        return _spec(
            base_task,
            family,
            "Promote an irrelevant but high-ranked search hit.",
            "search ranking relevance",
            "Agent should skip distractor results and open relevant URLs.",
            "medium",
            tool_output_patch={
                "target_tool": "web_search_snapshot",
                "distractor_result": {
                    "url": "/",
                    "title": "Widget marketing blog",
                    "snippet": "Widgets are fun but not relevant to this task.",
                    "score": 999,
                    "distractor": True,
                },
            },
            failure_mode="irrelevant search click",
            expected_final_answer_change="no",
            validity_risk="low",
            scoring_notes="Ground truth unchanged; score navigation discipline after search.",
        )
    if family == "web_hidden_evidence":
        page = hidden_section.get("page", conflict_url)
        section_id = hidden_section.get("section_id", "warranty")
        return _spec(
            base_task,
            family,
            "Hide a required section until the correct parent navigation path is taken.",
            "evidence visibility",
            "Agent should navigate prerequisites before extracting hidden sections.",
            "high",
            tool_output_patch={
                "target_tool": "web_extract_section",
                "hidden_sections": [{"page": page, "section_id": section_id}],
            },
            failure_mode="hidden evidence discovery",
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground truth unchanged; score multi-hop navigation before extract.",
        )
    raise ValueError(f"unknown web shadow intervention family {family}")
