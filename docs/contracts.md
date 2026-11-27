# API

`sequence(conditions, factors, index)` returns the permutation and factor for a zero-based index. `sequence_count(conditions, factors)` returns factorial of the number of conditions multiplied by the number of factors. Identifiers must be unique nonempty strings. At most eight conditions and 128 factor values. `source_hashes(root, sources)` returns a sorted SHA-256 manifest for explicitly selected relative files; rejects symlinks, duplicate paths and traversal. No allocation, subprocess execution or export. See [contract](../contracts/api.json).
