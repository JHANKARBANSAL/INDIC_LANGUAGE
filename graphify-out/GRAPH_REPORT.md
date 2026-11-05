# Graph Report - IndicSQL_Repo  (2026-10-05)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 238 nodes · 472 edges · 10 communities (7 shown, 3 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.92)
- Token cost: 52,534 input · 93 output

## Graph Freshness
- Built from commit: `afad0c94`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- IndicSQL Pipeline Orchestration
- Benchmark Dataset & Evaluation
- NDAP Catalog & Schema Registry
- DuckDB Sandbox & Execution
- SQL Validation & Language Detection
- FastAPI Server Gateway
- Cross-Lingual Schema Linking
- Session Initialization Hook

## God Nodes (most connected - your core abstractions)
1. `IndicSQLState` - 23 edges
2. `execute_indicsql_pipeline()` - 21 edges
3. `NDAPCatalog` - 16 edges
4. `DuckDBSandbox` - 15 edges
5. `BenchmarkQuery` - 13 edges
6. `IndicDBEvaluator` - 13 edges
7. `create_indicsql_graph()` - 13 edges
8. `schema_linker_node()` - 13 edges
9. `ingest_and_export_all_ndap_databases()` - 11 edges
10. `supervisor_node()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `TestNDAPCatalogs` --uses--> `NDAPCatalog`  [INFERRED]
  tests/test_ndap_catalogs.py → indicsql/schema/catalog.py
- `TestBenchmarkHarness` --uses--> `BenchmarkQuery`  [INFERRED]
  tests/test_benchmark_harness.py → indicsql/benchmark/dataset.py
- `TestBenchmarkHarness` --uses--> `IndicDBEvaluator`  [INFERRED]
  tests/test_benchmark_harness.py → indicsql/benchmark/evaluator.py
- `main()` --uses--> `NDAPCatalog`  [INFERRED]
  scripts/run_demo.py → indicsql/schema/catalog.py
- `TestNDAPCatalogs` --uses--> `DuckDBSandbox`  [INFERRED]
  tests/test_ndap_catalogs.py → indicsql/sandbox/duckdb_engine.py

## Import Cycles
- None detected.

## Communities (10 total, 3 thin omitted)

### Community 0 - "IndicSQL Pipeline Orchestration"
Cohesion: 0.08
Nodes (14): critic_node(), reflection_healer_node(), format_indian_currency_number(), response_verbalizer_node(), verbalize_tabular_result(), sandbox_executor_node(), generate_aggregation_sql(), sql_synthesizer_node() (+6 more)

### Community 1 - "Benchmark Dataset & Evaluation"
Cohesion: 0.08
Nodes (11): BenchmarkQuery, generate_benchmark_suite(), load_benchmark_dataset(), are_tabular_results_equivalent(), row_to_canonical(), BenchmarkResult, compute_schema_linking_f1(), IndicDBEvaluator (+3 more)

### Community 2 - "NDAP Catalog & Schema Registry"
Cohesion: 0.08
Nodes (7): list_schemas(), NDAPCatalog, generate_ddl_sql(), _generate_table_rows(), ingest_and_export_all_ndap_databases(), load_sample_queries(), main()

### Community 3 - "DuckDB Sandbox & Execution"
Cohesion: 0.10
Nodes (3): TabularResult, DuckDBSandbox, TestNDAPCatalogs

### Community 4 - "SQL Validation & Language Detection"
Cohesion: 0.11
Nodes (5): validate_sql_security(), detect_indic_script(), identify_language_code(), validate_and_limit_sql(), TestAgentNodes

### Community 5 - "FastAPI Server Gateway"
Cohesion: 0.10
Nodes (6): health_check(), QueryRequest, QueryResponse, root(), run_query(), Settings

### Community 6 - "Cross-Lingual Schema Linking"
Cohesion: 0.13
Nodes (5): link_schema_elements(), schema_linker_node(), SchemaElement, normalize_indic_phonetics(), TestSchemaLinking

## Knowledge Gaps
- **1 isolated node(s):** `indicsql`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 111 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `execute_indicsql_pipeline()` connect `IndicSQL Pipeline Orchestration` to `Benchmark Dataset & Evaluation`, `NDAP Catalog & Schema Registry`, `DuckDB Sandbox & Execution`, `FastAPI Server Gateway`, `Cross-Lingual Schema Linking`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `DuckDBSandbox` connect `DuckDB Sandbox & Execution` to `Benchmark Dataset & Evaluation`, `SQL Validation & Language Detection`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `NDAPCatalog` connect `NDAP Catalog & Schema Registry` to `DuckDB Sandbox & Execution`, `FastAPI Server Gateway`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `IndicSQLState` (e.g. with `critic_node()` and `reflection_healer_node()`) actually correct?**
  _`IndicSQLState` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `NDAPCatalog` (e.g. with `list_schemas()` and `ingest_and_export_all_ndap_databases()`) actually correct?**
  _`NDAPCatalog` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DuckDBSandbox` (e.g. with `IndicDBEvaluator` and `TabularResult`) actually correct?**
  _`DuckDBSandbox` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `indicsql` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._