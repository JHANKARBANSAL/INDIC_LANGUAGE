"""
IndicDB Benchmark Evaluation Harness.
Executes candidate multi-agent SQL queries against gold relational ground truth,
computing Execution Accuracy (EX), Schema-Linking F1, and Indic-to-English Gap Delta.
"""

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel

from indicsql.benchmark.dataset import BenchmarkQuery
from indicsql.core.state import TabularResult
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.duckdb_engine import DuckDBSandbox

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "benchmark_results"


class BenchmarkResult(BaseModel):
    """Evaluation result for an individual benchmark query instance."""

    query_id: str
    language: str
    script: str
    domain: str
    difficulty: str
    query_text: str
    gold_sql: str
    predicted_sql: str
    execution_match: bool
    schema_f1: float
    execution_time_ms: float
    error_message: Optional[str] = None


def normalize_value(val: Any) -> Any:
    """Normalizes database values for loose equivalence matching."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        # Round floating points to 2 decimal places to avoid floating point precision drifts
        return round(float(val), 2)
    if isinstance(val, str):
        return val.strip().upper()
    return str(val)


def are_tabular_results_equivalent(
    res_pred: Optional[TabularResult], res_gold: Optional[TabularResult]
) -> bool:
    """
    Evaluates whether two SQL tabular execution outputs are isomorphic:
    Checks row multiset equality regardless of column ordering or row ordering (unless explicit order is tested).
    """
    if res_pred is None or res_gold is None:
        return False

    rows_pred = res_pred.get("rows", [])
    rows_gold = res_gold.get("rows", [])

    if len(rows_pred) != len(rows_gold):
        return False

    if len(rows_pred) == 0:
        return True

    # Normalize rows
    def row_to_canonical(row: List[Any]) -> Tuple[Any, ...]:
        return tuple(normalize_value(x) for x in row)

    counter_pred = Counter([row_to_canonical(r) for r in rows_pred])
    counter_gold = Counter([row_to_canonical(r) for r in rows_gold])

    return counter_pred == counter_gold


def compute_schema_linking_f1(
    predicted_elements: List[Dict[str, Any]], gold_columns: List[str]
) -> float:
    """Computes F1 score on predicted columns vs gold ground-truth columns."""
    if not gold_columns:
        return 1.0

    pred_cols: Set[str] = set()
    for el in predicted_elements:
        col = el.get("column_name")
        if col:
            pred_cols.add(col.lower())

    gold_set = {c.lower() for c in gold_columns}
    intersection = pred_cols.intersection(gold_set)

    if not intersection:
        return 0.0

    precision = len(intersection) / len(pred_cols) if pred_cols else 0.0
    recall = len(intersection) / len(gold_set) if gold_set else 0.0

    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


class IndicDBEvaluator:
    """Harness that evaluates the IndicSQL multi-agent system on the IndicDB benchmark."""

    def __init__(self, sandbox: Optional[DuckDBSandbox] = None):
        self.sandbox = sandbox or DuckDBSandbox()

    def evaluate_query(self, bq: BenchmarkQuery) -> BenchmarkResult:
        """Runs a single query through the pipeline and compares execution against gold SQL."""
        # 1. Execute Gold SQL to obtain Ground Truth Result Table
        gold_result = self.sandbox.execute_query(bq.gold_sql)

        # 2. Run IndicSQL multi-agent pipeline
        start_time = time.perf_counter()
        agent_state = execute_indicsql_pipeline(bq.query, query_id=bq.query_id)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        pred_sql = agent_state.get("generated_sql", "")
        pred_result = agent_state.get("execution_result")
        err_msg = agent_state.get("execution_error")

        # 3. Check Execution Isomorphism
        is_match = are_tabular_results_equivalent(pred_result, gold_result)

        # 4. Compute Schema-Linking F1
        f1_sl = compute_schema_linking_f1(agent_state.get("pruned_schema", []), bq.target_columns)

        return BenchmarkResult(
            query_id=bq.query_id,
            language=bq.language,
            script=bq.script,
            domain=bq.domain,
            difficulty=bq.difficulty,
            query_text=bq.query,
            gold_sql=bq.gold_sql,
            predicted_sql=pred_sql,
            execution_match=is_match,
            schema_f1=f1_sl,
            execution_time_ms=latency_ms,
            error_message=err_msg,
        )

    def evaluate_suite(
        self, queries: List[BenchmarkQuery], save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Executes benchmark evaluation across a set of queries and computes aggregate metrics.
        Returns:
            Dictionary containing metrics breakdown by Language, Difficulty, and Domain.
        """
        results: List[BenchmarkResult] = []
        total = len(queries)

        print(f"🚀 Evaluating {total} IndicDB Benchmark Queries across 7 Languages...")
        for i, q in enumerate(queries, start=1):
            res = self.evaluate_query(q)
            results.append(res)
            status_icon = "✓" if res.execution_match else "✗"
            print(
                f"   [{i}/{total}] {status_icon} [{q.language}] {q.query[:45]}... ({res.execution_time_ms:.1f}ms)"
            )

        # Aggregate Metrics Calculation
        metrics_by_lang: Dict[str, Dict[str, Any]] = {}
        for res in results:
            lang = res.language
            if lang not in metrics_by_lang:
                metrics_by_lang[lang] = {
                    "total": 0,
                    "correct": 0,
                    "f1_sum": 0.0,
                    "latency_sum": 0.0,
                }
            metrics_by_lang[lang]["total"] += 1
            if res.execution_match:
                metrics_by_lang[lang]["correct"] += 1
            metrics_by_lang[lang]["f1_sum"] += res.schema_f1
            metrics_by_lang[lang]["latency_sum"] += res.execution_time_ms

        summary_table: Dict[str, Dict[str, Any]] = {}
        indic_accuracies: List[float] = []
        en_accuracy: float = 0.0

        for lang, data in metrics_by_lang.items():
            acc = (data["correct"] / data["total"]) * 100.0 if data["total"] else 0.0
            avg_f1 = (data["f1_sum"] / data["total"]) if data["total"] else 0.0
            avg_lat = (data["latency_sum"] / data["total"]) if data["total"] else 0.0
            summary_table[lang] = {
                "total_queries": data["total"],
                "execution_accuracy_pct": round(acc, 2),
                "schema_f1": round(avg_f1, 3),
                "avg_latency_ms": round(avg_lat, 2),
            }
            if lang == "en":
                en_accuracy = acc
            else:
                indic_accuracies.append(acc)

        # Compute Indic-to-English Delta
        avg_indic_acc = (sum(indic_accuracies) / len(indic_accuracies)) if indic_accuracies else 0.0
        delta_indic_en = round(en_accuracy - avg_indic_acc, 2)

        overall_acc = (
            (sum(1 for r in results if r.execution_match) / total) * 100.0 if total else 0.0
        )

        report: Dict[str, Any] = {
            "total_evaluated": total,
            "overall_execution_accuracy_pct": round(overall_acc, 2),
            "english_accuracy_pct": round(en_accuracy, 2),
            "average_indic_accuracy_pct": round(avg_indic_acc, 2),
            "indic_to_english_gap_delta_pct": delta_indic_en,
            "per_language_metrics": summary_table,
            "results": [r.model_dump() for r in results],
        }

        if save_results:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = RESULTS_DIR / f"indicdb_eval_{timestamp}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📊 Detailed Benchmark Report saved: {report_path}")

        return report
