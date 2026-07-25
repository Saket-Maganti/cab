# Baseline Agent Definitions

Status: design definitions only.

## Direct Answer Baseline

Answers without tools. Useful as a prior/guessing control. Cannot support tool-use robustness claims.

## ReAct Tool Baseline

Alternates reasoning, tool call, observation, and final answer. Useful for standard tool-use comparisons. Requires full trajectory logging.

## Function-Calling Baseline

Uses structured function calls. Useful for parser/schema robustness. Requires parse-outcome metadata.

## Self-Checking Agent

Performs a verification pass before final answer. Tests whether explicit self-checks reduce brittle successes.

## Recovery-Aware Agent

Has explicit retry/alternate-route policy after tool failure. Tests recoverability, not general intelligence.

## Abstention-Aware Agent

Can answer with uncertainty or clarification when evidence is insufficient. Must be evaluated with abstention correctness, not raw success alone.

## Oracle/Stub Engineering Baseline

Local engineering-only baseline for pipeline checks. It cannot support scientific claims.
