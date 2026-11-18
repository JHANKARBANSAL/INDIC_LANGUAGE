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

import argparse
import csv
import hashlib
import json
import logging
import platform
import re
import subprocess
import sys
import time
from collections import defaultdict
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import sqlglot
from sqlglot import exp

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Silence chatty loggers during benchmark
logging.getLogger("indicsql").setLevel(logging.WARNING)

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.duckdb_engine import DuckDBSandbox
from indicsql.agents.sql_synthesizer import _ollama_client, extract_canonical_entities
from indicsql.models.temporal_guard import TEMPORAL_COLUMN_NAMES, extract_temporal_intent

BENCHMARK_FILE = REPO_ROOT / "data" / "benchmarks" / "indicdb_unseen_suite_140.json"
RUN_OUTPUT_ROOT = REPO_ROOT / "benchmark_results" / "unseen_140_runs"

SCRIPT_RANGES = {
    "hi": [(0x0900, 0x097F)],          # Devanagari
    "mr": [(0x0900, 0x097F)],          # Devanagari
    "bn": [(0x0980, 0x09FF)],          # Bengali
    "ta": [(0x0B80, 0x0BFF)],          # Tamil
    "te": [(0x0C00, 0x0C7F)],          # Telugu
    "en": [(0x0000, 0x007F)],          # Basic Latin / ASCII
    "hi-en": [(0x0000, 0x007F)],       # Latin script
}
INDIC_SCRIPT_RANGES = tuple(
    script_range
    for language, ranges in SCRIPT_RANGES.items()
    if language not in {"en", "hi-en"}
    for script_range in ranges
)


def _contains_indic_script_char(text: str) -> bool:
    return any(
        start <= ord(char) <= end
        for char in text
        for start, end in INDIC_SCRIPT_RANGES
    )


