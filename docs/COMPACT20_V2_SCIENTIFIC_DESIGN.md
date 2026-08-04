# Compact-20 V2 scientific design

`compact20-review-ready-v2`

This document describes the design a reviewer is asked to judge. It contains no
task content, no answers, and no private identifiers.

## The unit of evaluation is a pair

The scientific unit is not a task. It is a **pair**: one base task instantiated
twice.

```text
base task -> clean instance
          -> intervention instance = operator(clean instance)
```

The intervention instance is *produced from* the clean instance by applying
exactly one executable environment operator. It is never produced by selecting a
different expected route and relabelling the row. Every pair carries an
enumerated structural diff, and a fail-closed isolation audit proves that
exactly one intended factor changed and that every declared invariant held.

## Composition

- 20 pairs; 4 intervention families x 5 pairs.
- 8 domains, no domain above 3 pairs.
- Difficulty: 4 easy, 8 medium, 4 hard, 4 stress.
- 16 semantically distinct objectives among the 16 non-anchor pairs.
- 4 true controlled anchors, one per family.

"Distinct" is not "a distinct identifier". Diversity is measured from objective
signatures built out of task archetype, structural schema signature, required
operation signature, gold-derivation signature and goal token set, plus a
shingle-similarity check across prompts. Anchors are excluded from the
uniqueness count and validated separately.

## True anchors

An anchor is a controlled repetition of one of the 16 objectives. It must
preserve the semantic objective, the answer logic, the difficulty, the
intervention family, the route requirement, the required inputs and the whole
multiset of decision-relevant numeric values. It may vary only record order and
identifier labels. The anchor validator checks each of those conditions
directly, so an anchor cannot be an unrelated row carrying a boolean flag.

## Deconfounding family from response type

The previous packet mapped each intervention family to exactly one required
response type, so family and response type were perfectly confounded. The frozen
V2 matrix breaks that:

| Intervention family | Completion | Recovery | Clarification | Abstention | Total |
|---|---:|---:|---:|---:|---:|
| Tool removal | 2 | 2 | 0 | 1 | 5 |
| Tool failure | 1 | 3 | 1 | 0 | 5 |
| Memory corruption | 2 | 0 | 2 | 1 | 5 |
| Observation conflict | 2 | 0 | 2 | 1 | 5 |
| **Total** | **7** | **5** | **5** | **3** | **20** |

No family maps to a single response type, and no response type is confined to a
single family. The matrix was frozen before any review or execution and is never
re-optimised after observing outcomes. The confounding audit also publishes the
domain x family, difficulty x family, archetype x family and route x difficulty
matrices.

## The four operators

Each operator is an executable transformation of a concrete environment.

- **`remove_tool`** revokes exactly one capability. Every other tool, all
  evidence, all memory and the goal are preserved. Removing a tool does *not*
  by itself make abstention correct.
- **`inject_tool_failure`** makes a declared tool fail through the real tool
  runtime with one of its declared failure modes. The tool stays declared.
- **`corrupt_memory_field`** replaces a previously valid, task-critical memory
  field with a stale or unusable value. Corrupting a field that never existed,
  or that has no valid clean predecessor, is refused.
- **`inject_conflicting_observation`** changes one field of one peer source so
  that two sources genuinely disagree. Injecting an identical value is refused,
  so a conflict cannot be declared without a conflicting observation.

## Tool contracts and evidence

Every tool declares `tool_id`, capability, the single source it reads, its
allowed arguments, its returned field projection, its failure modes and its
authorization scope. A tool returns a projection of exactly one source. There is
no general-purpose artifact reader in the scientific route: `read_file` and its
relatives are rejected by both the contract audit and the runtime.

Artifacts contain primitive facts only. The evidence scanner rejects
answer-bearing field names and their synonyms, answer phrases, and any record
that reproduces a gold string verbatim. Where the answer names an identifier
that also appears in the evidence — which is unavoidable, because selecting that
identifier *is* the task — the scanner reports it as an identifier echo rather
than failing.

## Route requirements

Route validation runs against the real environment and the real tool registry.
Private gold is touched once, at the final validation boundary; it never reaches
tool execution, observation creation, fact extraction, route search or
recovery-authorization matching.

- **Completion** requires every required input to resolve, no blocking conflict,
  a correct derived answer and contract compliance.
- **Recovery** requires an observed loss, an authorized fallback matched exactly
  on tool id and arguments, the attempt strictly after the loss, remaining
  budget, the lost inputs actually supplied by that fallback observation, and a
  correct final answer. Recovery credit is never inherited from an unrelated
  later success.
- **Clarification** requires a task-critical input that is unresolved after full
  route exhaustion *including* any authorized recovery, no completion route
  without it, and a specific question naming that input. Generic requests score
  zero.
- **Abstention** requires every declared route to be executed or eliminated, the
  blocked input to remain underivable by the declared reasoning closure
  (arithmetic, comparison, sorting, set membership, filtering, date reasoning,
  conjunction and direct lookup), no authorized recovery route, and no targeted
  clarification that the counterparty could answer.

## Clarification versus abstention

The distinction is the **counterparty**. Each objective declares who the
responder can actually ask and which inputs that counterparty holds. If the
blocked input is something they hold — a contracted threshold, a lead-time
limit, which of their own records is authoritative — a single targeted question
resolves it and clarification is correct. If the blocked input is external
system state the counterparty cannot supply — another team's calendar, a
warehouse feed, an internal holiday calendar owned by a different function —
then no question they can answer resolves it and abstention is correct.

This is a modelling decision, frozen prospectively and stated openly, and it is
exactly the kind of judgement Stage-1 reviewers are asked to assess under
`response_space_structurally_valid` and `intervention_realistic`.

## What the executable validation does and does not prove

Route validation proves that the environment genuinely supports the required
route: that the tools exist, the observations are real, the derivation runs on
observations alone, and the hostile cases are refused. Each objective also
carries a hand-written expected answer, independent of the executable
derivation, and generation fails if the two disagree — so the check is a real
cross-check rather than a tautology.

It does **not** prove that the gold is the right answer to the user's question.
That is a human judgement, and it is exactly what Stage 2 of the review exists
to obtain.
