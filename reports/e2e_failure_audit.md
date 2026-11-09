# IndicSQL End-to-End Execution Failure Audit (140-Query Unseen Benchmark)

**Audit Timestamp:** 2026-11-09  
**Target Suite:** `data/benchmarks/indicdb_unseen_suite_140.json` (140 unseen queries across 7 languages)  
**Official Report:** `data/benchmarks/unseen_140_evaluation_report.json`  
**Execution Engine:** DuckDB Parquet Storage Engine (`ndap_relational.duckdb` & Parquet data stores)  
**Inference Model:** Local Ollama Qwen-2.5-Coder / Qwen-2.5 (3B)  

---

## 1. Executive Summary & Benchmark Baseline Reproduction

The 140-query unseen benchmark suite was evaluated end-to-end through the complete IndicSQL multi-agent pipeline (`execute_indicsql_pipeline`).
The evaluation verified four independent dimensions of performance:

- **Total Benchmark Queries:** 140 (20 queries × 7 languages: English, Hinglish, Hindi, Marathi, Bengali, Tamil, Telugu)
- **Entity Grounding Accuracy:** **100.0%** (140/140 passed) — Pan-India state and district grounding achieved zero false collisions.
- **Schema/Table Routing Accuracy:** **100.0%** (140/140 passed) — All 140 queries correctly linked to their authoritative target NDAP database.
- **End-to-End Execution Accuracy (EX):** **71.43%** (100/140 passed, **40 failed**).
- **Verbalization Accuracy:** **98.57%** (138/140 passed).

### Key Finding
> **Zero Failures in Grounding or Table Routing**: Every single one of the 40 failures occurred after table routing was 100% correct.
> The failures reside strictly in SQL clause formulation: **Temporal Over-Constraint** (50.0%), **Metric/Aggregation Selection** (32.5%), **Value Casing/Filtering** (10.0%), and **Unprompted GROUP BY Aggregation** (7.5%).

---

## 2. Failure Category Breakdown

Every failed query was assigned exactly one primary category based on root-cause analysis:

| Primary Category | Failure Count | Share (%) | Primary Archetypes Involved |
| :--- | :---: | :---: | :--- |
| **Temporal filter handling** | 20 | 50.0% | Archetypes 012, 013, 016, 017 |
| **Metric/aggregation selection** | 13 | 32.5% | Archetypes 005 (MR/TE), 006 (TA), 008, 010 (TE), 018, 019, 020 |
| **Filtering logic** | 4 | 10.0% | Archetypes 005 (EN/HI-EN/HI), 006 (BN) |
| **GROUP BY / aggregation logic** | 3 | 7.5% | Archetypes 005 (BN/TA), 010 (BN) |
| **Entity/value grounding** | 0 | 0.0% | None (100% Passed) |
| **Schema/table routing** | 0 | 0.0% | None (100% Passed) |
| **SQL syntax/invalid column** | 0 | 0.0% | None (0 errors) |
| **JOIN planning or join keys** | 0 | 0.0% | None |
| **Result formatting/verbalization** | 0 | 0.0% | None |
| **Other** | 0 | 0.0% | None |
| **TOTAL FAILURES** | **40** | **100.0%** | **40 Unique Queries** |

---

## 3. Query-by-Query Execution Trace (All 40 Failures)

Below is the complete execution trace for all 40 failed queries, documenting the pipeline state at every stage.

### Failure #01: `unseen-en-005` (EN)

- **Primary Category:** `Filtering logic`
- **Original Question:** "What was the average mandi price of wheat in Maharashtra?"
- **Language / Script:** `en` / `Latin`
- **Normalized (Phonetic):** "What was the average mandi price of wheat in Maharashtra?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr', 'production_tonnes']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT AVG(modal_price_inr) AS avg_mandi_price_wheat_maharashtra FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT';

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Value casing mismatch: DuckDB string equality is case-sensitive. The query filtered on uppercase `commodity = 'WHEAT'`, whereas database records store Title Case `'Wheat'`, returning NULL/empty rows.

---

### Failure #02: `unseen-en-016` (EN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "How many primary health centres (PHCs) are operational in Haryana?"
- **Language / Script:** `en` / `Latin`
- **Normalized (Phonetic):** "How many primary health centres (PHCs) are operational in Haryana?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS operational_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #03: `unseen-en-017` (EN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "What is the total number of TB patients notified in Karnataka?"
- **Language / Script:** `en` / `Latin`
- **Normalized (Phonetic):** "What is the total number of TB patients notified in Karnataka?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_tuberculosis_patients FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2023;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[52898]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #04: `unseen-hi-en-005` (EN)

- **Primary Category:** `Filtering logic`
- **Original Question:** "Maharashtra ki mandis me wheat ka average price kya raha?"
- **Language / Script:** `en` / `Latin`
- **Normalized (Phonetic):** "Maharashtra ki mandis me wheat ka average price kya raha?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr', 'production_tonnes']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT AVG(modal_price_inr) AS average_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT';

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Value casing mismatch: DuckDB string equality is case-sensitive. The query filtered on uppercase `commodity = 'WHEAT'`, whereas database records store Title Case `'Wheat'`, returning NULL/empty rows.

