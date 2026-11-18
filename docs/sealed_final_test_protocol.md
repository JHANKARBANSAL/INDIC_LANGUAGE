# Sealed final-test protocol

The local 280-query suite is an iterative regression suite and must not be
reported as a held-out result. Create the paper's final test only from the
pinned official IndicDB revision `f57b0fb75d672114ae2d6e6be1a78d64056ce8af`.

1. Verify all seven Parquet SHA-256 values against
   `data/benchmarks/indicdb_source_manifest.json`.
2. Select multilingual `(pair_id, dataset_name)` groups with a published
   deterministic seed and cryptographic hash rule.
3. Write an immutable manifest containing revision, input hashes, selection
   rule, selected-key hash, and creation commit. Do not tune code using the
   selected questions or SQL.
4. Keep question text and gold SQL out of development fixtures and review
   packets. Before opening the selected-key file, create
   `data/benchmarks/indicdb_final_run_lock.json` with
   `scripts/lock_indicdb_final_run.py`. The lock records the sealed-manifest
   hash, all seven Parquet hashes, dump/archive hashes, source snapshot,
   model digest and sampling parameters, evaluator command, and PostgreSQL
   runtime. It must not contain credentials or selected keys.
5. Run the sealed evaluator only after the lock validates. The evaluator
   checks the lock and runtime before reading the ignored selected-key file,
   then reads only matching Parquet rows. It selects a PostgreSQL schema
   automatically from released schema metadata; the benchmark's
   `dataset_name` is used only for the gold reference and is never passed to
   the predictor. Invalid schema-router output is recorded as a failure,
   never replaced with the gold schema.
6. Keep question text and gold SQL out of the report. The report may contain
   generated SQL, execution errors, row counts, execution equivalence,
   latency, and per-language metrics. Run the sealed set once after model and
   configuration are locked.
7. Report the mapped-schema denominator and UDISE exclusions separately; do
   not claim full official parity while UDISE identity is unresolved.

The final set must be evaluated against the restored official PostgreSQL dump,
not the local NDAP/DuckDB regression data.

The evaluator's lock/run commands require `INDICDB_DSN` to be set to a
read-only PostgreSQL connection. Store the DSN outside the repository and do
not copy it into the lock or results.
