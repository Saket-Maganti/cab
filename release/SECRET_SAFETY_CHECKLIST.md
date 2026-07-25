# Secret Safety Checklist

Status: required before any public release.

- No API keys in configs.
- No API keys in docs.
- No API keys in reports.
- No API keys in notebooks.
- Provider credentials passed by environment variables only.
- Logs redacted before release.
- `.env` files excluded.
- Human reviewer IDs pseudonymized if release requires anonymity.
