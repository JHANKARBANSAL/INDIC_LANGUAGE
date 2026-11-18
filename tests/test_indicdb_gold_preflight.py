import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from indicsql.benchmark.indicdb import INDICDB_LANGUAGE_FILES
from scripts.preflight_indicdb_benchmark import build_gold_preflight


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestIndicDBGoldPreflight(unittest.TestCase):
    def test_checks_sql_parsing_schema_tables_and_cross_language_alignment(self):
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
                    "card_claims": {"tasks": 1},
                },
                "postgresql_dump": {
                    "source_archive_member": "database/indicDB.dump",
                    "local_sha256": "",
                    "local_size_bytes": 0,
                    "published_checksum": None,
                    "byte_for_byte_source_match_verified": False,
                    "verified_archive_schema_configs": {"schemas": 1, "tables": 1},
                },
                "official_source_archive": {"local_sha256": ""},
            }

            for language, filename in INDICDB_LANGUAGE_FILES.items():
                path = parquet_dir / filename
                pd.DataFrame(
                    {
                        "question": [f"Question ({language})"],
                        "sql": ["SELECT T.STATE_NAME FROM DIM_STATE AS T"],
                        "pair_id": ["pair-1"],
                        "original_question_id": ["original-1"],
                        "dataset_name": ["SCHEMA_A"],
                    }
                ).to_parquet(path, index=False)
                manifest["benchmark"]["files"][language] = {
                    "path": f"data/{language}/{filename}",
                    "rows": 1,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }

            archive_path = root / "indicDB.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr(
                    "database/schema_a/schema_config.yaml",
                    "database_name: SCHEMA_A\ndimension_tables:\n  DIM_STATE: {}\nfact_tables: {}\n",
                )
                archive.writestr(
                    "database/schema_a/DDL.csv",
                    'table_name,description,DDL\nDIM_STATE,State table,"CREATE TABLE DIM_STATE (STATE_ID BIGINT, STATE_NAME TEXT);"\n',
                )
                archive.writestr("database/indicDB.dump", b"dump")
            manifest["official_source_archive"]["local_sha256"] = _sha256(
                archive_path
            )

            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = build_gold_preflight(parquet_dir, archive_path, manifest_path=manifest_path)

        self.assertEqual(report["gold_sql_parse_valid_rows"], 7)
        self.assertEqual(report["gold_sql_parse_invalid_rows"], 0)
        self.assertEqual(
            report["cross_language_alignment"][
                "common_pair_schema_keys_all_seven_languages"
            ],
            1,
        )
        self.assertEqual(
            report["cross_language_alignment"][
                "common_keys_with_identical_gold_sql_all_languages"
            ],
            1,
        )
        self.assertEqual(
            report["table_reference_check"][
                "rows_with_all_referenced_tables_present"
            ],
            7,
        )
        self.assertFalse(report["gold_sql_execution_verified"])
        self.assertFalse(report["human_language_review_verified"])


if __name__ == "__main__":
    unittest.main()
