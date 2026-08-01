# CAB Pre-Run GitHub Publication

Status: `READY_FOR_DIRECT_MAIN_PUBLICATION`.

Baseline SHA: `c8b0d008a02f4bcc36a24635a1357d4210e073fd`.

Provider-free validation is complete. Publication must stage only task-owned
paths, push directly to `main` without force, verify local and remote SHA
equality, and observe required CI for a bounded interval. The post-push record
will replace this pre-publication state after those operations occur. A commit
cannot truthfully embed its own future SHA; the final branch-tip SHA is also
reported in the user-facing handoff after remote verification.
