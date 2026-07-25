# Reviewer Attacks And Defenses V2

Status: reviewer-defense planning only.

| attack | defense | current gate |
|---|---|---|
| “CAB is synthetic.” | Add naturalistic mini-study design and report transfer only after real runs. | RESULT_REQUIRED |
| “This is not causal inference.” | Frame as controlled perturbation benchmark; reserve causal language for validated assumptions. | C10_REQUIRED |
| “Scorers are brittle.” | Add scorer robustness policy, fixture tests, and human review. | HUMAN_REVIEW_REQUIRED |
| “Clean/intervention pairs are confounded.” | Use intervention validity checklist and C10 human isolation review. | C10_REQUIRED |
| “Rank instability is underpowered.” | Require 5+ models and larger samples for claims. | MAIN_STUDY_REQUIRED |
| “Proxy labels contaminate validation.” | Keep proxy labels visibly synthetic and excluded. | active policy |
| “Release cannot reproduce results.” | Release no-provider and provider-template commands separately. | release gate pending |
