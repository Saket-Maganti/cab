# Recovery Authorization V5 Report

Status: `CAB_RECOVERY_AUTHORIZATION_V5_READY`. Passed `11`
of `11` recovery attacks and controls. Each attempt records its failure
event, exact action/tool/arguments, step range, attempt number, remaining budget,
observation hash, returned facts, and predicate results. Authorization never
flows to later steps, another attempt's observation, or an unrelated tool.
`task_recovered` additionally requires the correct final answer.
