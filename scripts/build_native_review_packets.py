#!/usr/bin/env python3
"""Create native-review CSV packets from the non-sealed development partition."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data/benchmarks/indicdb_development_candidate.json"
REVIEWER_LANGUAGES = {
    "english": {"en"},
    "hindi": {"hi", "hi-en"},
    "marathi": {"mr"},
    "bengali": {"bn"},
    "tamil": {"ta"},
    "telugu": {"te"},
}
FIELDS = (
    "query_id", "language", "domain", "question", "gold_sql", "target_table",
    "natural_and_unambiguous", "terms_correct", "intent_explicit",
    "gold_sql_semantics", "review_status", "reviewer", "review_date", "notes",
)


def build_packets(items: list[dict]) -> dict[str, list[dict[str, str]]]:
    packets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for reviewer, languages in REVIEWER_LANGUAGES.items():
        for item in items:
            if item["language"] not in languages:
                continue
            packets[reviewer].append(
                {
                    "query_id": item["query_id"], "language": item["language"],
                    "domain": item["domain"], "question": item["query"],
                    "gold_sql": item["gold_sql"], "target_table": item["target_table"],
                    "natural_and_unambiguous": "", "terms_correct": "",
                    "intent_explicit": "", "gold_sql_semantics": "",
                    "review_status": "pending", "reviewer": "", "review_date": "", "notes": "",
                }
            )
    return dict(packets)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "benchmark_results/native_review_packets")
    args = parser.parse_args()
    items = json.loads(args.input.read_text(encoding="utf-8"))
    packets = build_packets(items)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for reviewer, rows in packets.items():
        path = args.output_dir / f"{reviewer}_development_review.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{reviewer}: {len(rows)} rows -> {path}")


if __name__ == "__main__":
    main()
