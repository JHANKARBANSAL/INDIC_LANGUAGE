#!/usr/bin/env python3
"""
CLI Benchmark Runner for IndicDB Evaluation Suite.
Usage:
    uv run scripts/evaluate_benchmark.py [--output results.json]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tabulate import tabulate  # noqa: E402

from indicsql.benchmark.dataset import load_benchmark_dataset  # noqa: E402
from indicsql.benchmark.evaluator import IndicDBEvaluator  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="IndicDB Text-to-SQL Benchmark Evaluation Harness")
    parser.add_argument(
        "--suite", type=str, default=None, help="Path to custom benchmark suite JSON file"
    )
    parser.add_argument(
        "--suite-expanded", action="store_true", help="Use the 105-query expanded IndicDB benchmark suite"
    )
    parser.add_argument(
        "--suite-280", "--pan-india", dest="suite_280", action="store_true", help="Use the comprehensive 280-query Pan-India benchmark suite"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit evaluation to first N queries"
    )
    parser.add_argument(
        "--compare-baselines", action="store_true", help="Print comparative baseline leaderboard against GPT-4o, Llama-3-70B, etc."
    )
    parser.add_argument(
        "--start", type=int, default=1, help="Start evaluation from query index (e.g. --start 121)"
    )
    parser.add_argument(
        "--resume", action="store_true", default=False, help="Resume from incremental checkpoint"
    )
    parser.add_argument(
        "--save", action="store_true", default=True, help="Save evaluation artifacts to disk"
    )
    args = parser.parse_args()

    if args.suite_280:
        suite_path = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_pan_india_280.json"
    elif args.suite_expanded:
        suite_path = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_expanded.json"
    elif args.suite:
        suite_path = Path(args.suite)
    else:
        suite_path = None

    queries = load_benchmark_dataset(suite_path)
    if args.limit:
        queries = queries[:args.limit]

    print("=" * 80)
    print("🇮🇳 IndicSQL: IndicDB Benchmark Evaluation Harness (April 2026)")
    print("=" * 80)
    print(f"Loaded {len(queries)} evaluation questions across 7 languages & 20 NDAP databases.\n")

    evaluator = IndicDBEvaluator()
    report = evaluator.evaluate_suite(
        queries,
        save_results=args.save,
        start_index=args.start,
        resume=args.resume,
    )

    # Format per-language summary table
    headers = [
        "Language",
        "Code",
        "Queries",
        "Exec Acc (EX)",
        "Exact Match (EM)",
        "SQL Validity",
        "AST Match",
        "Schema F1",
        "Latency",
    ]
    lang_names = {
        "en": "English (Baseline)",
        "hi-en": "Hinglish (Code-Mixed)",
        "mr": "Marathi",
        "hi": "Hindi",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
    }
    table_rows = []
    for code, m in report["per_language_metrics"].items():
        name = lang_names.get(code, code)
        table_rows.append(
            [
                name,
                code,
                m["total_queries"],
                f"{m['execution_accuracy_pct']:.1f}%",
                f"{m.get('exact_match_pct', 0.0):.1f}%",
                f"{m.get('sql_validity_pct', 100.0):.1f}%",
                f"{m.get('ast_structural_match_pct', 0.0):.1f}%",
                f"{m['schema_f1']:.3f}",
                f"{m['avg_latency_ms']:.1f}ms",
            ]
        )

    print("\n" + "=" * 95)
    print("📋 MULTI-TIER BENCHMARK PERFORMANCE MATRIX (EX, EM, VALIDITY & SCHEMA F1)")
    print("=" * 95)
    print(tabulate(table_rows, headers=headers, tablefmt="github"))

    print("\n📈 4-TIER RESEARCH EVALUATION METRICS:")
    print("=" * 60)
    print(f"  1. Execution Accuracy (EX)       : {report['overall_execution_accuracy_pct']}% (DuckDB ground-truth match)")
    print(f"  2. Exact Match Accuracy (EM)     : {report.get('overall_exact_match_pct', 0.0)}% (Normalized SQL string match)")
    print(f"  3. SQL Validity Rate             : {report.get('overall_sql_validity_pct', 100.0)}% (Syntactically valid AST)")
    print(f"  4. AST Structural Equivalence    : {report.get('overall_ast_structural_match_pct', 0.0)}% (Exact AST structure)")

    clauses = report.get("clause_accuracies_pct", {})
    if clauses:
        print("\n🧩 COMPONENT / CLAUSE ACCURACY BREAKDOWN:")
        print(f"  • SELECT (Projections & Aggs)    : {clauses.get('select', 0.0)}%")
        print(f"  • FROM (Target Table Mapping)    : {clauses.get('from', 0.0)}%")
        print(f"  • WHERE (Filters & Predicates)   : {clauses.get('where', 0.0)}%")
        print(f"  • GROUP BY (Grouping Dimensions) : {clauses.get('group_by', 0.0)}%")
        print(f"  • ORDER BY (Sort Expressions)    : {clauses.get('order_by', 0.0)}%")
        print(f"  • LIMIT (Row Slicing)            : {clauses.get('limit', 0.0)}%")

    print("\n🌐 CROSS-LINGUAL PARITY:")
    print(f"  • English Baseline Accuracy      : {report['english_accuracy_pct']}%")
    print(f"  • Average Indic Accuracy         : {report['average_indic_accuracy_pct']}%")
    delta = report["indic_to_english_gap_delta_pct"]
    delta_color = "🟢 Target Parity Achieved" if delta <= 2.0 else "🟡 Gap Pending Fine-Tuning"
    print(f"  • Indic-to-English Gap Delta     : {delta}% ({delta_color})")
    print("=" * 95)

    if args.compare_baselines:
        matrix_file = REPO_ROOT / "data" / "benchmarks" / "baseline_models_matrix.json"
        if matrix_file.exists():
            import json
            with open(matrix_file, "r", encoding="utf-8") as f:
                bdata = json.load(f)
            bmodels = bdata.get("models", {})
            bheaders = [
                "Model", "Weights / Path", "Params", "Edge Ready", "Overall EX", "EN EX", "Indic Avg", "Indic Gap (Δ)", "Schema F1", "Latency", "Cost/1K"
            ]
            brows = []
            order = [
                "indicsql-champion", "sarvam-adapter", "qwen-adapter",
                "indicsql-combo-a", "indicsql-combo-b", "indicsql-combo-c",
                "gpt-4o", "llama-3-70b-instruct", "sarvam-2b-base", "qwen-2.5-coder-3b-base"
            ]
            seen = set()
            for mid in order:
                if mid in bmodels and mid not in seen:
                    seen.add(mid)
                    m = bmodels[mid]
                    ex = m["execution_accuracy_pct"]
                    brows.append([
                        m["model_name"],
                        m.get("adapter_path", "N/A"),
                        m["parameter_size"],
                        "Yes (Edge)" if m["edge_deployable"] else "No (Cloud/API)",
                        f"{ex['overall']:.1f}%",
                        f"{ex['en']:.1f}%",
                        f"{m['indic_avg_ex_pct']:.1f}%",
                        f"{m['indic_to_english_gap_delta_pct']:+.2f}%",
                        f"{m['schema_f1']:.3f}",
                        f"{m['avg_latency_ms']:.0f}ms",
                        f"${m['cost_per_1k_queries_usd']:.2f}",
                    ])
            print("\n🏆 COMPARATIVE BASELINE LEADERBOARD (IndicDB April 2026)")
            print("=" * 80)
            print(tabulate(brows, headers=bheaders, tablefmt="github"))
            print("=" * 80)


if __name__ == "__main__":
    main()
