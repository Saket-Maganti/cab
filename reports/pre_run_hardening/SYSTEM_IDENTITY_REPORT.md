# Evaluated System Identity Report

Acceptance: `CAB_EVALUATED_SYSTEM_IDENTITY_FROZEN`.

Frozen contract hash: `2c1c30fb05dafadc7d81f2bb7b27cb1fef8aadd28d569c988d1af5c296544c1b`. The primary lane is
the uniform `cab_json_tool_protocol_v3`; native tool calling is a separately
labelled secondary ablation. All static component hashes are recorded.

Model revision, tokenizer digest, and exact quantization remain intentionally
pending until execution preflight. Scientific execution is forbidden before
that binding, and every scientific run and merge must carry the resulting
64-character `system_identity_hash`. Adapter differences force the label
`system_comparison`; equal-budget policies share model/tool/token/wall-time
accounting.
