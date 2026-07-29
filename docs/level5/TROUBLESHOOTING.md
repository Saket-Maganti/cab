# Level-5 troubleshooting

- Registry lock: allow the configured 30-second SQLite busy timeout; do not copy
  a live database manually. Use `cab registry backup`.
- Hash mismatch: quarantine the object/registry copy and restore from a verified
  backup. Never promote it.
- Resume mismatch: retain the old run and compile a new manifest identity.
- Private-field rejection: move protected content to the designated private
  store; do not rename a secret to bypass the check.
- C10 blocked: obtain missing genuine reviews/adjudication. Fixtures cannot fix
  this state.
- Docker unavailable: run mock evaluator contract tests; do not claim sandbox
  security validation.
- Full suite memory pressure: use the measured `-n4`, with documented `-n2`
  fallback only if instability occurs.
