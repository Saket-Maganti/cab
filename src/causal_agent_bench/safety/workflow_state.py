"""Canonical workflow states for the provider-free maximum-ceiling gate.

These are repository/workflow states, not per-run completion states.  Keeping
them in one enum prevents validators and tests from maintaining stale copied
sets of accepted strings.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    """Authoritative states emitted by the maximum-ceiling workflow gate."""

    ICLR_BUILD_INCOMPLETE = "ICLR_BUILD_INCOMPLETE"
    METHODOLOGY_READY = "METHODOLOGY_READY"
    HUMAN_VALIDATION_REQUIRED = "HUMAN_VALIDATION_REQUIRED"
    HUMAN_REVIEW_PENDING = "HUMAN_REVIEW_PENDING"
    HUMAN_REVIEW_INCOMPLETE = "HUMAN_REVIEW_INCOMPLETE"
    ADJUDICATION_PENDING = "ADJUDICATION_PENDING"
    C10_PENDING = "C10_PENDING"
    C10_FAILED = "C10_FAILED"
    SLICE_LOCK_PENDING = "SLICE_LOCK_PENDING"
    PROVIDER_APPROVAL_PENDING = "PROVIDER_APPROVAL_PENDING"
    COMPACT20_READY = "COMPACT20_READY"
    COMPACT20_AUDIT_PENDING = "COMPACT20_AUDIT_PENDING"
    COMPACT20_AUDIT_REQUIRED = "COMPACT20_AUDIT_REQUIRED"
    SCALE100_READY = "SCALE100_READY"
    NATURALISTIC_TRANSFER_READY = "NATURALISTIC_TRANSFER_READY"
    ICLR_EMPIRICAL_PACKAGE_READY = "ICLR_EMPIRICAL_PACKAGE_READY"
    ICLR_SUBMISSION_CANDIDATE = "ICLR_SUBMISSION_CANDIDATE"
    PAPER_CANDIDATE_READY = "PAPER_CANDIDATE_READY"


LIVE_EXECUTION_STATES = frozenset({WorkflowState.COMPACT20_READY})
PAPER_ELIGIBLE_STATES = frozenset({WorkflowState.PAPER_CANDIDATE_READY})


def parse_workflow_state(value: str | WorkflowState) -> WorkflowState:
    """Return a canonical state or raise ``ValueError`` for an unknown value."""

    return value if isinstance(value, WorkflowState) else WorkflowState(value)


def workflow_state_allows_live_execution(
    value: str | WorkflowState,
) -> bool:
    """Whether a workflow state can ever permit a live scientific run.

    Other independent gates (approval, immutable manifests, budgets, human
    review, and contamination checks) must still pass.  This helper only
    captures the state-machine invariant.
    """

    return parse_workflow_state(value) in LIVE_EXECUTION_STATES


def workflow_state_allows_paper_evidence(
    value: str | WorkflowState,
) -> bool:
    """Whether a workflow state can ever permit paper-eligible evidence."""

    return parse_workflow_state(value) in PAPER_ELIGIBLE_STATES


__all__ = [
    "LIVE_EXECUTION_STATES",
    "PAPER_ELIGIBLE_STATES",
    "WorkflowState",
    "parse_workflow_state",
    "workflow_state_allows_live_execution",
    "workflow_state_allows_paper_evidence",
]