---

### Failure #05: `unseen-hi-en-008` (HI-EN)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "Madhya Pradesh me PMGSY ke under total kitne km road construct hui?"
- **Language / Script:** `hi-en` / `Latin`
- **Normalized (Phonetic):** "Madhya Pradesh me PMGSY ke under total kitne km road construct hui?"
- **Extracted Entities:** `{"state_name": "MADHYA PRADESH"}`
- **Selected Table:** `ndap_pmgsy_rural_roads`
- **Target Columns (Schema Linker):** `['completed_road_length_km']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(completed_road_length_km) AS max_constructed_road_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[375.5]]`
- **Gold DuckDB Rows:** `[[2792.2799999999993]]`
- **Root Cause Analysis:** Aggregation function mismatch: Model selected `MAX()` instead of `SUM()` for total volume/mandays aggregation.

---

### Failure #06: `unseen-hi-en-013` (HI-EN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "Tamil Nadu me higher education me total kitne faculty members hain?"
- **Language / Script:** `hi-en` / `Latin`
- **Normalized (Phonetic):** "Tamil Nadu me higher education me total kitne faculty members hain?"
- **Extracted Entities:** `{"state_name": "TAMIL NADU"}`
- **Selected Table:** `ndap_higher_education_aishe`
- **Target Columns (Schema Linker):** `['total_colleges', 'total_faculty_count']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU' AND survey_year IN ('2022-23');

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[72303]]`
- **Gold DuckDB Rows:** `[[148486]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `survey_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #07: `unseen-hi-en-016` (HI-EN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "Haryana me total kitne primary health centres (PHC) chal rahe hain?"
- **Language / Script:** `hi-en` / `Latin`
- **Normalized (Phonetic):** "Haryana me total kitne primary health centres (PHC) chal rahe hain?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #08: `unseen-hi-en-017` (HI-EN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "Karnataka me Nikshay portal par total kitne TB patients notify hue?"
- **Language / Script:** `hi-en` / `Latin`
- **Normalized (Phonetic):** "Karnataka me Nikshay portal par total kitne TB patients notify hue?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #09: `unseen-hi-en-019` (HI-EN)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "Coimbatore district me Soil Health Card yojana ke under kitne soil samples test hue?"
- **Language / Script:** `hi-en` / `Latin`
- **Normalized (Phonetic):** "Coimbatore district me Soil Health Card yojana ke under kitne soil samples test hue?"
- **Extracted Entities:** `{"district_name": "Coimbatore", "state_name": "TAMIL NADU"}`
- **Selected Table:** `ndap_soil_health_records`
- **Target Columns (Schema Linker):** `['soil_health_card_issued', 'samples_tested']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(cards_issued) AS total_samples_tested FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[237761]]`
- **Gold DuckDB Rows:** `[[243640]]`
- **Root Cause Analysis:** Target column confusion: Model aggregated `cards_issued` instead of `samples_tested` in ndap_soil_health_records when citizen asked about soil sample testing.

---

### Failure #10: `unseen-hi-005` (HI)

- **Primary Category:** `Filtering logic`
- **Original Question:** "महाराष्ट्र की मंडियों में गेहूं का औसत मॉडल भाव क्या रहा?"
- **Language / Script:** `hi` / `Devanagari`
- **Normalized (Phonetic):** "महाराष्ट्र की मंडियों में गेहूं का औसत मॉडल भाव क्या रहा?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT AVG(modal_price_inr) AS average_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT';

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Value casing mismatch: DuckDB string equality is case-sensitive. The query filtered on uppercase `commodity = 'WHEAT'`, whereas database records store Title Case `'Wheat'`, returning NULL/empty rows.

---

### Failure #11: `unseen-hi-012` (HI)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "पुणे जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?"
- **Language / Script:** `hi` / `Devanagari`
- **Normalized (Phonetic):** "पुणे जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?"
- **Extracted Entities:** `{"district_name": "Pune", "state_name": "MAHARASHTRA"}`
- **Selected Table:** `ndap_school_infrastructure`
- **Target Columns (Schema Linker):** `['schools_with_electricity']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(schools_with_electricity) AS electric_schools_count FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1476]]`
- **Gold DuckDB Rows:** `[[4063]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `academic_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #12: `unseen-hi-016` (HI)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "हरियाणा में कुल कितने प्राथमिक स्वास्थ्य केंद्र संचालित हैं?"
- **Language / Script:** `hi` / `Devanagari`
- **Normalized (Phonetic):** "हरियाणा में कुल कितने प्राथमिक स्वास्थ्य केंद्र संचालित हैं?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #13: `unseen-hi-017` (HI)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "कर्नाटक में निक्षय पोर्टल पर कुल कितने टीबी के मरीज अधिसूचित किए गए?"
- **Language / Script:** `hi` / `Devanagari`
- **Normalized (Phonetic):** "कर्नाटक में निक्षय पोर्टल पर कुल कितने टीबी के मरीज अधिसूचित किए गए?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #14: `unseen-hi-019` (HI)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "कोयंबटूर जिले में मृदा स्वास्थ्य कार्ड योजना के तहत कितने मिट्टी के नमूनों की जांच की गई?"
- **Language / Script:** `hi` / `Devanagari`
- **Normalized (Phonetic):** "कोयंबटूर जिले में मृदा स्वास्थ्य कार्ड योजना के तहत कितने मिट्टी के नमूनों की जांच की गई?"
- **Extracted Entities:** `{"district_name": "Coimbatore", "state_name": "TAMIL NADU"}`
- **Selected Table:** `ndap_soil_health_records`
- **Target Columns (Schema Linker):** `['samples_tested', 'soil_health_card_issued', 'cards_issued']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(cards_issued) AS total_cards_issued FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' AND cycle_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[118853]]`
- **Gold DuckDB Rows:** `[[243640]]`
- **Root Cause Analysis:** Target column confusion: Model aggregated `cards_issued` instead of `samples_tested` in ndap_soil_health_records when citizen asked about soil sample testing.

