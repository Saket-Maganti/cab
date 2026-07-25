# Model Run Card Template

One card per provider+model combination in an experiment.

| Field | Value |
|---|---|
| **Run directory** | `results/<timestamp>_<name>/` |
| **Provider** | openai / anthropic / gemini / openrouter / local_openai / mock |
| **Model ID** | Exact API model string |
| **Model snapshot date** | If known |
| **Agent configurations** | List of agent names in run |
| **Dataset version** | Frozen manifest ID |
| **Split evaluated** | dev / validation / test / pilot_20 |
| **Trajectories** | Completed / expected |
| **Completion state** | complete / interrupted / dry_run |
| **Evidence scope** | From `run_metadata.json` |
| **Total cost (USD)** | |
| **Total latency (s)** | |
| **Token usage** | prompt / completion totals |
| **Known failures** | Rate limits, parse errors |
| **Evidence level** | |
| **Allowed claims** | |
| **Forbidden uses** | e.g., do not cite interrupted run |
