#!/usr/bin/env python3
"""
scripts/evaluate_35_stratified.py
Stratified 35-Query IndicDB Benchmark Evaluation (5 queries x 7 languages).
Evaluates Execution Accuracy (EX), Exact Match (EM), SQL Validity, and Schema F1.
"""

import json
import sys
import time
from pathlib import Path
from tabulate import tabulate

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.benchmark.dataset import BenchmarkQuery
from indicsql.benchmark.evaluator import IndicDBEvaluator

SUITE_PATH = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_pan_india_280.json"

def main():
    print("=" * 80)
    print("🇮🇳 IndicSQL: 35-Query Stratified Benchmark Evaluation (5 Queries x 7 Languages)")
    print("=" * 80)

    with open(SUITE_PATH) as f:
        raw_items = json.load(f)

    # Group by language and pick first 5 of each
    by_lang = {}
    for item in raw_items:
        lang = item["language"]
        by_lang.setdefault(lang, []).append(item)

    selected_items = []
    # Order of presentation: English, Hinglish, Hindi, Marathi, Bengali, Tamil, Telugu
    lang_order = ["en", "hi-en", "hi", "mr", "bn", "ta", "te"]
    for lang in lang_order:
        selected_items.extend(by_lang.get(lang, [])[:5])

    benchmark_queries = [
        BenchmarkQuery(
            query_id=q["query_id"],
            query=q["query"],
            language=q["language"],
            script=q["script"],
            domain=q["domain"],
            target_table=q["target_table"],
            gold_sql=q["gold_sql"],
            difficulty=q.get("difficulty", "medium"),
            target_columns=q.get("target_columns", []),
        )
        for q in selected_items
    ]

    print(f"Loaded {len(benchmark_queries)} stratified queries across 7 languages.\n")

    evaluator = IndicDBEvaluator()
    start_total = time.perf_counter()

    results_by_lang = {l: [] for l in lang_order}

    for idx, bq in enumerate(benchmark_queries, 1):
        print(f"[{idx:02d}/{len(benchmark_queries):02d}] Evaluating {bq.language.upper()} ({bq.query_id}): \"{bq.query[:50]}...\"")
        res = evaluator.evaluate_query(bq)
        results_by_lang[bq.language].append(res)
        status_icon = "✅" if res.execution_match else "❌"
        print(f"       -> EX: {status_icon} | Valid: {res.sql_validity} | F1: {res.schema_f1:.2f} | Latency: {res.execution_time_ms:.0f}ms")

    elapsed_total = time.perf_counter() - start_total

    # Summary Table
    lang_names = {
        "en": "English (Baseline)",
        "hi-en": "Hinglish (Code-Mixed)",
        "hi": "Hindi",
        "mr": "Marathi",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu (Indic Gap Focus)",
    }

    table_rows = []
    total_ex = 0
    total_valid = 0
    total_f1 = 0
    total_count = 0

    for lang in lang_order:
        l_res = results_by_lang[lang]
        count = len(l_res)
        ex_cnt = sum(1 for r in l_res if r.execution_match)
        valid_cnt = sum(1 for r in l_res if r.sql_validity)
        em_cnt = sum(1 for r in l_res if r.exact_match)
        avg_f1 = sum(r.schema_f1 for r in l_res) / count if count else 0
        avg_lat = sum(r.execution_time_ms for r in l_res) / count if count else 0

        total_ex += ex_cnt
        total_valid += valid_cnt
        total_f1 += sum(r.schema_f1 for r in l_res)
        total_count += count

        table_rows.append([
            lang_names.get(lang, lang),
            lang,
            count,
            f"{ex_cnt/count*100:.1f}% ({ex_cnt}/{count})",
            f"{em_cnt/count*100:.1f}%",
            f"{valid_cnt/count*100:.1f}%",
            f"{avg_f1:.3f}",
            f"{avg_lat:.0f}ms",
        ])

    table_rows.append([
        "OVERALL / POOLED",
        "ALL",
        total_count,
        f"{total_ex/total_count*100:.1f}% ({total_ex}/{total_count})",
        "-",
        f"{total_valid/total_count*100:.1f}%",
        f"{total_f1/total_count:.3f}",
        f"{elapsed_total*1000/total_count:.0f}ms",
    ])

    headers = [
        "Language",
        "Code",
        "Queries",
        "Exec Acc (EX)",
        "Exact Match",
        "SQL Validity",
        "Schema F1",
        "Avg Latency",
    ]

    print("\n" + "=" * 95)
    print("📊 INDICSQL STRATIFIED BENCHMARK SCORECARD (ACROSS ALL 7 LANGUAGES)")
    print("=" * 95)
    print(tabulate(table_rows, headers=headers, tablefmt="github"))
    print("=" * 95)
    print(f"Total Evaluation Time: {elapsed_total:.2f} seconds\n")

if __name__ == "__main__":
    main()

