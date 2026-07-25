# Do not overclaim

**Do not** treat the following as scientific benchmark results:

- Smoke / dev / stub / `pilot_stub` / `mock_diagnostic` runs
- Interrupted or incomplete runs (even if partially scored)
- Tables or figures with `placeholder: true` or missing `.meta.json`
- Generated LaTeX containing “not yet run”, “blocked”, “engineering-only”, or “placeholder”
- Claim ledger status `engineering_only` or `planned` presented as confirmed findings

## Hard rules

1. C1–C8 and C10 cannot be `supported` on mock/stub/interrupted/local-only evidence.
2. C9 (reproducibility) may be `engineering_only` from smoke docs — not empirical benchmark claims.
3. Default `export-paper-assets` and `fill-paper-from-run` **refuse** ineligible sources.
4. Overrides (`--allow-engineering-only`, `--allow-mock-stub`, etc.) must label outputs as **NOT SCIENTIFIC EVIDENCE**.

## Forbidden phrases

Until a `main_supported` run exists and the relevant ledger rows are approved,
**do not** write any of the following in the paper, README, abstract, or commit
messages:

| Forbidden phrase | Why it overclaims |
|---|---|
| "NeurIPS-ready" / "camera-ready benchmark" | No human validation or main run yet |
| "we prove" / "proves that" | The benchmark provides empirical evidence, not proofs |
| "state-of-the-art" / "SOTA" | No leaderboard from validated provider runs |
| "validated benchmark" / "gold standard" | Validation is automated-only so far |
| "models are robust" / "agents recover reliably" | No provider-backed results |
| "human validators agree" | Human validation is not complete |

### Safer alternatives

| Instead of… | Write… |
|---|---|
| "we prove agents fail under interventions" | "we observe degradation on the engineering pilot; provider-backed runs are pending" |
| "NeurIPS-ready benchmark" | "research scaffold with frozen synthetic pilot data" |
| "state-of-the-art evaluation" | "interventional evaluation protocol" |
| "validated benchmark" | "benchmark with automated schema/quality/leakage checks" |

When in doubt, use method-only wording ("we define", "we statically validate")
and cite the claim-ledger row id.

## Before writing results in the paper

Run:

```bash
python3 -m causal_agent_bench all-safety-reports
```

Review `reports/claim_evidence_matrix.md` and `reports/paper_asset_eligibility.md`. If uncertain, mark **needs review** — do not imply verified provider results.

## New static reports are not evidence

`benchmark-quality`, `intervention-isolation-audit`, `synthetic-fixture-check`, `human-validation-packet`, `estimate-run-cost`, `method-figure-scaffolds`, and `release-readiness` are governance and readiness tools. Passing them does not support empirical claims, does not make synthetic fixtures real LLM behavior, and does not unblock C1-C8 or C10.

The same applies to scored reports, dataset triage, provider preflight, evidence dashboard, config lint, dry-run human-validation samples, and method appendices. Scores and badges are conservative readiness aids, not empirical findings.
## Advanced No-Run Reports Do Not Promote Claims

The following reports improve repair planning, release readiness, and review
quality:

- repair plan
- benchmark cards
- intervention taxonomy
- gold-output validation
- tool-schema validation
- static leakage report
- benchmark manifest
- config profiles
- advisor review packet
- paper readiness map
- evidence dashboard

They can support method-only wording such as “we define,” “we statically
validate,” and “we prepare a pre-provider-pilot review packet.” They cannot
support wording such as “models are robust,” “performance improves,” “human
validators agree,” “provider pilot succeeded,” or “claims are supported.”

Current evidence state remains:

- paper-eligible runs: 0
- eligible paper assets: 0
- C1-C8: planned / unsupported
- C9: engineering_only
- C10: planned / unsupported

Do not run claim-promotion or paper-fill commands in a no-run phase:

```bash
python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...
python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...
```

## NeurIPS artifact firewall (abstract / conclusion)

Until Tier 4 provider evidence exists, paper sections must not imply:

| Section | Forbidden without evidence |
|---------|-------------------------|
| Abstract | Degradation %, ranking correlation ρ, "we show/find/demonstrate" on agents |
| Introduction | "Our experiments demonstrate…" |
| Results | Any performance table or figure from `table2_*` / `figure2_*` |
| Human validation | Agreement κ, expert validation complete |
| Conclusion | "Validated benchmark", "NeurIPS-ready", "models ranked by ACRS" |
| Public release | "v1.0 released", Zenodo/HF dataset live |

**Safe abstract tail:** State that empirical results from completed non-oracle provider runs are not yet reported.

NeurIPS artifact docs: `docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md`, `docs/REVIEWER_QUICKSTART_NEURIPS.md`, `reports/claim_evidence_matrix.md` (Evidence-to-paper firewall section).
