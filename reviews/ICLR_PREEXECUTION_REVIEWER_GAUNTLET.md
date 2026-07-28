# ICLR Pre-Execution Reviewer Gauntlet

Status: internal design critique, not a real review and not acceptance evidence.
Scores are conditional guesses about the manuscript *before experiments* on a
1–10 ICLR-style scale. They are included to expose rejection paths, not to
predict acceptance.

## 1. Sceptical ICLR generalist

- Likely pre-experiment score: 4/10.
- Confidence: 3/5.
- Fatal concerns: contribution may look like another benchmark; “causal” may
  overstate identification; no evidence that robustness differs from clean
  success or matters outside synthetic tasks.
- Required evidence: clear method-first framing, valid paired interventions,
  multi-model uncertainty, RAAC comparison, and naturalistic predictive
  validity.
- Possible rejection reason: engineering scale without a scientific insight.
- Mitigation status: formal paired methodology and claim boundaries exist;
  RAAC, validity, and transfer infrastructure are being completed.
- Remaining work: genuine C10 review, audited model runs, naturalistic transfer,
  and a result-driven paper revision.

## 2. Agent-systems reviewer

- Likely pre-experiment score: 5/10.
- Confidence: 3/5.
- Fatal concerns: RAAC could be prompt engineering with more calls; baselines
  may be unfair; tool adapters may not generalise across model families.
- Required evidence: typed observable-signal controller, strict hidden-label
  blindness, equal-budget comparison, clean-path parity, full overhead, strong
  ReAct/self-check baselines, and component ablations.
- Possible rejection reason: improvement purchased by extra inference rather
  than recovery logic.
- Mitigation status: bounded RAAC policies, trace contracts, and budget modes
  are implemented or under focused completion; no improvement is claimed.
- Remaining work: run equal-budget and practical-budget studies on common task
  support, audit traces, and report false abstention.

## 3. Causal-methodology reviewer

- Likely pre-experiment score: 4/10.
- Confidence: 4/5.
- Fatal concerns: interventions may change goals, answers, solvability, or
  multiple mechanisms; the word “causal” may be read as population-level causal
  identification.
- Required evidence: invariance checklist, manipulation checks, independent
  reviewers, adjudication, exposure-aware split policy, and restrained
  estimands.
- Possible rejection reason: paired perturbations are confounded difficulty
  changes.
- Mitigation status: the paper states controlled-intervention scope and audits
  rather than assumes validity; C10 is fail-closed.
- Remaining work: complete human review and exclusions, freeze the slice, and
  show sensitivity to invalid/ambiguous tasks.

## 4. Statistics reviewer

- Likely pre-experiment score: 5/10.
- Confidence: 4/5.
- Fatal concerns: pseudoreplication across variants; unstable ratios when clean
  success is low; rank claims from too few models; family multiplicity;
  post-hoc equivalence or power.
- Required evidence: base-task cluster bootstrap, exact paired tests,
  denominator diagnostics, rank probabilities over common support, locked
  SESOI/margin, missingness policy, and multiplicity control.
- Possible rejection reason: overly precise conclusions from dependent task
  variants and a small model panel.
- Mitigation status: paired, clustered, stratified, rank, scorer-sensitivity,
  equivalence, missingness, and resumable-bootstrap contracts exist.
- Remaining work: preregister SESOI/margins and allocations before data, then
  report intervals and undefined states honestly.

## 5. Benchmark/dataset reviewer

- Likely pre-experiment score: 3/10.
- Confidence: 4/5.
- Fatal concerns: public exposure invalidates old held-out packs; Scale-100 may
  contain 100 parameterised templates rather than independent tasks;
  naturalistic artifacts may still be synthetic; licences and privacy may be
  incomplete.
- Required evidence: permanent contamination registry, entirely new protected
  v2 architecture, exact/near-duplicate gates, diversity audit, source/licence/
  privacy/injection registry, and human review.
- Possible rejection reason: benchmark leakage plus superficial scaling.
- Mitigation status: exposed material is being permanently reclassified;
  private payloads are excluded from Git and only non-reversible public metadata
  is allowed.
- Remaining work: create genuinely new private v2 tasks outside this public
  build, complete review, and decide whether 80 high-quality tasks are stronger
  than a nominal 100.

## 6. Reproducibility reviewer

- Likely pre-experiment score: 6/10.
- Confidence: 3/5.
- Fatal concerns: nine notebooks could drift from code; free Kaggle availability
  and model downloads are not reproducible guarantees; release bundles could
  leak answers or omit dependencies.
- Required evidence: generated-and-validated notebooks, safe live defaults,
  pinned run manifests, disjoint resumable shards, integrity checks, open-model
  core, M4 workflow, release scan, and exact commit/data/scorer hashes.
- Possible rejection reason: impressive scaffolding that cannot recreate the
  submitted tables under realistic resources.
- Mitigation status: offline notebook fixture execution, checkpoints, merge,
  corruption detection, evidence gates, and resource-bounded workflows exist.
- Remaining work: measured approved smoke, clean-environment reproduction,
  final release sanitation, and artifact-to-paper provenance verification.

## Cross-review stop conditions

The package should not proceed to model execution until genuine human review,
adjudication, C10, and slice locking pass. It should not proceed to Main-500
because Scale-100 and naturalistic evidence do not yet exist. No score above is
a substitute for those gates.
