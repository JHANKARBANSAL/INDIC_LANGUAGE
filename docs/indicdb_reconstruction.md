# IndicDB source reconstruction

## Source audit

The official benchmark repository is
[`roshankaranth/IndicDB`](https://huggingface.co/datasets/roshankaranth/IndicDB),
pinned for this audit to revision
`f57b0fb75d672114ae2d6e6be1a78d64056ce8af`. The seven local language Parquets
were compared with this revision; every SHA-256 hash matches the corresponding
file listed by the Hugging Face Hub API. The per-file hashes and observed row
counts are recorded in
[`data/benchmarks/indicdb_source_manifest.json`](../data/benchmarks/indicdb_source_manifest.json).
Repeat the benchmark and database-source audit with:

```bash
uv sync --extra indicdb
uv run python scripts/verify_indicdb_sources.py \
  --download \
  --archive /path/to/indicDB.zip \
  --dump /path/to/indicDB.dump
```

Or pass an existing Parquet directory with `--parquet-dir`. The archive option
checks the pinned ZIP hash, declared schema/table counts and schema-name
coverage. When `--dump` is also provided, it checks that the dump matches the
embedded archive member.

The pinned Parquet files contain 17,246 physical rows in total and reference
17 distinct `dataset_name` values. The dataset card reports 15,617 tasks and
20 databases. These values do not match the files at the pinned revision;
evaluation should use and report the actual pinned-file counts, not silently
substitute the card summary. The English split also contains five repeated
`(pair_id, dataset_name)` keys and five rows with blank SQL.

The dataset card labels the benchmark license only as `cc`; it does not specify
a Creative Commons subtype. The exact reuse license therefore remains
unverified and must not be guessed.

The dataset card links the PostgreSQL artifacts through Google Drive. The
linked download is an `indicDB.zip` archive. Its downloaded bytes match the
local ZIP SHA-256 exactly, and its embedded `database/indicDB.dump` member
matches the local custom-format dump SHA-256 exactly. The archive has 17
distinct `schema_config.yaml` database names declaring 208 dimension/fact
tables, rather than the card's 20 databases and 237 tables. These archive
counts are verified. The byte-verified dump was also restored into a disposable
PostgreSQL 16.16 container. Its catalog has 17 `india_%` schemas, 208 tables,
and 3,910,112 rows across those tables; this verifies the release dump's
restored catalog and row counts, but does not verify the card's 7.69 million
row claim.
Only 14 of the 17 benchmark `dataset_name` values exactly match an archive
schema-config name. Two IHDS 2005 names are now mapped with direct evidence:
the benchmark names add only a trailing underscore, while the corresponding
archive paths/config names, DDL table inventories, and restored dump schemas
all use `INDIA_IHDS_2005_HOUSEHOLD_SURVEY` and
`INDIA_IHDS_2005_INDIVIDUAL_SURVEY`. `INDIA_UDISE_SCHOOL_PROFILES` remains
unresolved: the archive's UDISE schema is named
`INDIA_UDISE_Right_To_Education_RTE_and_School_Management_data`, and no source
evidence demonstrates that these are the same benchmark database. Do not
claim full benchmark/database parity.

The ZIP also contains source CSVs and schema configs used by the repository's
reconstruction script. A reconstructed database is a separate variant and
must not be presented as the official dump.

A gold-query preflight on the previously audited dump also found empty results
caused by missing foreign-key values. Treat benchmark-to-database parity as
unverified until schema-name coverage and gold-query execution are checked
against the restored, byte-verified dump.

## Gold benchmark preflight

The pinned benchmark already provides gold SQL, so a separate hand-written
gold set is not substituted for it. Run the preflight after verifying the
source files:

```bash
uv run python scripts/preflight_indicdb_benchmark.py \
  --parquet-dir /path/to/indicdb_parquet \
  --archive /path/to/indicDB.zip \
  --dump /path/to/indicDB.dump
```

The preflight checks SQL parsing, exact schema-name coverage, table references
for rows whose schema names match, duplicate/blank SQL rows, and cross-language
pair alignment. Its checked report is
[`benchmark_results/indicdb_gold_preflight.json`](../benchmark_results/indicdb_gold_preflight.json).
For this pinned revision, 17,241 nonblank gold SQL rows parse, all 14,108 rows
with exact schema-name matches reference tables declared in the corresponding
archive DDL, and 2,043 `(pair_id, dataset_name)` keys are shared across all
seven splits with identical SQL.

This is a structural preflight, not gold-answer verification; its checked
report preserves the state of that structural check. The subsequent execution
audit is separately recorded in
[`benchmark_results/indicdb_gold_execution.json`](../benchmark_results/indicdb_gold_execution.json).
It restored the official dump in an isolated PostgreSQL 16.16 container and
ran every nonblank gold row with a mapped schema (16,250 rows) in a read-only
transaction with a 5-second statement timeout. All 16,250 executed without an
execution error; 6,760 returned an empty result. The 991 rows for unresolved
`INDIA_UDISE_SCHOOL_PROFILES` were deliberately not executed. Successful SQL
execution does not establish semantic correctness, and native-speaker language
review remains unperformed.

To reproduce the execution audit, use a fresh PostgreSQL 16 database and then:

```bash
python scripts/execute_indicdb_gold.py \
  --parquet-dir /path/to/pinned/IndicDB/snapshot \
  --archive /path/to/indicDB.zip \
  --dsn 'postgresql://user:password@localhost:5432/indicdb_official_audit' \
  --statement-timeout-ms 5000 \
  --output benchmark_results/indicdb_gold_execution.json
```

The runner confirms each mapped archive DDL table set against the restored
catalog before executing SQL, sets the mapped PostgreSQL schema as the local
search path, and rolls every query back. It records individual row counts,
empty results, errors, schema coverage, and exact table row counts. It leaves
the UDISE name unmapped rather than applying an alias.

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
