# Phase 01 handoff

State: `CAB_LEVEL5_CORE_REGISTRY_READY`.

Registry default: `.cab/registry.sqlite3`. Validate with:

```bash
cab registry init
cab registry doctor
cab registry backup
```

Protected fields are rejected. Store payloads outside the registry.
