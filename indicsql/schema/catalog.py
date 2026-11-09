"""
NDAP Database Catalog Definitions and Schema Registry.
Manages comprehensive metadata for all 20 National Data & Analytics Platform (NDAP)
databases evaluated in the April 2026 IndicDB benchmark.
"""

from typing import Any, Dict, List


class NDAPCatalog:
    """Registry of 20 NDAP database schemas, tables, relationships, and data dictionaries."""

    _TABLES: Dict[str, Dict[str, Any]] = {
        # =====================================================================
        # 1. Agriculture & Allied Sector (5 Databases)
        # =====================================================================
        "ndap_pm_kisan_disbursement": {
            "domain": "Agriculture",
            "title": "PM-KISAN Direct Benefit Transfer Portal",
            "description": "Pradhan Mantri Kisan Samman Nidhi state and district level fund disbursements.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name (e.g., MAHARASHTRA, BIHAR, TAMIL NADU)",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year string (e.g., 2022-23, 2023-24, 2024-25)",
                "farmer_beneficiaries": "BIGINT - Number of farmer accounts credited",
                "amount_inr": "DOUBLE - Total fund amount disbursed in Indian Rupees",
            },
        },
        "ndap_crop_production_census": {
            "domain": "Agriculture",
            "title": "Annual Agricultural Crop Census",
            "description": "District-wise crop acreage, production yield, and seasonal harvest volumes.",
            "primary_key": ["state_name", "district_name", "crop_year", "crop_name", "season"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "crop_year": "INTEGER - Agricultural census year (e.g., 2022, 2023, 2024)",
                "crop_name": "VARCHAR - Crop variety (e.g., RICE, WHEAT, COTTON, SUGARCANE, SOYBEAN)",
                "season": "VARCHAR - Cropping season (Kharif, Rabi, Zaid)",
                "area_hectares": "DOUBLE - Cultivated land area in hectares",
                "production_tonnes": "DOUBLE - Crop production harvest in metric tonnes",
                "yield_kg_per_hectare": "DOUBLE - Crop productivity yield in kg per hectare",
            },
        },
        "ndap_mandi_commodity_prices": {
            "domain": "Agriculture",
            "title": "e-NAM Mandi Market Commodity Arrivals & Prices",
            "description": "Daily and monthly wholesale agricultural commodity prices across regulated mandis.",
            "primary_key": [
                "state_name",
                "district_name",
                "market_name",
                "commodity",
                "arrival_date",
            ],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "market_name": "VARCHAR - APMC Mandi market name",
                "commodity": "VARCHAR - Commodity name (e.g., ONION, TOMATO, POTATO, MUSTARD)",
                "arrival_date": "VARCHAR - Market reporting date (YYYY-MM-DD)",
                "arrival_quantity_tonnes": "DOUBLE - Quantity of arrivals in metric tonnes",
                "min_price_inr": "DOUBLE - Minimum modal price per quintal in INR",
                "max_price_inr": "DOUBLE - Maximum modal price per quintal in INR",
                "modal_price_inr": "DOUBLE - Prevailing modal trading price per quintal in INR",
            },
        },
        "ndap_fertilizer_distribution": {
            "domain": "Agriculture",
            "title": "Integrated Fertilizer Management System (iFMS)",
            "description": "District-level fertilizer allocations, stock availability, and retail point sales.",
            "primary_key": ["state_name", "district_name", "financial_year", "fertilizer_type"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year string",
                "fertilizer_type": "VARCHAR - Chemical fertilizer formulation (UREA, DAP, MOP, NPK)",
                "requirement_tonnes": "DOUBLE - Seasonal requirement projection in tonnes",
                "availability_tonnes": "DOUBLE - Stock dispatched to retail points in tonnes",
                "sales_tonnes": "DOUBLE - Actual DBT farmer point-of-sale volume in tonnes",
            },
        },
        "ndap_soil_health_records": {
            "domain": "Agriculture",
            "title": "Soil Health Card Scheme Database",
            "description": "Micro and macro nutrient soil test profiles and Soil Health Cards issued.",
            "primary_key": ["state_name", "district_name", "cycle_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "cycle_year": "INTEGER - Soil testing cycle year",
                "samples_tested": "INTEGER - Number of laboratory soil core samples analyzed",
                "cards_issued": "INTEGER - Soil Health Cards distributed to farmers",
                "nitrogen_status": "VARCHAR - Soil Nitrogen fertility classification (LOW, MEDIUM, HIGH)",
                "phosphorus_status": "VARCHAR - Soil Phosphorus status (LOW, MEDIUM, HIGH)",
                "organic_carbon_pct": "FLOAT - Percentage organic carbon soil content",
            },
        },
        # =====================================================================
        # 2. Education & Skill Development (5 Databases)
        # =====================================================================
        "ndap_education_stats": {
            "domain": "Education",
            "title": "UDISE+ School Education & Demographic Statistics",
            "description": "Unified District Information System for Education Plus student and literacy indicators.",
            "primary_key": ["state_name", "district_name", "census_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "census_year": "INTEGER - Academic recording year (e.g., 2022, 2023, 2024)",
                "student_count": "INTEGER - Total enrolled student count (Classes 1-12)",
                "female_literacy_rate": "FLOAT - Percentage female adult literacy rate",
                "male_literacy_rate": "FLOAT - Percentage male adult literacy rate",
                "pupil_teacher_ratio": "FLOAT - Number of students per accredited teacher",
            },
        },
        "ndap_school_infrastructure": {
            "domain": "Education",
            "title": "National School Facility & Basic Amenities Survey",
            "description": "School facility compliance including electricity, drinking water, toilets, and digital labs.",
            "primary_key": ["state_name", "district_name", "academic_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "academic_year": "VARCHAR - Academic calendar year (e.g., 2023-24)",
                "total_schools": "INTEGER - Total operational government and aided schools",
                "schools_with_electricity": "INTEGER - Schools with functional grid power",
                "schools_with_drinking_water": "INTEGER - Schools with verified potable drinking water",
                "schools_with_girl_toilets": "INTEGER - Schools with separate functional girls toilets",
                "schools_with_computer_labs": "INTEGER - Schools equipped with functional ICT computers",
            },
        },
        "ndap_higher_education_aishe": {
            "domain": "Education",
            "title": "All India Survey on Higher Education (AISHE)",
            "description": "Colleges, universities, faculty census, and Gross Enrollment Ratios (GER).",
            "primary_key": ["state_name", "survey_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "survey_year": "VARCHAR - AISHE survey year (e.g., 2022-23)",
                "university_count": "INTEGER - Number of chartered central, state, and private universities",
                "college_count": "INTEGER - Number of accredited degree colleges",
                "gross_enrollment_ratio_male": "FLOAT - Higher education GER for males (18-23 years)",
                "gross_enrollment_ratio_female": "FLOAT - Higher education GER for females (18-23 years)",
                "total_faculty_count": "INTEGER - Full-time instructional faculty personnel",
            },
        },
        "ndap_midday_meal_scheme": {
            "domain": "Education",
            "title": "PM POSHAN / Mid-Day Meal Nutrition Portal",
            "description": "Coverage of school meal nutrition, foodgrain quotas, and student beneficiaries.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial reporting year",
                "institutions_covered": "INTEGER - Government primary and upper primary schools covered",
                "primary_students_benefited": "INTEGER - Enrolled primary school children receiving hot meals",
                "upper_primary_students_benefited": "INTEGER - Upper primary children receiving meals",
                "foodgrains_allocated_mt": "DOUBLE - Foodgrain allocation in metric tonnes (Wheat/Rice)",
            },
        },
        "ndap_vocational_skill_training": {
            "domain": "Education",
            "title": "Skill India & PMKVY Vocational Database",
            "description": "Short-term skilling, ITI certifications, and placement records.",
            "primary_key": [
                "state_name",
                "district_name",
                "financial_year",
                "sector_skill_council",
            ],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year",
                "sector_skill_council": "VARCHAR - Industry sector (Healthcare, Electronics, Agriculture, IT)",
                "enrolled_candidates": "INTEGER - Trainees registered in accredited centers",
                "certified_candidates": "INTEGER - Candidates passing NSQF certification",
                "placed_candidates": "INTEGER - Candidates verified placed in formal employment",
            },
        },
        # =====================================================================
        # 3. Healthcare, Nutrition & Demographics (5 Databases)
        # =====================================================================
        "ndap_nfhs5_health_indicators": {
            "domain": "Healthcare",
            "title": "National Family Health Survey (NFHS-5)",
            "description": "District maternal health, child nutrition, immunization, and lifestyle indicators.",
            "primary_key": ["state_name", "district_name"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "institutional_births_pct": "FLOAT - Percentage of births delivered in health facilities",
                "fully_vaccinated_children_pct": "FLOAT - Percentage children aged 12-23 months fully vaccinated",
                "stunted_children_pct": "FLOAT - Percentage children under 5 years who are stunted (height-for-age)",
                "anaemic_women_pct": "FLOAT - Percentage pregnant/non-pregnant women who are anaemic",
                "households_improved_sanitation_pct": "FLOAT - Households using improved sanitation facility",
            },
        },
        "ndap_rural_health_infrastructure": {
            "domain": "Healthcare",
            "title": "Rural Health Statistics (RHS Bulletin)",
            "description": "Primary healthcare centers (PHC), community health centers (CHC), and specialist doctors.",
            "primary_key": ["state_name", "reporting_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "reporting_year": "INTEGER - RHS reporting year",
                "sub_centres_count": "INTEGER - Functioning rural Sub-Centres",
                "primary_health_centres_phc": "INTEGER - Primary Health Centres (PHC) functioning",
                "community_health_centres_chc": "INTEGER - Community Health Centres (CHC) functioning",
                "doctors_at_phc": "INTEGER - Allopathic doctors in position at PHCs",
                "specialists_at_chc": "INTEGER - Surgeons, OBGYN, Physicians, Pediatricians at CHCs",
            },
        },
        "ndap_maternal_child_mortality": {
            "domain": "Healthcare",
            "title": "Sample Registration System (SRS) Vital Statistics",
            "description": "Maternal Mortality Ratio (MMR), Infant Mortality Rate (IMR), and Under-5 Mortality.",
            "primary_key": ["state_name", "survey_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "survey_year": "VARCHAR - SRS release period (e.g., 2021-23)",
                "maternal_mortality_ratio_mmr": "INTEGER - Maternal deaths per 100,000 live births",
                "infant_mortality_rate_imr": "INTEGER - Infant deaths per 1,000 live births",
                "under_five_mortality_rate_u5mr": "INTEGER - Under-five deaths per 1,000 live births",
                "birth_rate": "FLOAT - Crude birth rate per 1,000 population",
            },
        },
        "ndap_ayushman_bharat_pmjay": {
            "domain": "Healthcare",
            "title": "Ayushman Bharat PM-JAY Health Protection Portal",
            "description": "Golden card issuances, hospital empanelment, and secondary/tertiary claim settlements.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year string",
                "cards_issued": "BIGINT - Ayushman Bharat beneficiaries registered with e-cards",
                "empanelled_hospitals": "INTEGER - Active public and private empanelled hospitals",
                "authorized_admissions": "INTEGER - Pre-authorized inpatient hospital treatments",
                "claim_amount_settled_inr": "DOUBLE - Value of approved insurance claims disbursed in INR",
            },
        },
        "ndap_national_tuberculosis_portal": {
            "domain": "Healthcare",
            "title": "Ni-kshay National TB Elimination Portal",
            "description": "Tuberculosis notifications, treatment completion outcomes, and nutritional support (Nikshay Poshan).",
            "primary_key": ["state_name", "district_name", "reporting_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "reporting_year": "INTEGER - Reporting year",
                "total_notified_patients": "INTEGER - Total public and private sector TB cases notified",
                "treatment_success_rate_pct": "FLOAT - Percentage successfully completing therapy regimen",
                "hiv_screened_pct": "FLOAT - Percentage TB patients with known HIV status",
                "dbt_nutritional_amount_inr": "DOUBLE - Nikshay Poshan Yojana direct cash assistance paid in INR",
            },
        },
        # =====================================================================
        # 4. Rural Development, Welfare & Infrastructure (5 Databases)
        # =====================================================================
        "mgnrega_state_annual_employment": {
            "domain": "Rural Development",
            "title": "MGNREGA National Rural Employment Portal",
            "description": "Mahatma Gandhi NREGA person-days generated, households engaged, and wage expenditures.",
            "primary_key": ["state_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "financial_year": "VARCHAR - Financial year string",
                "households_worked": "BIGINT - Unique rural households provided wage work",
                "total_mandays_generated": "BIGINT - Total person-days of employment generated",
                "women_mandays_pct": "FLOAT - Percentage of person-days generated by women workers",
                "total_wage_expenditure_inr": "DOUBLE - Total direct wage transfers to worker bank accounts",
            },
        },
        "ndap_pmgsy_rural_roads": {
            "domain": "Rural Development",
            "title": "Pradhan Mantri Gram Sadak Yojana (PMGSY)",
            "description": "All-weather road connectivity to eligible unconnected rural habitations.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year",
                "sanctioned_road_length_km": "DOUBLE - Road construction sanctioned in kilometers",
                "completed_road_length_km": "DOUBLE - All-weather road constructed in kilometers",
                "habitations_connected": "INTEGER - Rural habitations newly linked to paved network",
                "total_expenditure_inr": "DOUBLE - Total capital scheme expenditure disbursed",
            },
        },
        "ndap_jal_jeevan_tap_water": {
            "domain": "Rural Development",
            "title": "Jal Jeevan Mission Har Ghar Jal Portal",
            "description": "Rural household tap water connections (FHTC) and water quality surveillance.",
            "primary_key": ["state_name", "district_name"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "total_rural_households": "INTEGER - Total verified rural households in district",
                "households_with_tap_connection": "INTEGER - Households with functional tap connections",
                "tap_connection_coverage_pct": "FLOAT - Percentage household coverage attained",
                "villages_certified_har_ghar_jal": "INTEGER - Gram Panchayats with 100% certified tap coverage",
            },
        },
        "ndap_pmay_rural_housing": {
            "domain": "Rural Development",
            "title": "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
            "description": "Pucca houses sanctioned, constructed, and subsidy installments credited to homeless beneficiaries.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year",
                "houses_sanctioned": "INTEGER - Number of pucca dwelling units approved",
                "houses_completed": "INTEGER - Fully constructed and geo-tagged houses completed",
                "funds_transferred_inr": "DOUBLE - Direct housing subsidy assistance disbursed in INR",
            },
        },
        "ndap_gram_panchayat_finance": {
            "domain": "Rural Development",
            "title": "e-GramSwaraj Local Body Finance & 15th FC Grants",
            "description": "Fifteenth Finance Commission basic and tied grants allocated to Gram Panchayats.",
            "primary_key": ["state_name", "district_name", "financial_year"],
            "columns": {
                "state_name": "VARCHAR - State/UT name",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial accounting year",
                "gram_panchayat_count": "INTEGER - Number of rural local bodies reporting",
                "grant_allocated_inr": "DOUBLE - Central Finance Commission allocation in INR",
                "grant_utilized_inr": "DOUBLE - Audited development expenditure executed in INR",
                "sanitation_drinking_water_expenditure_inr": "DOUBLE - Tied expenditure on sanitation and water",
            },
        },
    }

    # Normalized 3NF Relational Star Schema Tables (Multi-Join Benchmark)
    _RELATIONAL_TABLES: Dict[str, Dict[str, Any]] = {
        "dim_geography": {
            "domain": "Cross-Domain Dimension",
            "title": "Geographic Hierarchy Dimension",
            "description": "Standardized geographic entity mapping: State, District, and Administrative Zone.",
            "primary_key": ["geo_id"],
            "columns": {
                "geo_id": "BIGINT - Unique geographic surrogate key",
                "state_name": "VARCHAR - State/UT name in UPPERCASE (e.g. UTTAR PRADESH, BIHAR)",
                "district_name": "VARCHAR - Administrative district name",
                "zone": "VARCHAR - Regional geographic zone (North, South, East, West, Central, North-East)",
            },
        },
        "dim_time": {
            "domain": "Cross-Domain Dimension",
            "title": "Temporal Interval Dimension",
            "description": "Standardized fiscal and seasonal temporal hierarchy.",
            "primary_key": ["time_id"],
            "columns": {
                "time_id": "BIGINT - Unique temporal surrogate key",
                "financial_year": "VARCHAR - Fiscal accounting year (e.g. 2022-23, 2023-24)",
                "calendar_year": "INTEGER - Gregorian calendar year",
                "season": "VARCHAR - Agricultural season (Kharif, Rabi, Zaid)",
            },
        },
        "fact_pm_kisan_disbursement": {
            "domain": "Agriculture",
            "title": "PM-KISAN Disbursement Fact Table",
            "description": "Normalized DBT payments with foreign keys referencing dim_geography and dim_time.",
            "primary_key": ["fact_id"],
            "foreign_keys": {"geo_id": "dim_geography.geo_id", "time_id": "dim_time.time_id"},
            "columns": {
                "fact_id": "BIGINT - Primary surrogate key",
                "geo_id": "BIGINT - Foreign key to dim_geography(geo_id)",
                "time_id": "BIGINT - Foreign key to dim_time(time_id)",
                "farmer_beneficiaries": "BIGINT - Count of credited farmers",
                "amount_inr": "DOUBLE - Total funds disbursed in INR",
            },
        },
        "fact_crop_production": {
            "domain": "Agriculture",
            "title": "Crop Production Census Fact Table",
            "description": "Normalized crop harvest metrics with foreign keys referencing dim_geography and dim_time.",
            "primary_key": ["fact_id"],
            "foreign_keys": {"geo_id": "dim_geography.geo_id", "time_id": "dim_time.time_id"},
            "columns": {
                "fact_id": "BIGINT - Primary surrogate key",
                "geo_id": "BIGINT - Foreign key to dim_geography(geo_id)",
                "time_id": "BIGINT - Foreign key to dim_time(time_id)",
                "crop_name": "VARCHAR - Crop commodity in UPPERCASE (e.g. WHEAT, RICE, COTTON)",
                "area_hectares": "DOUBLE - Cultivation area in hectares",
                "production_tonnes": "DOUBLE - Metric tonnes produced",
                "yield_kg_per_hectare": "DOUBLE - Productivity yield per hectare",
            },
        },
        "fact_education_stats": {
            "domain": "Education",
            "title": "Educational Statistics Fact Table",
            "description": "Normalized school and literacy metrics with foreign keys referencing dim_geography and dim_time.",
            "primary_key": ["fact_id"],
            "foreign_keys": {"geo_id": "dim_geography.geo_id", "time_id": "dim_time.time_id"},
            "columns": {
                "fact_id": "BIGINT - Primary surrogate key",
                "geo_id": "BIGINT - Foreign key to dim_geography(geo_id)",
                "time_id": "BIGINT - Foreign key to dim_time(time_id)",
                "student_count": "BIGINT - Total enrolled student population",
                "male_literacy_rate": "DOUBLE - Male literacy rate percentage",
                "female_literacy_rate": "DOUBLE - Female literacy rate percentage",
                "pupil_teacher_ratio": "DOUBLE - Ratio of pupils to teachers",
            },
        },
    }

    @classmethod
    def list_tables(cls) -> List[str]:
        """Returns all 20 registered table names."""
        return list(cls._TABLES.keys())

    @classmethod
    def get_table_schema(cls, table_name: str) -> Dict[str, Any]:
        """Returns the schema dictionary for a specific table."""
        if table_name in cls._TABLES:
            return cls._TABLES[table_name]
        return cls._RELATIONAL_TABLES.get(table_name, {})

    @classmethod
    def list_domains(cls) -> List[str]:
        """Returns distinct domain sectors covered in NDAP."""
        return sorted(list({t["domain"] for t in cls._TABLES.values()}))

    @classmethod
    def get_tables_by_domain(cls, domain: str) -> List[str]:
        """Returns tables associated with a given domain sector."""
        return [k for k, v in cls._TABLES.items() if v.get("domain", "").lower() == domain.lower()]

    @classmethod
    def get_total_table_count(cls) -> int:
        """Returns the total number of registered NDAP databases."""
        return len(cls._TABLES)
