# Intervention Reachability Report

Acceptance: `CAB_INTERVENTION_REACHABILITY_GATE_READY`.

- Compact v2 intervention instances audited: 20
- Passed: 20
- Failed: 0
- Collection hash: `c7b5c8d2be711cc9d29c87ed225cddf134221099a841a9ff2fbde9ec84b825d6`
- Failure-code counts: `{}`

Each audit represents required fact → source artifact → accessible tool →
permitted action → intermediate evidence → valid response. The CLI commands
`cab benchmark reachability-check` and `cab benchmark intervention-audit` fail
closed on an impossible or policy-inconsistent route.
