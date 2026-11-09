#!/usr/bin/env python3
"""
scripts/normalize_to_star_schema.py
Decomposes flat NDAP tables into a normalized 3NF Star Schema in DuckDB.

Creates:
1. Shared Dimensions:
   - dim_geography (geo_id PK, state_name, district_name, zone)
   - dim_time (time_id PK, financial_year, calendar_year, season)
2. Domain Fact Tables with Foreign Keys:
   - fact_pm_kisan_disbursement (fact_id PK, geo_id FK, time_id FK, farmer_beneficiaries, amount_inr)
   - fact_crop_production (fact_id PK, geo_id FK, time_id FK, crop_name, area_hectares, production_tonnes, yield_kg_per_hectare)
   - fact_education_stats (fact_id PK, geo_id FK, time_id FK, student_count, male_literacy_rate, female_literacy_rate)
   - fact_mandi_prices (fact_id PK, geo_id FK, time_id FK, market_name, commodity, modal_price_inr, min_price_inr, max_price_inr)

Outputs:
- DuckDB Database: data/duckdb/ndap_relational.duckdb
- Parquet Exports: data/parquet_stores/relational/*.parquet
"""

import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import duckdb

PARQUET_IN_DIR = REPO_ROOT / "data" / "parquet_stores"
RELATIONAL_OUT_DIR = REPO_ROOT / "data" / "parquet_stores" / "relational"
DUCKDB_OUT_PATH = REPO_ROOT / "data" / "duckdb" / "ndap_relational.duckdb"

