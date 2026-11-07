"""
IndicDB Benchmark Evaluation Harness.
Executes candidate multi-agent SQL queries against gold relational ground truth,
computing:
1. Execution Accuracy (EX) - Relational multiset isomorphism
2. Exact Match Accuracy (EM) - Normalized query string equivalence
3. SQL Validity Rate - Syntactically valid AST parsing
4. Component / Clause Accuracy - AST breakdown of SELECT, FROM, WHERE, GROUP BY, ORDER BY, LIMIT
5. Schema-Linking F1 and Indic-to-English Delta
"""

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlglot
from sqlglot import exp
from pydantic import BaseModel, Field

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
    exact_match: bool = False
    sql_validity: bool = True
    ast_match: bool = False
    clause_accuracy: Dict[str, bool] = Field(default_factory=dict)
    schema_f1: float = 0.0
    execution_time_ms: float = 0.0
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


def check_sql_validity(sql_str: str) -> Tuple[bool, Optional[exp.Expression]]:
    """Checks whether the SQL query is syntactically valid and parses into an AST."""
    if not sql_str or not sql_str.strip():
        return False, None
    try:
        clean = sql_str.strip().rstrip(";")
        parsed = sqlglot.parse_one(clean)
        return True, parsed
    except Exception:
        return False, None


def normalize_sql_tokens(sql_str: str) -> str:
    """Normalizes SQL query string for Exact Match (EM) comparison."""
    if not sql_str:
        return ""
    return " ".join(sql_str.strip().rstrip(";").split()).upper()


def extract_where_predicates(where_node: Optional[exp.Where]) -> List[str]:
    """Flattens conjunctive WHERE predicates to allow order-independent condition comparison."""
    if not where_node:
        return []
    cond = where_node.this if hasattr(where_node, "this") else where_node
    preds: List[str] = []

    def flatten_and(node: Any) -> None:
        if isinstance(node, exp.And):
            flatten_and(node.left)
            flatten_and(node.right)
        else:
            preds.append(node.sql().upper())

    flatten_and(cond)
    return sorted(preds)


