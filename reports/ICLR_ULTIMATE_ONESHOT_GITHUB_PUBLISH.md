# CAB ICLR Ultimate One-Shot GitHub Publication

## Publication state

- State: `PUSHED_TO_GITHUB_MAIN`
- Repository: `Saket-Maganti/cab`
- Remote: `https://github.com/Saket-Maganti/cab.git`
- Branch: `main`
- Pre-run commit: `d3469045a78de3a20b37783b29167805e7417e04`
- Final implementation commit:
  `45f9209631c6152314dcb82d3e315a8cf4e751a9`
- Commit message: `Complete CAB ICLR pre-execution build`
- Publication-record commit: this report and the final ledger entry are
  intentionally recorded in the immediately following audit-only commit; its
  exact SHA is reported by the verified Git log and task handoff.

## Committed scope

- Files committed: 153
- Diff: 26,838 insertions and 591 deletions
- Scope: Prompt 1 blocker repairs; protected-heldout contamination controls;
  canonical workflow state and split registry; Recovery-Aware Agent Control;
  genuine-human validation and C10 machinery; private Scale-100 and
  naturalistic candidate infrastructure; M4 and dual-T4 resource controls;
  paired/transfer/RAAC analysis; paper gates; tests; reports; and handoff.

## Validation completed before commit

- Focused ICLR regression slice: `145 passed in 69.05s`.
- Complete provider-free suite:
  `1091 passed, 1 skipped in 171.32s`.
- Post-format human/gate regression:
  `26 passed in 1.37s`.
- Ruff: passed.
- mypy: passed across 205 source files; the final changed source file was also
  checked independently after deterministic CSV line-ending repair.
- JSON/YAML parsing: 15 JSON and 102 YAML files passed.
- Nine Kaggle notebooks: all offline fixture checks passed with 72 receipts;
  live execution was refused.
- Paper: checks and three-pass LaTeX build passed; 14 pages with seven
  deliberately visible empirical placeholders.
- Security check, release check, split-registry check, private-heldout
  commitment check, private-candidate validator, and `git diff --check`:
  passed.
- Release bundle hash:
  `daca304de2c3557f22108f773a58b45f3f432785d65558b5fc0bd76b498a6e7a`
  with 652 inventoried files.

## Push and verification

- Push command: `git push origin main`
- Push result: success,
  `d346904..45f9209 main -> main`.
- Local HEAD at implementation verification:
  `45f9209631c6152314dcb82d3e315a8cf4e751a9`
- Remote `refs/heads/main` at implementation verification:
  `45f9209631c6152314dcb82d3e315a8cf4e751a9`
- Local and remote heads matched: yes.
- Force push used: no.
- Pull request created: no.

## Remote CI observation

At the first post-push observation, GitHub Actions existed and was active for
the implementation commit:

- `CI`: queued;
- `Fast Check`: in progress;
- `Docs Check`: in progress;
- `Claim Safety`: in progress;
- `Max Ceiling Provider-Free Gates`: in progress;
- `Batch smoke`: in progress;
- `Docs`: in progress.

The aggregate commit-status endpoint reported `pending` with no attached
legacy status contexts. No CI success claim is made here. The final publication
handoff records the state observed for the final remote head without waiting
indefinitely.

## Preserved and excluded material

- Preserved unrelated user edit:
  `reports/ICLR_PROMPT1_POSTFIX_BASELINE.md` remained untracked and was not
  staged or committed.
- Excluded ignored private roots:
  `private_data/heldout_challenge_v2/`,
  `private_data/scale100_confirmatory_v2/`, and
  `private_data/naturalistic_transfer_v2/`.
- Tracked private files: 0.
- Staged or committed private payload files: 0.
- Public manifests contain only schemas, aggregate counts, provenance
  summaries, and non-reversible commitments.

## Remaining publication blocker

None. Remaining project gates are scientific rather than publication
failures: genuine human review, adjudication, C10, slice locking, real model
execution, audited postrun analysis, and evidence-backed final paper writing.
