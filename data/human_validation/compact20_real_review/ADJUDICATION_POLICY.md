# Compact-20 Adjudication Policy

Adjudication begins only after both initial review sheets are locked and raw
agreement is computed.

## Required cases

Create one `adjudication.csv` row for every candidate × dimension where the
independent labels differ. Link the exact reviewer IDs and labels with `|`
separators.

## Adjudicator eligibility

The adjudicator must be qualified and registered with an `adj_...` privacy-safe
ID. They cannot be either reviewer for the candidate, a candidate author, or a
person with a disclosed conflict. AI/proxy adjudication is forbidden.

## Decision

The adjudicator reads the candidate packet and both rationales, selects one
allowed final value for that dimension, writes a substantive rationale, and
records a timezone-aware timestamp. Preserve minority concerns in the
rationale. If evidence is insufficient, choose the dimension's `unclear` or
revision/exclusion value; never choose a pass value merely to clear C10.

Adjudication resolves a final label but does not change or replace initial
labels, raw agreement, kappa/alpha inputs, prevalence diagnostics, or the
reported disagreement rate.

Invalid linkage, duplicated decisions, missing rationale, a non-separate
adjudicator, or unresolved disagreement keeps C10 pending.
