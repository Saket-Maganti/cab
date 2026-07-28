# RAAC fairness and budget policy

Status: `DESIGN_ONLY`. This policy defines comparisons; it contains no measured
costs or effectiveness results.

## Two mandatory comparison modes

### Equal-budget

All treatment arms receive the same ceiling:

| Resource | Shared ceiling |
|---|---:|
| Extra model calls | 8 |
| Extra tool calls | 6 |
| Same-tool retries | 2 |
| Alternate routes | 2 |
| Verification steps | 3 |
| Clarification steps | 1 |
| Extra tokens | 1,536 |
| Wall clock | 90 seconds |

An arm may leave allowance unused. Realized overhead, not merely the allowance,
is reported. The base agent and RAAC controller together must remain within the
predeclared total run limits; unused budget is not converted into extra samples
or a larger context for one arm.

### Practical-budget

Each policy uses its native resource contract. LIGHT and FULL may therefore
have different ceilings. This comparison estimates practical deployment
trade-offs, not an equal-compute causal contrast. Results from the two modes
must not be pooled under one treatment estimate.

## Accounting rules

RAAC overhead is logged separately for:

- extra model calls;
- extra tool calls;
- retries and alternate routes;
- verification and clarification steps;
- extra tokens;
- controller wall-clock time.

All counts start at zero for each trajectory. Clean supported trajectories must
show zero RAAC recovery overhead. Base-agent work is still recorded by the
existing runner counters and must not be relabeled as RAAC overhead.

Provider retries caused by rate limits or transport errors remain provider
infrastructure overhead. They do not count as agent recovery, and the
trajectory must preserve the infrastructure-failure distinction.

## Clean-performance parity

The preregistered clean-side checks are:

1. excess tool-call rate;
2. excess model-call and token overhead;
3. latency overhead;
4. clean success degradation;
5. false abstention.

No intervention on a clean, observably supported success is the default policy.
A clean degradation or over-abstention finding must be reported, not hidden by
an intervention-only aggregate.

## Termination and fail-closed behavior

Every policy declares all ceilings before execution. A decision that cannot be
funded is replaced by a legal bounded fallback: alternate route when available,
otherwise qualified answer or abstention. Infrastructure failure terminates
with a distinct reason. The controller also has a hard decision-count bound
derived from its contract, preventing zero-cost control loops.

Checkpoint restore validates the policy hash, compute contract, state history,
contiguous trace indices, and realized overhead. A mismatch fails closed.

## Evidence boundaries

Configs and pseudocode are `DESIGN_ONLY`; code and runner plumbing are
`ENGINEERING_ONLY`; deterministic scenarios are `FIXTURE_ONLY`. A run inherits
its input evidence class and RAAC never upgrades it. Oracle controls stay
engineering-only. Paper eligibility requires the repository's independent
audit and evidence-promotion gates.
