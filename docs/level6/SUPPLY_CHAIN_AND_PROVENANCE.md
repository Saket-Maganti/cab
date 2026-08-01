# Supply Chain and Provenance

The release path archives one exact full commit, sets `SOURCE_DATE_EPOCH`, builds
from the detached archive, and binds the Git tree, source archive, dependency
lock, wheel, sdist, SBOM, provenance, tests, and environment. Two builds compare
raw hashes; any normalized fallback is documented rather than called byte
reproducible.

Final scientific tags require a clean tree, local/remote SHA equality, passing
gates, external receipt storage, and signature/transparency verification. Private
keys never enter Git. Key policy covers scoped issuers, rotation before expiry,
immediate compromise revocation, historical verification material, and a signed
revocation log.

The foundation prepares `cab-level6-foundation-v1`; it does not publish a final
scientific release tag.
