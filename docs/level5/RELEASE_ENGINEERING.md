# Level-5 release engineering

A release candidate requires static/type/spelling checks, structured-data
validation, package build, wheel/sdist inspection, clean install, CLI smoke,
docs build, SBOM, licence inventory, security scans, fixture reproduction,
chaos/evaluator/red-team campaigns and the Level-5 gate.

Release artifacts include checksums, SBOM, dependency licences, benchmark and
dataset cards, model-card templates, security/red-team reports, reproducibility
receipt, schema migrations, deprecations and exact commands. Protected payloads
are forbidden.

The current foundation is not a Level-5 final release because genuine evidence,
external reproduction and pilots are absent. Tagging a final Level-5 release is
therefore deferred.