---

### Failure #15: `unseen-mr-005` (MR)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "महाराष्ट्रातील बाजार समित्यांमध्ये गव्हाचा सरासरी भाव काय होता?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "महाराष्ट्रातील बाजार समित्यांमध्ये गव्हाचा सरासरी भाव काय होता?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(modal_price_inr) AS highest_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' AND arrival_date IN ( SELECT MAX(arrival_date) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' );

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Aggregation function mismatch: Query asked for average price, but model generated `MAX(modal_price_inr)` with an arrival_date subquery.

---

### Failure #16: `unseen-mr-012` (MR)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "पुणे जिल्ह्यातील वीज सुविधा असलेल्या शाळांची संख्या किती आहे?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "पुणे जिल्ह्यातील वीज सुविधा असलेल्या शाळांची संख्या किती आहे?"
- **Extracted Entities:** `{"district_name": "Pune", "state_name": "MAHARASHTRA"}`
- **Selected Table:** `ndap_school_infrastructure`
- **Target Columns (Schema Linker):** `['schools_with_electricity']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(schools_with_electricity) AS total_schools_with_electricity FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1476]]`
- **Gold DuckDB Rows:** `[[4063]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `academic_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #17: `unseen-mr-016` (MR)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "हरियाणामध्ये एकूण किती प्राथमिक आरोग्य केंद्रे कार्यरत आहेत?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "हरियाणामध्ये एकूण किती प्राथमिक आरोग्य केंद्रे कार्यरत आहेत?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #18: `unseen-mr-017` (MR)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "कर्नाटकात एकूण किती क्षयरोग रुग्णांची नोंद करण्यात आली?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "कर्नाटकात एकूण किती क्षयरोग रुग्णांची नोंद करण्यात आली?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #19: `unseen-mr-018` (MR)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "एनएफएचएस-५ नुसार आंध्र प्रदेशात संस्थात्मक प्रसूतीचे सरासरी प्रमाण किती टक्के आहे?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "एनएफएचएस-५ नुसार आंध्र प्रदेशात संस्थात्मक प्रसूतीचे सरासरी प्रमाण किती टक्के आहे?"
- **Extracted Entities:** `{"state_name": "ANDHRA PRADESH"}`
- **Selected Table:** `ndap_nfhs5_health_indicators`
- **Target Columns (Schema Linker):** `['institutional_births_pct']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(institutional_births_pct) AS total_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[541.8000000000001]]`
- **Gold DuckDB Rows:** `[[90.30000000000001]]`
- **Root Cause Analysis:** Aggregation function mismatch: Model selected `SUM()` instead of `AVG()` when aggregating a percentage rate metric (institutional_births_pct), yielding meaningless cumulative sums > 100%.

---

### Failure #20: `unseen-mr-019` (MR)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "कोईम्बतूर जिल्ह्यात मृदा आरोग्य पत्रिका अंतर्गत मातीचे किती नमुने तपासण्यात आले?"
- **Language / Script:** `mr` / `Devanagari`
- **Normalized (Phonetic):** "कोईम्बतूर जिल्ह्यात मृदा आरोग्य पत्रिका अंतर्गत मातीचे किती नमुने तपासण्यात आले?"
- **Extracted Entities:** `{"district_name": "Coimbatore", "state_name": "TAMIL NADU"}`
- **Selected Table:** `ndap_soil_health_records`
- **Target Columns (Schema Linker):** `['soil_health_card_issued']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' AND cycle_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[118853]]`
- **Gold DuckDB Rows:** `[[243640]]`
- **Root Cause Analysis:** Target column confusion: Model aggregated `cards_issued` instead of `samples_tested` in ndap_soil_health_records when citizen asked about soil sample testing.

---

### Failure #21: `unseen-bn-005` (BN)

- **Primary Category:** `GROUP BY / aggregation logic`
- **Original Question:** "মহারাষ্ট্রের বাজারগুলিতে গমের গড় মূল্য কত ছিল?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "মহারাষ্ট্রের বাজারগুলিতে গমের গড় মূল্য কত ছিল?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT state_name, district_name, commodity, AVG(modal_price_inr) AS average_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' GROUP BY state_name, district_name, commodity ORDER BY average_price ASC LIMIT 1;

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Unsolicited multi-column grouping: Model injected unsolicited `GROUP BY` clause and non-aggregated projected dimensions, returning a multi-row breakdown or localized extreme instead of the requested state-level scalar aggregate.

