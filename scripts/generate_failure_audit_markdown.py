#!/usr/bin/env python3
"""
scripts/generate_failure_audit_markdown.py
Compiles reports/e2e_failure_audit.md from reports/e2e_failure_audit.json.
Provides complete forensic traceability, tables, and ranked recommendations.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = REPO_ROOT / "reports" / "e2e_failure_audit.json"
MD_PATH = REPO_ROOT / "reports" / "e2e_failure_audit.md"


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data["benchmark_summary"]
    cat_counts = data["failure_category_counts"]
    traces = data["traces"]

    md = []

    # Title & Metadata
    md.append("# IndicSQL End-to-End Execution Failure Audit (140-Query Unseen Benchmark)")
    md.append("")
    md.append("**Audit Timestamp:** 2026-11-09  ")
    md.append("**Target Suite:** `data/benchmarks/indicdb_unseen_suite_140.json` (140 unseen queries across 7 languages)  ")
    md.append("**Official Report:** `data/benchmarks/unseen_140_evaluation_report.json`  ")
    md.append("**Execution Engine:** DuckDB Parquet Storage Engine (`ndap_relational.duckdb` & Parquet data stores)  ")
    md.append("**Inference Model:** Local Ollama Qwen-2.5-Coder / Qwen-2.5 (3B)  ")
    md.append("")
    md.append("---")
    md.append("")

    # Executive Summary
    md.append("## 1. Executive Summary & Benchmark Baseline Reproduction")
    md.append("")
    md.append("The 140-query unseen benchmark suite was evaluated end-to-end through the complete IndicSQL multi-agent pipeline (`execute_indicsql_pipeline`).")
    md.append("The evaluation verified four independent dimensions of performance:")
    md.append("")
    md.append(f"- **Total Benchmark Queries:** {summary['total_queries']} (20 queries × 7 languages: English, Hinglish, Hindi, Marathi, Bengali, Tamil, Telugu)")
    md.append(f"- **Entity Grounding Accuracy:** **{summary['grounding_accuracy_pct']}%** (140/140 passed) — Pan-India state and district grounding achieved zero false collisions.")
    md.append(f"- **Schema/Table Routing Accuracy:** **{summary['table_routing_accuracy_pct']}%** (140/140 passed) — All 140 queries correctly linked to their authoritative target NDAP database.")
    md.append(f"- **End-to-End Execution Accuracy (EX):** **{summary['execution_accuracy_pct']}%** ({summary['passed_queries']}/140 passed, **{summary['failed_queries']} failed**).")
    md.append(f"- **Verbalization Accuracy:** **{summary['verbalization_accuracy_pct']}%** (138/140 passed).")
    md.append("")
    md.append("### Key Finding")
    md.append("> **Zero Failures in Grounding or Table Routing**: Every single one of the 40 failures occurred after table routing was 100% correct.")
    md.append("> The failures reside strictly in SQL clause formulation: **Temporal Over-Constraint** (50.0%), **Metric/Aggregation Selection** (32.5%), **Value Casing/Filtering** (10.0%), and **Unprompted GROUP BY Aggregation** (7.5%).")
    md.append("")
    md.append("---")
    md.append("")

    # Failure Category Table
    md.append("## 2. Failure Category Breakdown")
    md.append("")
    md.append("Every failed query was assigned exactly one primary category based on root-cause analysis:")
    md.append("")
    md.append("| Primary Category | Failure Count | Share (%) | Primary Archetypes Involved |")
    md.append("| :--- | :---: | :---: | :--- |")

    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    archetype_by_cat = {
        "Temporal filter handling": "Archetypes 012, 013, 016, 017",
        "Metric/aggregation selection": "Archetypes 005 (MR/TE), 006 (TA), 008, 010 (TE), 018, 019, 020",
        "Filtering logic": "Archetypes 005 (EN/HI-EN/HI), 006 (BN)",
        "GROUP BY / aggregation logic": "Archetypes 005 (BN/TA), 010 (BN)",
        "Entity/value grounding": "None (100% Passed)",
        "Schema/table routing": "None (100% Passed)",
        "SQL syntax/invalid column": "None (0 errors)",
        "JOIN planning or join keys": "None",
        "Result formatting/verbalization": "None",
        "Other": "None",
    }

    # Add missing zero categories
    all_cat_names = [
        "Temporal filter handling",
        "Metric/aggregation selection",
        "Filtering logic",
        "GROUP BY / aggregation logic",
        "Entity/value grounding",
        "Schema/table routing",
        "SQL syntax/invalid column",
        "JOIN planning or join keys",
        "Result formatting/verbalization",
        "Other",
    ]

    for cat_name in all_cat_names:
        cnt = cat_counts.get(cat_name, 0)
        pct = (cnt / summary["failed_queries"]) * 100.0 if summary["failed_queries"] else 0.0
        archs = archetype_by_cat.get(cat_name, "-")
        md.append(f"| **{cat_name}** | {cnt} | {pct:.1f}% | {archs} |")

    md.append(f"| **TOTAL FAILURES** | **{summary['failed_queries']}** | **100.0%** | **40 Unique Queries** |")
    md.append("")
    md.append("---")
    md.append("")

    # Query by query trace
    md.append("## 3. Query-by-Query Execution Trace (All 40 Failures)")
    md.append("")
    md.append("Below is the complete execution trace for all 40 failed queries, documenting the pipeline state at every stage.")
    md.append("")

    for i, t in enumerate(traces, 1):
        md.append(f"### Failure #{i:02d}: `{t['query_id']}` ({t['language_detected'].upper()})")
        md.append("")
        md.append(f"- **Primary Category:** `{t['primary_category']}`")
        md.append(f"- **Original Question:** \"{t['original_question']}\"")
        md.append(f"- **Language / Script:** `{t['language_detected']}` / `{t['detected_script']}`")
        md.append(f"- **Normalized (Phonetic):** \"{t['normalized_question']}\"")
        md.append(f"- **Extracted Entities:** `{json.dumps(t['extracted_entities'], ensure_ascii=False)}`")
        md.append(f"- **Selected Table:** `{t['selected_table']}`")
        md.append(f"- **Target Columns (Schema Linker):** `{t['selected_metric_columns']}`")
        md.append("")
        md.append("```sql")
        md.append(f"-- PREDICTED SQL (IndicSQL Generated)")
        md.append(f"{t['generated_sql']}")
        md.append("")
        md.append(f"-- GOLD SQL (Benchmark Ground Truth)")
        md.append(f"{t['gold_sql_and_result']['gold_sql']}")
        md.append("```")
        md.append("")
        md.append(f"- **Critic AST Validation:** Valid = `{t['critic_validation']['syntax_valid']}` (Feedback: `{t['critic_validation']['feedback']}`)")
        md.append(f"- **Predicted DuckDB Rows:** `{t['duckdb_execution_result']['rows']}`")
        md.append(f"- **Gold DuckDB Rows:** `{t['gold_sql_and_result']['rows']}`")
        md.append(f"- **Root Cause Analysis:** {t['exact_failure_reason']}")
        md.append("")
        md.append("---")
        md.append("")

    # Section 4: Deep Dive Analysis by Category
    md.append("## 4. Root Cause Deep-Dive by Failure Category")
    md.append("")
    md.append("### 4.1 Temporal Filter Handling (20 Failures / 50.0% of Failures)")
    md.append("")
    md.append("#### The Defect:")
    md.append("When a citizen asks a cumulative, lifetime question without mentioning any year (e.g., *'How many primary health centres are operational in Haryana?'* or *'What is the total number of TB patients notified in Karnataka?'*), local 3B LLMs instinctively inject a single-year filter, such as:")
    md.append("- `AND reporting_year = 2022` (in `ndap_rural_health_infrastructure` and `ndap_national_tuberculosis_portal`)")
    md.append("- `AND academic_year = '2023-24'` (in `ndap_school_infrastructure`)")
    md.append("- `AND survey_year IN ('2022-23')` (in `ndap_higher_education_aishe`)")
    md.append("- `AND cycle_year = 2022` (in `ndap_soil_health_records`)")
    md.append("")
    md.append("#### The Mechanism:")
    md.append("In `indicsql/models/ollama_client.py`, `_clean_sql()` attempts to prune unprompted year conditions using a regex search. However:")
    md.append("1. If the LLM generates `WHERE state_name = 'HARYANA' AND reporting_year = 2022;`, the prompt instructions in `system_prompt` did not strictly forbid default year assumption for non-temporal questions.")
    md.append("2. In multi-stage fallback, dynamic fallback or model outputs containing trailing semicolon boundaries bypassed certain lookahead regex patterns (`reporting_year = 2022;` vs `reporting_year = 2022`).")
    md.append("3. For `academic_year` and `survey_year`, specific regex boundary patterns failed on quoted string formats like `'2023-24'`.")
    md.append("")
    md.append("#### Specific Queries Affected (20 total):")
    md.append("- Archetype 012 (Schools Electricity): `unseen-hi-en-012`, `unseen-hi-012`, `unseen-mr-012`, `unseen-ta-012`, `unseen-te-012` (5 queries)")
    md.append("- Archetype 013 (Higher Education Faculty): `unseen-hi-en-013` (1 query)")
    md.append("- Archetype 016 (Rural Health PHCs): `unseen-en-016`, `unseen-hi-en-016`, `unseen-hi-016`, `unseen-mr-016`, `unseen-bn-016`, `unseen-ta-016`, `unseen-te-016` (7 queries)")
    md.append("- Archetype 017 (Tuberculosis Portal Patients): `unseen-en-017`, `unseen-hi-en-017`, `unseen-hi-017`, `unseen-mr-017`, `unseen-bn-017`, `unseen-ta-017`, `unseen-te-017` (7 queries)")
    md.append("")

    md.append("### 4.2 Metric / Aggregation Selection (13 Failures / 32.5% of Failures)")
    md.append("")
    md.append("#### The Defect:")
    md.append("The multi-agent pipeline selected either an incorrect target measure column or an incorrect aggregation function:")
    md.append("1. **Soil Testing vs Cards Issued (4 queries)**: In `ndap_soil_health_records`, questions asked for soil samples tested (`नमूनों की जांच`, `samples test hue`, `நேల నమూనాలను పరీక్షించారు`). The Schema Linker ranked `cards_issued` instead of `samples_tested`, causing the model to aggregate cards.")
    md.append("2. **MAX instead of SUM on Physical Volumes (3 queries)**: In `ndap_pmgsy_rural_roads` (`completed_road_length_km`) and `mgnrega_state_annual_employment` (`total_mandays_generated`), questions asking for *'total km constructed'* or *'total mandays'* generated `MAX()` instead of `SUM()`.")
    md.append("3. **SUM on Percentage Rates (2 queries)**: In `ndap_nfhs5_health_indicators`, questions in Marathi (`unseen-mr-018`) and Telugu (`unseen-te-018`) asked for the average institutional deliveries percentage (`संस्थात्मक प्रसूतीचे सरासरी प्रमाण`, `సంస్థాగత ప్రసవాల సగటు శాతం`). The model used `SUM(institutional_births_pct)` (yielding 541.8%) instead of `AVG()` (yielding 90.3%).")
    md.append("4. **MAX with Arrival Date Subquery on Price (2 queries)**: In Marathi (`unseen-mr-005`) and Telugu (`unseen-te-005`), questions asked for average mandi price, but the model generated `MAX(modal_price_inr)` with a subquery filtering for `MAX(arrival_date)`.")
    md.append("5. **Scalar MAX instead of Ordered District for Superlatives (1 query)**: In Telugu (`unseen-te-010`), the question asked for the district with lowest female literacy rate. The model returned `SELECT MAX(female_literacy_rate)` instead of `SELECT district_name, female_literacy_rate ... ORDER BY female_literacy_rate ASC LIMIT 1`.")
    md.append("6. **Job Placed vs Certified Trainees (1 query)**: In Tamil (`unseen-ta-020`), the question asked for certified candidates (`சான்றிதழ் பெற்றவர்கள்`). The model generated `SUM(placed_candidates)` instead of `SUM(certified_candidates)`.")
    md.append("")

    md.append("### 4.3 Filtering Logic (4 Failures / 10.0% of Failures)")
    md.append("")
    md.append("#### The Defect:")
    md.append("1. **Mandi Commodity Casing Mismatch (3 queries)**: In `ndap_mandi_commodity_prices`, commodity names in DuckDB are stored in Title Case (e.g., `'Wheat'`, `'Tomato'`, `'Rice'`). However, `_COMMODITY_LEXICON` extracts `'WHEAT'`, and `ollama_client.py`'s system prompt explicitly instructs: *'Table values for state_name ... and categories ('WHEAT', 'COTTON', 'UREA', 'DAP') are stored in UPPERCASE.'* Because DuckDB string equality is case-sensitive, `commodity = 'WHEAT'` matches 0 rows and returns `[[None]]`.")
    md.append("2. **Colloquial Scheme Number Extraction (1 query)**: In Bengali `unseen-bn-006`, MGNREGA is colloquially known across West Bengal as *'১০০ দিনের কাজ'* (100 Days Work). The LLM perceived `১০০` (100) as a data constraint and injected `AND total_mandays_generated = 100`, returning NULL.")
    md.append("")

    md.append("### 4.4 GROUP BY / Aggregation Logic (3 Failures / 7.5% of Failures)")
    md.append("")
    md.append("#### The Defect:")
    md.append("The prompt instructs the model: *'Never include GROUP BY unless the citizen question explicitly asks for a breakdown by district, year, or state.'*")
    md.append("However, for Bengali (`unseen-bn-005`, `unseen-bn-010`) and Tamil (`unseen-ta-005`), the model added unprompted `GROUP BY` clauses with multi-column dimensions (`state_name, district_name, commodity` or `census_year`) along with `LIMIT 1`.")
    md.append("Because `_clean_sql()` only strips `GROUP BY` when no non-aggregated columns are in the SELECT clause, the model's projection of `district_name` preserved the invalid `GROUP BY`.")
    md.append("")
    md.append("---")
    md.append("")

    # Section 5: Recommendations
    md.append("## 5. Prioritized Recommendations & Action Plan")
    md.append("")
    md.append("Fixes are ranked strictly by the number of benchmark failures resolved and architectural regression risk:")
    md.append("")
    md.append("| Rank | Recommended Action | Failures Addressed | Potential Gain in EX | Affected Files / Functions | Regression Risk |")
    md.append("| :---: | :--- | :---: | :---: | :--- | :---: |")
    md.append("| **1** | **Strengthen Temporal Filter Pruner & Prompt Rule**<br>Ensure `_clean_sql` unconditionally strips unprompted `reporting_year`, `academic_year`, `survey_year`, and `cycle_year` when no temporal expression exists in the citizen question. | **20** | **+14.29%** (71.43% → 85.71%) | `indicsql/models/ollama_client.py` (`_clean_sql`, `system_prompt`) | **LOW** (Safe against non-temporal queries; explicit year regex tests already pass) |")
    md.append("| **2** | **Align Mandi Commodity Casing to Database Title Case**<br>Update `extract_canonical_entities()` or `ollama_client.py` to map commodity to Title Case `'Wheat'`, `'Tomato'`, etc., for `ndap_mandi_commodity_prices`. | **3** | **+2.14%** (85.71% → 87.85%) | `indicsql/agents/sql_synthesizer.py` (`_COMMODITY_LEXICON`), `indicsql/models/ollama_client.py` | **ZERO** (Restores data parity with DuckDB parquet tables) |")
    md.append("| **3** | **Enrich Schema Linker Lexicon for Soil Testing & Skill Metrics**<br>Add explicit vernacular synonyms for `samples_tested` (soil testing) vs `cards_issued`, and `certified_candidates` vs `placed_candidates`. | **5** | **+3.57%** (87.85% → 91.43%) | `indicsql/schema/multilingual_index.py`, `indicsql/agents/schema_linker.py` | **LOW** (Additive dictionary entries) |")
    md.append("| **4** | **Enforce Rate Aggregation Rule (SUM vs AVG) & Superlative Handling**<br>Add schema linker prompt rule: Any column with `_pct` or `_rate` MUST default to `AVG()`, never `SUM()`. Superlatives ('lowest' / 'తక్కువ') must yield `ORDER BY col ASC LIMIT 1`. | **4** | **+2.86%** (91.43% → 94.29%) | `indicsql/agents/sql_synthesizer.py`, `indicsql/models/ollama_client.py` | **LOW** (Standard SQL semantic guardrails) |")
    md.append("| **5** | **Strip Unsolicited Multi-Column GROUP BY on Scalar Aggregate Queries**<br>Enhance AST Critic / Sanitizer to strip unprompted `GROUP BY` when citizen query lacks breakdown keywords ('district-wise', 'year-wise'). | **3** | **+2.14%** (94.29% → 96.43%) | `indicsql/models/ollama_client.py` (`_clean_sql`), `indicsql/agents/critic.py` | **LOW** (Preserves scalar aggregation semantics) |")
    md.append("| **6** | **Protect Colloquial Scheme Names with Digits from Literal Filtering**<br>Add phrase-level protection for Bengali *'১০০ দিনের কাজ'* (100 Days Work) so digits inside scheme names are not emitted as WHERE constraints. | **1** | **+0.71%** (96.43% → 97.14%) | `indicsql/agents/sql_synthesizer.py`, `indicsql/schema/multilingual_index.py` | **LOW** |")
    md.append("| **TOTAL** | **Target Cumulative Optimization** | **36 / 40** | **+25.71%** (71.43% → **97.14%**) | **All Core Modules** | **Target EX: 97.14%** |")
    md.append("")
    md.append("### Required Regression Tests Before Code Changes")
    md.append("Before implementing these fixes in future iterations:")
    md.append("1. `tests/test_temporal_regression.py`: Verify that explicit year queries (`'in 2022'`, `'2023-24'`, `'2021 से 2023'`) retain their temporal filter, while unrequested queries remain unconstrained.")
    md.append("2. `tests/test_case_sensitivity.py`: Verify that mandi commodity queries across all 7 languages correctly query Title Case `'Wheat'` and return non-empty prices.")
    md.append("3. `tests/test_rate_aggregation.py`: Verify that NFHS-5 percentage rates (`institutional_births_pct`, `stunted_children_pct`) produce `AVG()` and never `SUM()`.")
    md.append("4. Full 87-test unit test suite must remain 100% passing.")

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Generated comprehensive forensic audit markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
