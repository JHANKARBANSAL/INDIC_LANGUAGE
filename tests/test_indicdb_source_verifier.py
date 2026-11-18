import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from indicsql.benchmark.indicdb import INDICDB_LANGUAGE_FILES
from scripts.verify_indicdb_sources import _resolve_parquet_path, verify_indicdb_sources


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestIndicDBSourceVerifier(unittest.TestCase):
    def test_accepts_hugging_face_snapshot_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "data" / "english" / "test_english.parquet"
            expected.parent.mkdir(parents=True)
            expected.touch()
            actual = _resolve_parquet_path(
                "en",
                root,
                False,
                {"benchmark": {"files": {"en": {"path": "data/english/test_english.parquet"}}}},
            )

        self.assertEqual(actual, expected)

    def test_verifies_pinned_splits_archive_configs_and_embedded_dump(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            parquet_dir = root / "parquets"
            parquet_dir.mkdir()
            manifest = {
                "benchmark": {
                    "repo_id": "test/IndicDB",
                    "revision": "test-revision",
                    "license_metadata": "cc",
                    "license_subtype": None,
                    "files": {},
                    "observed_totals": {
                        "physical_rows": len(INDICDB_LANGUAGE_FILES),
                        "distinct_dataset_names": 1,
                    },
                },
                "postgresql_dump": {
                    "source_archive_member": "database/indicDB.dump",
                    "local_sha256": "",
                    "local_size_bytes": 0,
                    "published_checksum": None,
                    "verified_archive_schema_configs": {"schemas": 1, "tables": 1},
                },
                "official_source_archive": {"local_sha256": ""},
            }

            for language, filename in INDICDB_LANGUAGE_FILES.items():
                path = parquet_dir / filename
                pd.DataFrame(
                    {
                        "question": [f"Question ({language})"],
                        "sql": ["SELECT 1"],
                        "pair_id": ["pair-1"],
                        "dataset_name": ["SCHEMA_A"],
                    }
                ).to_parquet(path, index=False)
                manifest["benchmark"]["files"][language] = {
                    "path": f"data/{language}/{filename}",
                    "rows": 1,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }

            dump_bytes = b"official dump bytes"
            dump_path = root / "indicDB.dump"
            dump_path.write_bytes(dump_bytes)
            manifest["postgresql_dump"]["local_sha256"] = _sha256(dump_path)
            manifest["postgresql_dump"]["local_size_bytes"] = dump_path.stat().st_size

            archive_path = root / "indicDB.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr(
                    "database/schema_a/schema_config.yaml",
                    "database_name: SCHEMA_A\ndimension_tables:\n  DIM_A: {}\nfact_tables: {}\n",
                )
                archive.writestr("database/indicDB.dump", dump_bytes)
            manifest["official_source_archive"]["local_sha256"] = _sha256(archive_path)

            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = verify_indicdb_sources(
                parquet_dir=parquet_dir,
                download=False,
                manifest_path=manifest_path,
                archive_path=archive_path,
                dump_path=dump_path,
            )

        self.assertTrue(report["benchmark_parquets_verified"])
        self.assertTrue(report["source_artifacts_verified"])
        self.assertTrue(report["source_archive"]["schema_configs_match"])
        self.assertTrue(report["postgresql_dump"]["embedded_archive_member_matches"])
        self.assertEqual(report["database_parity_status"], "unverified")

    def test_rejects_modified_parquet_checksum(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            parquet_dir = root / "parquets"
            parquet_dir.mkdir()
            for language, filename in INDICDB_LANGUAGE_FILES.items():
                pd.DataFrame(
                    {
                        "question": ["Question"],
                        "sql": ["SELECT 1"],
                        "pair_id": ["pair-1"],
                        "dataset_name": ["SCHEMA_A"],
                    }
                ).to_parquet(parquet_dir / filename, index=False)

            report = verify_indicdb_sources(
                parquet_dir=parquet_dir,
                download=False,
                manifest_path=Path(__file__).resolve().parents[1]
                / "data/benchmarks/indicdb_source_manifest.json",
            )

        self.assertFalse(report["benchmark_parquets_verified"])
        self.assertFalse(report["source_artifacts_verified"])


if __name__ == "__main__":
    unittest.main()
