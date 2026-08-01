# Held-Out Dataset Release Governance

Status: pre-execution policy; no held-out scientific results are released.

This policy governs confirmatory and challenge material registered in
`data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json`. It supplements
`DATASET_VERSIONING_AND_RELEASE_POLICY.md`, `SECURITY_AND_PRIVACY.md`, and
`DATA_LICENSE.md`.

## Release tiers

| Study role | Default disclosure | Earliest allowed release |
|---|---|---|
| `dev_fixture` | Public fixture | Development release |
| `compact20_v2_pilot` | Harness, blank packet, and public commitments only | After genuine dual review, adjudication, C10, and execution-entry gates |
| `scale100_confirmatory_v2` | Aggregate public commitment; private task pack | After genuine two-stage review, C10, content-bound scientific approval, execution, and confirmatory decisions are frozen |
| `artifact_rich_synthetic_transfer_v2` | Aggregate artifact/assignment commitment; private task pack | After provenance, privacy, license, genuine review, C10, and content-bound scientific approval |
| `heldout_challenge` | Membership and answers withheld | Post-study full release or separately governed challenge release |

Main-500 and all v1 scientific roles are superseded. They have no release tier
that restores confirmatory eligibility.

Publishing a generator, schema, task count, or membership hash does not
authorize publishing protected task text, labels, gold outputs, or answer keys.

## Authority and separation

- The canonical registry binds each role to source and membership hashes.
- Task-generation, scorer-development, model-selection, and held-out evaluation
  roles should be separated where staffing permits.
- A person with access to protected answers must not use them for prompt,
  scorer, or model selection without logging the exposure and invalidating the
  affected confirmatory role.
- Notebooks and CI default to fixture-only mode and must not embed protected
  answer content.

## Entry gates

Release or live evaluation remains blocked until all applicable gates pass:

1. Source and membership hashes match the canonical registry.
2. Cross-role base-task overlap is zero or an approved, documented exception.
3. Static leakage reports contain no blocker cluster.
4. Independent human task/gold/isolation review is complete, including C10.
5. Privacy, PII, injection, source provenance, and license reviews are complete.
6. Scorer version 3.0.0, typed answer contracts, abstention opportunities, and
   the endpoint specification are frozen.
7. Analysis decisions, exclusions, seeds, and the complete evaluated-system
   identity (model plus adapter components) are registered and hashed.
8. A trusted cryptographic scientific-scope receipt binds the exact reviewed
   candidates, exclusions, C10, reachability, scorer, system identity, code,
   budget, and revocation state. Directory names and approval Booleans do not
   authorize execution.
9. Run manifests and append-only ledgers pass integrity validation.
10. Claim and release checks pass without converting fixture evidence into
    scientific evidence.

## Versioning and change control

- Any task text, context, tool schema, intervention, gold output, split
  membership, or scorer-affecting change creates a new dataset version.
- Record source SHA-256 and membership SHA-256 before execution.
- Never edit a frozen release in place. Create a new version, changelog entry,
  and freeze manifest.
- Cosmetic documentation changes may retain the dataset version only when they
  cannot affect task interpretation or scoring.
- A discovered leak after execution triggers quarantine, incident review, and
  either exclusion with preregistered handling or a new unexposed evaluation.

## Privacy, provenance, and licensing

- Synthetic data follows `DATA_LICENSE.md`; code follows `LICENSE`.
- Artifact-rich synthetic transfer material must retain deterministic
  provenance and the no-real-world-origin claim. Any later genuine external
  material requires an item-level source/license log and explicit
  redistribution authority; unknown or incompatible rights block release.
- Do not commit real reviewer identities, provider credentials, customer data,
  private communications, or unredacted model logs.
- Pseudonymize reviewer identifiers and minimize retained free-text notes.
- Record every transformation from source material to released task, including
  the responsible reviewer and version.

## Release contents

An authorized release must include the applicable dataset card, data license,
freeze manifest, split policy, provenance/license log, hashes, changelog,
scorer name/version, and known limitations. Protected answer keys may be
released later or held by a challenge evaluator; that choice must be explicit
in the release manifest.

## Current decision

All non-fixture study roles remain `HUMAN_INPUT_REQUIRED` or
`EXECUTION_PENDING`. No protected held-out material is approved for scientific
execution or public answer-key release by this document.
