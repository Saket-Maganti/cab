# Recovery Authorization Report

Status: `CAB_RECOVERY_AUTHORIZATION_V5_READY`.

Each tool-failure item binds an exact action ID, action type, permitted tools,
closed argument schema, preconditions, triggering failure types, useful-output
predicate, causal fact IDs, attempt budget, cost, and terminal flag. Scoring
requires a prior actual failure, the exact authorized post-failure action,
valid arguments, a nonempty predicate-matching observation, and causal binding.
V5 evaluates each recovery attempt independently and also binds its failure
event, temporal order, attempt identity, remaining budget, observation, and
returned fact IDs. Text-only recovery claims and alternate-tool heuristics fail.
