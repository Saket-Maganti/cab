# Endpoint Freeze

Acceptance: `CAB_ENDPOINTS_FROZEN_PRE_RUN`.

Primary: `clean_task_completion`, `intervention_task_completion`, `clean_conditioned_retained_completion`, `paired_completion_degradation`, `completion_acrs`, `safe_response_rate`, `false_abstention_rate`, `recovery_adjusted_completion`.

Secondary: `contract_compliance`, `justified_abstention`, `clarification_quality`, `recovery_attempt_rate`, `recovery_success_rate`, `tool_calls`, `model_calls`, `token_overhead`, `wall_time_overhead`, `worst_family_completion`, `worst_family_safe_response`.

The freeze predates model outcomes. Each estimator reports its own denominator;
safe response, compliance, abstention, and recovery cannot silently replace
substantive completion.
