#!/usr/bin/env python3
"""Verify IndicDB benchmark Parquets against the pinned Hugging Face revision."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd

MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "benchmarks"
    / "indicdb_source_manifest.json"
)
REQUIRED_COLUMNS = {"question", "sql", "pair_id", "dataset_name"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_parquet_path(
    language: str,
    local_dir: Path | None,
    download: bool,
    manifest: dict[str, Any],
) -> Path:
    entry = manifest["benchmark"]["files"][language]
    if local_dir is not None:
        nested_path = local_dir / entry["path"]
        return nested_path if nested_path.is_file() else local_dir / Path(entry["path"]).name
    if not download:
        raise ValueError("Provide --parquet-dir or use --download.")

    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            repo_id=manifest["benchmark"]["repo_id"],
            filename=entry["path"],
            repo_type="dataset",
            revision=manifest["benchmark"]["revision"],
        )
    )


def verify_indicdb_sources(
    *,
    parquet_dir: Path | None,
    download: bool,
    manifest_path: Path = MANIFEST_PATH,
    archive_path: Path | None = None,
    dump_path: Path | None = None,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    split_results: dict[str, dict[str, Any]] = {}
    all_dataset_names: set[str] = set()

    for language, expected in manifest["benchmark"]["files"].items():
        path = _resolve_parquet_path(language, parquet_dir, download, manifest)
        if not path.is_file():
            raise FileNotFoundError(f"IndicDB Parquet not found: {path}")

        frame = pd.read_parquet(path)
        missing_columns = sorted(REQUIRED_COLUMNS - set(frame.columns))
        if missing_columns:
            raise ValueError(
                f"{path.name} is missing required columns: {', '.join(missing_columns)}"
            )

        actual_sha256 = _sha256_file(path)
        actual_size = path.stat().st_size
        dataset_names = set(frame["dataset_name"].dropna().astype(str))
        all_dataset_names.update(dataset_names)
        blank_sql = frame["sql"].isna() | frame["sql"].astype(str).str.strip().eq("")
        duplicate_keys = frame.duplicated(
            subset=["pair_id", "dataset_name"], keep="first"
        )
        split_results[language] = {
            "file": path.name,
            "rows": len(frame),
            "expected_rows": expected["rows"],
            "sha256": actual_sha256,
            "expected_sha256": expected["sha256"],
            "size_bytes": actual_size,
            "expected_size_bytes": expected["size_bytes"],
            "distinct_dataset_names": len(dataset_names),
            "blank_sql_rows": int(blank_sql.sum()),
            "repeated_pair_schema_keys": int(duplicate_keys.sum()),
            "sha256_matches": actual_sha256 == expected["sha256"],
            "size_matches": actual_size == expected["size_bytes"],
            "row_count_matches": len(frame) == expected["rows"],
        }

    observed = manifest["benchmark"]["observed_totals"]
    total_rows = sum(result["rows"] for result in split_results.values())
    verification_passed = all(
        result["sha256_matches"]
        and result["size_matches"]
        and result["row_count_matches"]
        for result in split_results.values()
    )
    verification_passed = verification_passed and (
        total_rows == observed["physical_rows"]
        and len(all_dataset_names) == observed["distinct_dataset_names"]
    )

    archive_result = None
    archive_dump_sha256 = None
    if archive_path is not None:
        if not archive_path.is_file():
            raise FileNotFoundError(f"IndicDB source archive not found: {archive_path}")
        expected_archive = manifest["official_source_archive"]
        archive_sha256 = _sha256_file(archive_path)
        with ZipFile(archive_path) as archive:
            config_paths = [
                name for name in archive.namelist() if name.endswith("/schema_config.yaml")
            ]
            if not config_paths:
                raise ValueError(f"No schema_config.yaml files found in {archive_path}.")

            try:
                import yaml
            except ImportError as exc:
                raise RuntimeError(
                    "Archive schema verification requires PyYAML; install the 'indicdb' extra."
                ) from exc

            schema_names: set[str] = set()
            declared_table_count = 0
            for config_path in config_paths:
                config = yaml.safe_load(archive.read(config_path))
                schema_name = config.get("database_name")
                if not schema_name:
                    raise ValueError(f"{config_path} has no database_name.")
                if schema_name in schema_names:
                    raise ValueError(f"Duplicate schema_config for {schema_name!r}.")
                schema_names.add(schema_name)
                declared_table_count += len(config.get("dimension_tables") or {})
                declared_table_count += len(config.get("fact_tables") or {})

            dump_member = manifest["postgresql_dump"]["source_archive_member"]
            if dump_member in archive.namelist():
                digest = hashlib.sha256()
                with archive.open(dump_member) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                archive_dump_sha256 = digest.hexdigest()

        archive_result = {
            "file": archive_path.name,
            "size_bytes": archive_path.stat().st_size,
            "sha256": archive_sha256,
            "expected_sha256": expected_archive["local_sha256"],
            "sha256_matches": archive_sha256 == expected_archive["local_sha256"],
            "schema_count": len(schema_names),
            "expected_schema_count": manifest["postgresql_dump"][
                "verified_archive_schema_configs"
            ]["schemas"],
            "declared_table_count": declared_table_count,
            "expected_declared_table_count": manifest["postgresql_dump"][
                "verified_archive_schema_configs"
            ]["tables"],
            "benchmark_schema_names_missing_from_archive": sorted(
                all_dataset_names - schema_names
            ),
            "archive_schema_names_missing_from_benchmark": sorted(
                schema_names - all_dataset_names
            ),
            "exact_schema_name_match_count": len(all_dataset_names & schema_names),
            "embedded_dump_member": dump_member,
            "embedded_dump_sha256": archive_dump_sha256,
        }
        archive_result["schema_configs_match"] = (
            len(schema_names) == archive_result["expected_schema_count"]
            and declared_table_count == archive_result["expected_declared_table_count"]
        )

    dump_result = None
    if dump_path is not None:
        if not dump_path.is_file():
            raise FileNotFoundError(f"PostgreSQL dump not found: {dump_path}")
        expected_dump = manifest["postgresql_dump"]
        dump_sha256 = _sha256_file(dump_path)
        embedded_dump_matches = (
            archive_dump_sha256 is not None and dump_sha256 == archive_dump_sha256
        )
        dump_result = {
            "file": dump_path.name,
            "size_bytes": dump_path.stat().st_size,
            "sha256": dump_sha256,
            "matches_recorded_local_artifact": (
                dump_sha256 == expected_dump["local_sha256"]
                and dump_path.stat().st_size == expected_dump["local_size_bytes"]
            ),
            "official_source_checksum_available": (
                expected_dump["published_checksum"] is not None
            ),
            "embedded_archive_member_matches": embedded_dump_matches,
            "official_source_match_verified": embedded_dump_matches
            and bool(archive_result and archive_result["sha256_matches"]),
        }

    source_artifacts_verified = verification_passed and (
        archive_result is None
        or (
            archive_result["sha256_matches"]
            and archive_result["schema_configs_match"]
            and (
                dump_result is None
                or dump_result["embedded_archive_member_matches"]
            )
        )
    )
    return {
        "benchmark_repo_id": manifest["benchmark"]["repo_id"],
        "benchmark_revision": manifest["benchmark"]["revision"],
        "benchmark_license_metadata": manifest["benchmark"]["license_metadata"],
        "exact_license_subtype": manifest["benchmark"]["license_subtype"],
        "split_results": split_results,
        "physical_rows": total_rows,
        "distinct_dataset_names": len(all_dataset_names),
        "dataset_names": sorted(all_dataset_names),
        "benchmark_parquets_verified": verification_passed,
        "source_artifacts_verified": source_artifacts_verified,
        "source_archive": archive_result,
        "postgresql_dump": dump_result,
        "database_parity_status": (
            "schema_name_mismatch"
            if archive_result
            and (
                archive_result["benchmark_schema_names_missing_from_archive"]
                or archive_result["archive_schema_names_missing_from_benchmark"]
            )
            else "unverified"
        ),
        "notes": [
            "Benchmark Parquet checksums are compared to the pinned Hugging Face revision.",
            "Database parity requires a restore and gold-query checks; matching artifact hashes do not establish benchmark correctness.",
            "The dataset card license metadata is only 'cc'; its exact subtype is unresolved.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", type=Path)
    parser.add_argument(
        "--archive",
        type=Path,
        help="Optionally verify the official ZIP and its declared schema configs.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download each Parquet from the pinned public Hugging Face revision.",
    )
    parser.add_argument("--dump", type=Path, help="Optionally hash a local PostgreSQL dump.")
    parser.add_argument("--output", type=Path, help="Write the audit report as JSON.")
    args = parser.parse_args()
    if args.parquet_dir is None and not args.download:
        parser.error("Provide --parquet-dir or use --download.")
    if args.parquet_dir is not None and args.download:
        parser.error("Use either --parquet-dir or --download, not both.")

    report = verify_indicdb_sources(
        parquet_dir=args.parquet_dir,
        download=args.download,
        archive_path=args.archive,
        dump_path=args.dump,
    )
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized)
    return 0 if report["source_artifacts_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