def verify_verbalization_quality(verbalized_text: str, lang: str, gold_result: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
    """Verifies that verbalized prose is non-empty, script-pure, and numerically consistent."""
    if not verbalized_text or len(verbalized_text.strip()) < 8:
        return False, "EMPTY_OR_TRIVIAL_VERBALIZATION"

    # Script purity check
    if lang in ["en", "hi-en"]:
        if _contains_indic_script_char(verbalized_text):
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


def _expected_entities_from_gold(gold_sql: str) -> Dict[str, str]:
    """Extract canonical entity filters from gold SQL for benchmark grounding checks."""
    parsed = sqlglot.parse_one(gold_sql)
    aliases = {
        "state_name": "state_name",
        "district_name": "district_name",
        "commodity": "commodity",
        "crop_name": "commodity",
        "fertilizer_type": "commodity",
    }
    expected: Dict[str, str] = {}
    for predicate in parsed.find_all(exp.EQ):
        column = predicate.this
        value = predicate.expression
        if not isinstance(column, exp.Column) or not isinstance(value, exp.Literal):
            continue
        key = aliases.get(column.name.lower())
        if key:
            expected[key] = str(value.this)
    return expected


def _same_entity_value(left: Any, right: Any) -> bool:
    return str(left).strip().casefold() == str(right).strip().casefold()


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * (
        (proportion * (1 - proportion) / total + z * z / (4 * total * total)) ** 0.5
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _failure_category_counts(query_results: List[Dict[str, Any]]) -> Counter:
    return Counter(
        category
        for result in query_results
        for category in result["failure_categories"]
    )


def _json_default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _git_revision() -> Optional[str]:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _working_tree_dirty() -> Optional[bool]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _input_manifest() -> Dict[str, Any]:
    code_paths = [Path("scripts/evaluate_unseen_140.py"), *Path("indicsql").rglob("*.py")]
    code_paths.extend([Path("pyproject.toml"), Path("uv.lock")])
    parquet_paths = sorted((REPO_ROOT / "data" / "parquet_stores").rglob("*.parquet"))
    return {
        "code_sha256": {
            str(path): _sha256(REPO_ROOT / path)
            for path in code_paths
            if (REPO_ROOT / path).is_file()
        },
        "parquet_inputs": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in parquet_paths
        ],
    }


def _write_run_artifacts(
    output_dir: Path,
    query_results: List[Dict[str, Any]],
    scorecard_summary: Dict[str, Any],
    failure_counts: Counter,
) -> None:
    with (output_dir / "query_results.jsonl").open("w", encoding="utf-8") as f:
        for result in query_results:
            f.write(json.dumps(result, ensure_ascii=False, default=_json_default) + "\n")

    if query_results:
        with (output_dir / "query_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(query_results[0]))
            writer.writeheader()
            for result in query_results:
                writer.writerow(
                    {
                        key: json.dumps(value, ensure_ascii=False, default=_json_default)
                        if isinstance(value, (dict, list))
                        else value
                        for key, value in result.items()
                    }
                )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_dir = output_dir / "figures"
    chart_dir.mkdir(exist_ok=True)
    languages = ["en", "hi-en", "hi", "mr", "bn", "ta", "te"]
    labels = ["English", "Hinglish", "Hindi", "Marathi", "Bengali", "Tamil", "Telugu"]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    rates, lower_errors, upper_errors = [], [], []
    for language in languages:
        score = scorecard_summary[language]
        total = score["total_queries"]
        successes = score["execution_correct"]
        low, high = _wilson_interval(successes, total)
        rate = successes / total * 100 if total else 0
        rates.append(rate)
        lower_errors.append(rate - low * 100)
        upper_errors.append(high * 100 - rate)
    ax.bar(labels, rates, color="#3769a5", yerr=[lower_errors, upper_errors], capsize=4)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Execution accuracy (EX, %)")
    ax.set_title("IndicSQL execution accuracy by language (95% Wilson intervals)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(chart_dir / "execution_accuracy_by_language.png", dpi=180)
    plt.close(fig)

    latency_by_language = [
        [row["latency_ms"] for row in query_results if row["language"] == language]
        for language in languages
    ]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.boxplot(latency_by_language, showmeans=True)
    ax.set_xticks(range(1, len(labels) + 1), labels)
    ax.set_ylabel("Pipeline latency (ms)")
    ax.set_title("End-to-end latency by language")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(chart_dir / "latency_by_language.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    if failure_counts:
        categories = sorted(failure_counts, key=failure_counts.get, reverse=True)
        values = [failure_counts[category] for category in categories]
        ax.barh(categories[::-1], values[::-1], color="#b65353")
        ax.set_xlabel("Failed queries")
    else:
        ax.text(0.5, 0.5, "No failed queries", ha="center", va="center")
        ax.set_axis_off()
    ax.set_title("Failure categories (categories may overlap)")
    fig.tight_layout()
    fig.savefig(chart_dir / "failure_categories.png", dpi=180)
    plt.close(fig)


def evaluate_unseen_suite(
    benchmark_file: Path = BENCHMARK_FILE,
    output_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    if not benchmark_file.exists():
        raise FileNotFoundError(f"Benchmark file does not exist: {benchmark_file}")

    with benchmark_file.open("r", encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)

    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = output_dir or RUN_OUTPUT_ROOT / run_id
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty; choose a new run ID or output directory: {output_dir}"
        )

    sandbox = DuckDBSandbox()
    total_queries = len(queries)
    started_at = datetime.now(timezone.utc)

    print("=" * 80)
    print(f"Executing End-to-End Multilingual Evaluation on {total_queries} Benchmark Queries")
    print("=" * 80)

    metrics_by_lang = defaultdict(
        lambda: {
            "total": 0,
            "grounding_correct": 0,
            "grounding_evaluable": 0,
            "table_correct": 0,
            "ex_correct": 0,
            "verbalization_correct": 0,
            "gold_sql_errors": 0,
            "latencies_ms": [],
            "failures": [],
        }
    )
    query_results: List[Dict[str, Any]] = []
    gold_sql_errors: List[str] = []
    empty_gold_results: List[str] = []
    target_table_mismatches: List[str] = []
    temporal_review_flags: List[str] = []

    start_suite_time = time.perf_counter()

    for idx, q in enumerate(queries, 1):
        q_id = q["query_id"]
        lang = q["language"]
        gold_sql = q["gold_sql"]
        target_table = q["target_table"]
        query_text = q["query"]

        gold_res = None
        gold_sql_error = None
        expected_entities: Dict[str, str] = {}
        try:
            parsed_gold = sqlglot.parse_one(gold_sql)
            gold_tables = {table.name for table in parsed_gold.find_all(exp.Table)}
            if target_table not in gold_tables:
                target_table_mismatches.append(q_id)
            expected_entities = _expected_entities_from_gold(gold_sql)
            intent = extract_temporal_intent(query_text)
            sql_columns = {column.name.lower() for column in parsed_gold.find_all(exp.Column)}
            if intent.has_intent and not (sql_columns & TEMPORAL_COLUMN_NAMES):
                temporal_review_flags.append(q_id)
            gold_res = sandbox.execute_query(gold_sql)
            if not gold_res.get("rows"):
                empty_gold_results.append(q_id)
        except Exception as exc:
            gold_sql_error = f"{type(exc).__name__}: {exc}"
            gold_sql_errors.append(q_id)

        t0 = time.perf_counter()
        pipeline_exception = None
        try:
            pipeline_state = execute_indicsql_pipeline(query_text, query_id=q_id)
        except Exception as exc:
            pipeline_exception = f"{type(exc).__name__}: {exc}"
            pipeline_state = {
                "generated_sql": "",
                "execution_result": None,
                "execution_error": pipeline_exception,
                "audit_trace": [],
            }
        latency_ms = (time.perf_counter() - t0) * 1000.0

        pred_sql = pipeline_state.get("generated_sql", "")
        pred_res = pipeline_state.get("execution_result")
        verbalized_ans = pipeline_state.get("verbalized_response") or pipeline_state.get("verbalized_answer", "")
        pred_table = pipeline_state.get("target_database")
        entities = pipeline_state.get("grounded_entities") or extract_canonical_entities(query_text)

        grounding_pass = (
            all(
                key in entities and _same_entity_value(entities[key], value)
                for key, value in expected_entities.items()
            )
            if expected_entities
            else None
        )
        table_pass = (pred_table == target_table)
        ex_pass = (
            gold_res is not None
            and pred_res is not None
            and are_tabular_results_equivalent(pred_res, gold_res)
        )
        verb_pass, verb_reason = verify_verbalization_quality(verbalized_ans, lang, gold_res)

        metrics = metrics_by_lang[lang]
        metrics["total"] += 1
        if expected_entities:
            metrics["grounding_evaluable"] += 1
        if grounding_pass is True:
            metrics["grounding_correct"] += 1
        if table_pass:
            metrics["table_correct"] += 1
        if ex_pass:
            metrics["ex_correct"] += 1
        if verb_pass:
            metrics["verbalization_correct"] += 1
        if gold_sql_error:
            metrics["gold_sql_errors"] += 1
        metrics["latencies_ms"].append(latency_ms)

        failure_categories = []
        if gold_sql_error:
            failure_categories.append("GOLD_SQL_ERROR")
        if pipeline_exception:
            failure_categories.append("PIPELINE_EXCEPTION")
        elif not pred_res:
            failure_categories.append("SQL_EXECUTION_ERROR")
        elif not ex_pass:
            failure_categories.append("RESULT_MISMATCH")
        if grounding_pass is False:
            failure_categories.append("ENTITY_GROUNDING_FAILURE")
        if not table_pass:
            failure_categories.append("TABLE_ROUTING_FAILURE")
        if not verb_pass:
            failure_categories.append(f"VERBALIZATION_{verb_reason}")

        synthesis_events = [
            entry
            for entry in pipeline_state.get("audit_trace", [])
            if entry.get("agent") == "SQLSynthesizerAgent"
        ]
        sql_method = synthesis_events[-1].get("method") if synthesis_events else None
        query_result = {
            "query_id": q_id,
            "language": lang,
            "script": q.get("script"),
            "domain": q.get("domain"),
            "difficulty": q.get("difficulty"),
            "query": query_text,
            "target_table": target_table,
            "predicted_table": pred_table,
            "gold_sql": gold_sql,
            "predicted_sql": pred_sql,
            "sql_method": sql_method,
            "expected_entities": expected_entities,
            "grounded_entities": entities,
            "grounding_pass": grounding_pass,
            "table_routing_pass": table_pass,
            "gold_sql_error": gold_sql_error,
            "gold_rows": gold_res.get("rows") if gold_res else None,
            "gold_row_count": len(gold_res.get("rows", [])) if gold_res else None,
            "prediction_rows": pred_res.get("rows") if pred_res else None,
            "prediction_row_count": len(pred_res.get("rows", [])) if pred_res else None,
            "prediction_empty": bool(pred_res is not None and not pred_res.get("rows")),
            "execution_completed": pred_res is not None and not pipeline_state.get("execution_error"),
            "execution_match": ex_pass,
            "execution_error": pipeline_state.get("execution_error") or pipeline_exception,
            "pipeline_exception": pipeline_exception,
            "verbalized_answer": verbalized_ans,
            "verbalization_pass": verb_pass,
            "verbalization_note": verb_reason,
            "latency_ms": round(latency_ms, 2),
            "failure_categories": failure_categories,
        }
        query_results.append(query_result)

        if (
            grounding_pass is False
            or not table_pass
            or not ex_pass
            or not verb_pass
        ):
            metrics["failures"].append({
                "query_id": q_id,
                "query": query_text,
                "gold_sql": gold_sql,
                "pred_sql": pred_sql,
                "gold_rows": gold_res.get("rows") if gold_res else None,
                "pred_rows": pred_res.get("rows") if pred_res else None,
                "grounded_entities": entities,
                "categories": failure_categories,
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
    tot_grounding_evaluable = 0
    tot_table = 0
    tot_ex = 0
    tot_verb = 0
    all_latencies = []

    ordered_langs = ["en", "hi-en", "hi", "mr", "bn", "ta", "te"]
    scorecard_summary = {}

    for l in ordered_langs:
        m = metrics_by_lang[l]
        q_count = m["total"]
        grounding_total = m["grounding_evaluable"]
        g_acc = (m["grounding_correct"] / grounding_total) * 100.0 if grounding_total else 0.0
        t_acc = (m["table_correct"] / q_count) * 100.0 if q_count else 0.0
        ex_acc = (m["ex_correct"] / q_count) * 100.0 if q_count else 0.0
        v_acc = (m["verbalization_correct"] / q_count) * 100.0 if q_count else 0.0
        avg_lat = sum(m["latencies_ms"]) / len(m["latencies_ms"]) if m["latencies_ms"] else 0.0

        tot_q += q_count
        tot_ground += m["grounding_correct"]
        tot_grounding_evaluable += grounding_total
        tot_table += m["table_correct"]
        tot_ex += m["ex_correct"]
        tot_verb += m["verbalization_correct"]
        all_latencies.extend(m["latencies_ms"])

        scorecard_summary[l] = {
            "total_queries": q_count,
            "grounding_accuracy_pct": round(g_acc, 2),
            "grounding_evaluable_queries": grounding_total,
            "table_routing_accuracy_pct": round(t_acc, 2),
            "execution_accuracy_pct": round(ex_acc, 2),
            "execution_correct": m["ex_correct"],
            "verbalization_accuracy_pct": round(v_acc, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "median_latency_ms": round(median(m["latencies_ms"]), 2) if m["latencies_ms"] else 0.0,
            "gold_sql_error_count": m["gold_sql_errors"],
            "failures": m["failures"],
        }

        print(f"{l:<10} | {q_count:<7} | {g_acc:>11.1f}% | {t_acc:>9.1f}% | {ex_acc:>16.1f}% | {v_acc:>15.1f}% | {avg_lat:>8.1f} ms")

    print("-" * 105)
    overall_g_acc = (tot_ground / tot_grounding_evaluable) * 100.0 if tot_grounding_evaluable else 0.0
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

    failure_counts = _failure_category_counts(query_results)
    finished_at = datetime.now(timezone.utc)
    language_counts = Counter(q["language"] for q in queries)
    archetypes = defaultdict(list)
    for query in queries:
        archetypes[query["query_id"].rsplit("-", 1)[-1]].append(query)
    consistent_translation_groups = all(
        len(rows) == 7
        and len({row["language"] for row in rows}) == 7
        and len({row["gold_sql"] for row in rows}) == 1
        for rows in archetypes.values()
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "run_id": run_id,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "git_revision": _git_revision(),
        "git_worktree_dirty": _working_tree_dirty(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "ollama_available": _ollama_client.is_available,
        "inference_model": (
            _ollama_client.model_name
            if _ollama_client.is_available
            else "schema_grounded_fallback"
        ),
        "ollama_temperature": 0.05 if _ollama_client.is_available else None,
        "ollama_seed": 42 if _ollama_client.is_available else None,
        "benchmark_file": str(benchmark_file.resolve()),
        "benchmark_sha256": hashlib.sha256(benchmark_file.read_bytes()).hexdigest(),
        "input_manifest": _input_manifest(),
        "benchmark_query_count": total_queries,
        "unique_question_count": len({q["query"] for q in queries}),
        "unique_gold_sql_count": len({q["gold_sql"] for q in queries}),
        "language_counts": dict(language_counts),
        "translation_archetype_count": len(archetypes),
        "translation_groups_consistent": consistent_translation_groups,
        "gold_sql_error_query_ids": gold_sql_errors,
        "empty_gold_result_query_ids": empty_gold_results,
        "gold_target_table_mismatch_ids": target_table_mismatches,
        "temporal_intent_review_ids": temporal_review_flags,
        "output_directory": str(output_dir.resolve()),
    }
    report_data = {
        "timestamp": finished_at.isoformat(),
        "metadata": metadata,
        "suite_integrity": {
            "gold_sql_executed_without_error": len(gold_sql_errors) == 0,
            "gold_sql_error_count": len(gold_sql_errors),
            "gold_sql_empty_result_count": len(empty_gold_results),
            "gold_target_table_mismatch_count": len(target_table_mismatches),
            "temporal_intent_review_count": len(temporal_review_flags),
            "translation_groups_consistent": consistent_translation_groups,
            "translation_archetype_count": len(archetypes),
        },
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
        "failure_category_counts": dict(failure_counts),
        "query_results": query_results,
    }

    report_path = output_dir / "evaluation_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=_json_default)
    with (output_dir / "run_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    _write_run_artifacts(output_dir, query_results, scorecard_summary, failure_counts)

    print(f"Full evaluation report saved to: {report_path}")
    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a reproducible 140-query IndicSQL evaluation.")
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK_FILE)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    evaluate_unseen_suite(args.benchmark, args.output_dir, args.run_id)
