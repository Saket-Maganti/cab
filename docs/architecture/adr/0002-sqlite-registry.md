# ADR 0002: SQLite as the local registry default

Status: accepted

SQLite provides transactions, foreign keys, integrity checks, online backup and
WAL concurrency without an external service. The registry API is storage
independent, allowing a future PostgreSQL adapter. Registry rows contain only
public-safe metadata; protected payloads remain in separate stores.
