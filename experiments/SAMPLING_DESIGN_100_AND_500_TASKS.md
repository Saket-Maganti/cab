# Sampling Design For 100 And 500 Tasks

Status: future execution design only.

## Design Goals

- Balance intervention families, domains, and difficulty.
- Avoid overrepresenting easy families such as simple tool removal.
- Preserve paired clean/intervention design.
- Keep replacement and exclusion decisions independent of model outcomes.

## Compact-20

Compact-20 is enough for pipeline debugging, human-review rehearsal, scorer sanity, and directional pilot inspection. It is not enough for headline ACRS/rank-instability claims.

## 100-Task Study

Use when the goal is a powered pilot:

- 10 intervention families x 10 task pairs, or 12 families with minimum 8 pairs each plus documented imbalance.
- minimum 3 non-oracle models; 5 preferred for rank instability.
- minimum one trajectory per model-condition for pilot; more for reliability if budget allows.
- stratify by domain and difficulty.
- report wide CIs and null results.

## Main-500

Use only after Compact-20 and 100-task gates pass:

- target 20-25 families or subfamilies,
- minimum 20 pairs per primary family,
- minimum 5 models,
- enough repeats to estimate scorer disagreement and run variance,
- preregister primary families and claims.

## Budget Tiers

- Tier 0: static/no-provider checks only.
- Tier 1: Compact-20 approval run after human review.
- Tier 2: 100-task multi-model pilot.
- Tier 3: Main-500 with locked analysis and release plan.

No tier is currently authorized by this document.