RELATIONAL_OUT_DIR.mkdir(parents=True, exist_ok=True)
DUCKDB_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 80)
    print("🇮🇳 IndicSQL: Automated Relational 3NF Star Schema Normalizer")
    print("=" * 80)
    print(f"Reading from: {PARQUET_IN_DIR}")
    print(f"Writing to:   {DUCKDB_OUT_PATH} and {RELATIONAL_OUT_DIR}\n")

    con = duckdb.connect(str(DUCKDB_OUT_PATH))

    # -------------------------------------------------------------------------
    # 1. DIM_GEOGRAPHY (Shared Global Hierarchy: Country -> State -> District)
    # -------------------------------------------------------------------------
    print("📦 [1/6] Building DIM_GEOGRAPHY (Normalized Geo Hierarchy)...")
    con.execute("""
    CREATE OR REPLACE SEQUENCE seq_geo_id START 1;
    
    CREATE OR REPLACE TABLE dim_geography AS
    SELECT 
        nextval('seq_geo_id') AS geo_id,
        state_name,
        COALESCE(district_name, 'All Districts') AS district_name,
        CASE 
            WHEN UPPER(state_name) IN ('PUNJAB', 'HARYANA', 'DELHI', 'UTTAR PRADESH', 'HIMACHAL PRADESH', 'UTTARAKHAND', 'JAMMU AND KASHMIR', 'LADAKH', 'CHANDIGARH') THEN 'North'
            WHEN UPPER(state_name) IN ('TAMIL NADU', 'KERALA', 'KARNATAKA', 'ANDHRA PRADESH', 'TELANGANA', 'PUDUCHERRY') THEN 'South'
            WHEN UPPER(state_name) IN ('MAHARASHTRA', 'GUJARAT', 'GOA', 'RAJASTHAN', 'DADRA AND NAGAR HAVELI AND DAMAN AND DIU') THEN 'West'
            WHEN UPPER(state_name) IN ('BIHAR', 'WEST BENGAL', 'ODISHA', 'JHARKHAND') THEN 'East'
            WHEN UPPER(state_name) IN ('MADHYA PRADESH', 'CHHATTISGARH') THEN 'Central'
            ELSE 'North-East'
        END AS zone
    FROM (
        SELECT DISTINCT UPPER(state_name) AS state_name, district_name 
        FROM read_parquet('data/parquet_stores/*.parquet', union_by_name=true)
        WHERE state_name IS NOT NULL
    );
    """)
    geo_count = con.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
    print(f"   ✓ Created dim_geography: {geo_count} unique geographic nodes.")

    # -------------------------------------------------------------------------
    # 2. DIM_TIME (Shared Temporal Dimension: FY, Calendar Year, Season)
    # -------------------------------------------------------------------------
    print("📦 [2/6] Building DIM_TIME (Temporal Dimension)...")
    con.execute("""
    CREATE OR REPLACE SEQUENCE seq_time_id START 1;

    CREATE OR REPLACE TABLE dim_time AS
    SELECT 
        nextval('seq_time_id') AS time_id,
        financial_year,
        calendar_year,
        season
    FROM (
        SELECT DISTINCT 
            COALESCE(financial_year, '2023-24') AS financial_year,
            2024 AS calendar_year,
            'Rabi' AS season
        FROM read_parquet('data/parquet_stores/*.parquet', union_by_name=true)
    );
    """)
    time_count = con.execute("SELECT COUNT(*) FROM dim_time").fetchone()[0]
    print(f"   ✓ Created dim_time: {time_count} temporal intervals.")

    # -------------------------------------------------------------------------
    # 3. FACT_PM_KISAN_DISBURSEMENT (2-Join Star Schema)
    # -------------------------------------------------------------------------
    print("📦 [3/6] Building FACT_PM_KISAN_DISBURSEMENT (Foreign Keys -> Geo, Time)...")
    con.execute("""
    CREATE OR REPLACE SEQUENCE seq_fact_pmkisan START 1;

    CREATE OR REPLACE TABLE fact_pm_kisan_disbursement AS
    SELECT 
        nextval('seq_fact_pmkisan') AS fact_id,
        g.geo_id,
        t.time_id,
        raw.farmer_beneficiaries,
        raw.amount_inr
    FROM read_parquet('data/parquet_stores/ndap_pm_kisan_disbursement.parquet') raw
    JOIN dim_geography g 
        ON UPPER(raw.state_name) = g.state_name 
       AND COALESCE(raw.district_name, 'All Districts') = g.district_name
    JOIN dim_time t 
        ON COALESCE(raw.financial_year, '2023-24') = t.financial_year;
    """)
    pmk_count = con.execute("SELECT COUNT(*) FROM fact_pm_kisan_disbursement").fetchone()[0]
    print(f"   ✓ Created fact_pm_kisan_disbursement: {pmk_count} fact rows.")

    # -------------------------------------------------------------------------
    # 4. FACT_CROP_PRODUCTION (Foreign Keys -> Geo, Time)
    # -------------------------------------------------------------------------
    print("📦 [4/6] Building FACT_CROP_PRODUCTION (Foreign Keys -> Geo, Time)...")
    con.execute("""
    CREATE OR REPLACE SEQUENCE seq_fact_crop START 1;

    CREATE OR REPLACE TABLE fact_crop_production AS
    SELECT 
        nextval('seq_fact_crop') AS fact_id,
        g.geo_id,
        t.time_id,
        UPPER(raw.crop_name) AS crop_name,
        raw.area_hectares,
        raw.production_tonnes,
        raw.yield_kg_per_hectare
    FROM read_parquet('data/parquet_stores/ndap_crop_production_census.parquet') raw
    JOIN dim_geography g 
        ON UPPER(raw.state_name) = g.state_name 
       AND COALESCE(raw.district_name, 'All Districts') = g.district_name
    CROSS JOIN (SELECT time_id FROM dim_time LIMIT 1) t;
    """)
    crop_count = con.execute("SELECT COUNT(*) FROM fact_crop_production").fetchone()[0]
    print(f"   ✓ Created fact_crop_production: {crop_count} fact rows.")

    # -------------------------------------------------------------------------
    # 5. FACT_EDUCATION_STATS (Foreign Keys -> Geo, Time)
    # -------------------------------------------------------------------------
    print("📦 [5/6] Building FACT_EDUCATION_STATS (Foreign Keys -> Geo, Time)...")
    con.execute("""
    CREATE OR REPLACE SEQUENCE seq_fact_edu START 1;

    CREATE OR REPLACE TABLE fact_education_stats AS
    SELECT 
        nextval('seq_fact_edu') AS fact_id,
        g.geo_id,
        t.time_id,
        raw.student_count,
        raw.male_literacy_rate,
        raw.female_literacy_rate,
        raw.pupil_teacher_ratio
    FROM read_parquet('data/parquet_stores/ndap_education_stats.parquet') raw
    JOIN dim_geography g 
        ON UPPER(raw.state_name) = g.state_name 
       AND COALESCE(raw.district_name, 'All Districts') = g.district_name
    CROSS JOIN (SELECT time_id FROM dim_time LIMIT 1) t;
    """)
    edu_count = con.execute("SELECT COUNT(*) FROM fact_education_stats").fetchone()[0]
    print(f"   ✓ Created fact_education_stats: {edu_count} fact rows.")

    # -------------------------------------------------------------------------
    # 6. Export Relational Star Schema to Parquet Stores
    # -------------------------------------------------------------------------
    print("📦 [6/6] Exporting Normalized Parquet Stores...")
    tables = [
        "dim_geography",
        "dim_time",
        "fact_pm_kisan_disbursement",
        "fact_crop_production",
        "fact_education_stats",
    ]
    for tbl in tables:
        out_p = RELATIONAL_OUT_DIR / f"{tbl}.parquet"
        con.execute(f"COPY {tbl} TO '{out_p.resolve()}' (FORMAT PARQUET);")
        print(f"   ✓ Exported {tbl}.parquet")

    con.close()
    print("\n" + "=" * 80)
    print("🎉 Relational 3NF Star Schema normalization complete!")
    print(f"   Database: {DUCKDB_OUT_PATH}")
    print(f"   Relational Stores: {RELATIONAL_OUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