def evaluate_clause_accuracy(
    pred_parsed: Optional[exp.Expression], gold_parsed: Optional[exp.Expression]
) -> Dict[str, bool]:
    """
    Evaluates component / clause accuracy between predicted and gold SQL ASTs:
    - SELECT (projections & aggregations, ignoring column alias names)
    - FROM (tables queried)
    - WHERE (filtering predicates, commutative under AND)
    - GROUP BY (grouping dimensions)
    - ORDER BY (ordering expressions and sort direction)
    - LIMIT (limit slice)
    """
    if pred_parsed is None or gold_parsed is None:
        return {
            "select": False,
            "from": False,
            "where": False,
            "group_by": False,
            "order_by": False,
            "limit": False,
        }

    # 1. SELECT clause (unaliased expressions, sorted)
    p_sel = sorted([e.unalias().sql().upper() for e in pred_parsed.expressions]) if hasattr(pred_parsed, "expressions") else []
    g_sel = sorted([e.unalias().sql().upper() for e in gold_parsed.expressions]) if hasattr(gold_parsed, "expressions") else []
    select_match = (p_sel == g_sel)

    # 2. FROM / Table clause
    p_from = sorted([t.name.upper() for t in pred_parsed.find_all(exp.Table)])
    g_from = sorted([t.name.upper() for t in gold_parsed.find_all(exp.Table)])
    from_match = (p_from == g_from)

    # 3. WHERE clause
    p_where_preds = extract_where_predicates(pred_parsed.find(exp.Where))
    g_where_preds = extract_where_predicates(gold_parsed.find(exp.Where))
    where_match = (p_where_preds == g_where_preds)

    # 4. GROUP BY clause
    p_g = pred_parsed.find(exp.Group)
    g_g = gold_parsed.find(exp.Group)
    if p_g is None and g_g is None:
        group_match = True
    elif p_g is not None and g_g is not None:
        p_ge = sorted([e.sql().upper() for e in p_g.expressions])
        g_ge = sorted([e.sql().upper() for e in g_g.expressions])
        group_match = (p_ge == g_ge)
    else:
        group_match = False

    # 5. ORDER BY clause
    p_o = pred_parsed.find(exp.Order)
    g_o = gold_parsed.find(exp.Order)
    if p_o is None and g_o is None:
        order_match = True
    elif p_o is not None and g_o is not None:
        p_oe = [e.sql().upper() for e in p_o.expressions]
        g_oe = [e.sql().upper() for e in g_o.expressions]
        order_match = (p_oe == g_oe)
    else:
        order_match = False

    # 6. LIMIT clause
    p_l = pred_parsed.find(exp.Limit)
    g_l = gold_parsed.find(exp.Limit)
    if p_l is None and g_l is None:
        limit_match = True
    elif p_l is not None and g_l is not None:
        limit_match = (p_l.expression.sql() == g_l.expression.sql())
    else:
        limit_match = False

    return {
        "select": select_match,
        "from": from_match,
        "where": where_match,
        "group_by": group_match,
        "order_by": order_match,
        "limit": limit_match,
    }
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
        """Runs a single query through the pipeline and computes EX, EM, SQL Validity, and Clause metrics."""
        # 1. Execute Gold SQL to obtain Ground Truth Result Table
        gold_result = self.sandbox.execute_query(bq.gold_sql)

        # 2. Run IndicSQL multi-agent pipeline
        start_time = time.perf_counter()
        try:
            agent_state = execute_indicsql_pipeline(bq.query, query_id=bq.query_id)
        except Exception as e:
            agent_state = {
                "generated_sql": "",
                "execution_result": None,
                "execution_error": str(e),
                "pruned_schema": [],
            }
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        pred_sql = agent_state.get("generated_sql", "")
        pred_result = agent_state.get("execution_result")
        err_msg = agent_state.get("execution_error")

        # 1. Execution Accuracy (EX)
        is_ex_match = are_tabular_results_equivalent(pred_result, gold_result)

        # 2. SQL Validity Check
        is_valid, pred_parsed = check_sql_validity(pred_sql)
        _, gold_parsed = check_sql_validity(bq.gold_sql)

        # 3. Exact Match Accuracy (EM)
        exact_match = (normalize_sql_tokens(pred_sql) == normalize_sql_tokens(bq.gold_sql))

        # 4. Component / Clause Accuracy
        clauses = evaluate_clause_accuracy(pred_parsed, gold_parsed)
        ast_match = is_valid and all(clauses.values())

        # 5. Schema-Linking F1
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
            execution_match=is_ex_match,
            exact_match=exact_match,
            sql_validity=is_valid,
            ast_match=ast_match,
            clause_accuracy=clauses,
            schema_f1=f1_sl,
            execution_time_ms=latency_ms,
            error_message=err_msg,
        )

    def evaluate_suite(
        self,
        queries: List[BenchmarkQuery],
        save_results: bool = True,
        start_index: int = 1,
        resume: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes benchmark evaluation across a set of queries and computes aggregate metrics:
        - Execution Accuracy (EX)
        - Exact Match Accuracy (EM)
        - SQL Validity Rate
        - Component / Clause Accuracies (SELECT, FROM, WHERE, GROUP BY, ORDER BY, LIMIT)
        Supports resuming from failure via start_index and incremental checkpointing.
        """
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint_path = RESULTS_DIR / ".benchmark_eval_checkpoint.jsonl"
        results: List[BenchmarkResult] = []
        evaluated_qids: Set[str] = set()

        if resume and checkpoint_path.exists():
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            bdata = json.loads(line)
                            r = BenchmarkResult(**bdata)
                            results.append(r)
                            evaluated_qids.add(r.query_id)
                print(f"⚡ Resumed from checkpoint: {len(results)} queries loaded.")
            except Exception as e:
                print(f"Warning: Could not read checkpoint: {e}")

        total = len(queries)
        print(f"🚀 Evaluating {total} IndicDB Benchmark Queries across 7 Languages...")
        for i, q in enumerate(queries, start=1):
            if i < start_index:
                continue
            if q.query_id in evaluated_qids:
                continue

            res = self.evaluate_query(q)
            results.append(res)
            evaluated_qids.add(q.query_id)

            # Persist incrementally to checkpoint
            try:
                with open(checkpoint_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(res.model_dump(), ensure_ascii=False) + "\n")
            except Exception:
                pass

            ex_icon = "✓" if res.execution_match else "✗"
            em_icon = "✓" if res.exact_match else "✗"
            print(
                f"   [{i:03d}/{total:03d}] EX:{ex_icon} EM:{em_icon} [{q.language}] {q.query[:45]}... ({res.execution_time_ms:.1f}ms)"
            )

        # Aggregate Metrics Calculation
        metrics_by_lang: Dict[str, Dict[str, Any]] = {}
        clause_overall: Counter[str] = Counter()

        for res in results:
            lang = res.language
            if lang not in metrics_by_lang:
                metrics_by_lang[lang] = {
                    "total": 0,
                    "correct_ex": 0,
                    "correct_em": 0,
                    "valid_sql": 0,
                    "ast_match": 0,
                    "clause_counts": Counter(),
                    "f1_sum": 0.0,
                    "latency_sum": 0.0,
                }
            metrics_by_lang[lang]["total"] += 1
            if res.execution_match:
                metrics_by_lang[lang]["correct_ex"] += 1
            if res.exact_match:
                metrics_by_lang[lang]["correct_em"] += 1
            if res.sql_validity:
                metrics_by_lang[lang]["valid_sql"] += 1
            if res.ast_match:
                metrics_by_lang[lang]["ast_match"] += 1

            for c_name, c_match in res.clause_accuracy.items():
                if c_match:
                    metrics_by_lang[lang]["clause_counts"][c_name] += 1
                    clause_overall[c_name] += 1

            metrics_by_lang[lang]["f1_sum"] += res.schema_f1
            metrics_by_lang[lang]["latency_sum"] += res.execution_time_ms

        summary_table: Dict[str, Dict[str, Any]] = {}
        indic_accuracies: List[float] = []
        en_accuracy: float = 0.0

        for lang, data in metrics_by_lang.items():
            tot = data["total"]
            ex_acc = (data["correct_ex"] / tot) * 100.0 if tot else 0.0
            em_acc = (data["correct_em"] / tot) * 100.0 if tot else 0.0
            val_pct = (data["valid_sql"] / tot) * 100.0 if tot else 0.0
            ast_pct = (data["ast_match"] / tot) * 100.0 if tot else 0.0
            avg_f1 = (data["f1_sum"] / tot) if tot else 0.0
            avg_lat = (data["latency_sum"] / tot) if tot else 0.0

            clause_pcts = {
                c: round((data["clause_counts"][c] / tot) * 100.0, 1) if tot else 0.0
                for c in ["select", "from", "where", "group_by", "order_by", "limit"]
            }

            summary_table[lang] = {
                "total_queries": tot,
                "execution_accuracy_pct": round(ex_acc, 2),
                "exact_match_pct": round(em_acc, 2),
                "sql_validity_pct": round(val_pct, 2),
                "ast_structural_match_pct": round(ast_pct, 2),
                "clause_accuracies_pct": clause_pcts,
                "schema_f1": round(avg_f1, 3),
                "avg_latency_ms": round(avg_lat, 2),
            }
            if lang == "en":
                en_accuracy = ex_acc
            else:
                indic_accuracies.append(ex_acc)

        # Compute Indic-to-English Delta
        avg_indic_acc = (sum(indic_accuracies) / len(indic_accuracies)) if indic_accuracies else 0.0
        delta_indic_en = round(en_accuracy - avg_indic_acc, 2)

        eval_count = len(results) if results else total

        overall_ex = (
            (sum(1 for r in results if r.execution_match) / eval_count) * 100.0 if eval_count else 0.0
        )
        overall_em = (
            (sum(1 for r in results if r.exact_match) / eval_count) * 100.0 if eval_count else 0.0
        )
        overall_valid = (
            (sum(1 for r in results if r.sql_validity) / eval_count) * 100.0 if eval_count else 0.0
        )
        overall_ast = (
            (sum(1 for r in results if r.ast_match) / eval_count) * 100.0 if eval_count else 0.0
        )

        overall_clauses = {
            c: round((clause_overall[c] / eval_count) * 100.0, 2) if eval_count else 0.0
            for c in ["select", "from", "where", "group_by", "order_by", "limit"]
        }

        report: Dict[str, Any] = {
            "total_evaluated": eval_count,
            "overall_execution_accuracy_pct": round(overall_ex, 2),
            "overall_exact_match_pct": round(overall_em, 2),
            "overall_sql_validity_pct": round(overall_valid, 2),
            "overall_ast_structural_match_pct": round(overall_ast, 2),
            "clause_accuracies_pct": overall_clauses,
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
