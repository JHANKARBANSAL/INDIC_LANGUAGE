#!/usr/bin/env python3
"""
scripts/inspect_pipeline.py
Ultra-Transparent End-to-End Pipeline & SQL Verification Inspector.

Allows deep inspection of any query (custom or benchmark query_id):
1. Language detection & Phonetic Transliteration Bridge
2. Dynamic Entity Grounding (State, District, Commodity)
3. Schema Linker (Table routing & Column selection)
4. Side-by-side SQL Comparison: Gold SQL vs Predicted SQL
5. Live Dual DuckDB Execution: Gold Result Rows vs Predicted Result Rows
6. Forensic Agent Audit Trace

Usage:
    uv run scripts/inspect_pipeline.py --id indicdb-hi-001
    uv run scripts/inspect_pipeline.py --id indicdb-te-001
    uv run scripts/inspect_pipeline.py --query "उत्तर प्रदेश में कुल कितने किसानों को पीएम किसान का लाभ मिला?"
"""

import argparse
import json
import sys
import time
from pathlib import Path
from tabulate import tabulate

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.benchmark.dataset import BenchmarkQuery
from indicsql.benchmark.evaluator import IndicDBEvaluator, are_tabular_results_equivalent
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.schema.phonetic import transliterate_indic_to_latin

SUITE_PATH = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_pan_india_280.json"


