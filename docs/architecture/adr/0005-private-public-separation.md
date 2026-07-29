# ADR 0005: Private/public separation

Status: accepted

The authoring compiler creates explicit public and private views. The registry
rejects protected field names recursively. Evaluator public manifests expose
only opaque task hashes and aggregates. Docker build context excludes private
data and result roots.
