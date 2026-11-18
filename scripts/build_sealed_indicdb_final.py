#!/usr/bin/env python3
"""Create a deterministic, sealed IndicDB final-test manifest.

The tracked manifest intentionally contains no final question text, SQL, or
selected keys.  The locally generated key file belongs in an ignored results
directory and is required only by the final evaluator after code is locked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent
LANGUAGE_FILES = {
    "en": "test_english.parquet",
    "hi": "test_hindi.parquet",
    "hi-en": "test_hinglish.parquet",
    "mr": "test_marathi.parquet",
    "ta": "test_tamil.parquet",
    "te": "test_telugu.parquet",
    "bn": "test_bengali.parquet",
}
REQUIRED_LANGUAGES = frozenset(LANGUAGE_FILES)
UNRESOLVED_SCHEMA_NAMES = frozenset(
    {
        "INDIA_IHDS_2005_HOUSEHOLD_SURVEY_",
        "INDIA_IHDS_2005_INDIVIDUAL_SURVEY_",
        "INDIA_UDISE_SCHOOL_PROFILES",
    }
)
DEFAULT_FIXTURES = (
    REPO_ROOT / "data/benchmarks/indicdb_eval_suite_pan_india_280.json",
    REPO_ROOT / "data/benchmarks/indicdb_development_candidate.json",
    REPO_ROOT / "data/benchmarks/indicdb_unseen_suite_140.json",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def _fixture_terms(paths: tuple[Path, ...]) -> tuple[set[str], set[str]]:
    questions: set[str] = set()
    sql: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Fixture is not a list: {path}")
        for item in payload:
            if isinstance(item.get("query"), str):
                questions.add(_normalise(item["query"]))
            if isinstance(item.get("gold_sql"), str):
                sql.add(_normalise(item["gold_sql"]))
    return questions, sql


def _load_groups(parquet_dir: Path) -> tuple[dict[tuple[str, str], dict[str, dict[str, str]]], dict[str, str]]:
    groups: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    hashes: dict[str, str] = {}
    for language, filename in LANGUAGE_FILES.items():
        path = parquet_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)
        hashes[language] = _sha256_file(path)
        for row in pq.read_table(path, columns=["question", "sql", "pair_id", "dataset_name"]).to_pylist():
            question = row["question"]
            sql = row["sql"]
            if not isinstance(question, str) or not isinstance(sql, str) or not sql.strip():
                continue
            key = (row["pair_id"], row["dataset_name"])
            if language in groups[key]:
                raise ValueError(f"Duplicate language row for key {key!r} in {language}")
            groups[key][language] = {"question": question, "sql": sql}
    return groups, hashes


def _key_digest(key: tuple[str, str]) -> str:
    return hashlib.sha256(f"{key[0]}\0{key[1]}".encode("utf-8")).hexdigest()


def build_selection(
    groups: dict[tuple[str, str], dict[str, dict[str, str]]],
    fixture_questions: set[str],
    fixture_sql: set[str],
    seed: str,
    group_count: int,
    excluded_keys: set[tuple[str, str]] | None = None,
) -> tuple[list[tuple[str, str]], Counter[str]]:
    exclusions: Counter[str] = Counter()
    excluded_keys = excluded_keys or set()
    candidates: list[tuple[str, str]] = []
    for key, translations in groups.items():
        if key in excluded_keys:
            exclusions["previously_opened_sealed_key"] += 1
            continue
        if key[1] in UNRESOLVED_SCHEMA_NAMES:
            exclusions["unresolved_schema_name"] += 1
            continue
        if set(translations) != REQUIRED_LANGUAGES:
            exclusions["incomplete_language_group"] += 1
            continue
        sql_values = {item["sql"] for item in translations.values()}
        if len(sql_values) != 1:
            exclusions["nonidentical_gold_sql"] += 1
            continue
        if any(_normalise(item["question"]) in fixture_questions for item in translations.values()):
            exclusions["question_overlap_with_development_fixture"] += 1
            continue
        if _normalise(next(iter(sql_values))) in fixture_sql:
            exclusions["sql_overlap_with_development_fixture"] += 1
            continue
        candidates.append(key)

    ranked = sorted(
        candidates,
        key=lambda key: hashlib.sha256(f"{seed}\0{key[0]}\0{key[1]}".encode("utf-8")).hexdigest(),
    )
    if len(ranked) < group_count:
        raise ValueError(f"Only {len(ranked)} eligible multilingual groups; requested {group_count}")
    return ranked[:group_count], exclusions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", type=Path, required=True)
    parser.add_argument("--seed", default="indicdb-final-v1-20261117")
    parser.add_argument("--group-count", type=int, default=40)
    parser.add_argument(
        "--exclude-key-file",
        type=Path,
        help="Ignored prior sealed-key file; its keys are excluded from a replacement set.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=REPO_ROOT / "data/benchmarks/indicdb_final_sealed_manifest.json",
    )
    parser.add_argument(
        "--sealed-key-output",
        type=Path,
        default=REPO_ROOT / "benchmark_results/sealed_final/indicdb_final_keys_v1.json",
    )
    args = parser.parse_args()
    args.manifest_output = args.manifest_output.resolve()
    args.sealed_key_output = args.sealed_key_output.resolve()

    groups, parquet_hashes = _load_groups(args.parquet_dir)
    fixture_questions, fixture_sql = _fixture_terms(DEFAULT_FIXTURES)
    excluded_keys = set()
    if args.exclude_key_file:
        excluded_keys = {
            (str(item["pair_id"]), str(item["dataset_name"]))
            for item in json.loads(args.exclude_key_file.read_text(encoding="utf-8"))
        }
    selected, exclusions = build_selection(
        groups, fixture_questions, fixture_sql, args.seed, args.group_count, excluded_keys
    )
    key_payload = [{"pair_id": pair_id, "dataset_name": dataset_name} for pair_id, dataset_name in selected]
    key_bytes = json.dumps(key_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    manifest = {
        "artifact_type": "IndicDB sealed final-test manifest",
        "status": "sealed_pending_official_postgresql_evaluation",
        "benchmark_repo_id": "roshankaranth/IndicDB",
        "benchmark_revision": "f57b0fb75d672114ae2d6e6be1a78d64056ce8af",
        "selection_rule": "SHA-256(seed + NUL + pair_id + NUL + dataset_name), ascending",
        "seed": args.seed,
        "group_count": len(selected),
        "question_count": len(selected) * len(REQUIRED_LANGUAGES),
        "languages": sorted(REQUIRED_LANGUAGES),
        "input_parquet_sha256": parquet_hashes,
        "development_fixture_files": [str(path.relative_to(REPO_ROOT)) for path in DEFAULT_FIXTURES if path.exists()],
        "eligible_group_exclusions": dict(sorted(exclusions.items())),
        "excluded_unresolved_schema_names": sorted(UNRESOLVED_SCHEMA_NAMES),
        "selected_key_sha256": hashlib.sha256(key_bytes).hexdigest(),
        "previously_opened_key_count_excluded": len(excluded_keys),
        "question_and_sql_in_manifest": False,
        "sealed_key_file_is_gitignored": str(args.sealed_key_output.relative_to(REPO_ROOT)),
        "official_postgresql_requirement": "Evaluate only on the byte-verified official dump restored with PostgreSQL 16 or newer; report unresolved UDISE rows separately.",
        "publication_warning": "No code or vocabulary tuning may use these selected questions or SQL.",
    }
    args.sealed_key_output.parent.mkdir(parents=True, exist_ok=True)
    args.sealed_key_output.write_text(json.dumps(key_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote sealed manifest: {args.manifest_output}")
    print(f"Wrote ignored selected-key file: {args.sealed_key_output}")
    print(f"Selected {len(selected)} seven-language groups ({len(selected) * len(REQUIRED_LANGUAGES)} questions)")


if __name__ == "__main__":
    main()
