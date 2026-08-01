# Public Held-Out Contamination and Git-History Policy

Status: active, fail-closed policy
Applies to: every CAB task, answer, intervention, evaluator field, manifest, archive, notebook, and generated bundle ever committed to a public Git ref

## Scientific decision

The v1 “confirmatory” and “held-out” payloads were committed to public Git at
`ca9c13b87ea546c6d079ca4b400c06c04e558b8b` and remained reachable from
`origin/main`. Their prompts, answers or answer-bearing fields, intervention
metadata, evaluator-only metadata, deterministic seeds, identifiers, and
reconstruction recipes must therefore be treated as public.

Public exposure is permanent for scientific purposes. CAB does not infer that a
model actually trained on these files. It makes the narrower and auditable
decision that secrecy can no longer be established, so the rows are not valid
future hidden or confirmatory evaluation units.

The machine-readable source of truth is
`data/manifests/CAB_PUBLIC_CONTAMINATION_REGISTRY.json`. The path-level audit is
`reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`.

## Permanent disposition

Every exposed record has exactly one of these dispositions:

- `PUBLIC_DEVELOPMENT_ONLY`
- `PILOT_ONLY`
- `CONTAMINATED_NOT_CONFIRMATORY`
- `INVALID_FOR_FUTURE_EVALUATION`

None permits confirmatory Scale-100, confirmatory Main, hidden-challenge,
paper-eligible, or external-validity evidence. Public v1 rows may remain in the
repository for transparent auditing, regression tests, demonstrations, scorer
development, and explicitly labelled pilots. Keeping them visible is not a
claim that they are still hidden.

The canonical split registry therefore names the exposed roles
`scale100_public_development_v1`,
`naturalistic_public_development_v1`,
`main500_public_development_v1`, and
`heldout_challenge_v1_contaminated`. Each has:

- `confirmatory_eligible: false`;
- `scientific_execution_allowed: false`;
- `paper_eligible: false`;
- a public release tier; and
- a link to its permanent contamination record.

Future code must not restore the former confirmatory role names, change these
eligibility flags, or cite results on these rows as a substitute for a private
replacement.

The current protected replacements are the Scale-100 v2 and
`artifact_rich_synthetic_transfer` v2 private candidates. Public Git contains
only aggregate commitments and assignment/artifact diagnostics. Their
`scientific_execution_allowed` flags remain false until genuine review,
adjudication, C10, approved private materialization, and a bound execution
manifest exist. Main-500 has no v2 replacement and is not part of the current
scientific plan.

## Why deletion is insufficient

Deleting a file from the current branch does not delete earlier blobs, forks,
clones, caches, release downloads, notebook copies, or model-training corpora.
It also cannot establish that nobody read or copied the payload while it was
public. A later filename, seed, or split label does not create a new evaluation
unit when the underlying task text or answer is unchanged or trivially
parameterized.

For the same reason, moving exposed rows under `private_data/`, changing their
IDs, encrypting a copy after exposure, or publishing only a new hash does not
restore validity. Scientific invalidation follows the content and its
near-duplicates, not its current path.

## Replacement architecture

The replacement role is `heldout_challenge_v2_protected`.

Public Git may contain only:

- the schema and safety validators;
- aggregate target counts and distribution summaries;
- provenance and licence summaries;
- HMAC-SHA256 commitments made with a private key;
- generation and review constraints; and
- the payload-free public manifest at
  `data/manifests/heldout_challenge_v2_public_manifest.json`.

Private material belongs under:

`private_data/heldout_challenge_v2/`

That entire root is ignored. `private_lock.json`, task text, answers,
interventions, evaluator metadata, reviewer material, seeds, HMAC keys, exact
IDs, and private manifests must never be staged, committed, archived into a
public notebook, or added to a release bundle.

`scripts/initialize_private_heldout_v2.py` creates a new 256-bit private seed,
private HMAC key, opaque v2 identifiers, and public commitments without
printing private values. It does not author payloads. The current manifest
therefore remains `PRIVATE_IDS_LOCKED_PAYLOAD_AUTHORING_PENDING`, with live
execution and paper eligibility false, until genuine private authoring and
human review occur.

Before a private candidate can be locked:

1. use new private IDs, seeds, and commitments;
2. do not copy public v1 task text;
3. do not use trivial parameter replacement;
4. avoid answer overlap where feasible;
5. do not select tasks using model outputs;
6. compare private text with every exposed source using exact and near-duplicate
   checks;
7. reject any exposed ID or namespace reuse;
8. scan tracked notebooks and archives for private markers;
9. complete task, gold-policy, intervention-isolation, and C10 human review; and
10. regenerate and independently verify the public commitments.

Passing the engineering architecture check is not equivalent to a materialized,
reviewed, or execution-ready private dataset.

## Public manifest rules

The public manifest must not contain task text, prompts, exact task or instance
IDs, answers, gold fields, intervention payloads, evaluator fields, private
seeds, private keys, or reversible encodings. A raw hash of a low-entropy seed
is not an acceptable commitment; CAB uses HMAC-SHA256 with a key retained only
under the private root.

Aggregate counts and commitments do not prove task quality, non-contamination,
intervention validity, or paper eligibility. They prove only that a private
holder can later demonstrate consistency with a locked value.

## Release and execution gates

The held-out release validator fails when:

- a protected v2 payload is tracked;
- a legacy public payload lacks a permanent contamination record;
- a contaminated role is named or marked confirmatory;
- the private root is not ignored;
- a public manifest contains forbidden or reversible fields;
- a private identifier reuses an exposed ID or namespace;
- public/private task text is an exact or near duplicate;
- a tracked notebook or archive contains private markers; or
- a public release inventory includes private/protected files.

Human review, C10, slice lock, an immutable run manifest, budget approval, and
an explicit execution approval remain separate prerequisites. No static check
in this policy authorizes model execution.

## Git-history rewrite policy

A history rewrite may be considered later for repository hygiene, privacy, or
distribution-size reasons. It requires a separate destructive-operation plan,
owner approval, backup, collaborator coordination, force-push plan, tag and
fork analysis, and post-rewrite secret/protected-content scan.

No history rewrite is authorized by this document, and none was performed for
this repair.

Even a complete rewrite does **not** change any scientific disposition in the
contamination registry. Previously public blobs may remain in clones, forks,
caches, releases, logs, or training corpora. The rewrite can reduce future
accidental distribution; it cannot make an exposed evaluation secret again.

## Audit maintenance

Regenerate the exposure inventory after any new public-data discovery:

```bash
PYTHONPATH=src python3 scripts/build_protected_heldout_exposure_inventory.py
```

Verify the private/public boundary without writing payloads:

```bash
python3 scripts/initialize_private_heldout_v2.py --check
python3 -m pytest -q tests/test_protected_heldout_contamination.py
```

Any newly discovered exposure is appended as a new permanent registry record.
Existing records are never deleted merely because their current files were
renamed or removed.
