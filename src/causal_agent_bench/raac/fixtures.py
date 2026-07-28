"""Deterministic, model-free RAAC fixture scenarios."""

from __future__ import annotations

from pydantic import Field

from causal_agent_bench.raac.controller import RAACController
from causal_agent_bench.raac.signals import ObservationEnvelope
from causal_agent_bench.raac.types import PolicyVariant, RAACDecision, StrictModel


class FixtureScenario(StrictModel):
    name: str
    description: str
    events: list[ObservationEnvelope] = Field(min_length=1)
    default_variant: PolicyVariant = PolicyVariant.RAAC_FULL


class FixtureRun(StrictModel):
    scenario: str
    variant: PolicyVariant
    decisions: list[RAACDecision]
    final_controller_metadata: dict[str, object]
    evidence_class: str = "FIXTURE_ONLY"
    scientific_evidence: bool = False
    paper_eligible: bool = False


def _success(answer: str = "fixture answer") -> ObservationEnvelope:
    return ObservationEnvelope(
        parsed_output={"value": answer},
        evidence_count=1,
        minimum_evidence=1,
        success_claimed=True,
        success_verifiable=True,
        candidate_answer=answer,
    )


FIXTURE_SCENARIOS: dict[str, FixtureScenario] = {
    "clean_success": FixtureScenario(
        name="clean_success",
        description="A supported clean result requires no extra RAAC action.",
        events=[_success()],
        default_variant=PolicyVariant.RAAC_LIGHT,
    ),
    "transient_tool_failure": FixtureScenario(
        name="transient_tool_failure",
        description="A single tool error is followed by a successful bounded retry.",
        events=[ObservationEnvelope(error="transient", tool_name="primary"), _success()],
    ),
    "persistent_failure": FixtureScenario(
        name="persistent_failure",
        description="Repeated tool failures exhaust retry and alternate-route ceilings.",
        events=[
            ObservationEnvelope(error="persistent", tool_name="primary")
            for _ in range(6)
        ],
    ),
    "conflicting_observations": FixtureScenario(
        name="conflicting_observations",
        description="A contradiction triggers a cross-source check.",
        events=[ObservationEnvelope(contradicts_previous=True), _success()],
    ),
    "stale_memory": FixtureScenario(
        name="stale_memory",
        description="A stale observable timestamp triggers current-evidence verification.",
        events=[
            ObservationEnvelope(
                parsed_output={"value": "old"},
                observed_at=10,
                reference_time=100,
                max_staleness_seconds=20,
            ),
            _success(),
        ],
    ),
    "malformed_output": FixtureScenario(
        name="malformed_output",
        description="Unparseable output triggers bounded recovery.",
        events=[ObservationEnvelope(raw_output="{not-json"), _success()],
    ),
    "partial_output": FixtureScenario(
        name="partial_output",
        description="A marked partial result is not treated as complete.",
        events=[ObservationEnvelope(parsed_output={"partial": True}, partial=True), _success()],
    ),
    "premature_success_signal": FixtureScenario(
        name="premature_success_signal",
        description="An unverifiable success claim triggers final verification.",
        events=[
            ObservationEnvelope(
                parsed_output={"status": "success"},
                success_claimed=True,
                success_verifiable=False,
                candidate_answer="unsupported",
            ),
            _success(),
        ],
    ),
    "insufficient_evidence": FixtureScenario(
        name="insufficient_evidence",
        description="Insufficient evidence is verified only within the contract.",
        events=[
            ObservationEnvelope(
                evidence_count=0,
                minimum_evidence=2,
                insufficient_evidence=True,
            )
            for _ in range(5)
        ],
    ),
    "clarification": FixtureScenario(
        name="clarification",
        description="Resolvable underspecification requests one clarification.",
        events=[
            ObservationEnvelope(
                insufficient_evidence=True,
                clarification_possible=True,
                minimum_evidence=1,
            ),
            _success(),
        ],
    ),
    "correct_abstention": FixtureScenario(
        name="correct_abstention",
        description="Persistent unsupported evidence ends in a bounded abstention.",
        events=[
            ObservationEnvelope(error="persistent", tool_name="primary")
            for _ in range(8)
        ],
    ),
    "false_abstention": FixtureScenario(
        name="false_abstention",
        description="ABSTAIN_ONLY exposes over-abstention on a recoverable transient failure.",
        events=[ObservationEnvelope(error="transient", tool_name="primary"), _success()],
        default_variant=PolicyVariant.ABSTAIN_ONLY,
    ),
    "alternate_route_recovery": FixtureScenario(
        name="alternate_route_recovery",
        description="A failed retry switches once to an alternate route and succeeds.",
        events=[
            ObservationEnvelope(error="transient", tool_name="primary"),
            ObservationEnvelope(error="persistent", tool_name="primary"),
            _success(),
        ],
        default_variant=PolicyVariant.RAAC_LIGHT,
    ),
}


def run_fixture_scenario(
    name: str,
    *,
    variant: PolicyVariant | str | None = None,
) -> FixtureRun:
    scenario = FIXTURE_SCENARIOS[name]
    selected = PolicyVariant(variant or scenario.default_variant)
    controller = RAACController(selected, evidence_class="FIXTURE_ONLY")
    decisions: list[RAACDecision] = []
    for event in scenario.events:
        decision = controller.evaluate(event)
        decisions.append(decision)
        if decision.next_state.value in {"ANSWER", "ABSTAIN", "TERMINATE"}:
            break
    if controller.machine.state.value in {"ANSWER", "ABSTAIN"}:
        controller.finalize()
    return FixtureRun(
        scenario=name,
        variant=selected,
        decisions=decisions,
        final_controller_metadata=controller.metadata(),
    )


def run_all_fixtures() -> list[FixtureRun]:
    return [run_fixture_scenario(name) for name in sorted(FIXTURE_SCENARIOS)]
