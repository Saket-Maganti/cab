# ADR 0003: Filesystem content-addressed artifact store

Status: accepted

Local artifacts use SHA-256 addresses, immutable objects, atomic staging and
metadata sidecars. Raw evidence stays outside Git and is never garbage-collected
by default. Export/import bundles retain hashes and class metadata.
