# Execution OS architecture

`RunPlanSpec` compiles a frozen task/split, models, policies, repeats, seeds,
scorer, code revision and backend into an immutable matrix. Units receive
deterministic IDs and disjoint shard numbers. Provider backends introduce
explicit approval requirements.

The local scheduler writes the manifest before work, links attempts, retries
within a bound, checkpoints after every completed unit and skips completed
units on resume. A different manifest cannot reuse a checkpoint. Collection
stores each output in the CAS and merges in manifest order.

The initial supported backend executes provider-free fixtures. Local model,
Kaggle, provider and cloud backends must implement the same discovery, prepare,
execute/checkpoint, cancel, collect and cleanup invariants before activation.
