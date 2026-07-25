# Self-Authorization for Tiny Provider Pilot

Recorded date: 2026-06-12

## 1. Authorization Type

Authorization type: Self-authorization
Project: Causal Agent Bench
Purpose: Tiny provider pilot for provider integration, scorer sanity, and pipeline sanity only.

## 2. Authorizing Person

Name: Saket Maganti
Role: Project owner / researcher

## 3. Scope of Approval

I authorize a tiny provider-backed pilot for Causal Agent Bench under the following strict limits:

* Maximum trajectories: 5
* Maximum estimated provider calls: 30
* Maximum approved budget: USD 5.00
* Approved dataset/config scope: provider pilot tiny only
* Approved evidence scope: debug / preliminary provider-pipeline sanity only
* Scientific claim promotion allowed: No
* Paper claim support allowed: No
* Main benchmark run allowed: No
* main_200 allowed: No
* main_500 allowed: No
* Broad sweeps allowed: No
* Local LLM runs allowed: No

## 4. Dry-Run Approval

Dry-run approval: Yes

The project may create:

* `configs/provider_pilot_tiny_APPROVED.yaml`

for dry-run/preflight purposes only.

During dry-run:

* `allow_paid_calls` must remain `false`
* no provider API calls may be made
* no paid calls may be made
* no claims may be promoted
* no paper assets may be marked eligible

## 5. Live-Run Approval

Live-run approval: No

A live provider call is not authorized by this file unless this section is explicitly changed to:

`Live-run approval: Yes`

Before live execution, the following must pass:

* evidence safety check
* validate-config
* plan-run
* estimate-run-cost
* dry-run/preflight
* leakage blocker check
* budget estimate within USD 5.00
* max trajectories <= 5
* no API keys stored in YAML

## 6. Risk Acknowledgement

I understand that:

* provider calls may cost money
* model outputs may be noisy or incomplete
* this pilot may fail
* this pilot may reveal scorer or gold-output problems
* this pilot is not sufficient for NeurIPS claims
* this pilot is not sufficient for benchmark validity claims
* this pilot is not sufficient for model ranking claims
* this pilot must not be used to promote C1-C8 or C10

## 7. Evidence Restrictions

The tiny provider pilot may support only:

* provider integration sanity
* pipeline sanity
* trajectory logging sanity
* scorer sanity inspection
* cost/runtime sanity
* preliminary debugging observations

It must not support:

* final empirical claims
* model ranking claims
* NeurIPS readiness claims
* human-validation claims
* general robustness claims
* causal validity claims

## 8. Required Post-Run Audit

If a live tiny pilot is later authorized and executed, the project must create:

* `reports/TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md`
* `reports/TINY_PROVIDER_PILOT_TRAJECTORY_REVIEW.csv`
* `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.md`
* `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.csv`

Every trajectory must be manually inspected.

## 9. Authorization Statement

I authorize only the dry-run/preflight preparation stage at this time.

I do not authorize live paid provider calls yet.

Signature / typed name: Saket Maganti
