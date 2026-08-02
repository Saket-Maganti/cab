# Private Compact-20 human-review protocol

This protocol applies only to the new packet identified by the public commitment in
`data/manifests/compact20_final_private_commitment.json`. The earlier Compact packets are exposed
development fixtures and are ineligible for genuine review or C10.

The coordinator recruits two independent reviewers, records qualification without committing
their identities, and distributes the physically separate Reviewer A and Reviewer B Stage-1 ZIPs.
Reviewers see only prompts, declared tools, and primitive source records. They independently commit
all Stage-1 judgments. The coordinator verifies a content-bound Stage-1 receipt before enabling the
separate Stage-2 decrypt/generation path. No Stage-2 material or key is sent before that check.

After Stage 2, a distinct adjudicator resolves disagreements. C10 is evaluated under
`configs/human_validation/c10_contract_v1.json`; fixture judgments never count. A passing C10
receipt and a content-bound slice-lock receipt are then created. Any task, packet, scorer, endpoint,
analysis-plan, or system-identity hash change invalidates the review and requires a new version.

The coordinator must keep private candidate bodies, Stage-2 plaintext/ciphertext, keys, reviewer
identities, and judgments outside public Git. Human review is still required; no judgments were
created during engineering freeze.
