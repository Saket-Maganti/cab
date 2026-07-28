# Claim-Safe Abstract Templates

Status: templates only. Bracketed slots are not results.

## 1. No-Evidence Scaffold Version

Tool-using agents are often evaluated by clean-task success, but such scores
conflate execution, verification, and recovery. We introduce a methodology for
intervention-validity auditing and paired robustness inference, Recovery-Aware
Agent Control (RAAC), and CAB as the empirical vehicle. This version reports
the pre-execution system only; human and model evidence are RESULT_REQUIRED.

## 2. Audited Compact-20 Pilot Version

We evaluate [MODEL_COUNT] agents on a human-reviewed Compact-20 CAB subset.
Across paired clean/intervention tasks, we report clean success, intervention
success, ACRS, RAAC overhead, and rank uncertainty. RESULT_REQUIRED: insert only
audited preliminary values after scorer sanity; do not use pilot results as
confirmatory evidence.

## 3. Confirmatory Scale-100 Version

We run [MODEL_COUNT] agents on [TASK_COUNT] locked paired CAB tasks spanning
[FAMILY_COUNT] intervention families. The study tests [LOCKED PRIMARY
HYPOTHESES] and compares standard tool use with RAAC under [LOCKED BUDGET MODE].
RESULT_REQUIRED: every estimate, interval, and rank probability must come from
audited real trajectories on the hashed slice.

## 4. Final Audited Evidence Version

Using [MODEL_COUNT] models, [CONTROLLED TASK COUNT] controlled tasks, and
[NATURALISTIC TASK COUNT] naturalistic workflows, we estimate [LOCKED
ENDPOINTS] and test whether controlled robustness predicts naturalistic
outcomes. RESULT_REQUIRED: wording must be generated from paper-eligible
evidence with data, scorer, code, and study hashes. A Main-500 count is not
required unless the resource-aware decision gate justifies it.
