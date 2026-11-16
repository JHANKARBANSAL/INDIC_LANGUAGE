import unittest

import pandas as pd

from scripts.reconstruct_indicdb import (
    _align_frame_to_ddl,
    _normalize_integer_value,
    build_table_frames,
)


class TestIndicDbReconstruction(unittest.TestCase):
    def test_integer_fields_accept_integer_valued_decimals_only(self):
        self.assertEqual(
            _normalize_integer_value("-1.0", "DIM_HOUSEHOLD", "FARM_DECISION_MAKER_ID"),
            "-1",
        )
        self.assertEqual(
            _normalize_integer_value("2.00", "DIM_HOUSEHOLD", "FARM_DECISION_MAKER_ID"),
            "2",
        )
        with self.assertRaisesRegex(ValueError, "non-integer source value"):
            _normalize_integer_value("1.5", "DIM_HOUSEHOLD", "FARM_DECISION_MAKER_ID")

    def test_config_ddl_mismatch_drops_only_unmapped_optional_columns(self):
        frame = pd.DataFrame({"ID": ["1"], "NAME": ["District"], "EXTRA": ["x"]})

        aligned, mismatch = _align_frame_to_ddl(
            "DIM_DISTRICT",
            frame,
            {"key_column": "ID", "foreign_keys": []},
            {"id", "name", "ddl_only"},
        )

        self.assertEqual(list(aligned.columns), ["ID", "NAME"])
        self.assertEqual(mismatch["config_columns_absent_from_ddl"], ["extra"])
        self.assertEqual(mismatch["ddl_columns_without_config_mapping"], ["ddl_only"])

    def test_config_ddl_mismatch_rejects_missing_key_columns(self):
        frame = pd.DataFrame({"NAME": ["District"]})

        with self.assertRaisesRegex(ValueError, "required key columns absent"):
            _align_frame_to_ddl(
                "DIM_DISTRICT",
                frame,
                {"key_column": "ID", "foreign_keys": []},
                {"name"},
            )

    def test_foreign_keys_follow_source_hierarchy(self):
        source = pd.DataFrame(
            [
                ["India", "Andhra Pradesh", "District A", "1.5"],
                ["India", "Andhra Pradesh", "District B", "2.5"],
                ["India", "Karnataka", "District C", "3.5"],
            ]
        )
        config = {
            "dimension_tables": {
                "DIM_COUNTRY": {
                    "key_column": "COUNTRY_ID",
                    "dedup_columns": [0],
                    "columns": [{"source_index": 0, "target_name": "COUNTRY_NAME"}],
                },
                "DIM_STATE": {
                    "key_column": "STATE_ID",
                    "dedup_columns": [1],
                    "columns": [{"source_index": 1, "target_name": "STATE_NAME"}],
                    "foreign_keys": [
                        {"column": "COUNTRY_ID", "references": "DIM_COUNTRY"}
                    ],
                },
                "DIM_DISTRICT": {
                    "key_column": "DISTRICT_ID",
                    "dedup_columns": [2],
                    "columns": [{"source_index": 2, "target_name": "DISTRICT_NAME"}],
                    "foreign_keys": [
                        {"column": "STATE_ID", "references": "DIM_STATE"}
                    ],
                },
            },
            "fact_tables": {
                "FACT_METRIC": {
                    "key_column": "FACT_ID",
                    "foreign_keys": [
                        {"column": "DISTRICT_ID", "references": "DIM_DISTRICT"}
                    ],
                    "columns": [{"source_index": 3, "target_name": "VALUE"}],
                }
            },
        }

        frames, ambiguous, unresolved, fact_links, _ = build_table_frames(source, config)

        self.assertEqual(frames["DIM_COUNTRY"]["COUNTRY_ID"].tolist(), ["1"])
        self.assertEqual(frames["DIM_STATE"]["COUNTRY_ID"].tolist(), ["1", "1"])
        self.assertEqual(frames["DIM_DISTRICT"]["STATE_ID"].tolist(), ["1", "1", "2"])
        self.assertEqual(frames["FACT_METRIC"]["DISTRICT_ID"].tolist(), ["1", "2", "3"])
        self.assertEqual(ambiguous, [])
        self.assertEqual(unresolved, [])
        self.assertEqual(fact_links, [])

    def test_parent_identity_is_added_to_prevent_ambiguous_dimension_links(self):
        source = pd.DataFrame(
            [
                ["State A", "Shared District"],
                ["State B", "Shared District"],
            ]
        )
        config = {
            "dimension_tables": {
                "DIM_STATE": {
                    "key_column": "STATE_ID",
                    "dedup_columns": [0],
                    "columns": [{"source_index": 0, "target_name": "STATE_NAME"}],
                },
                "DIM_DISTRICT": {
                    "key_column": "DISTRICT_ID",
                    "dedup_columns": [1],
                    "columns": [{"source_index": 1, "target_name": "DISTRICT_NAME"}],
                    "foreign_keys": [
                        {"column": "STATE_ID", "references": "DIM_STATE"}
                    ],
                },
            },
            "fact_tables": {},
        }

        frames, ambiguous, _, _, _ = build_table_frames(source, config)

        self.assertEqual(frames["DIM_DISTRICT"]["STATE_ID"].tolist(), ["1", "2"])
        self.assertEqual(len(ambiguous), 0)

    def test_self_reference_without_source_mapping_is_reported(self):
        source = pd.DataFrame([["Village A"], ["Village B"]])
        config = {
            "dimension_tables": {
                "DIM_GEO": {
                    "key_column": "GEO_ID",
                    "dedup_columns": [0],
                    "columns": [{"source_index": 0, "target_name": "NAME"}],
                    "foreign_keys": [{"column": "PARENT_ID", "references": "DIM_GEO"}],
                }
            },
            "fact_tables": {},
        }

        frames, _, unresolved, _, _ = build_table_frames(source, config)

        self.assertEqual(frames["DIM_GEO"]["PARENT_ID"].tolist(), [None, None])
        self.assertEqual(unresolved[0]["column"], "PARENT_ID")

    def test_year_transform_requires_a_four_digit_year(self):
        source = pd.DataFrame([["No year here"]])
        config = {
            "dimension_tables": {
                "DIM_TIME": {
                    "key_column": "YEAR_ID",
                    "key_source_index": 0,
                    "key_transform": "extract_year",
                    "dedup_columns": [0],
                    "columns": [],
                }
            },
            "fact_tables": {},
        }

        with self.assertRaisesRegex(ValueError, "Cannot extract"):
            build_table_frames(source, config)

    def test_fact_foreign_keys_follow_matching_source_rows(self):
        source = pd.DataFrame([["a"], ["b"], ["c"]])
        config = {
            "dimension_tables": {},
            "fact_tables": {
                "FACT_PARENT": {
                    "key_column": "PARENT_ID",
                    "columns": [{"source_index": 0, "target_name": "VALUE"}],
                },
                "FACT_CHILD": {
                    "key_column": "CHILD_ID",
                    "foreign_keys": [
                        {"column": "PARENT_ID", "references": "FACT_PARENT"}
                    ],
                    "columns": [{"source_index": 0, "target_name": "VALUE"}],
                },
            },
        }

        frames, _, _, fact_links, _ = build_table_frames(source, config)

        self.assertEqual(frames["FACT_CHILD"]["PARENT_ID"].tolist(), ["1", "2", "3"])
        self.assertEqual(fact_links[0]["mapping"], "source-row position")

    def test_dimension_without_dedup_columns_uses_source_row_identity(self):
        source = pd.DataFrame([["first"], ["second"]])
        config = {
            "dimension_tables": {
                "DIM_PERSON": {
                    "key_column": "PERSON_ID",
                    "foreign_keys": [
                        {"column": "HOUSEHOLD_ID", "references": "DIM_HOUSEHOLD"}
                    ],
                    "columns": [],
                },
                "DIM_HOUSEHOLD": {
                    "key_column": "HOUSEHOLD_ID",
                    "dedup_columns": [0],
                    "columns": [{"source_index": 0, "target_name": "NAME"}],
                },
            },
            "fact_tables": {},
        }

        frames, _, _, _, effective_keys = build_table_frames(source, config)

        self.assertEqual(frames["DIM_PERSON"]["PERSON_ID"].tolist(), ["1", "2"])
        self.assertEqual(frames["DIM_PERSON"]["HOUSEHOLD_ID"].tolist(), ["1", "2"])
        self.assertEqual(effective_keys["DIM_PERSON"], [-1, 0])


if __name__ == "__main__":
    unittest.main()