def inspect_single_query(query_text: str, gold_sql: str = None, query_id: str = "custom-query", target_table: str = None):
    print("=" * 90)
    print(f"🔍 INDICSQL TRANSPARENT QUERY INSPECTOR: [{query_id}]")
    print("=" * 90)
    print(f"Input Query: \"{query_text}\"")

    # 1. Transliteration Bridge
    latin_bridge = transliterate_indic_to_latin(query_text)
    print(f"\n[STEP 1: PHONETIC TRANSLITERATION BRIDGE]")
    print(f"  • Transliterated Latin (ITRANS): \"{latin_bridge}\"")

    # 2. Dynamic Entity Grounding
    grounded = dynamic_entity_grounder.ground_entities(query_text)
    print(f"\n[STEP 2: DYNAMIC ENTITY GROUNDING]")
    print(f"  • Grounded State     : {grounded.get('state_name', 'None')}")
    print(f"  • Grounded District  : {grounded.get('district_name', 'None')}")
    print(f"  • Grounded Commodity : {grounded.get('commodity', 'None')}")

    # 3. Pipeline Execution
    print(f"\n[STEP 3: MULTI-AGENT SWARM EXECUTION]")
    start = time.perf_counter()
    evaluator = IndicDBEvaluator()
    state = execute_indicsql_pipeline(query_text, query_id=query_id)
    latency_ms = (time.perf_counter() - start) * 1000.0

    pred_sql = state.get("generated_sql", "")
    detected_lang = state.get("detected_lang", "unknown")
    detected_script = state.get("detected_script", "unknown")
    target_db = state.get("target_database", "unknown")

    print(f"  • Detected Language : {detected_lang} ({detected_script})")
    print(f"  • Routed Database   : {target_db}")
    print(f"  • Swarm Latency     : {latency_ms:.1f}ms")

    # 4. Side-by-side SQL comparison
    print(f"\n[STEP 4: SIDE-BY-SIDE SQL COMPARISON]")
    if gold_sql:
        print(f"  🎯 GOLD SQL (Ground Truth):\n     {gold_sql}")
    print(f"  🤖 PREDICTED SQL (IndicSQL Swarm):\n     {pred_sql}")

    # 5. Live DuckDB Execution on Real Parquet Stores
    print(f"\n[STEP 5: REAL DUCKDB DATABASE EXECUTION (SOURCE OF TRUTH)]")
    pred_res = evaluator.sandbox.execute_query(pred_sql) if pred_sql else None

    if gold_sql:
        gold_res = evaluator.sandbox.execute_query(gold_sql)
        is_match = are_tabular_results_equivalent(pred_res, gold_res)

        g_rows = gold_res.get("rows") if isinstance(gold_res, dict) else (gold_res.rows if gold_res else None)
        p_rows = pred_res.get("rows") if isinstance(pred_res, dict) else (pred_res.rows if pred_res else None)

        print(f"  • Gold Execution Rows      : {g_rows}")
        print(f"  • Predicted Execution Rows : {p_rows}")

        verdict_str = "✅ PASS (EX = 100% RELATIONAL ISOMORPHISM)" if is_match else "❌ FAIL (ROW MISMATCH OR EMPTY)"
        print(f"  • EXECUTION ACCURACY (EX)  : {verdict_str}")
    else:
        p_rows = pred_res.get("rows") if isinstance(pred_res, dict) else (pred_res.rows if pred_res else None)
        print(f"  • Execution Result Rows    : {p_rows}")

    # 6. Verbalized Response
    verbalized = state.get("verbalized_response")
    if verbalized:
        print(f"\n[STEP 6: CITIZEN VERBALIZED RESPONSE]")
        print(f"  🔊 \"{verbalized}\"")

    # 7. Forensic Audit Trace
    print(f"\n[STEP 7: COMPLETE FORENSIC AUDIT TRACE]")
    audit_trace = state.get("audit_trace", [])
    audit_table = []
    for entry in audit_trace:
        step_num = entry.get("step", "-")
        agent_name = entry.get("agent", "-")
        action = entry.get("action", "-")
        # Extract main detail
        details = {k: v for k, v in entry.items() if k not in ["step", "agent", "action"]}
        detail_str = ", ".join(f"{k}={v}" for k, v in list(details.items())[:3])
        audit_table.append([step_num, agent_name, action, detail_str[:55]])

    print(tabulate(audit_table, headers=["Step", "Agent", "Action", "Audited Telemetry"], tablefmt="github"))
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Inspect internal execution and compare Gold vs Predicted SQL")
    parser.add_argument("--id", type=str, default=None, help="Benchmark Query ID from 280 suite (e.g. indicdb-hi-001, indicdb-te-001)")
    parser.add_argument("--query", type=str, default=None, help="Custom natural language query string in any Indic language")
    parser.add_argument("--lang", type=str, default=None, help="Run first 3 queries of a specific language (en, hi-en, hi, mr, bn, ta, te)")
    args = parser.parse_args()

    with open(SUITE_PATH) as f:
        suite = json.load(f)

    if args.id:
        matches = [x for x in suite if x["query_id"] == args.id]
        if not matches:
            print(f"Error: Query ID '{args.id}' not found in 280-suite.")
            sys.exit(1)
        item = matches[0]
        inspect_single_query(
            query_text=item["query"],
            gold_sql=item["gold_sql"],
            query_id=item["query_id"],
            target_table=item["target_table"]
        )

    elif args.lang:
        matches = [x for x in suite if x["language"] == args.lang][:3]
        for item in matches:
            inspect_single_query(
                query_text=item["query"],
                gold_sql=item["gold_sql"],
                query_id=item["query_id"],
                target_table=item["target_table"]
            )

    elif args.query:
        # Check if query matches any benchmark item
        matched_gold = None
        for item in suite:
            if item["query"].strip() == args.query.strip():
                matched_gold = item["gold_sql"]
                break
        inspect_single_query(query_text=args.query, gold_sql=matched_gold)

    else:
        # Default: demonstrate 3 diverse queries (Hindi, Telugu, English)
        demo_ids = ["indicdb-en-001", "indicdb-hi-001", "indicdb-te-001"]
        for did in demo_ids:
            item = [x for x in suite if x["query_id"] == did][0]
            inspect_single_query(
                query_text=item["query"],
                gold_sql=item["gold_sql"],
                query_id=item["query_id"],
                target_table=item["target_table"]
            )


if __name__ == "__main__":
    main()

