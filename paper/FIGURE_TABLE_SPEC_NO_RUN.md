# Figure And Table Specification, No-Run

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

All entries below are future required result assets. None is currently paper-eligible.

All performance assets must use scorer-v3 completion, safe response, false
abstention, and executed-recovery fields as distinct columns. The primary and
secondary endpoint names are frozen in `configs/pre_run/frozen_endpoints.json`;
no figure may silently replace completion with contract compliance or a safe
non-completion response.

| Asset | Data needed | Why it matters | Claim it could support later | Claim it cannot support alone | Minimum evidence threshold | Current status |
|---|---|---|---|---|---|---|
| Table 1 intervention taxonomy and examples | Taxonomy plus reviewed examples | Explains design | Method contribution | Model performance | Static docs plus review of examples | planned |
| Table 2 future clean vs intervention success by model | Provider outputs for clean/intervention pairs | Tests degradation | C1 | C10 or causal proof | Provider run, intervals, audit | blocked |
| Figure 1 paired perturbation design | Method schematic | Shows benchmark structure | Design clarity | Empirical effects | Static schematic approved | planned |
| Figure 2 future completion-rank vs completion-ACRS-rank crossing plot | Multi-model results | Tests ranking instability | C4 | General leaderboard truth | Multi-model audited run with synchronized uncertainty | blocked |
| Figure 3 future per-family degradation | Family-level provider results | Shows intervention-specific brittleness | C2 | Universal robustness | Provider run plus family audit | blocked |
| Table 3 future C10 human validation agreement | Regenerated Compact-20 v2 sheets from two independent reviewers plus separate adjudication | Defends isolation | C10 | Model performance | Completed genuine review and agreement | blocked |
| Table 4 future self-check/scaffold ablation | Controlled ablation results | Tests scaffold effect | C6 | Broad agent capability | Fixed-task ablation with audit | blocked |
| Figure 4 future failure gallery | Provider trajectories plus human/scorer labels | Makes failures inspectable | C3 | Statistical frequency alone | Audited examples from real outputs | blocked |
| Table 5 future artifact-rich synthetic transfer | Approved v2 transfer trajectories and artifact commitments | Tests controlled artifact-class transfer | C8 | Real-world deployment validity | Genuine review, approved materialization, audited model run | blocked |
