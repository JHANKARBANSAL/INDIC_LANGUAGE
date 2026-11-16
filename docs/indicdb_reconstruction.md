# IndicDB source reconstruction

The Hugging Face test questions and the linked PostgreSQL dump do not form a
consistent release. The dump contains 17 schemas and 208 tables, while the
paper/card advertise 20 databases and 237 tables. A gold-query preflight also
found empty results caused by missing foreign-key values.

The reconstruction script creates a separate PostgreSQL database from
`indicDB.zip`'s `schema_config.yaml`, `DDL.csv`, and `data/total_data.csv`
members. It is not a repair of, or a replacement for, the released dump. Its
manifest records archive/config/source hashes, row counts, ambiguous
foreign-key mappings, and self-references that the source config cannot map.
Where a declared dimension deduplication key omits the parent identity required
by its foreign key, the reconstructed key is expanded with that identity. This
preserves source-row relationships but can change table row counts and is one
reason the result is a separate variant.
Integer-typed columns normalize source values such as `-1.0` to `-1`. Optional
config columns absent from the table DDL are omitted and recorded in the
manifest; missing key or foreign-key columns stop reconstruction. DDL columns
with no config mapping are also recorded and remain at their database defaults.
If the schema config declares a foreign-key column missing from the DDL, the
loader adds it using the referenced key's integer type and records that schema
change; it does not invent a PostgreSQL constraint.
The loader refuses to run against a database that already contains any of the
release schemas.

Install the optional tools with `pip install '.[indicdb]'`, create a fresh
empty PostgreSQL database, then run:

```bash
python scripts/reconstruct_indicdb.py \
  --archive /path/to/indicDB.zip \
  --dsn 'postgresql://user:password@localhost:5432/indicdb_reconstructed' \
  --manifest benchmark_results/indicdb_reconstruction_manifest.json
```

Do not present evaluation against this reconstructed variant as an official
IndicDBBench result. Report its provenance and limitations separately.

## Seven-language evaluation

`scripts/evaluate_indicdb_languages.py` runs aligned questions through the
existing IndicSQL pipeline and read-only PostgreSQL executor. It uses only the
Parquet `question`, `sql`, `pair_id`, and `dataset_name` fields; duplicate IDs
are disambiguated by schema name, and English prediction/leakage columns are
ignored. The seven files currently align on 2,043 `(pair_id, dataset_name)`
queries per language.

The benchmark's `dataset_name` supplies the expected schema to this evaluator.
This is schema-oracle evaluation: it measures multilingual SQL generation and
execution, not automatic database selection. Automatic selection remains a
separate capability to implement and measure.

Before PostgreSQL execution, generated SQL is checked against the selected
schema for table and column names. A failed schema check gets one retry with
the full selected schema; if it still fails, the query is not executed.
Passing this check verifies identifiers, not that the query matches the
question's meaning.

For a quick run of one question across all languages:

```bash
python scripts/evaluate_indicdb_languages.py \
  --parquet-dir /path/to/indicdb_parquet \
  --dsn 'postgresql://user:password@localhost:5432/indicdb_reconstructed' \
  --pair-id 685ad1fb \
  --output benchmark_results/indicdb_all_languages_smoke.json
```

By default the command evaluates every aligned pair in all seven languages
(14,301 pipeline runs); use `--limit 20` for a smaller check. Output records
the database variant, schema-selection mode, per-language execution accuracy,
gold-empty count, latency, SQL, errors, and source Parquet hashes. Results
against the reconstructed variant are not official paper-comparable scores.

Execution accuracy compares normalized, order-insensitive result rows from the
generated and gold queries on the same reconstructed database; it is not a
comparison of SQL text. Successful execution alone does not establish
correctness. For unseen questions without gold SQL or a reviewed expected
result, the system can show its SQL and returned rows, but cannot prove they
answer the user's intent. Automatic schema selection and universal correctness
are not established by this evaluation.