---

### Failure #22: `unseen-bn-006` (BN)

- **Primary Category:** `Filtering logic`
- **Original Question:** "বিহারে ১০০ দিনের কাজের প্রকল্পে মোট কত কর্মদিবস তৈরি হয়েছে?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "বিহারে ১০০ দিনের কাজের প্রকল্পে মোট কত কর্মদিবস তৈরি হয়েছে?"
- **Extracted Entities:** `{"state_name": "BIHAR"}`
- **Selected Table:** `mgnrega_state_annual_employment`
- **Target Columns (Schema Linker):** `['total_mandays_generated']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR' AND total_mandays_generated = 100;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[1084897541]]`
- **Root Cause Analysis:** Idiomatic number extraction flaw: The Bengali colloquial phrase for MGNREGA ('১০০ দিনের কাজ' / 100 Days Work) was mistakenly parsed as a numerical WHERE filter `total_mandays_generated = 100` instead of recognizing the scheme entity.

---

### Failure #23: `unseen-bn-010` (BN)

- **Primary Category:** `GROUP BY / aggregation logic`
- **Original Question:** "বিহারের কোন জেলায় মহিলা সাক্ষরতার হার সবচেয়ে কম রেকর্ড করা হয়েছে?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "বিহারের কোন জেলায় মহিলা সাক্ষরতার হার সবচেয়ে কম রেকর্ড করা হয়েছে?"
- **Extracted Entities:** `{"state_name": "BIHAR"}`
- **Selected Table:** `ndap_education_stats`
- **Target Columns (Schema Linker):** `['female_literacy_rate']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT state_name, district_name, census_year, MIN(female_literacy_rate) AS lowest_female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' GROUP BY state_name, district_name, census_year ORDER BY lowest_female_literacy_rate ASC LIMIT 1;

-- GOLD SQL (Benchmark Ground Truth)
SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[['BIHAR', 'Purnia', 2024, 62.2]]`
- **Gold DuckDB Rows:** `[['Purnia', 62.2]]`
- **Root Cause Analysis:** Unsolicited multi-column grouping: Model injected unsolicited `GROUP BY` clause and non-aggregated projected dimensions, returning a multi-row breakdown or localized extreme instead of the requested state-level scalar aggregate.

---

