# Pre-Experiment Freeze Checklist

Use this checklist **before any real experiment** (mock, stub, local, or provider). All gates are conservative; when in doubt, stop and re-read [docs/DO_NOT_OVERCLAIM.md](../docs/DO_NOT_OVERCLAIM.md).

**Current project classification:** `build_infrastructure_ready` — infrastructure complete; empirical claims not supported.

---

## Global sections

### Code state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| `make fast-check` passes | ready | Re-run before each experiment session | CI / local terminal |
| Claim ledger valid | ready | `python3 scripts/check_claim_ledger.py` | `docs/claim_ledger.json` |
| Evidence safety clean | ready | `python3 scripts/check_evidence_safety.py` | script output |
| No uncommitted breaking changes | partial | Review `git status`; commit or stash intentionally | git |

### Config state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Target config validates | ready | `validate-config --config <path>` | CLI JSON |
| `allow_paid_calls` explicit | ready | Must be `false` unless budget approved | config YAML |
| Budget caps set (paid) | partial | Paid configs need `budget.max_total_usd` + approval | config YAML |
| Config audit clean | partial | `make audit-configs` — warnings OK if documented | `audits/config_consistency/` |

### Dataset state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Instances file exists | ready | `audit-dataset --config <path>` | dataset audit report |
| Frozen manifest (pilot+) | partial | Freeze before provider pilot | `data/frozen/pilot_v0.1/` |
| Intervention audit passed | ready | `audit-interventions` on benchmark dir | audit JSON |

### Evidence-level state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Evidence level declared in config | ready | `scientific_evidence_level` or implied by config type | YAML |
| Mock/stub labeled engineering | ready | Run metadata `evidence_scope` | run_metadata.json |
| No incomplete runs as evidence | ready | Do not score interrupted for claims | INCOMPLETE_RUN.json policy |

### Claim-ledger state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| C1–C8 planned | ready | Do not promote without pilot | claim_ledger.json |
| C9 engineering_only | ready | Stub reproducibility only | claim_ledger.json |
| C10 planned | ready | Needs human validation | claim_ledger.json |

### Paper state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Placeholders unfilled | ready | Do not fill [N]/[M]/[K]/[X]/[rho] without runs | paper/generated/ |
| Draft validation passes | ready | `validate_paper_assets.py --mode draft` | script output |
| No false empirical figures | ready | Placeholder PNGs only | paper/figures/*_placeholder.* |

### Budget / cost state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Zero-cost default | ready | `max_total_usd: 0` on micro/stub/mock | config |
| Cost estimate (paid) | blocked | `estimate-cost` before any paid run | CLI JSON |
| Budget approval recorded | blocked | Written approval before `allow_paid_calls: true` | experiment log |

### Runtime state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| `plan-run` reviewed | ready | Check trajectory count and limits | plan-run output |
| Stop conditions set | ready | `limits.max_trajectories`, `max_runtime_minutes` | config |
| Interrupted run policy understood | ready | Read INTERRUPTED_AND_MICRO_RUNS.md | docs |

### Human validation state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Protocol documented | ready | HUMAN_VALIDATION_GUIDELINES.md | docs |
| Sample exported | blocked | After complete pilot | data/human_validation/ |
| Annotations complete | blocked | Required for C3, C10 supported | annotation CSV |

### Security / privacy state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| No secrets in repo | ready | `make security-check` | script |
| `.env` gitignored | ready | Copy from .env.example only | .gitignore |

### Advisor approval state

| Item | Status | Required action | Evidence path |
|---|---|---|---|
| Advisor brief reviewed | ready | ONE_PAGE_PROJECT_BRIEF.md | handoff/ |
| Paid pilot approved | blocked | Advisor sign-off before provider run | email/notes |
| Main experiment approved | blocked | MAIN_EXPERIMENT_GATE.md GO | experiments/ |

---

## Experiment-specific gates

### Micro mock run

**Config:** `configs/pilot_mock_diagnostic_micro.yaml`

| Gate | Status | Action |
|---|---|---|
| Freeze checklist (code, config, dataset) | ready | Run fast-check |
| Mock evidence level understood | ready | engineering_only only |
| Post-run audit | ready | `check_evidence_safety.py` |

**Allowed claims:** detector wiring validated — not real LLM behavior.

### Micro stub run

**Config:** `configs/pilot_stub_micro_3.yaml`

| Gate | Status | Action |
|---|---|---|
| Mock run optional first | not applicable | Recommended order |
| Stub provider only | ready | `local_stub` in config |
| Auto-score policy | ready | `auto_score: false` OK for micro |

**Allowed claims:** C9 pipeline reproducibility (engineering_only).

### Mock diagnostic 10

**Config:** `configs/pilot_mock_diagnostic_10.yaml`

| Gate | Status | Action |
|---|---|---|
| Limits reviewed | ready | plan-run |
| Runtime < 10 min | ready | mock agents deterministic |

### Local micro 3

**Config:** `configs/pilot_free_local_micro_3.yaml`

| Gate | Status | Action |
|---|---|---|
| Ollama/local model available | partial | User environment |
| Long-run risk acknowledged | partial | Set limits; mark-interrupted if stopped |
| Not scientific evidence | ready | local_model_preliminary at best |

**Requires:** explicit user decision to run local models (not part of build-mode default).

### 20-task local run

**Config:** `configs/pilot_free_local_20.yaml`

| Gate | Status | Action |
|---|---|---|
| Overnight runtime expected | blocked | Plan limits + disk space |
| Previous micro succeeded | partial | Optional prerequisite |
| Interrupted runs marked | partial | Clean up partial artifacts |

### Provider pilot (20 tasks)

**Config:** `configs/pilot_multi_provider_20.yaml`

| Gate | Status | Action |
|---|---|---|
| PRE_EXPERIMENT_FREEZE all sections | blocked | Complete checklist |
| `allow_paid_calls: true` + approval | blocked | Budget sign-off |
| `estimate-cost` reviewed | blocked | CLI |
| `dry-run` passed | ready | dry-run report |
| Frozen dataset | partial | data/frozen/pilot_v0.1 |
| Providers configured | partial | list-providers |

### 100-task pilot

**Config:** `configs/commercial_api_pilot_medium_100.yaml`

| Gate | Status | Action |
|---|---|---|
| 20-task pilot complete + analyzed | blocked | results/ |
| Claim ledger updated (weakened max) | blocked | No supported without main |
| Cost cap approved | blocked | budget block |

### 500-task main experiment

**Config:** `configs/commercial_api_main_500.yaml`

| Gate | Status | Action |
|---|---|---|
| MAIN_EXPERIMENT_GATE.md = GO | blocked | experiments/ |
| Human validation sample plan | blocked | export-human-validation |
| All prerequisites 1–14 | blocked | gate doc |

---

See [SAFE_NEXT_RUN_DECISION_TREE.md](SAFE_NEXT_RUN_DECISION_TREE.md) and [MASTER_STATUS.md](../MASTER_STATUS.md).
