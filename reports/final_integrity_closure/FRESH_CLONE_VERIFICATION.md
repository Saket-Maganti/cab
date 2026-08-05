# CAB final integrity closure — fresh-clone verification

Recorded at `2026-08-05T06:00:59.165032+00:00`.

The repository was cloned with `--single-branch --branch main` into a clean
path at commit `f63464b97148c3e87cdcf09bd0a6b325e193dff0`. No untracked file was copied in,
so every check below ran against exactly what a reviewer would receive.

The private packet is not in the clone at all — it is gitignored — so the
private-package surfaces are verified by hash and by externally supplied
protected paths, never by a Git-tracked private body.

| check | result |
| --- | --- |
| `clone` | PASS |
| `clean_worktree` | PASS |
| `no_tracked_private_data` | PASS |
| `private_root_absent` | PASS |
| `import` | PASS |
| `verify_freeze` | PASS |
| `verify_provenance` | PASS |
| `fixture_e2e` | PASS |
| `hostile_audit` | PASS |
| `focused_tests` | PASS 283 passed, 1 skipped in 34.76s |
| `retired_schema_rejected` | PASS |
| `status_documents` | PASS |
| `release_hashes` | PASS |

**Result: CAB_FRESH_CLONE_VERIFICATION_PASSED**
