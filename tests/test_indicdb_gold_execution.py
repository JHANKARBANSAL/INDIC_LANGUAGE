import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.execute_indicdb_gold import DIRECT_SCHEMA_MAPPINGS, build_schema_mapping


class TestIndicDBGoldExecution(unittest.TestCase):
    def test_maps_only_directly_evidenced_trailing_underscore_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "indicDB.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                for schema_name in {
                    *DIRECT_SCHEMA_MAPPINGS.values(),
                    "INDIA_UDISE_Right_To_Education_RTE_and_School_Management_data",
                }:
                    root = f"database/{schema_name}/{schema_name}"
                    archive.writestr(
                        f"{root}/schema_config.yaml",
                        "\n".join(
                            [
                                f"database_name: {schema_name}",
                                "dimension_tables:",
                                "  DIM_A: {}",
                                "fact_tables: {}",
                            ]
                        ),
                    )
                    archive.writestr(
                        f"{root}/DDL.csv",
                        "table_name,description,DDL\nDIM_A,test,CREATE TABLE DIM_A ();\n",
                    )
            mappings = build_schema_mapping(archive_path)

        self.assertEqual(
            mappings["INDIA_IHDS_2005_HOUSEHOLD_SURVEY_"]["archive_schema_name"],
            "INDIA_IHDS_2005_HOUSEHOLD_SURVEY",
        )
        self.assertEqual(
            mappings["INDIA_IHDS_2005_INDIVIDUAL_SURVEY_"]["postgres_schema_name"],
            "india_ihds_2005_individual_survey",
        )
        self.assertNotIn("INDIA_UDISE_SCHOOL_PROFILES", mappings)


if __name__ == "__main__":
    unittest.main()
