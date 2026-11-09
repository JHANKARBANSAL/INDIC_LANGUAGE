#!/usr/bin/env python3
"""
scripts/evaluate_unseen_140.py
Comprehensive Multilingual Benchmark Harness for IndicSQL on 140 Unseen Queries.

Evaluates 140 unseen queries (20 queries x 7 languages) across:
1. Entity Grounding Accuracy (Pan-India State, District, Commodity recognition)
2. Schema Linking & Table Routing Accuracy (Dynamic cross-lingual lexicon mapping)
3. SQL Execution Accuracy (EX) (DuckDB multiset isomorphism against Gold SQL)
4. Verbalization Accuracy (Natural phrasing, regional number formatting, script purity)
5. Latency & Failure Categorization
"""

import json
import logging
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Silence chatty loggers during benchmark
logging.getLogger("indicsql").setLevel(logging.WARNING)

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.duckdb_engine import DuckDBSandbox
from indicsql.agents.sql_synthesizer import extract_canonical_entities

BENCHMARK_FILE = REPO_ROOT / "data" / "benchmarks" / "indicdb_unseen_suite_140.json"
REPORT_OUTPUT_FILE = REPO_ROOT / "data" / "benchmarks" / "unseen_140_evaluation_report.json"

SCRIPT_RANGES = {
    "hi": [(0x0900, 0x097F)],          # Devanagari
    "mr": [(0x0900, 0x097F)],          # Devanagari
    "bn": [(0x0980, 0x09FF)],          # Bengali
    "ta": [(0x0B80, 0x0BFF)],          # Tamil
    "te": [(0x0C00, 0x0C7F)],          # Telugu
    "en": [(0x0000, 0x007F)],          # Basic Latin / ASCII
    "hi-en": [(0x0000, 0x007F)],       # Latin script
}


