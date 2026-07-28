# ICLR Naturalistic Transfer v2 Candidate Audit

Status: `STATIC_PREVALIDATION_PASS_HUMAN_REVIEW_REQUIRED`

Evidence class: `HUMAN_INPUT_REQUIRED`

The private candidate contains 60 locally authored synthetic workflow tasks,
300 intervention mappings, and 360 planned instances. The public commitment is
`data/manifests/naturalistic_transfer_v2_public_manifest.json`; task IDs, task
text, answers, artifacts, mappings, and evaluator metadata are excluded.

## Aggregate quality

- 60 unique task IDs, content hashes, templates, workflows, and normalised
  instruction patterns.
- Conservative genuinely-distinct lower bound: 60.
- 10 workflow domains with six tasks each.
- 10 tool combinations.
- Four canonical answer contracts.
- Four difficulty bands with 15 tasks each.
- All 10 intervention families occur 30 times.
- 300 linked manipulation checks; 0 missing.
- 0 exact, normalised, structural, answer, or registered role-overlap groups.
- 0 lexical near-duplicate pairs at the preregistered 0.82 threshold.
- Maximum observed lexical similarity: 0.711111.

The domains cover calendar coordination, data pipelines, email casework,
incident response, policy packets, repository debugging, service
configuration/logs, spreadsheet exports, support tickets, and travel records.

## Review state

The packet has 60 review items and 660 blank dimension rows across 11
dimensions. It requires two independent qualified human reviewers per task and
separate adjudication. Completed genuine human judgment rows: 0.

Static validation passes, but the candidate is not confirmatory-ready,
paper-eligible, or executable. Predictive-validity estimands and small-panel
limits are preregistered in `docs/ICLR_CONFIRMATORY_ANALYSIS_PLAN.md`.
