# Compact-20 Two-Stage Review Instructions

Status: `HUMAN_VALIDATION_REQUIRED`. No review judgments exist in this packet.

Stage 1 exposes tasks, controlled artifacts, tool contracts, and intervention
materialization. It does not expose gold answers, intended routes, or scorer
policies. Complete every assigned Stage-1 row independently. A coordinator must
then freeze the completed CSV hash in `stage1_commitment.json`; only the
canonical unlock validator can authorize Stage 2.

Stage 2 uses a separately randomized order and exposes frozen gold derivations,
answer contracts, scorer policies, and typed recovery authorizations. Do not
revise Stage-1 judgments after unlock. Do not use AI/proxy assistance or inspect
model/provider identities or outputs.
