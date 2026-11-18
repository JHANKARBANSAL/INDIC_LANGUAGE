#!/usr/bin/env python3
"""Export unresolved multilingual linking cases for native-speaker review.

This tool is deliberately an audit exporter, not a training-data generator.
It never edits the multilingual index. Reviewers decide the minimal source
phrase, table, and column mapping before an approved term can be added.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = (
    REPO_ROOT
    / "benchmark_results/query_audit_pan_india_280_20261117_entity_sector_v1/evaluation_report.json"
)


def build_review_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for result in report["query_results"]:
        categories = set(result.get("failure_categories", []))
        if not (
            "TABLE_ROUTING_FAILURE" in categories
            or "ENTITY_GROUNDING_FAILURE" in categories
        ):
            continue
        rows.append(
            {
                "query_id": result["query_id"],
                "language": result["language"],
                "target_table": result["target_table"],
                "target_columns": ", ".join(result.get("target_columns", [])),
                "question": result["query"],
                "failure_categories": ", ".join(sorted(categories)),
                "reviewed_source_phrase": "",
                "approved_table": "",
                "approved_column": "",
                "review_status": "pending",
                "reviewer": "",
                "review_notes": "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "benchmark_results/multilingual_vocabulary_review_queue.csv",
    )
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    rows = build_review_rows(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    print(f"Wrote {len(rows)} review rows to {args.output}")


if __name__ == "__main__":
    main()
