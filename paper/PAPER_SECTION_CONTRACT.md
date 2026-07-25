# Paper Section Evidence Contract

This contract is a no-run authoring guard for turning Causal Agent Bench into a
NeurIPS-style paper without accidentally promoting unsupported evidence.

Machine-readable source: `paper/paper_section_contract.json`

Checker:

```bash
python3 scripts/check_paper_section_contract.py --mode draft
python3 scripts/check_paper_section_contract.py --mode submission
```

## What It Guards

The contract maps each claim-sensitive paper section to the claim IDs it relies
on. While C1-C8 and C10 remain planned, those sections must keep visible
planned/blocked/placeholder wording and must not switch to result language such
as "we show", "we find", or unqualified human-validation claims.

| Section | Claims | Current contract state |
|---|---:|---|
| Abstract | C1, C3, C4 | Empirical placeholders allowed in draft only |
| Introduction | C1-C8 | Hypothesis/framing only |
| Interventional Framework | C2, C3, C5, C7, C8, C10 | Method draft, C10 risk explicit |
| Results | C1-C8 | Blocked until supported evidence exists |
| Human Validation | C3, C10 | Blocked until annotations and agreement exist |
| Ablations | C5, C6 | Blocked until verified non-oracle ablations exist |
| Ethics/Reproducibility | C9 | Engineering-only reproducibility wording allowed |
| Conclusion | C1-C8 | Hypothesis until verified results replace placeholders |

## Promotion Rule

Before a blocked section can become submission-ready:

1. Its dependent claims must be `supported` in `docs/claim_ledger.json`.
2. The support must include linked run directories, artifact paths, and
   validation files where required by the claim ledger.
3. Paper result placeholders must be replaced through the verified paper-fill
   path, not by hand-written numbers.
4. The section contract, claim-ledger check, placeholder check, and paper asset
   validator must all pass in submission mode.

Tiny provider dry-runs, mock diagnostics, stub runs, and engineering-only
artifacts may improve the repository and reviewer packet, but they do not
unblock empirical sections.