### Failure #24: `unseen-bn-012` (BN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "পুনে জেলায় বিদ্যুৎ সংযোগ থাকা স্কুলের সংখ্যা কত?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "পুনে জেলায় বিদ্যুৎ সংযোগ থাকা স্কুলের সংখ্যা কত?"
- **Extracted Entities:** `{"district_name": "Pune", "state_name": "MAHARASHTRA"}`
- **Selected Table:** `ndap_school_infrastructure`
- **Target Columns (Schema Linker):** `['schools_with_electricity']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(schools_with_electricity) AS electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1476]]`
- **Gold DuckDB Rows:** `[[4063]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `academic_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #25: `unseen-bn-016` (BN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "হরিয়ানায় মোট কতগুলি প্রাথমিক স্বাস্থ্য কেন্দ্র চালু রয়েছে?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "হরিয়ানায় মোট কতগুলি প্রাথমিক স্বাস্থ্য কেন্দ্র চালু রয়েছে?"
- **Extracted Entities:** `{"state_name": "HARYANA", "commodity": "RICE"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc', 'production_tonnes']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #26: `unseen-bn-017` (BN)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "কর্ণাটকে মোট কতজন যক্ষ্মা রোগী সরকারিভাবে নথিভুক্ত হয়েছেন?"
- **Language / Script:** `bn` / `Bengali`
- **Normalized (Phonetic):** "কর্ণাটকে মোট কতজন যক্ষ্মা রোগী সরকারিভাবে নথিভুক্ত হয়েছেন?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #27: `unseen-ta-005` (TA)

- **Primary Category:** `GROUP BY / aggregation logic`
- **Original Question:** "மகாராஷ்டிரா சந்தைகளில் கோதுமையின் சராசரி மாதிரி விலை என்ன?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "மகாராஷ்டிரா சந்தைகளில் கோதுமையின் சராசரி மாதிரி விலை என்ன?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT state_name, district_name, commodity, AVG(modal_price_inr) AS avg_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' GROUP BY state_name, district_name, commodity ORDER BY avg_price_inr DESC LIMIT 1;

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Unsolicited multi-column grouping: Model injected unsolicited `GROUP BY` clause and non-aggregated projected dimensions, returning a multi-row breakdown or localized extreme instead of the requested state-level scalar aggregate.

---

### Failure #28: `unseen-ta-006` (TA)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "பீகாரில் மகாத்மா காந்தி ஊரக வேலை திட்டத்தில் உருவாக்கப்பட்ட மொத்த மனித வேலை நாட்கள் எத்தனை?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "பீகாரில் மகாத்மா காந்தி ஊரக வேலை திட்டத்தில் உருவாக்கப்பட்ட மொத்த மனித வேலை நாட்கள் எத்தனை?"
- **Extracted Entities:** `{"state_name": "BIHAR"}`
- **Selected Table:** `mgnrega_state_annual_employment`
- **Target Columns (Schema Linker):** `['total_mandays_generated']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(total_mandays_generated) AS max_mandays_generated FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[390269311]]`
- **Gold DuckDB Rows:** `[[1084897541]]`
- **Root Cause Analysis:** Aggregation function mismatch: Model selected `MAX()` instead of `SUM()` for total volume/mandays aggregation.

---

### Failure #29: `unseen-ta-008` (TA)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "மத்தியப் பிரதேசத்தில் கிராமப்புற சாலை திட்டத்தில் முடிக்கப்பட்ட மொத்த சாலை நீளம் எத்தனை கி.மீ?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "மத்தியப் பிரதேசத்தில் கிராமப்புற சாலை திட்டத்தில் முடிக்கப்பட்ட மொத்த சாலை நீளம் எத்தனை கி.மீ?"
- **Extracted Entities:** `{"state_name": "MADHYA PRADESH"}`
- **Selected Table:** `ndap_pmgsy_rural_roads`
- **Target Columns (Schema Linker):** `['completed_road_length_km']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(completed_road_length_km) AS max_completed_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[375.5]]`
- **Gold DuckDB Rows:** `[[2792.2799999999993]]`
- **Root Cause Analysis:** Aggregation function mismatch: Model selected `MAX()` instead of `SUM()` for total volume/mandays aggregation.

---

### Failure #30: `unseen-ta-012` (TA)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "புனே மாவட்டத்தில் மின்சார வசதி கொண்ட பள்ளிகள் எத்தனை?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "புனே மாவட்டத்தில் மின்சார வசதி கொண்ட பள்ளிகள் எத்தனை?"
- **Extracted Entities:** `{"district_name": "Pune", "state_name": "MAHARASHTRA"}`
- **Selected Table:** `ndap_school_infrastructure`
- **Target Columns (Schema Linker):** `['schools_with_electricity']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(schools_with_electricity) AS electricity_compliance FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1476]]`
- **Gold DuckDB Rows:** `[[4063]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `academic_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #31: `unseen-ta-016` (TA)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "ஹரியானாவில் செயல்படும் மொத்த ஆரம்ப சுகாதார நிலையங்கள் எத்தனை?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "ஹரியானாவில் செயல்படும் மொத்த ஆரம்ப சுகாதார நிலையங்கள் எத்தனை?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #32: `unseen-ta-017` (TA)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "கர்நாடகாவில் பதிவு செய்யப்பட்ட மொத்த காசநோய் நோயாளிகள் எத்தனை பேர்?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "கர்நாடகாவில் பதிவு செய்யப்பட்ட மொத்த காசநோய் நோயாளிகள் எத்தனை பேர்?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_patients FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #33: `unseen-ta-020` (TA)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "ஜார்கண்டில் தொழிற்கல்வி திறன் பயிற்சியில் தேர்ச்சி பெற்று சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?"
- **Language / Script:** `ta` / `Tamil`
- **Normalized (Phonetic):** "ஜார்கண்டில் தொழிற்கல்வி திறன் பயிற்சியில் தேர்ச்சி பெற்று சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?"
- **Extracted Entities:** `{"state_name": "JHARKHAND"}`
- **Selected Table:** `ndap_vocational_skill_training`
- **Target Columns (Schema Linker):** `['certified_candidates']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(placed_candidates) AS total_recruits FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND' AND sector_skill_council = 'Agriculture';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[42467]]`
- **Gold DuckDB Rows:** `[[170007]]`
- **Root Cause Analysis:** Target column confusion: Model selected `placed_candidates` instead of `certified_candidates` when citizen asked for certified skill trainees.

---

### Failure #34: `unseen-te-005` (TE)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "మహారాష్ట్ర మార్కెట్లలో గోధుమల సగటు ధర ఎంత?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "మహారాష్ట్ర మార్కెట్లలో గోధుమల సగటు ధర ఎంత?"
- **Extracted Entities:** `{"state_name": "MAHARASHTRA", "commodity": "WHEAT"}`
- **Selected Table:** `ndap_mandi_commodity_prices`
- **Target Columns (Schema Linker):** `['modal_price_inr']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(modal_price_inr) AS highest_price_in_maharashtra_wheat FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' AND arrival_date IN ( SELECT MAX(arrival_date) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'WHEAT' );

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[None]]`
- **Gold DuckDB Rows:** `[[2963.93]]`
- **Root Cause Analysis:** Aggregation function mismatch: Query asked for average price, but model generated `MAX(modal_price_inr)` with an arrival_date subquery.

---

### Failure #35: `unseen-te-010` (TE)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "బీహార్‌లో మహిళా అక్షరాస్యత రేటు అత్యల్పంగా నమోదైన జిల్లా ఏది?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "బీహార్‌లో మహిళా అక్షరాస్యత రేటు అత్యల్పంగా నమోదైన జిల్లా ఏది?"
- **Extracted Entities:** `{"state_name": "BIHAR"}`
- **Selected Table:** `ndap_education_stats`
- **Target Columns (Schema Linker):** `['female_literacy_rate']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT MAX(female_literacy_rate) AS highest_female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR';

-- GOLD SQL (Benchmark Ground Truth)
SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[95.9]]`
- **Gold DuckDB Rows:** `[['Purnia', 62.2]]`
- **Root Cause Analysis:** Superlative direction mismatch: Query asked for lowest female literacy district, but model returned scalar `MAX()` instead of `ORDER BY female_literacy_rate ASC LIMIT 1`.

---

### Failure #36: `unseen-te-012` (TE)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "పుణే జిల్లాలో విద్యుత్ సదుపాయం ఉన్న పాఠశాలల సంఖ్య ఎంత?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "పుణే జిల్లాలో విద్యుత్ సదుపాయం ఉన్న పాఠశాలల సంఖ్య ఎంత?"
- **Extracted Entities:** `{"district_name": "Pune", "state_name": "MAHARASHTRA"}`
- **Selected Table:** `ndap_school_infrastructure`
- **Target Columns (Schema Linker):** `['schools_with_electricity']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(schools_with_electricity) AS total_schools_with_electricity FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1476]]`
- **Gold DuckDB Rows:** `[[4063]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `academic_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #37: `unseen-te-016` (TE)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "హర్యానాలో పనిచేస్తున్న మొత్తం ప్రాథమిక ఆరోగ్య కేంద్రాల సంఖ్య ఎంత?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "హర్యానాలో పనిచేస్తున్న మొత్తం ప్రాథమిక ఆరోగ్య కేంద్రాల సంఖ్య ఎంత?"
- **Extracted Entities:** `{"state_name": "HARYANA"}`
- **Selected Table:** `ndap_rural_health_infrastructure`
- **Target Columns (Schema Linker):** `['primary_health_centres_phc']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[1462]]`
- **Gold DuckDB Rows:** `[[3298]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #38: `unseen-te-017` (TE)

- **Primary Category:** `Temporal filter handling`
- **Original Question:** "కర్ణాటకలో నోటిఫై చేయబడిన మొత్తం టీబీ రోగుల సంఖ్య ఎంత?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "కర్ణాటకలో నోటిఫై చేయబడిన మొత్తం టీబీ రోగుల సంఖ్య ఎంత?"
- **Extracted Entities:** `{"state_name": "KARNATAKA"}`
- **Selected Table:** `ndap_national_tuberculosis_portal`
- **Target Columns (Schema Linker):** `['total_notified_patients']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[70218]]`
- **Gold DuckDB Rows:** `[[123116]]`
- **Root Cause Analysis:** Unprompted temporal constraint injection: The query requested cumulative or lifetime totals without specifying any year or time boundary. The pipeline incorrectly injected `reporting_year` condition, drastically truncating the dataset to a single reporting period and returning partial counts.

---

### Failure #39: `unseen-te-018` (TE)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "ఎన్ఎఫ్ హెచ్ ఎస్-5 ప్రకారం ఆంధ్రప్రదేశ్‌లో సంస్థాగత ప్రసవాల సగటు శాతం ఎంత?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "ఎన్ఎఫ్ హెచ్ ఎస్-5 ప్రకారం ఆంధ్రప్రదేశ్‌లో సంస్థాగత ప్రసవాల సగటు శాతం ఎంత?"
- **Extracted Entities:** `{"state_name": "ANDHRA PRADESH"}`
- **Selected Table:** `ndap_nfhs5_health_indicators`
- **Target Columns (Schema Linker):** `['institutional_births_pct']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(institutional_births_pct) AS total_institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';

