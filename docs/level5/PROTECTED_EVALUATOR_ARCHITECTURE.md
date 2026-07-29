# Protected evaluator architecture

The public foundation defines a submission manifest, resource request, sandbox
contract, trusted task broker, output audit and signed receipt. Docker is the
target fixture runtime; CI may use the mock runtime when Docker is unavailable.

The sandbox is ephemeral, non-root and network-denied. Evaluator code is
read-only, Linux capabilities are dropped, CPU/memory/process/wall/output limits
are explicit, the environment has no secrets and private tasks mount only
inside the trusted runtime. Cleanup is verified before a receipt can pass.

The task broker resolves opaque IDs only for trusted callers. Public receipts
contain evaluator/submission/task-set hashes, declarations, aggregate resource
use, audit status and disqualification reasons. Development signatures are
marked and cannot be mistaken for production keys.
