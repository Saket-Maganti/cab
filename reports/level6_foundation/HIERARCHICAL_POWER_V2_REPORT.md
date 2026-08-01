# Hierarchical Power V2 Report

Analytic mode is labeled `ANALYTIC_PLANNING_APPROXIMATION` and contains only
approximate power, CI width, MDE, assumptions, and formulas. It contains no
simulation count or Monte Carlo error. Simulation mode generated
`20000` deterministic paired synthetic
hierarchical datasets with every declared random/error/missingness component and
reports empirical simulation probability plus actual Monte Carlo standard error.
Fixed-panel, model-superpopulation, family, interaction, RAAC, non-inferiority,
rank instability, and unresolved-ranking estimands are separate. These are
design simulations, not observed model performance.