-- GOLD SQL (Benchmark Ground Truth)
SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[541.8000000000001]]`
- **Gold DuckDB Rows:** `[[90.30000000000001]]`
- **Root Cause Analysis:** Aggregation function mismatch: Model selected `SUM()` instead of `AVG()` when aggregating a percentage rate metric (institutional_births_pct), yielding meaningless cumulative sums > 100%.

---

### Failure #40: `unseen-te-019` (TE)

- **Primary Category:** `Metric/aggregation selection`
- **Original Question:** "కోయంబత్తూర్ జిల్లాలో సాయిల్ హెల్త్ కార్డ్ పథకం కింద ఎన్ని నేల నమూనాలను పరీక్షించారు?"
- **Language / Script:** `te` / `Telugu`
- **Normalized (Phonetic):** "కోయంబత్తూర్ జిల్లాలో సాయిల్ హెల్త్ కార్డ్ పథకం కింద ఎన్ని నేల నమూనాలను పరీక్షించారు?"
- **Extracted Entities:** `{"district_name": "Coimbatore", "state_name": "TAMIL NADU"}`
- **Selected Table:** `ndap_soil_health_records`
- **Target Columns (Schema Linker):** `['soil_health_card_issued', 'samples_tested']`

```sql
-- PREDICTED SQL (IndicSQL Generated)
SELECT SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';

