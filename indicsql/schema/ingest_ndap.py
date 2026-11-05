"""
NDAP Ingestion and Parquet Export Pipeline.
Generates realistic benchmark data aligned with Government of India NDAP statistics
and exports clean, compressed Apache Parquet tables and DDL catalog definitions for all 20 databases.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from indicsql.schema.catalog import NDAPCatalog

# Directory targets
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PARQUET_DIR = DATA_DIR / "parquet_stores"
CATALOG_DIR = DATA_DIR / "ndap_catalogs"

# Representative Indian States & Administrative Districts
INDIAN_GEOGRAPHY = {
    "MAHARASHTRA": ["Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Kolhapur"],
    "UTTAR PRADESH": ["Varanasi", "Lucknow", "Gorakhpur", "Kanpur", "Prayagraj", "Agra"],
    "BIHAR": ["Patna", "Gaya", "Purnia", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
    "TAMIL NADU": ["Chennai", "Madurai", "Coimbatore", "Tiruchirappalli", "Salem"],
    "WEST BENGAL": ["Kolkata", "Murshidabad", "Howrah", "Darjeeling", "Nadia"],
    "KARNATAKA": ["Bengaluru Rural", "Mysuru", "Belagavi", "Dharwad", "Kalaburagi"],
    "GUJARAT": ["Ahmedabad", "Surat", "Rajkot", "Vadodara", "Mehsana"],
    "ANDHRA PRADESH": ["Visakhapatnam", "Vijayawada", "Guntur", "Kurnool", "Nellore"],
    "RAJASTHAN": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Udaipur"],
    "MADHYA PRADESH": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
}

FINANCIAL_YEARS = ["2021-22", "2022-23", "2023-24", "2024-25"]
CALENDAR_YEARS = [2021, 2022, 2023, 2024]


def _generate_table_rows(table_name: str) -> List[Dict[str, Any]]:
    """Generates realistic rows for a given NDAP database table."""
    rows: List[Dict[str, Any]] = []

    if table_name == "ndap_pm_kisan_disbursement":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS:
                    base_farmers = 200_000 + (hash(f"{state}_{dist}") % 1_500_000)
                    amt = float(base_farmers * 6_000)  # PM-KISAN ₹6,000 per beneficiary
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "farmer_beneficiaries": int(base_farmers),
                            "amount_inr": amt,
                        }
                    )

    elif table_name == "ndap_crop_production_census":
        crops = [
            ("RICE", "Kharif"),
            ("WHEAT", "Rabi"),
            ("COTTON", "Kharif"),
            ("SUGARCANE", "Zaid"),
            ("SOYBEAN", "Kharif"),
        ]
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for year in CALENDAR_YEARS:
                    for crop, season in crops:
                        area = 10_000.0 + (hash(f"{dist}_{crop}_{year}") % 80_000)
                        yield_rate = 1800.0 + (hash(f"{crop}_{state}") % 2500)
                        production = (area * yield_rate) / 1000.0
                        rows.append(
                            {
                                "state_name": state,
                                "district_name": dist,
                                "crop_year": year,
                                "crop_name": crop,
                                "season": season,
                                "area_hectares": round(area, 2),
                                "production_tonnes": round(production, 2),
                                "yield_kg_per_hectare": round(yield_rate, 2),
                            }
                        )

    elif table_name == "ndap_mandi_commodity_prices":
        commodities = ["ONION", "TOMATO", "POTATO", "WHEAT", "MUSTARD"]
        dates = ["2024-09-01", "2024-09-10", "2024-09-15", "2024-09-20"]
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts[:2]:  # Select mandis in top districts
                market = f"{dist} APMC Mandi"
                for comm in commodities:
                    for dt in dates:
                        base = 1200 + (hash(f"{dist}_{comm}") % 3500)
                        rows.append(
                            {
                                "state_name": state,
                                "district_name": dist,
                                "market_name": market,
                                "commodity": comm,
                                "arrival_date": dt,
                                "arrival_quantity_tonnes": round(50.0 + (hash(dt) % 400), 2),
                                "min_price_inr": float(base - 200),
                                "max_price_inr": float(base + 450),
                                "modal_price_inr": float(base),
                            }
                        )

    elif table_name == "ndap_fertilizer_distribution":
        fert_types = ["UREA", "DAP", "MOP", "NPK"]
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS:
                    for ft in fert_types:
                        req = 20_000.0 + (hash(f"{dist}_{ft}_{fy}") % 50_000)
                        avail = req * (0.95 + (hash(ft) % 10) / 100.0)
                        sales = avail * 0.94
                        rows.append(
                            {
                                "state_name": state,
                                "district_name": dist,
                                "financial_year": fy,
                                "fertilizer_type": ft,
                                "requirement_tonnes": round(req, 2),
                                "availability_tonnes": round(avail, 2),
                                "sales_tonnes": round(sales, 2),
                            }
                        )

    elif table_name == "ndap_soil_health_records":
        classes = ["LOW", "MEDIUM", "HIGH"]
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for cy in [2022, 2023, 2024]:
                    samples = 15_000 + (hash(f"{dist}_{cy}") % 35_000)
                    cards = int(samples * 0.96)
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "cycle_year": cy,
                            "samples_tested": samples,
                            "cards_issued": cards,
                            "nitrogen_status": classes[hash(f"{dist}_n") % 3],
                            "phosphorus_status": classes[hash(f"{dist}_p") % 3],
                            "organic_carbon_pct": round(0.35 + (hash(dist) % 50) / 100.0, 2),
                        }
                    )

    elif table_name == "ndap_education_stats":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for cy in CALENDAR_YEARS:
                    students = 250_000 + (hash(f"{dist}_{cy}") % 600_000)
                    f_lit = 55.0 + (hash(f"{state}_{dist}") % 38)
                    m_lit = f_lit + 8.5
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "census_year": cy,
                            "student_count": int(students),
                            "female_literacy_rate": round(min(f_lit, 96.0), 2),
                            "male_literacy_rate": round(min(m_lit, 98.5), 2),
                            "pupil_teacher_ratio": round(22.0 + (hash(dist) % 15), 1),
                        }
                    )

    elif table_name == "ndap_school_infrastructure":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for ay in ["2022-23", "2023-24"]:
                    tot = 1200 + (hash(f"{dist}_{ay}") % 1800)
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "academic_year": ay,
                            "total_schools": tot,
                            "schools_with_electricity": int(tot * 0.92),
                            "schools_with_drinking_water": int(tot * 0.98),
                            "schools_with_girl_toilets": int(tot * 0.95),
                            "schools_with_computer_labs": int(tot * 0.48),
                        }
                    )

    elif table_name == "ndap_higher_education_aishe":
        for state in INDIAN_GEOGRAPHY.keys():
            for sy in ["2021-22", "2022-23"]:
                univ = 25 + (hash(state) % 60)
                colleges = univ * (20 + (hash(state) % 30))
                rows.append(
                    {
                        "state_name": state,
                        "survey_year": sy,
                        "university_count": univ,
                        "college_count": colleges,
                        "gross_enrollment_ratio_male": round(26.5 + (hash(state) % 10), 1),
                        "gross_enrollment_ratio_female": round(27.2 + (hash(state) % 12), 1),
                        "total_faculty_count": colleges * 28,
                    }
                )

    elif table_name == "ndap_midday_meal_scheme":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS[-2:]:
                    inst = 800 + (hash(dist) % 1200)
                    prim = inst * 110
                    up_prim = inst * 75
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "institutions_covered": inst,
                            "primary_students_benefited": prim,
                            "upper_primary_students_benefited": up_prim,
                            "foodgrains_allocated_mt": round((prim + up_prim) * 0.024, 2),
                        }
                    )

    elif table_name == "ndap_vocational_skill_training":
        sectors = ["Healthcare", "Electronics & IT", "Agriculture", "Apparel & Textiles"]
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts[:3]:
                for fy in ["2023-24", "2024-25"]:
                    for sec in sectors:
                        enr = 1200 + (hash(f"{dist}_{sec}") % 2500)
                        cert = int(enr * 0.88)
                        placed = int(cert * 0.65)
                        rows.append(
                            {
                                "state_name": state,
                                "district_name": dist,
                                "financial_year": fy,
                                "sector_skill_council": sec,
                                "enrolled_candidates": enr,
                                "certified_candidates": cert,
                                "placed_candidates": placed,
                            }
                        )

    elif table_name == "ndap_nfhs5_health_indicators":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                inst_birth = 82.0 + (hash(dist) % 16)
                vacc = 74.0 + (hash(f"{dist}_v") % 22)
                stunted = 28.0 + (hash(f"{dist}_s") % 18)
                anaemic = 48.0 + (hash(f"{dist}_a") % 24)
                sanitation = 65.0 + (hash(f"{dist}_san") % 30)
                rows.append(
                    {
                        "state_name": state,
                        "district_name": dist,
                        "institutional_births_pct": round(min(inst_birth, 99.4), 1),
                        "fully_vaccinated_children_pct": round(min(vacc, 98.0), 1),
                        "stunted_children_pct": round(stunted, 1),
                        "anaemic_women_pct": round(anaemic, 1),
                        "households_improved_sanitation_pct": round(min(sanitation, 98.0), 1),
                    }
                )

    elif table_name == "ndap_rural_health_infrastructure":
        for state in INDIAN_GEOGRAPHY.keys():
            for yr in [2022, 2023]:
                phc = 850 + (hash(state) % 1400)
                chc = int(phc / 4)
                sub = phc * 6
                rows.append(
                    {
                        "state_name": state,
                        "reporting_year": yr,
                        "sub_centres_count": sub,
                        "primary_health_centres_phc": phc,
                        "community_health_centres_chc": chc,
                        "doctors_at_phc": int(phc * 1.15),
                        "specialists_at_chc": int(chc * 2.4),
                    }
                )

    elif table_name == "ndap_maternal_child_mortality":
        for state in INDIAN_GEOGRAPHY.keys():
            for sy in ["2020-22", "2021-23"]:
                mmr = 65 + (hash(state) % 110)
                imr = 18 + (hash(state) % 25)
                rows.append(
                    {
                        "state_name": state,
                        "survey_year": sy,
                        "maternal_mortality_ratio_mmr": mmr,
                        "infant_mortality_rate_imr": imr,
                        "under_five_mortality_rate_u5mr": imr + 6,
                        "birth_rate": round(15.2 + (hash(state) % 8), 1),
                    }
                )

    elif table_name == "ndap_ayushman_bharat_pmjay":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS[-2:]:
                    cards = 350_000 + (hash(f"{dist}_{fy}") % 800_000)
                    adm = int(cards * 0.04)
                    claim = adm * 16_500.0
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "cards_issued": int(cards),
                            "empanelled_hospitals": 32 + (hash(dist) % 85),
                            "authorized_admissions": adm,
                            "claim_amount_settled_inr": claim,
                        }
                    )

    elif table_name == "ndap_national_tuberculosis_portal":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for yr in [2022, 2023, 2024]:
                    notified = 2400 + (hash(f"{dist}_{yr}") % 5500)
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "reporting_year": yr,
                            "total_notified_patients": notified,
                            "treatment_success_rate_pct": round(84.0 + (hash(dist) % 11), 1),
                            "hiv_screened_pct": round(94.5 + (hash(yr) % 5), 1),
                            "dbt_nutritional_amount_inr": float(notified * 3000),
                        }
                    )

    elif table_name == "mgnrega_state_annual_employment":
        for state in INDIAN_GEOGRAPHY.keys():
            for fy in FINANCIAL_YEARS:
                households = 2_500_000 + (hash(f"{state}_{fy}") % 4_000_000)
                mandays = households * (42 + (hash(state) % 18))
                wages = mandays * 245.0  # ~ ₹245 daily wage rate
                rows.append(
                    {
                        "state_name": state,
                        "financial_year": fy,
                        "households_worked": int(households),
                        "total_mandays_generated": int(mandays),
                        "women_mandays_pct": round(52.5 + (hash(state) % 12), 1),
                        "total_wage_expenditure_inr": wages,
                    }
                )

    elif table_name == "ndap_pmgsy_rural_roads":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS[-3:]:
                    sanctioned = 120.0 + (hash(f"{dist}_{fy}") % 250)
                    completed = sanctioned * (0.85 + (hash(dist) % 14) / 100.0)
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "sanctioned_road_length_km": round(sanctioned, 2),
                            "completed_road_length_km": round(completed, 2),
                            "habitations_connected": int(completed / 4.2),
                            "total_expenditure_inr": round(completed * 4_800_000.0, 2),
                        }
                    )

    elif table_name == "ndap_jal_jeevan_tap_water":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                tot_hh = 180_000 + (hash(dist) % 450_000)
                cov_pct = 68.0 + (hash(f"{state}_{dist}") % 31)
                tap_hh = int(tot_hh * (cov_pct / 100.0))
                rows.append(
                    {
                        "state_name": state,
                        "district_name": dist,
                        "total_rural_households": tot_hh,
                        "households_with_tap_connection": tap_hh,
                        "tap_connection_coverage_pct": round(cov_pct, 1),
                        "villages_certified_har_ghar_jal": int(12 + (hash(dist) % 85)),
                    }
                )

    elif table_name == "ndap_pmay_rural_housing":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS[-3:]:
                    sanc = 14_000 + (hash(f"{dist}_{fy}") % 28_000)
                    comp = int(sanc * 0.89)
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "houses_sanctioned": sanc,
                            "houses_completed": comp,
                            "funds_transferred_inr": float(
                                comp * 130_000
                            ),  # ₹1.3 lakh unit assistance
                        }
                    )

    elif table_name == "ndap_gram_panchayat_finance":
        for state, districts in INDIAN_GEOGRAPHY.items():
            for dist in districts:
                for fy in FINANCIAL_YEARS[-2:]:
                    gps = 280 + (hash(dist) % 650)
                    grant = gps * 2_200_000.0
                    util = grant * 0.91
                    rows.append(
                        {
                            "state_name": state,
                            "district_name": dist,
                            "financial_year": fy,
                            "gram_panchayat_count": gps,
                            "grant_allocated_inr": grant,
                            "grant_utilized_inr": util,
                            "sanitation_drinking_water_expenditure_inr": util * 0.55,
                        }
                    )

    return rows


def generate_ddl_sql(table_name: str, schema_dict: Dict[str, Any]) -> str:
    """Generates standard SQL DDL for an NDAP table."""
    cols = schema_dict.get("columns", {})
    pk = schema_dict.get("primary_key", [])

    lines = [
        f"-- DDL Specification: {table_name}",
        f"-- Domain: {schema_dict.get('domain')}",
        f"-- {schema_dict.get('description')}",
    ]
    lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
    col_defs = []
    for col_name, col_meta in cols.items():
        col_type = col_meta.split(" - ")[0].strip()
        col_defs.append(f"    {col_name} {col_type}")

    if pk:
        col_defs.append(f"    PRIMARY KEY ({', '.join(pk)})")

    lines.append(",\n".join(col_defs))
    lines.append(");")
    return "\n".join(lines)


def ingest_and_export_all_ndap_databases(
    parquet_dir: Path = PARQUET_DIR, catalog_dir: Path = CATALOG_DIR
) -> Dict[str, int]:
    """
    Executes the Ingestion Pipeline:
    1. Creates target directories for parquet files and SQL DDLs.
    2. Synthesizes full datasets for all 20 NDAP databases.
    3. Exports compressed Apache Parquet (.parquet) tables.
    4. Writes DDL .sql files and a consolidated catalog metadata JSON.
    Returns:
        Dict mapping table_name to row count.
    """
    parquet_dir.mkdir(parents=True, exist_ok=True)
    catalog_dir.mkdir(parents=True, exist_ok=True)

    tables = NDAPCatalog.list_tables()
    summary: Dict[str, int] = {}
    master_metadata: Dict[str, Any] = {
        "benchmark": "IndicDB (April 2026)",
        "source": "National Data & Analytics Platform (NDAP) - NITI Aayog / GoI",
        "total_databases": len(tables),
        "domains": NDAPCatalog.list_domains(),
        "tables": {},
    }

    print(f"🚀 Starting Ingestion for all {len(tables)} NDAP Databases...")

    for tbl in tables:
        schema = NDAPCatalog.get_table_schema(tbl)
        rows = _generate_table_rows(tbl)
        df = pd.DataFrame(rows)

        # Export to compressed Parquet
        parquet_path = parquet_dir / f"{tbl}.parquet"
        df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)

        # Export DDL SQL
        ddl_sql = generate_ddl_sql(tbl, schema)
        sql_path = catalog_dir / f"{tbl}.sql"
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(ddl_sql)

        summary[tbl] = len(df)
        master_metadata["tables"][tbl] = {
            "domain": schema.get("domain"),
            "title": schema.get("title"),
            "description": schema.get("description"),
            "row_count": len(df),
            "parquet_file": str(parquet_path.name),
            "columns": schema.get("columns"),
            "primary_key": schema.get("primary_key", []),
        }
        print(f"   ✓ Ingested '{tbl}': {len(df):,} records -> {parquet_path.name}")

    # Write master catalog metadata
    metadata_path = catalog_dir / "catalog_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(master_metadata, f, indent=2)

    print(
        f"\n✨ Ingestion Complete: {sum(summary.values()):,} total records across 20 NDAP databases."
    )
    print(f"📁 Parquet Stores: {parquet_dir}")
    print(f"📁 Catalog DDLs: {catalog_dir}")
    return summary


if __name__ == "__main__":
    ingest_and_export_all_ndap_databases()