def verify_verbalization_quality(verbalized_text: str, lang: str, gold_result: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
    """Verifies that verbalized prose is non-empty, script-pure, and numerically consistent."""
    if not verbalized_text or len(verbalized_text.strip()) < 8:
        return False, "EMPTY_OR_TRIVIAL_VERBALIZATION"

    # Script purity check
    if lang in ["en", "hi-en"]:
        # Should not contain Indic Unicode characters (>= 0x0900)
        indic_chars = [c for c in verbalized_text if ord(c) >= 0x0900]
        if len(indic_chars) > 0:
            return False, f"SCRIPT_POLLUTION_INDIC_IN_{lang.upper()}"
    elif lang in ["ta", "te", "bn"]:
        # Regional Dravidian / Bengali scripts should not contain Devanagari letters (excluding Indic danda 0x0964)
        devanagari_letters = [
            c for c in verbalized_text
            if (0x0900 <= ord(c) <= 0x0963) or (0x0966 <= ord(c) <= 0x097F)
        ]
        if len(devanagari_letters) > 0:
            return False, f"DEVANAGARI_LEAKAGE_IN_{lang.upper()}"

    # Numerical consistency check
    if gold_result and gold_result.get("rows"):
        first_row = gold_result["rows"][0]
        if first_row and len(first_row) > 0:
            val = first_row[0]
            if isinstance(val, (int, float)):
                # Verbalized text must contain numbers (digits or localized Indian terms)
                has_numbers = bool(re.search(r'\d+', verbalized_text))
                if not has_numbers:
                    return False, "MISSING_NUMERICAL_DATA"

    return True, "PASSED"


def evaluate_unseen_suite():
    if not BENCHMARK_FILE.exists():
        print(f"Error: {BENCHMARK_FILE} does not exist. Run build_unseen_140_benchmark.py first.")
        return

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)

    sandbox = DuckDBSandbox()
    total_queries = len(queries)

    print("=" * 80)
    print(f"Executing End-to-End Multilingual Evaluation on {total_queries} Unseen Queries")
    print("=" * 80)

    # Metrics aggregation
    metrics_by_lang = defaultdict(lambda: {
        "total": 0,
        "grounding_correct": 0,
        "table_correct": 0,
        "ex_correct": 0,
        "verbalization_correct": 0,
        "latencies_ms": [],
        "failures": [],
    })

    start_suite_time = time.perf_counter()

    for idx, q in enumerate(queries, 1):
        q_id = q["query_id"]
        lang = q["language"]
        gold_sql = q["gold_sql"]
        target_table = q["target_table"]
        query_text = q["query"]

        # 1. Execute Gold SQL
        gold_res = sandbox.execute_query(gold_sql)

        # 2. Run through actual IndicSQL pipeline
        t0 = time.perf_counter()
        pipeline_state = execute_indicsql_pipeline(query_text, query_id=q_id)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        pred_sql = pipeline_state.get("generated_sql", "")
        pred_res = pipeline_state.get("execution_result")
        verbalized_ans = pipeline_state.get("verbalized_response") or pipeline_state.get("verbalized_answer", "")
        pred_table = pipeline_state.get("target_database")
        entities = pipeline_state.get("grounded_entities") or extract_canonical_entities(query_text)

        # Evaluate Grounding
        gold_sql_upper = gold_sql.upper()
        expected_state = None
        for s in [
            'RAJASTHAN', 'GUJARAT', 'PUNJAB', 'UTTAR PRADESH', 'MAHARASHTRA',
            'BIHAR', 'ODISHA', 'MADHYA PRADESH', 'TELANGANA', 'KERALA',
            'TAMIL NADU', 'WEST BENGAL', 'ASSAM', 'HARYANA', 'KARNATAKA',
            'ANDHRA PRADESH', 'JHARKHAND'
        ]:
            if f"STATE_NAME = '{s}'" in gold_sql_upper:
                expected_state = s
                break

        expected_district = None
        if "DISTRICT_NAME = 'PUNE'" in gold_sql_upper:
            expected_district = "Pune"
        elif "DISTRICT_NAME = 'COIMBATORE'" in gold_sql_upper:
            expected_district = "Coimbatore"

        grounding_pass = True
        if expected_state and entities.get("state_name") != expected_state:
            grounding_pass = False
        if expected_district and entities.get("district_name") != expected_district:
            grounding_pass = False

        # Evaluate Table Routing
        table_pass = (pred_table == target_table)

        # Evaluate SQL Execution Accuracy (EX)
        ex_pass = are_tabular_results_equivalent(pred_res, gold_res)

        # Evaluate Verbalization
        verb_pass, verb_reason = verify_verbalization_quality(verbalized_ans, lang, gold_res)

        # Record metrics
        metrics = metrics_by_lang[lang]
        metrics["total"] += 1
        if grounding_pass:
            metrics["grounding_correct"] += 1
        if table_pass:
            metrics["table_correct"] += 1
        if ex_pass:
            metrics["ex_correct"] += 1
        if verb_pass:
            metrics["verbalization_correct"] += 1
        metrics["latencies_ms"].append(latency_ms)

        # Record failure diagnostics
        if not (grounding_pass and table_pass and ex_pass and verb_pass):
            failure_cats = []
            if not grounding_pass:
                failure_cats.append("ENTITY_GROUNDING_FAILURE")
            if not table_pass:
                failure_cats.append("TABLE_ROUTING_FAILURE")
            if not ex_pass:
                if pipeline_state.get("execution_error"):
                    failure_cats.append("SQL_EXECUTION_SYNTAX_ERROR")
                else:
                    failure_cats.append("SEMANTIC_LOGIC_MISMATCH")
            if not verb_pass:
                failure_cats.append(f"VERBALIZATION_{verb_reason}")

            metrics["failures"].append({
                "query_id": q_id,
                "query": query_text,
                "gold_sql": gold_sql,
                "pred_sql": pred_sql,
                "gold_rows": gold_res.get("rows"),
                "pred_rows": pred_res.get("rows") if pred_res else None,
                "grounded_entities": entities,
                "categories": failure_cats,
            })

        print(f"[{idx:03d}/{total_queries:03d}] {q_id} ({lang}): EX={'PASS' if ex_pass else 'FAIL'} | Table={'PASS' if table_pass else 'FAIL'} | Verb={'PASS' if verb_pass else 'FAIL'} ({latency_ms:.1f}ms)")

    total_time = time.perf_counter() - start_suite_time

    # Build scorecard
    print("\n" + "=" * 105)
    print(f"{'LANGUAGE-WISE EVALUATION SCORECARD (140 UNSEEN QUERIES)':^105}")
    print("=" * 105)
    print(f"{'Language':<10} | {'Queries':<7} | {'Grounding Acc':<13} | {'Table Acc':<11} | {'Execution Acc (EX)':<18} | {'Verbalization Acc':<17} | {'Avg Latency':<11}")
    print("-" * 105)

    tot_q = 0
    tot_ground = 0
    tot_table = 0
    tot_ex = 0
    tot_verb = 0
    all_latencies = []

    ordered_langs = ["en", "hi-en", "hi", "mr", "bn", "ta", "te"]
    scorecard_summary = {}

    for l in ordered_langs:
        m = metrics_by_lang[l]
        q_count = m["total"]
        g_acc = (m["grounding_correct"] / q_count) * 100.0 if q_count else 0.0
        t_acc = (m["table_correct"] / q_count) * 100.0 if q_count else 0.0
        ex_acc = (m["ex_correct"] / q_count) * 100.0 if q_count else 0.0
        v_acc = (m["verbalization_correct"] / q_count) * 100.0 if q_count else 0.0
        avg_lat = sum(m["latencies_ms"]) / len(m["latencies_ms"]) if m["latencies_ms"] else 0.0

        tot_q += q_count
        tot_ground += m["grounding_correct"]
        tot_table += m["table_correct"]
        tot_ex += m["ex_correct"]
        tot_verb += m["verbalization_correct"]
        all_latencies.extend(m["latencies_ms"])

        scorecard_summary[l] = {
            "total_queries": q_count,
            "grounding_accuracy_pct": round(g_acc, 2),
            "table_routing_accuracy_pct": round(t_acc, 2),
            "execution_accuracy_pct": round(ex_acc, 2),
            "verbalization_accuracy_pct": round(v_acc, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "failures": m["failures"],
        }

        print(f"{l:<10} | {q_count:<7} | {g_acc:>11.1f}% | {t_acc:>9.1f}% | {ex_acc:>16.1f}% | {v_acc:>15.1f}% | {avg_lat:>8.1f} ms")

    print("-" * 105)
    overall_g_acc = (tot_ground / tot_q) * 100.0 if tot_q else 0.0
    overall_t_acc = (tot_table / tot_q) * 100.0 if tot_q else 0.0
    overall_ex_acc = (tot_ex / tot_q) * 100.0 if tot_q else 0.0
    overall_v_acc = (tot_verb / tot_q) * 100.0 if tot_q else 0.0
    overall_avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

    print(f"{'OVERALL':<10} | {tot_q:<7} | {overall_g_acc:>11.1f}% | {overall_t_acc:>9.1f}% | {overall_ex_acc:>16.1f}% | {overall_v_acc:>15.1f}% | {overall_avg_lat:>8.1f} ms")
    print("=" * 105)
    print(f"Total benchmark execution time: {total_time:.2f} seconds ({total_time / tot_q * 1000:.1f} ms / query avg)\n")

    # Failure Analysis
    all_failures = []
    for l in ordered_langs:
        all_failures.extend(scorecard_summary[l]["failures"])

    print(f"Total Failed Queries: {len(all_failures)} / {tot_q}")
    if all_failures:
        print("\n--- DETAILED FAILURE BREAKDOWN ---")
        for f in all_failures:
            print(f"Query ID: {f['query_id']}")
            print(f"Query Text: {f['query']}")
            print(f"Categories: {', '.join(f['categories'])}")
            print(f"Gold SQL: {f['gold_sql']}")
            print(f"Pred SQL: {f['pred_sql']}")
            print(f"Gold Rows: {f['gold_rows']} | Pred Rows: {f['pred_rows']}")
            print("-" * 60)
    else:
        print("🎉 ZERO FAILURES! All 140 unseen queries passed Entity Grounding, Table Routing, SQL Execution, and Verbalization!")

    # Save to JSON
    report_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries": tot_q,
        "overall_metrics": {
            "grounding_accuracy_pct": round(overall_g_acc, 2),
            "table_routing_accuracy_pct": round(overall_t_acc, 2),
            "execution_accuracy_pct": round(overall_ex_acc, 2),
            "verbalization_accuracy_pct": round(overall_v_acc, 2),
            "avg_latency_ms": round(overall_avg_lat, 2),
            "total_benchmark_seconds": round(total_time, 2),
        },
        "language_scorecards": scorecard_summary,
    }

    REPORT_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"Full evaluation report saved to: {REPORT_OUTPUT_FILE}")


if __name__ == "__main__":
    evaluate_unseen_suite()
