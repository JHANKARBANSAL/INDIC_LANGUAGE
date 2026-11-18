#!/usr/bin/env python3
"""Build a development partition with no exact question or gold-SQL overlap.

The 280-query pan-India suite is frozen for local evaluation.  This script
derives a separate development candidate from the older expanded suite, after
excluding every item whose normalized question or gold SQL appears in the
frozen suite.  It does not certify translation quality; native-speaker review
is recorded separately and remains required before research claims.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "data/benchmarks/indicdb_eval_suite_expanded.json"
FROZEN_PATH = REPO_ROOT / "data/benchmarks/indicdb_eval_suite_pan_india_280.json"
OUTPUT_PATH = REPO_ROOT / "data/benchmarks/indicdb_development_candidate.json"


def _load_items(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of benchmark items in {path}")
    return payload


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def build_partition(
    source_items: list[dict[str, Any]], frozen_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    frozen_questions = {_normalized(item["query"]) for item in frozen_items}
    frozen_sql = {_normalized(item["gold_sql"]) for item in frozen_items}
    selected = [
        item
        for item in source_items
        if _normalized(item["query"]) not in frozen_questions
        and _normalized(item["gold_sql"]) not in frozen_sql
    ]
    languages = {item["language"] for item in selected}
    expected_languages = {"en", "hi-en", "hi", "mr", "bn", "ta", "te"}
    if languages != expected_languages:
        raise ValueError(f"Development partition languages are incomplete: {languages}")
    return selected


def main() -> None:
    source_items = _load_items(SOURCE_PATH)
    frozen_items = _load_items(FROZEN_PATH)
    selected = build_partition(source_items, frozen_items)
    with OUTPUT_PATH.open("w", encoding="utf-8") as output:
        json.dump(selected, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(f"Wrote {len(selected)} development-candidate items to {OUTPUT_PATH}")
    print(f"Frozen suite SHA-256: {hashlib.sha256(FROZEN_PATH.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
