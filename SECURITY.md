# Security Policy

## Supported versions

CausalAgentBench is a pre-1.0 research scaffold (`0.1.0`). Only the latest
`main` is supported; fixes are not back-ported to earlier tags.

| Version | Supported |
|---------|-----------|
| `main` / latest `0.1.x` | ✅ |
| anything older | ❌ |

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

1. Use GitHub's private reporting: the repository **Security** tab →
   **Report a vulnerability** (GitHub Security Advisories).
2. Include affected files/commit, reproduction steps, and impact.

We aim to acknowledge within 5 working days and to agree on a disclosure
timeline before any public discussion.

## Scope and design

This project is built to be safe by default; security-relevant properties are
documented and enforced in the codebase, not just here:

- **No live side effects by default.** Tools are *simulated* (email drafts only,
  booking stubs, no live web access). See
  [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md).
- **No paid/network calls by default.** Provider runs require explicit
  `allow_paid_calls: true` plus reviewed cost estimates.
- **Secrets stay out of the repo.** API keys are read only from environment
  variables (see [`.env.example`](.env.example)); the runner logs whether a
  provider is configured but never logs key values. `.env` is gitignored.
- **Automated secret/unsafe-default scan.** Run before every release:

  ```bash
  make security-check        # python scripts/security_check.py
  ```

When reporting, please note whether the issue concerns the code, the simulated
tool environment, or handling of provider credentials.
