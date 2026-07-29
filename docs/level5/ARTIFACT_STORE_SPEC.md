# Artifact store specification

The local CAS stores bytes under `objects/<sha256-prefix>/<remainder>` with a
metadata sidecar. Writes stage in the same filesystem, flush, fsync and atomically
replace the final path. Existing hashes are read and reverified before
deduplication.

Metadata records original/stored size, media type, raw/derived/fixture class,
compression and creation time. Reads recompute SHA-256 after decompression.
Corrupt or partial objects cannot be collected as evidence.

Bundles contain uncompressed blobs plus a manifest and are rehashed on import.
Garbage collection is dry-run only in the public CLI; raw evidence has no
automatic deletion path.