-- GOLD SQL (Benchmark Ground Truth)
SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';
```

- **Critic AST Validation:** Valid = `True` (Feedback: `None`)
- **Predicted DuckDB Rows:** `[[237761]]`
- **Gold DuckDB Rows:** `[[243640]]`
- **Root Cause Analysis:** Target column confusion: Model aggregated `cards_issued` instead of `samples_tested` in ndap_soil_health_records when citizen asked about soil sample testing.

---

## 4. Root Cause Deep-Dive by Failure Category

### 4.1 Temporal Filter Handling (20 Failures / 50.0% of Failures)

#### The Defect:
When a citizen asks a cumulative, lifetime question without mentioning any year (e.g., *'How many primary health centres are operational in Haryana?'* or *'What is the total number of TB patients notified in Karnataka?'*), local 3B LLMs instinctively inject a single-year filter, such as:
- `AND reporting_year = 2022` (in `ndap_rural_health_infrastructure` and `ndap_national_tuberculosis_portal`)
- `AND academic_year = '2023-24'` (in `ndap_school_infrastructure`)
- `AND survey_year IN ('2022-23')` (in `ndap_higher_education_aishe`)
- `AND cycle_year = 2022` (in `ndap_soil_health_records`)

#### The Mechanism:
In `indicsql/models/ollama_client.py`, `_clean_sql()` attempts to prune unprompted year conditions using a regex search. However:
1. If the LLM generates `WHERE state_name = 'HARYANA' AND reporting_year = 2022;`, the prompt instructions in `system_prompt` did not strictly forbid default year assumption for non-temporal questions.
2. In multi-stage fallback, dynamic fallback or model outputs containing trailing semicolon boundaries bypassed certain lookahead regex patterns (`reporting_year = 2022;` vs `reporting_year = 2022`).
3. For `academic_year` and `survey_year`, specific regex boundary patterns failed on quoted string formats like `'2023-24'`.

#### Specific Queries Affected (20 total):
- Archetype 012 (Schools Electricity): `unseen-hi-en-012`, `unseen-hi-012`, `unseen-mr-012`, `unseen-ta-012`, `unseen-te-012` (5 queries)
- Archetype 013 (Higher Education Faculty): `unseen-hi-en-013` (1 query)
- Archetype 016 (Rural Health PHCs): `unseen-en-016`, `unseen-hi-en-016`, `unseen-hi-016`, `unseen-mr-016`, `unseen-bn-016`, `unseen-ta-016`, `unseen-te-016` (7 queries)
- Archetype 017 (Tuberculosis Portal Patients): `unseen-en-017`, `unseen-hi-en-017`, `unseen-hi-017`, `unseen-mr-017`, `unseen-bn-017`, `unseen-ta-017`, `unseen-te-017` (7 queries)

### 4.2 Metric / Aggregation Selection (13 Failures / 32.5% of Failures)

#### The Defect:
The multi-agent pipeline selected either an incorrect target measure column or an incorrect aggregation function:
1. **Soil Testing vs Cards Issued (4 queries)**: In `ndap_soil_health_records`, questions asked for soil samples tested (`नमूनों की जांच`, `samples test hue`, `நேల నమూనాలను పరీక్షించారు`). The Schema Linker ranked `cards_issued` instead of `samples_tested`, causing the model to aggregate cards.
2. **MAX instead of SUM on Physical Volumes (3 queries)**: In `ndap_pmgsy_rural_roads` (`completed_road_length_km`) and `mgnrega_state_annual_employment` (`total_mandays_generated`), questions asking for *'total km constructed'* or *'total mandays'* generated `MAX()` instead of `SUM()`.
3. **SUM on Percentage Rates (2 queries)**: In `ndap_nfhs5_health_indicators`, questions in Marathi (`unseen-mr-018`) and Telugu (`unseen-te-018`) asked for the average institutional deliveries percentage (`संस्थात्मक प्रसूतीचे सरासरी प्रमाण`, `సంస్థాగత ప్రసవాల సగటు శాతం`). The model used `SUM(institutional_births_pct)` (yielding 541.8%) instead of `AVG()` (yielding 90.3%).
4. **MAX with Arrival Date Subquery on Price (2 queries)**: In Marathi (`unseen-mr-005`) and Telugu (`unseen-te-005`), questions asked for average mandi price, but the model generated `MAX(modal_price_inr)` with a subquery filtering for `MAX(arrival_date)`.
5. **Scalar MAX instead of Ordered District for Superlatives (1 query)**: In Telugu (`unseen-te-010`), the question asked for the district with lowest female literacy rate. The model returned `SELECT MAX(female_literacy_rate)` instead of `SELECT district_name, female_literacy_rate ... ORDER BY female_literacy_rate ASC LIMIT 1`.
6. **Job Placed vs Certified Trainees (1 query)**: In Tamil (`unseen-ta-020`), the question asked for certified candidates (`சான்றிதழ் பெற்றவர்கள்`). The model generated `SUM(placed_candidates)` instead of `SUM(certified_candidates)`.

### 4.3 Filtering Logic (4 Failures / 10.0% of Failures)

#### The Defect:
1. **Mandi Commodity Casing Mismatch (3 queries)**: In `ndap_mandi_commodity_prices`, commodity names in DuckDB are stored in Title Case (e.g., `'Wheat'`, `'Tomato'`, `'Rice'`). However, `_COMMODITY_LEXICON` extracts `'WHEAT'`, and `ollama_client.py`'s system prompt explicitly instructs: *'Table values for state_name ... and categories ('WHEAT', 'COTTON', 'UREA', 'DAP') are stored in UPPERCASE.'* Because DuckDB string equality is case-sensitive, `commodity = 'WHEAT'` matches 0 rows and returns `[[None]]`.
2. **Colloquial Scheme Number Extraction (1 query)**: In Bengali `unseen-bn-006`, MGNREGA is colloquially known across West Bengal as *'১০০ দিনের কাজ'* (100 Days Work). The LLM perceived `১০০` (100) as a data constraint and injected `AND total_mandays_generated = 100`, returning NULL.

### 4.4 GROUP BY / Aggregation Logic (3 Failures / 7.5% of Failures)

#### The Defect:
The prompt instructs the model: *'Never include GROUP BY unless the citizen question explicitly asks for a breakdown by district, year, or state.'*
However, for Bengali (`unseen-bn-005`, `unseen-bn-010`) and Tamil (`unseen-ta-005`), the model added unprompted `GROUP BY` clauses with multi-column dimensions (`state_name, district_name, commodity` or `census_year`) along with `LIMIT 1`.
Because `_clean_sql()` only strips `GROUP BY` when no non-aggregated columns are in the SELECT clause, the model's projection of `district_name` preserved the invalid `GROUP BY`.

---

## 5. Prioritized Recommendations & Action Plan

Fixes are ranked strictly by the number of benchmark failures resolved and architectural regression risk:

| Rank | Recommended Action | Failures Addressed | Potential Gain in EX | Affected Files / Functions | Regression Risk |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **1** | **Strengthen Temporal Filter Pruner & Prompt Rule**<br>Ensure `_clean_sql` unconditionally strips unprompted `reporting_year`, `academic_year`, `survey_year`, and `cycle_year` when no temporal expression exists in the citizen question. | **20** | **+14.29%** (71.43% → 85.71%) | `indicsql/models/ollama_client.py` (`_clean_sql`, `system_prompt`) | **LOW** (Safe against non-temporal queries; explicit year regex tests already pass) |
| **2** | **Align Mandi Commodity Casing to Database Title Case**<br>Update `extract_canonical_entities()` or `ollama_client.py` to map commodity to Title Case `'Wheat'`, `'Tomato'`, etc., for `ndap_mandi_commodity_prices`. | **3** | **+2.14%** (85.71% → 87.85%) | `indicsql/agents/sql_synthesizer.py` (`_COMMODITY_LEXICON`), `indicsql/models/ollama_client.py` | **ZERO** (Restores data parity with DuckDB parquet tables) |
| **3** | **Enrich Schema Linker Lexicon for Soil Testing & Skill Metrics**<br>Add explicit vernacular synonyms for `samples_tested` (soil testing) vs `cards_issued`, and `certified_candidates` vs `placed_candidates`. | **5** | **+3.57%** (87.85% → 91.43%) | `indicsql/schema/multilingual_index.py`, `indicsql/agents/schema_linker.py` | **LOW** (Additive dictionary entries) |
| **4** | **Enforce Rate Aggregation Rule (SUM vs AVG) & Superlative Handling**<br>Add schema linker prompt rule: Any column with `_pct` or `_rate` MUST default to `AVG()`, never `SUM()`. Superlatives ('lowest' / 'తక్కువ') must yield `ORDER BY col ASC LIMIT 1`. | **4** | **+2.86%** (91.43% → 94.29%) | `indicsql/agents/sql_synthesizer.py`, `indicsql/models/ollama_client.py` | **LOW** (Standard SQL semantic guardrails) |
| **5** | **Strip Unsolicited Multi-Column GROUP BY on Scalar Aggregate Queries**<br>Enhance AST Critic / Sanitizer to strip unprompted `GROUP BY` when citizen query lacks breakdown keywords ('district-wise', 'year-wise'). | **3** | **+2.14%** (94.29% → 96.43%) | `indicsql/models/ollama_client.py` (`_clean_sql`), `indicsql/agents/critic.py` | **LOW** (Preserves scalar aggregation semantics) |
| **6** | **Protect Colloquial Scheme Names with Digits from Literal Filtering**<br>Add phrase-level protection for Bengali *'১০০ দিনের কাজ'* (100 Days Work) so digits inside scheme names are not emitted as WHERE constraints. | **1** | **+0.71%** (96.43% → 97.14%) | `indicsql/agents/sql_synthesizer.py`, `indicsql/schema/multilingual_index.py` | **LOW** |
| **TOTAL** | **Target Cumulative Optimization** | **36 / 40** | **+25.71%** (71.43% → **97.14%**) | **All Core Modules** | **Target EX: 97.14%** |

### Required Regression Tests Before Code Changes
Before implementing these fixes in future iterations:
1. `tests/test_temporal_regression.py`: Verify that explicit year queries (`'in 2022'`, `'2023-24'`, `'2021 से 2023'`) retain their temporal filter, while unrequested queries remain unconstrained.
2. `tests/test_case_sensitivity.py`: Verify that mandi commodity queries across all 7 languages correctly query Title Case `'Wheat'` and return non-empty prices.
3. `tests/test_rate_aggregation.py`: Verify that NFHS-5 percentage rates (`institutional_births_pct`, `stunted_children_pct`) produce `AVG()` and never `SUM()`.
4. Full 87-test unit test suite must remain 100% passing.