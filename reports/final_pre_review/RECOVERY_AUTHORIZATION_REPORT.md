# Recovery Authorization Report

Status: `CAB_RECOVERY_AUTHORIZATION_V4_READY`.

Each tool-failure item binds an exact action ID, action type, permitted tools,
closed argument schema, preconditions, triggering failure types, useful-output
predicate, causal fact IDs, attempt budget, cost, and terminal flag. Scoring
requires a prior actual failure, the exact authorized post-failure action,
valid arguments, a nonempty predicate-matching observation, and causal binding.
Text-only recovery claims and alternate-tool heuristics cannot pass v4.
