# Evaluation registry policy

Result records include immutable submission/model/policy/task/scorer/run hashes,
support set, uncertainty, audit and reproduction status. CAB does not publish a
point-only leaderboard. Comparisons require common support and display
uncertainty or rank probabilities.

Corrections create a superseding version; withdrawals retain the old identifier
and reason. Scorer changes create new score/evidence nodes rather than altering
old artifacts. Comparability is versioned and may be revoked after
contamination.

Only public-safe aggregates enter the public registry. Raw trajectories,
protected tasks, reviewer identity maps and evaluator-only metadata stay out.
