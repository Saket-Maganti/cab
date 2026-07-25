"""Benchmark contamination and memorization audit utilities."""

from causal_agent_bench.contamination.audit import (
    apply_canary_metadata,
    assign_canary_strings,
    contamination_report_markdown,
    run_contamination_audit,
    template_fingerprint,
)

__all__ = [
    "apply_canary_metadata",
    "assign_canary_strings",
    "contamination_report_markdown",
    "run_contamination_audit",
    "template_fingerprint",
]
