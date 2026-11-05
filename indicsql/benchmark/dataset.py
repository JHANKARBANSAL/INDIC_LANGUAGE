"""
IndicDB Benchmark Dataset Definition and Suite Generator.
Structures test instances covering 7 languages across 20 NDAP databases and 3 difficulty tiers.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

BENCHMARK_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "benchmarks"


class BenchmarkQuery(BaseModel):
    """Represents an IndicDB benchmark test query with ground-truth SQL and execution expectation."""

    query_id: str = Field(..., description="Unique query identifier (e.g. ind-q-001)")
    query: str = Field(
        ..., description="Natural language question in Indic language or Hinglish/English"
    )
    language: str = Field(
        ..., description="ISO language code ('hi', 'mr', 'ta', 'te', 'bn', 'hi-en', 'en')"
    )
    script: str = Field(
        ..., description="Unicode script ('Devanagari', 'Tamil', 'Telugu', 'Bengali', 'Latin')"
    )
    domain: str = Field(
        ...,
        description="Sector domain ('Agriculture', 'Education', 'Healthcare', 'Rural Development')",
    )
    target_table: str = Field(..., description="Target NDAP database table name")
    gold_sql: str = Field(..., description="Gold standard executable SQL query")
    difficulty: str = Field(default="medium", description="'easy', 'medium', or 'hard'")
    target_columns: List[str] = Field(
        default_factory=list, description="Ground truth columns for schema linking"
    )


# Benchmark query templates covering the 7 IndicDB languages
CURATED_BENCHMARK_INSTANCES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # Marathi (mr)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-mr-001",
        "query": "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?",
        "language": "mr",
        "script": "Devanagari",
        "domain": "Agriculture",
        "target_table": "ndap_pm_kisan_disbursement",
        "gold_sql": "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        "difficulty": "medium",
        "target_columns": ["farmer_beneficiaries", "amount_inr", "state_name"],
    },
    {
        "query_id": "indicdb-mr-002",
        "query": "महाराष्ट्रात कापूस पिकाचे एकूण उत्पादन किती टन झाले?",
        "language": "mr",
        "script": "Devanagari",
        "domain": "Agriculture",
        "target_table": "ndap_crop_production_census",
        "gold_sql": "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND crop_name = 'COTTON';",
        "difficulty": "medium",
        "target_columns": ["production_tonnes", "state_name", "crop_name"],
    },
    {
        "query_id": "indicdb-mr-003",
        "query": "पुणे जिल्ह्यातील शाळांमध्ये संगणक प्रयोगशाळा किती आहेत?",
        "language": "mr",
        "script": "Devanagari",
        "domain": "Education",
        "target_table": "ndap_school_infrastructure",
        "gold_sql": "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
        "difficulty": "easy",
        "target_columns": ["schools_with_computer_labs", "state_name", "district_name"],
    },
    # -------------------------------------------------------------------------
    # Hindi (hi)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-hi-001",
        "query": "बिहार के किस जिले में सबसे कम महिला साक्षरता दर दर्ज की गई?",
        "language": "hi",
        "script": "Devanagari",
        "domain": "Education",
        "target_table": "ndap_education_stats",
        "gold_sql": "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        "difficulty": "hard",
        "target_columns": ["district_name", "female_literacy_rate", "state_name"],
    },
    {
        "query_id": "indicdb-hi-002",
        "query": "उत्तर प्रदेश में यूरिया उर्वरक की कुल बिक्री कितनी रही?",
        "language": "hi",
        "script": "Devanagari",
        "domain": "Agriculture",
        "target_table": "ndap_fertilizer_distribution",
        "gold_sql": "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'UTTAR PRADESH' AND fertilizer_type = 'UREA';",
        "difficulty": "medium",
        "target_columns": ["sales_tonnes", "state_name", "fertilizer_type"],
    },
    {
        "query_id": "indicdb-hi-003",
        "query": "मध्य प्रदेश में आयुष्मान भारत योजना के तहत कितने कार्ड जारी किए गए?",
        "language": "hi",
        "script": "Devanagari",
        "domain": "Healthcare",
        "target_table": "ndap_ayushman_bharat_pmjay",
        "gold_sql": "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MADHYA PRADESH';",
        "difficulty": "easy",
        "target_columns": ["cards_issued", "state_name"],
    },
    # -------------------------------------------------------------------------
    # Hinglish (hi-en)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-hien-001",
        "query": "Maharashtra mein pichle saal kitne kisano ne PM-Kisan yojana ka fayda liya?",
        "language": "hi-en",
        "script": "Latin",
        "domain": "Agriculture",
        "target_table": "ndap_pm_kisan_disbursement",
        "gold_sql": "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        "difficulty": "medium",
        "target_columns": ["farmer_beneficiaries", "amount_inr", "state_name"],
    },
    {
        "query_id": "indicdb-hien-002",
        "query": "Bihar ke kis district mein female literacy sabse kam hai?",
        "language": "hi-en",
        "script": "Latin",
        "domain": "Education",
        "target_table": "ndap_education_stats",
        "gold_sql": "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        "difficulty": "hard",
        "target_columns": ["district_name", "female_literacy_rate", "state_name"],
    },
    {
        "query_id": "indicdb-hien-003",
        "query": "Rajasthan mein total kitne pucca houses PMAY ke under complete hue?",
        "language": "hi-en",
        "script": "Latin",
        "domain": "Rural Development",
        "target_table": "ndap_pmay_rural_housing",
        "gold_sql": "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'RAJASTHAN';",
        "difficulty": "medium",
        "target_columns": ["houses_completed", "state_name"],
    },
    # -------------------------------------------------------------------------
    # Tamil (ta)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-ta-001",
        "query": "தமிழ்நாட்டில் மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் எத்தனை மனித வேலை நாட்கள் உருவாக்கப்பட்டன?",
        "language": "ta",
        "script": "Tamil",
        "domain": "Rural Development",
        "target_table": "mgnrega_state_annual_employment",
        "gold_sql": "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' GROUP BY financial_year ORDER BY financial_year DESC;",
        "difficulty": "hard",
        "target_columns": ["total_mandays_generated", "state_name", "financial_year"],
    },
    {
        "query_id": "indicdb-ta-002",
        "query": "மதுரை மாவட்டத்தில் எத்தனை கிராமப்புற வீடுகளுக்கு குடிநீர் குழாய் இணைப்பு வழங்கப்பட்டுள்ளது?",
        "language": "ta",
        "script": "Tamil",
        "domain": "Rural Development",
        "target_table": "ndap_jal_jeevan_tap_water",
        "gold_sql": "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
        "difficulty": "easy",
        "target_columns": ["households_with_tap_connection", "state_name", "district_name"],
    },
    # -------------------------------------------------------------------------
    # Telugu (te)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-te-001",
        "query": "ఆంధ్రప్రదేశ్ రాష్ట్రంలో పీఎం-కిసాన్ పథకం ద్వారా ఎంత మొత్తం నిధులు విడుదలయ్యాయి?",
        "language": "te",
        "script": "Telugu",
        "domain": "Agriculture",
        "target_table": "ndap_pm_kisan_disbursement",
        "gold_sql": "SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement WHERE state_name = 'ANDHRA PRADESH';",
        "difficulty": "medium",
        "target_columns": ["amount_inr", "state_name"],
    },
    {
        "query_id": "indicdb-te-002",
        "query": "విశాఖపట్నం జిల్లాలో పీఎంజీఎస్వై కింద పూర్తయిన రోడ్ల పొడవు ఎంత?",
        "language": "te",
        "script": "Telugu",
        "domain": "Rural Development",
        "target_table": "ndap_pmgsy_rural_roads",
        "gold_sql": "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Visakhapatnam';",
        "difficulty": "medium",
        "target_columns": ["completed_road_length_km", "state_name", "district_name"],
    },
    # -------------------------------------------------------------------------
    # Bengali (bn)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-bn-001",
        "query": "পশ্চিমবঙ্গে মোট চাল উৎপাদনের পরিমাণ কত টন?",
        "language": "bn",
        "script": "Bengali",
        "domain": "Agriculture",
        "target_table": "ndap_crop_production_census",
        "gold_sql": "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'WEST BENGAL' AND crop_name = 'RICE';",
        "difficulty": "medium",
        "target_columns": ["production_tonnes", "state_name", "crop_name"],
    },
    {
        "query_id": "indicdb-bn-002",
        "query": "মুর্শিদাবাদ জেলায় প্রাথমিকে মিড-ডে মিলের মাধ্যমে কতজন শিক্ষার্থী উপকৃত হয়েছে?",
        "language": "bn",
        "script": "Bengali",
        "domain": "Education",
        "target_table": "ndap_midday_meal_scheme",
        "gold_sql": "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'WEST BENGAL' AND district_name = 'Murshidabad';",
        "difficulty": "easy",
        "target_columns": ["primary_students_benefited", "state_name", "district_name"],
    },
    # -------------------------------------------------------------------------
    # English (en - Baseline Control)
    # -------------------------------------------------------------------------
    {
        "query_id": "indicdb-en-001",
        "query": "What is the total number of farmer beneficiaries under PM-KISAN in Maharashtra?",
        "language": "en",
        "script": "Latin",
        "domain": "Agriculture",
        "target_table": "ndap_pm_kisan_disbursement",
        "gold_sql": "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        "difficulty": "medium",
        "target_columns": ["farmer_beneficiaries", "amount_inr", "state_name"],
    },
    {
        "query_id": "indicdb-en-002",
        "query": "Which district in Bihar had the lowest female literacy rate?",
        "language": "en",
        "script": "Latin",
        "domain": "Education",
        "target_table": "ndap_education_stats",
        "gold_sql": "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        "difficulty": "hard",
        "target_columns": ["district_name", "female_literacy_rate", "state_name"],
    },
    {
        "query_id": "indicdb-en-003",
        "query": "How many mandays were generated under MGNREGA in Tamil Nadu by financial year?",
        "language": "en",
        "script": "Latin",
        "domain": "Rural Development",
        "target_table": "mgnrega_state_annual_employment",
        "gold_sql": "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' GROUP BY financial_year ORDER BY financial_year DESC;",
        "difficulty": "hard",
        "target_columns": ["total_mandays_generated", "state_name", "financial_year"],
    },
]


def generate_benchmark_suite(output_file: Optional[Path] = None) -> List[BenchmarkQuery]:
    """Generates and writes the standard IndicDB benchmark evaluation suite JSON."""
    if output_file is None:
        BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
        output_file = BENCHMARK_DIR / "indicdb_eval_suite.json"

    queries = [BenchmarkQuery(**item) for item in CURATED_BENCHMARK_INSTANCES]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([q.model_dump() for q in queries], f, ensure_ascii=False, indent=2)

    return queries


def load_benchmark_dataset(input_file: Optional[Path] = None) -> List[BenchmarkQuery]:
    """Loads benchmark queries from disk or generates the default suite."""
    target_path = input_file or (BENCHMARK_DIR / "indicdb_eval_suite.json")
    if not target_path.exists():
        return generate_benchmark_suite(target_path)

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [BenchmarkQuery(**item) for item in data]
