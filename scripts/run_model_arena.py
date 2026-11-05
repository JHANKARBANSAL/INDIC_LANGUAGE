#!/usr/bin/env python3
"""
IndicSQL Model Arena CLI Runner.
Benchmarks queries against Tri-Combo configurations:
- Combo A (Hybrid Champion): Sarvam-2B + Qwen-2.5-Coder-3B LoRA
- Combo B (Sarvam-only): Sarvam-2B + Heuristic ToT
- Combo C (Qwen-only): Heuristic Transliteration + Qwen-2.5-Coder-3B LoRA

Outputs a rich terminal comparison table and writes timestamped JSON audit results.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from indicsql.benchmark.dataset import CURATED_BENCHMARK_INSTANCES
from indicsql.core.state import IndicSQLState
from indicsql.models.combo import ComboResult, TriComboEngine


def run_arena_query(
    query: str,
    target_table: str = "ndap_pm_kisan_disbursement",
    language: str = "hi",
    engine: TriComboEngine = None,
) -> List[ComboResult]:
    if engine is None:
        engine = TriComboEngine()

    state: IndicSQLState = {
        "raw_query": query,
        "language": language,
        "detected_script": "Devanagari",
        "target_table": target_table,
        "query_id": f"arena-{int(datetime.now().timestamp())}",
        "canonical_query": query,
        "selected_columns": ["farmer_beneficiaries", "amount_inr", "state_name"],
        "schema_confidence": 0.95,
        "join_path": [],
        "generated_sql": "",
        "syntax_valid": False,
        "execution_result": None,
        "row_count": 0,
        "execution_error": None,
        "execution_time_ms": 0.0,
        "reflection_attempts": 0,
        "error_category": None,
        "remediation_applied": None,
        "audit_trace": [],
        "final_response": "",
        "audio_input_bytes": None,
        "audio_output_bytes": None,
        "voice_gender": "female",
        "transcribed_text": None,
        "hands_free_mode": False,
        "audio_turn_count": 0,
        "voice_latency_ms": 0.0,
    }

    return engine.run_all(state)


def display_and_save_results(
    query: str,
    results: List[ComboResult],
    console: Console,
    output_dir: Path,
) -> Dict[str, Any]:
    table = Table(title=f"Tri-Combo Model Arena: \"{query}\"", show_header=True, header_style="bold magenta")
    table.add_column("Combo", style="cyan", width=22)
    table.add_column("SQL Generated", style="green", min_width=40, max_width=60, overflow="ellipsis", no_wrap=True)
    table.add_column("Method", style="yellow", width=15)
    table.add_column("Latency (ms)", justify="right", width=14)
    table.add_column("Utility Score", justify="right", style="bold", width=14)

    winner: ComboResult = max(results, key=lambda r: (r.utility_score, -r.latency_ms))

    for r in results:
        is_winner = (r.combo == winner.combo)
        combo_label = "Combo A (Hybrid)" if r.combo == "hybrid" else ("Combo B (Sarvam)" if r.combo == "sarvam_pure" else "Combo C (Qwen)")
        if is_winner:
            combo_label += " 🏆"
        table.add_row(
            combo_label,
            r.generated_sql.strip().replace("\n", " "),
            r.method,
            f"{r.latency_ms:.2f}",
            f"{r.utility_score:.4f}",
        )

    console.print(table)
    console.print(f"[bold green]Winner:[/bold green] {winner.combo.upper()} (Utility: {winner.utility_score:.4f}, Latency: {winner.latency_ms:.2f}ms)\n")

    # Record timestamped audit
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "results": [r.to_dict() for r in results],
        "winner": winner.to_dict(),
    }

    out_file = output_dir / f"arena_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    console.print(f"[dim]Results written to: {out_file}[/dim]")
    return record


def main():
    parser = argparse.ArgumentParser(description="IndicSQL Tri-Combo Model Arena Runner")
    parser.add_argument("--query", type=str, default="", help="Specific NL query to benchmark")
    parser.add_argument("--suite", action="store_true", help="Run full benchmark suite across all instances")
    parser.add_argument("--output-dir", type=str, default="benchmark_results", help="Target results directory")
    args = parser.parse_args()

    console = Console()
    engine = TriComboEngine()
    out_dir = Path(args.output_dir)

    console.print("\n[bold cyan]=== IndicSQL Sovereign Tri-Combo Model Arena ===[/bold cyan]")
    console.print(f"[dim]Sarvam Adapter Available: {engine.sarvam_adapter.is_available}[/dim]")
    console.print(f"[dim]Qwen Adapter Available:   {engine.qwen_adapter.is_available}[/dim]\n")

    if args.suite:
        console.print(f"Executing suite over {len(CURATED_BENCHMARK_INSTANCES)} benchmark queries...\n")
        suite_records = []
        for item in CURATED_BENCHMARK_INSTANCES:
            res = run_arena_query(
                query=item["query"],
                target_table=item.get("target_table", "ndap_pm_kisan_disbursement"),
                language=item.get("language", "hi"),
                engine=engine,
            )
            rec = display_and_save_results(item["query"], res, console, out_dir)
            suite_records.append(rec)
        console.print(f"\n[bold green]Suite evaluation completed: {len(suite_records)} queries evaluated.[/bold green]")
    else:
        q = args.query or "बिहार में सबसे कम महिला साक्षरता दर किस जिले में है?"
        res = run_arena_query(query=q, engine=engine)
        display_and_save_results(q, res, console, out_dir)


if __name__ == "__main__":
    main()
