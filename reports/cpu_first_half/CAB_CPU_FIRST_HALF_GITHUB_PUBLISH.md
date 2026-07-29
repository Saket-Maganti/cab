# CAB CPU First-Half GitHub Publish

State: `PUBLISHED_CI_PARTIAL_AT_BOUNDED_CUTOFF`

Publication policy:

- branch remains `main`;
- no force push;
- no branch or pull request;
- stage only the root execution/handoff files and `reports/cpu_first_half/`;
- exclude the private machine audit, `.cab/`, build output, site output,
  prompt packs, pre-existing user work, review exports, protected payloads, and
  raw trajectories.

## Publication receipt

- Report-content commit: `8bb560d8662ef50aad67287e4e2ce93da2adc4d1`
- Push: `main -> origin/main`, fast-forward from
  `c5dba2d20402c993fd92365232fabefc7b4d8268`
- Local SHA after content push:
  `8bb560d8662ef50aad67287e4e2ce93da2adc4d1`
- Remote SHA after content push:
  `8bb560d8662ef50aad67287e4e2ce93da2adc4d1`
- Equality check: PASS

## Bounded CI observation

At the bounded cutoff, four workflows had completed successfully:

- Docs Check
- Claim Safety
- Level-5 foundation
- Max Ceiling Provider-Free Gates

Fast Check and CI remained `in_progress`. No workflow had failed. This report
does not claim a fully green CI suite while those jobs are active.

The commit containing this publication receipt follows the report-content
commit. Its exact local/remote equality is verified after publication and
reported in the execution handoff.
