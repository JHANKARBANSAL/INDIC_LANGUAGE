import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.graph.workflow import execute_indicsql_pipeline  # noqa: E402
from indicsql.schema.catalog import NDAPCatalog  # noqa: E402

SAMPLE_QUERIES_PATH = REPO_ROOT / "data" / "sample_queries" / "queries.json"


def load_sample_queries():
    if SAMPLE_QUERIES_PATH.exists():
        with open(SAMPLE_QUERIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    parser = argparse.ArgumentParser(
        description="IndicSQL Swarm Interactive CLI Demonstration"
    )
    parser.add_argument("query", nargs="?", default=None, help="Custom natural language query")
    parser.add_argument(
        "--list", action="store_true", help="List available sample queries across NDAP domains"
    )
    parser.add_argument(
        "--sample", type=int, default=None, help="Run a specific sample query index (1-based)"
    )
    args = parser.parse_args()

    samples = load_sample_queries()

    if args.list:
        print("=" * 80)
        print("🇮🇳 IndicSQL Sample Queries Across 20 NDAP Databases & 7 Languages")
        print("=" * 80)
        for i, s in enumerate(samples, start=1):
            print(f"[{i}] [{s.get('language')}] ({s.get('target_table')}):")
            print(f'    "{s.get("query")}"\n')
        print("To run a sample, use: uv run scripts/run_demo.py --sample <index>")
        return

    selected_query = "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
    if args.sample is not None:
        if 1 <= args.sample <= len(samples):
            selected_query = samples[args.sample - 1]["query"]
        else:
            print(f"Error: Sample index must be between 1 and {len(samples)}.")
            sys.exit(1)
    elif args.query:
        selected_query = args.query

    print("=" * 75)
    print("🇮🇳 IndicSQL: Autonomous Cross-Lingual Text-to-SQL Swarm")
    print(
        f"   Registered NDAP Databases: {NDAPCatalog.get_total_table_count()} | Parquet Stores Mounted"
    )
    print("=" * 75)
    print(f"📥 Input Query: {selected_query}\n")

    state = execute_indicsql_pipeline(selected_query)

    print("🔍 [Step 1] Supervisor Script & Language Detection:")
    print(
        f"   • Detected Language: {state.get('detected_lang')} | Script: {state.get('detected_script')}"
    )

    print("\n🔗 [Step 2] Cross-Lingual Schema Linking:")
    target_tbl = state.get("target_database", "Unknown")
    tbl_meta = NDAPCatalog.get_table_schema(target_tbl)
    domain = tbl_meta.get("domain", "NDAP")
    print(f"   • Target Domain: {domain} -> Table: '{target_tbl}'")
    for elem in state.get("pruned_schema", []):
        print(f"   • Linked Column: '{elem['column_name']}' ({elem.get('data_type', 'TEXT')})")

    print("\n⚡ [Step 3] Generated SQL:")
    print(f"   {state.get('generated_sql')}")

    print("\n💾 [Step 4] Sandboxed DuckDB Parquet Execution:")
    res = state.get("execution_result")
    if res:
        print(f"   • Columns: {res.get('columns')}")
        print(
            f"   • Rows ({res.get('row_count')} record(s), {res.get('execution_time_ms', 0):.2f}ms latency):"
        )
        for row in res.get("rows", [])[:5]:
            print(f"     -> {row}")
    else:
        print(f"   • Execution Error: {state.get('execution_error')}")

    print("\n🗣️ [Step 5] Vernacular Natural Language Answer:")
    print(f"   👉 {state.get('verbalized_response')}")
    print("=" * 75)


if __name__ == "__main__":
    main()
