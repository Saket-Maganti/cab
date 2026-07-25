## Summary

<!-- What changed and why? -->

## Evidence level

<!-- e.g., engineering_only, docs_only, no runs -->

## Checklist

- [ ] `make fast-check` passes (or explain why not)
- [ ] No paid API calls (`allow_paid_calls: false` in any new config)
- [ ] No long / Ollama model runs in CI or PR artifacts
- [ ] No secrets (.env, keys) committed
- [ ] No unsupported scientific claims (C1–C8/C10 remain planned unless explicitly evidenced)
- [ ] Claim ledger updated if claim status or evidence paths changed
- [ ] Docs updated and linked from `docs/README.md` if applicable
- [ ] New/changed configs validated: `validate-config --config ...`
- [ ] Evidence level declared for any new run artifacts
- [ ] Paper placeholders **not** filled with fake values
- [ ] Mock/stub outputs labeled engineering-only (not described as LLM results)

## Tests run

```bash
make fast-check
# other commands:
```

## Related issues

<!-- Fixes # -->
