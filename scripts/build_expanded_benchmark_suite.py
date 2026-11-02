#!/usr/bin/env python3
"""
Generates and validates the expanded 105-query IndicDB benchmark suite
across 7 languages and 20 authentic NDAP databases.
Validates each SQL query against DuckDBSandbox.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.sandbox.duckdb_engine import DuckDBSandbox


def build_benchmark_items():
    # We define 15 queries per language for 7 languages (105 total)
    queries = []

    # Helper to add
    def add_q(qid, lang, script, domain, table, difficulty, query_text, gold_sql, cols):
        queries.append({
            "query_id": qid,
            "query": query_text,
            "language": lang,
            "script": script,
            "domain": domain,
            "target_table": table,
            "gold_sql": gold_sql,
            "difficulty": difficulty,
            "target_columns": cols,
        })

    # =========================================================================
    # 1. MARATHI (mr) - 15 Queries
    # =========================================================================
    add_q("indicdb-mr-001", "mr", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?",
          "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
          ["farmer_beneficiaries", "amount_inr", "state_name"])

    add_q("indicdb-mr-002", "mr", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
          "महाराष्ट्रात कापूस पिकाचे एकूण उत्पादन किती टन झाले?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND crop_name = 'COTTON';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-mr-003", "mr", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
          "पुणे जिल्ह्यातील शाळांमध्ये संगणक प्रयोगशाळा किती आहेत?",
          "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
          ["schools_with_computer_labs", "state_name", "district_name"])

    add_q("indicdb-mr-004", "mr", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
          "महाराष्ट्रात आयुष्यमान भारत अंतर्गत किती क्लेम रक्कम मंजूर झाली?",
          "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MAHARASHTRA';",
          ["claim_amount_settled_inr", "state_name"])

    add_q("indicdb-mr-005", "mr", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "hard",
          "महाराष्ट्रातील कोणत्या जिल्ह्यात पीएमएवाय अंतर्गत सर्वाधिक घरे पूर्ण झाली?",
          "SELECT district_name, SUM(houses_completed) AS total_houses FROM ndap_pmay_rural_housing WHERE state_name = 'MAHARASHTRA' GROUP BY district_name ORDER BY total_houses DESC LIMIT 1;",
          ["district_name", "houses_completed", "state_name"])

    add_q("indicdb-mr-006", "mr", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "नाशिक जिल्ह्यात किती ग्रामीण कुटुंबांना नळाचे पाणी मिळाले आहे?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'MAHARASHTRA' AND district_name = 'Nashik';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-mr-007", "mr", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "महाराष्ट्रात डीएपी खताची एकूण विक्री किती टन झाली?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'MAHARASHTRA' AND fertilizer_type = 'DAP';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-mr-008", "mr", "Devanagari", "Education", "ndap_education_stats", "hard",
          "महाराष्ट्रातील सर्वात कमी स्त्री साक्षरता दर असलेला जिल्हा कोणता?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'MAHARASHTRA' ORDER BY female_literacy_rate ASC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-mr-009", "mr", "Devanagari", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
          "महाराष्ट्रात टीबी रुग्णांचा उपचार यश दर किती टक्के आहे?",
          "SELECT AVG(treatment_success_rate_pct) FROM ndap_national_tuberculosis_portal WHERE state_name = 'MAHARASHTRA';",
          ["treatment_success_rate_pct", "state_name"])

    add_q("indicdb-mr-010", "mr", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "medium",
          "महाराष्ट्रात मनरेगा अंतर्गत महिलांचे मनुष्यदिन किती टक्के आहेत?",
          "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'MAHARASHTRA';",
          ["women_mandays_pct", "state_name"])

    add_q("indicdb-mr-011", "mr", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
          "महाराष्ट्रात बालकांचे पूर्ण लसीकरण प्रमाण कोणत्या जिल्ह्यात सर्वात जास्त आहे?",
          "SELECT district_name, fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'MAHARASHTRA' ORDER BY fully_vaccinated_children_pct DESC LIMIT 1;",
          ["district_name", "fully_vaccinated_children_pct", "state_name"])

    add_q("indicdb-mr-012", "mr", "Devanagari", "Agriculture", "ndap_soil_health_records", "easy",
          "महाराष्ट्रात एकूण किती माती आरोग्य पत्रिका वाटप करण्यात आल्या?",
          "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'MAHARASHTRA';",
          ["cards_issued", "state_name"])

    add_q("indicdb-mr-013", "mr", "Devanagari", "Education", "ndap_midday_meal_scheme", "medium",
          "महाराष्ट्रात प्राथमिक वर्गातील किती विद्यार्थ्यांना माध्यान्ह भोजन मिळाले?",
          "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'MAHARASHTRA';",
          ["primary_students_benefited", "state_name"])

    add_q("indicdb-mr-014", "mr", "Devanagari", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "महाराष्ट्रात पीएमजीएसवाय अंतर्गत किती लांबीचे रस्ते पूर्ण झाले आहेत?",
          "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'MAHARASHTRA';",
          ["completed_road_length_km", "state_name"])

    add_q("indicdb-mr-015", "mr", "Devanagari", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "महाराष्ट्रात ग्रामपंचायतींना एकूण किती अनुदान वितरित झाले आणि किती खर्च झाले?",
          "SELECT SUM(grant_allocated_inr) AS total_allocated, SUM(grant_utilized_inr) AS total_utilized FROM ndap_gram_panchayat_finance WHERE state_name = 'MAHARASHTRA';",
          ["grant_allocated_inr", "grant_utilized_inr", "state_name"])

    # =========================================================================
    # 2. HINDI (hi) - 15 Queries
    # =========================================================================
    add_q("indicdb-hi-001", "hi", "Devanagari", "Education", "ndap_education_stats", "hard",
          "बिहार के किस जिले में सबसे कम महिला साक्षरता दर दर्ज की गई?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-hi-002", "hi", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "उत्तर प्रदेश में यूरिया उर्वरक की कुल बिक्री कितनी रही?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'UTTAR PRADESH' AND fertilizer_type = 'UREA';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-hi-003", "hi", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "easy",
          "मध्य प्रदेश में आयुष्मान भारत योजना के तहत कितने कार्ड जारी किए गए?",
          "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MADHYA PRADESH';",
          ["cards_issued", "state_name"])

    add_q("indicdb-hi-004", "hi", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "उत्तर प्रदेश में पीएम किसान योजना के कुल कितने लाभार्थी हैं?",
          "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH';",
          ["farmer_beneficiaries", "state_name"])

    add_q("indicdb-hi-005", "hi", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "राजस्थान में मनरेगा के तहत कुल कितने मानव दिवस सृजित किए गए?",
          "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'RAJASTHAN' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["total_mandays_generated", "state_name", "financial_year"])

    add_q("indicdb-hi-006", "hi", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
          "बिहार में संस्थागत प्रसव का औसत प्रतिशत कितना है?",
          "SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'BIHAR';",
          ["institutional_births_pct", "state_name"])

    add_q("indicdb-hi-007", "hi", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
          "मध्य प्रदेश में गेहूं का कुल उत्पादन कितना हुआ?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MADHYA PRADESH' AND crop_name = 'WHEAT';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-hi-008", "hi", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
          "पटना जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?",
          "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'BIHAR' AND district_name = 'Patna';",
          ["schools_with_electricity", "state_name", "district_name"])

    add_q("indicdb-hi-009", "hi", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "hard",
          "उत्तर प्रदेश में वित्तीय वर्ष के अनुसार कितने ग्रामीण आवास स्वीकृत हुए?",
          "SELECT financial_year, SUM(houses_sanctioned) FROM ndap_pmay_rural_housing WHERE state_name = 'UTTAR PRADESH' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["houses_sanctioned", "state_name", "financial_year"])

    add_q("indicdb-hi-010", "hi", "Devanagari", "Healthcare", "ndap_maternal_child_mortality", "easy",
          "उत्तर प्रदेश में मातृ मृत्यु अनुपात (MMR) कितना दर्ज किया गया?",
          "SELECT maternal_mortality_ratio_mmr FROM ndap_maternal_child_mortality WHERE state_name = 'UTTAR PRADESH';",
          ["maternal_mortality_ratio_mmr", "state_name"])

    add_q("indicdb-hi-011", "hi", "Devanagari", "Education", "ndap_vocational_skill_training", "medium",
          "राजस्थान में कौशल प्रशिक्षण के तहत कितने उम्मीदवारों को रोजगार मिला?",
          "SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'RAJASTHAN';",
          ["placed_candidates", "state_name"])

    add_q("indicdb-hi-012", "hi", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "वाराणसी जिले में कितने ग्रामीण घरों में नल कनेक्शन है?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'UTTAR PRADESH' AND district_name = 'Varanasi';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-hi-013", "hi", "Devanagari", "Healthcare", "ndap_rural_health_infrastructure", "easy",
          "बिहार में कुल कितने प्राथमिक स्वास्थ्य केंद्र (PHC) कार्यरत हैं?",
          "SELECT primary_health_centres_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'BIHAR';",
          ["primary_health_centres_phc", "state_name"])

    add_q("indicdb-hi-014", "hi", "Devanagari", "Agriculture", "ndap_soil_health_records", "medium",
          "उत्तर प्रदेश में मिट्टी के कितने नमूनों की जांच की गई?",
          "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'UTTAR PRADESH';",
          ["samples_tested", "state_name"])

    add_q("indicdb-hi-015", "hi", "Devanagari", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "बिहार में ग्राम पंचायतों द्वारा स्वच्छता पर कुल कितना खर्च किया गया?",
          "SELECT SUM(sanitation_drinking_water_expenditure_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'BIHAR';",
          ["sanitation_drinking_water_expenditure_inr", "state_name"])

    # =========================================================================
    # 3. HINGLISH (hi-en) - 15 Queries
    # =========================================================================
    add_q("indicdb-hien-001", "hi-en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "Maharashtra mein pichle saal kitne kisano ne PM-Kisan yojana ka fayda liya?",
          "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
          ["farmer_beneficiaries", "amount_inr", "state_name"])

    add_q("indicdb-hien-002", "hi-en", "Latin", "Education", "ndap_education_stats", "hard",
          "Bihar ke kis district mein female literacy sabse kam hai?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-hien-003", "hi-en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "medium",
          "Rajasthan mein total kitne pucca houses PMAY ke under complete hue?",
          "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'RAJASTHAN';",
          ["houses_completed", "state_name"])

    add_q("indicdb-hien-004", "hi-en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "easy",
          "Madhya Pradesh mein Ayushman Bharat ke kitne golden cards issue hue?",
          "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MADHYA PRADESH';",
          ["cards_issued", "state_name"])

    add_q("indicdb-hien-005", "hi-en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "Tamil Nadu mein MGNREGA ke under total kitne person-days create hue?",
          "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["total_mandays_generated", "state_name", "financial_year"])

    add_q("indicdb-hien-006", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
          "Gujarat mein Groundnut ya Cotton ka total production kitna hua?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'GUJARAT' AND crop_name = 'COTTON';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-hien-007", "hi-en", "Latin", "Education", "ndap_school_infrastructure", "easy",
          "Pune district mein kitne schools mein functional computer labs hain?",
          "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
          ["schools_with_computer_labs", "state_name", "district_name"])

    add_q("indicdb-hien-008", "hi-en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "Madurai district mein kitne rural households ko functional tap water mila?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-hien-009", "hi-en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "Uttar Pradesh mein Urea fertilizer ki total sales kitni thi?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'UTTAR PRADESH' AND fertilizer_type = 'UREA';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-hien-010", "hi-en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
          "Bihar ke districts mein average child stunting percentage kitna hai?",
          "SELECT AVG(stunted_children_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'BIHAR';",
          ["stunted_children_pct", "state_name"])

    add_q("indicdb-hien-011", "hi-en", "Latin", "Education", "ndap_midday_meal_scheme", "medium",
          "West Bengal mein Mid-Day Meal scheme se primary school ke kitne bache benefit hue?",
          "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'WEST BENGAL';",
          ["primary_students_benefited", "state_name"])

    add_q("indicdb-hien-012", "hi-en", "Latin", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
          "Maharashtra mein total kitne TB cases notify kiye gaye?",
          "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'MAHARASHTRA';",
          ["total_notified_patients", "state_name"])

    add_q("indicdb-hien-013", "hi-en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "Andhra Pradesh mein PMGSY ke under kitne km rural roads complete hui?",
          "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'ANDHRA PRADESH';",
          ["completed_road_length_km", "state_name"])

    add_q("indicdb-hien-014", "hi-en", "Latin", "Education", "ndap_higher_education_aishe", "easy",
          "Karnataka mein AISHE survey ke mutabiq total kitni universities hain?",
          "SELECT university_count FROM ndap_higher_education_aishe WHERE state_name = 'KARNATAKA';",
          ["university_count", "state_name"])

    add_q("indicdb-hien-015", "hi-en", "Latin", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "Rajasthan mein gram panchayats ne total kitna grant utilize kiya?",
          "SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'RAJASTHAN';",
          ["grant_utilized_inr", "state_name"])

    # =========================================================================
    # 4. TAMIL (ta) - 15 Queries
    # =========================================================================
    add_q("indicdb-ta-001", "ta", "Tamil", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "தமிழ்நாட்டில் மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் எத்தனை மனித வேலை நாட்கள் உருவாக்கப்பட்டன?",
          "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["total_mandays_generated", "state_name", "financial_year"])

    add_q("indicdb-ta-002", "ta", "Tamil", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "மதுரை மாவட்டத்தில் எத்தனை கிராமப்புற வீடுகளுக்கு குடிநீர் குழாய் இணைப்பு வழங்கப்பட்டுள்ளது?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-ta-003", "ta", "Tamil", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "தமிழ்நாட்டில் பிஎம் கிசான் திட்டத்தின் கீழ் வழங்கப்பட்ட மொத்த நிதி எவ்வளவு?",
          "SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement WHERE state_name = 'TAMIL NADU';",
          ["amount_inr", "state_name"])

    add_q("indicdb-ta-004", "ta", "Tamil", "Agriculture", "ndap_crop_production_census", "medium",
          "தமிழ்நாட்டில் நெல் பயிரின் மொத்த உற்பத்தி எத்தனை டன்கள்?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'TAMIL NADU' AND crop_name = 'RICE';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-ta-005", "ta", "Tamil", "Education", "ndap_school_infrastructure", "easy",
          "கோயம்புத்தூர் மாவட்டத்தில் மின்சார வசதி உள்ள பள்ளிகள் எத்தனை?",
          "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';",
          ["schools_with_electricity", "state_name", "district_name"])

    add_q("indicdb-ta-006", "ta", "Tamil", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
          "தமிழ்நாட்டில் பதிவு செய்யப்பட்ட மருத்துவமனைகளின் எண்ணிக்கை எவ்வளவு?",
          "SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'TAMIL NADU';",
          ["empanelled_hospitals", "state_name"])

    add_q("indicdb-ta-007", "ta", "Tamil", "Rural Development", "ndap_pmay_rural_housing", "hard",
          "தமிழ்நாட்டில் பிஎம்ஏஒய் கீழ் கட்டி முடிக்கப்பட்ட கிராமப்புற வீடுகள் எத்தனை?",
          "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'TAMIL NADU';",
          ["houses_completed", "state_name"])

    add_q("indicdb-ta-008", "ta", "Tamil", "Education", "ndap_education_stats", "hard",
          "தமிழ்நாட்டில் பெண் எழுத்தறிவு விகிதம் எந்த மாவட்டத்தில் மிக அதிகமாக உள்ளது?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'TAMIL NADU' ORDER BY female_literacy_rate DESC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-ta-009", "ta", "Tamil", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
          "தமிழ்நாட்டில் மருத்துவமனை பிரசவங்களின் சராசரி சதவீதம் என்ன?",
          "SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'TAMIL NADU';",
          ["institutional_births_pct", "state_name"])

    add_q("indicdb-ta-010", "ta", "Tamil", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "தமிழ்நாட்டில் யூரியா உரத்தின் மொத்த விற்பனை எத்தனை டன்கள்?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'TAMIL NADU' AND fertilizer_type = 'UREA';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-ta-011", "ta", "Tamil", "Healthcare", "ndap_maternal_child_mortality", "easy",
          "தமிழ்நாட்டில் தாய்மார்கள் இறப்பு விகிதம் (MMR) என்னவாக உள்ளது?",
          "SELECT maternal_mortality_ratio_mmr FROM ndap_maternal_child_mortality WHERE state_name = 'TAMIL NADU';",
          ["maternal_mortality_ratio_mmr", "state_name"])

    add_q("indicdb-ta-012", "ta", "Tamil", "Education", "ndap_higher_education_aishe", "easy",
          "தமிழ்நாட்டில் உள்ள மொத்த பல்கலைக்கழகங்களின் எண்ணிக்கை எவ்வளவு?",
          "SELECT university_count FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';",
          ["university_count", "state_name"])

    add_q("indicdb-ta-013", "ta", "Tamil", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "தமிழ்நாட்டில் கிராம சாலைகள் திட்டத்தின் கீழ் இணைக்கப்பட்ட குடியிருப்புகள் எத்தனை?",
          "SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE state_name = 'TAMIL NADU';",
          ["habitations_connected", "state_name"])

    add_q("indicdb-ta-014", "ta", "Tamil", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
          "தமிழ்நாட்டில் காசநோய் சிகிச்சை வெற்றி சதவீதம் சராசரியாக என்ன?",
          "SELECT AVG(treatment_success_rate_pct) FROM ndap_national_tuberculosis_portal WHERE state_name = 'TAMIL NADU';",
          ["treatment_success_rate_pct", "state_name"])

    add_q("indicdb-ta-015", "ta", "Tamil", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "தமிழ்நாட்டில் கிராம ஊராட்சிகளுக்கு ஒதுக்கப்பட்ட மொத்த நிதி எவ்வளவு?",
          "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'TAMIL NADU';",
          ["grant_allocated_inr", "state_name"])

    # =========================================================================
    # 5. TELUGU (te) - 15 Queries
    # =========================================================================
    add_q("indicdb-te-001", "te", "Telugu", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "ఆంధ్రప్రదేశ్ రాష్ట్రంలో పీఎం-కిసాన్ పథకం ద్వారా ఎంత మొత్తం నిధులు విడుదలయ్యాయి?",
          "SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement WHERE state_name = 'ANDHRA PRADESH';",
          ["amount_inr", "state_name"])

    add_q("indicdb-te-002", "te", "Telugu", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "విశాఖపట్నం జిల్లాలో పీఎంజీఎస్వై కింద పూర్తయిన రోడ్ల పొడవు ఎంత?",
          "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Visakhapatnam';",
          ["completed_road_length_km", "state_name", "district_name"])

    add_q("indicdb-te-003", "te", "Telugu", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "గుంటూరు జిల్లాలో ఎన్ని ఇళ్లకు తాగునీటి కుళాయి కనెక్షన్లు ఉన్నాయి?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Guntur';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-te-004", "te", "Telugu", "Healthcare", "ndap_ayushman_bharat_pmjay", "easy",
          "ఆంధ్రప్రదేశ్ లో ఎంత క్లెయిమ్ మొత్తం చెల్లించబడింది?",
          "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'ANDHRA PRADESH';",
          ["claim_amount_settled_inr", "state_name"])

    add_q("indicdb-te-005", "te", "Telugu", "Agriculture", "ndap_crop_production_census", "medium",
          "ఆంధ్రప్రదేశ్ లో వరి పంట మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ANDHRA PRADESH' AND crop_name = 'RICE';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-te-006", "te", "Telugu", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "ఆంధ్రప్రదేశ్ లో ఉపాధి హామీ పథకం కింద మహిళల పని దినాల శాతం ఎంత?",
          "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'ANDHRA PRADESH';",
          ["women_mandays_pct", "state_name"])

    add_q("indicdb-te-007", "te", "Telugu", "Education", "ndap_school_infrastructure", "easy",
          "కృష్ణా జిల్లాలో తాగునీటి సదుపాయం ఉన్న పాఠశాలలు ఎన్ని?",
          "SELECT SUM(schools_with_drinking_water) FROM ndap_school_infrastructure WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Krishna';",
          ["schools_with_drinking_water", "state_name", "district_name"])

    add_q("indicdb-te-008", "te", "Telugu", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
          "ఆంధ్రప్రదేశ్ లో పూర్తి టీకాలు పొందిన పిల్లల సగటు శాతం ఎంత?",
          "SELECT AVG(fully_vaccinated_children_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';",
          ["fully_vaccinated_children_pct", "state_name"])

    add_q("indicdb-te-009", "te", "Telugu", "Rural Development", "ndap_pmay_rural_housing", "medium",
          "ఆంధ్రప్రదేశ్ లో పీఎంఏవై గ్రామీణ కింద పూర్తయిన ఇళ్లు ఎన్ని?",
          "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'ANDHRA PRADESH';",
          ["houses_completed", "state_name"])

    add_q("indicdb-te-010", "te", "Telugu", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "ఆంధ్రప్రదేశ్ లో డీఏపీ ఎరువుల మొత్తం అమ్మకాలు ఎన్ని టన్నులు?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'ANDHRA PRADESH' AND fertilizer_type = 'DAP';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-te-011", "te", "Telugu", "Education", "ndap_education_stats", "hard",
          "ఆంధ్రప్రదేశ్ లో స్త్రీల అక్షరాస్యత రేటు అత్యధికంగా ఉన్న జిల్లా ఏది?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'ANDHRA PRADESH' ORDER BY female_literacy_rate DESC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-te-012", "te", "Telugu", "Healthcare", "ndap_maternal_child_mortality", "easy",
          "ఆంధ్రప్రదేశ్ లో శిశు మరణాల రేటు (IMR) ఎంత?",
          "SELECT infant_mortality_rate_imr FROM ndap_maternal_child_mortality WHERE state_name = 'ANDHRA PRADESH';",
          ["infant_mortality_rate_imr", "state_name"])

    add_q("indicdb-te-013", "te", "Telugu", "Agriculture", "ndap_soil_health_records", "easy",
          "ఆంధ్రప్రదేశ్ లో రైతులకు జారీ చేయబడిన సాయిల్ హెల్త్ కార్డులు ఎన్ని?",
          "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'ANDHRA PRADESH';",
          ["cards_issued", "state_name"])

    add_q("indicdb-te-014", "te", "Telugu", "Healthcare", "ndap_rural_health_infrastructure", "easy",
          "ఆంధ్రప్రదేశ్ లో ఎన్ని ప్రాథమిక ఆరోగ్య కేంద్రాలు (PHC) పనిచేస్తున్నాయి?",
          "SELECT primary_health_centres_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'ANDHRA PRADESH';",
          ["primary_health_centres_phc", "state_name"])

    add_q("indicdb-te-015", "te", "Telugu", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "ఆంధ్రప్రదేశ్ లో పంచాయతీలు ఉపయోగించిన మొత్తం గ్రాంట్ ఎంత?",
          "SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'ANDHRA PRADESH';",
          ["grant_utilized_inr", "state_name"])

    # =========================================================================
    # 6. BENGALI (bn) - 15 Queries
    # =========================================================================
    add_q("indicdb-bn-001", "bn", "Bengali", "Agriculture", "ndap_crop_production_census", "medium",
          "পশ্চিমবঙ্গে মোট চাল উৎপাদনের পরিমাণ কত টন?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'WEST BENGAL' AND crop_name = 'RICE';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-bn-002", "bn", "Bengali", "Education", "ndap_midday_meal_scheme", "easy",
          "মুর্শিদাবাদ জেলায় প্রাথমিকে মিড-ডে মিলের মাধ্যমে কতজন শিক্ষার্থী উপকৃত হয়েছে?",
          "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'WEST BENGAL' AND district_name = 'Murshidabad';",
          ["primary_students_benefited", "state_name", "district_name"])

    add_q("indicdb-bn-003", "bn", "Bengali", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "পশ্চিমবঙ্গে পিএম-কিষাণ প্রকল্পে কতজন কৃষক উপকৃত হয়েছেন?",
          "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'WEST BENGAL';",
          ["farmer_beneficiaries", "state_name"])

    add_q("indicdb-bn-004", "bn", "Bengali", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "পশ্চিমবঙ্গে একশো দিনের কাজে কত মানবদিবস তৈরি হয়েছে?",
          "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'WEST BENGAL' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["total_mandays_generated", "state_name", "financial_year"])

    add_q("indicdb-bn-005", "bn", "Bengali", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "মালদা জেলায় কতগুলি গ্রামীণ পরিবারে পানীয় জলের সংযোগ রয়েছে?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'WEST BENGAL' AND district_name = 'Malda';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-bn-006", "bn", "Bengali", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
          "পশ্চিমবঙ্গে কতজন রোগী হাসপাতালে ভর্তি হয়েছেন?",
          "SELECT SUM(authorized_admissions) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'WEST BENGAL';",
          ["authorized_admissions", "state_name"])

    add_q("indicdb-bn-007", "bn", "Bengali", "Education", "ndap_school_infrastructure", "easy",
          "পশ্চিমবঙ্গে কতগুলি স্কুলে ছাত্রীদের পৃথক শৌচাগার রয়েছে?",
          "SELECT SUM(schools_with_girl_toilets) FROM ndap_school_infrastructure WHERE state_name = 'WEST BENGAL';",
          ["schools_with_girl_toilets", "state_name"])

    add_q("indicdb-bn-008", "bn", "Bengali", "Education", "ndap_education_stats", "hard",
          "পশ্চিমবঙ্গের কোন জেলায় নারী সাক্ষরতার হার সবচেয়ে কম?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'WEST BENGAL' ORDER BY female_literacy_rate ASC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-bn-009", "bn", "Bengali", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
          "পশ্চিমবঙ্গে রক্তাল্পতায় ভোগা মহিলাদের গড় শতাংশ কত?",
          "SELECT AVG(anaemic_women_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'WEST BENGAL';",
          ["anaemic_women_pct", "state_name"])

    add_q("indicdb-bn-010", "bn", "Bengali", "Rural Development", "ndap_pmay_rural_housing", "hard",
          "পশ্চিমবঙ্গে আর্থিক বছর অনুযায়ী কতগুলি গ্রামীণ বাড়ি তৈরি হয়েছে?",
          "SELECT financial_year, SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'WEST BENGAL' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["houses_completed", "state_name", "financial_year"])

    add_q("indicdb-bn-011", "bn", "Bengali", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "পশ্চিমবঙ্গে ইউরিয়া সারের মোট বিক্রির পরিমাণ কত টন?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'WEST BENGAL' AND fertilizer_type = 'UREA';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-bn-012", "bn", "Bengali", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
          "পশ্চিমবঙ্গে মোট কতজন যক্ষ্মা রোগী নথিভুক্ত হয়েছেন?",
          "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'WEST BENGAL';",
          ["total_notified_patients", "state_name"])

    add_q("indicdb-bn-013", "bn", "Bengali", "Education", "ndap_higher_education_aishe", "easy",
          "পশ্চিমবঙ্গে উচ্চশিক্ষায় মোট অধ্যাপকের সংখ্যা কত?",
          "SELECT total_faculty_count FROM ndap_higher_education_aishe WHERE state_name = 'WEST BENGAL';",
          ["total_faculty_count", "state_name"])

    add_q("indicdb-bn-014", "bn", "Bengali", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "পশ্চিমবঙ্গে পিএমজিএসওয়াই প্রকল্পে কত কিমি পাকা রাস্তা নির্মিত হয়েছে?",
          "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'WEST BENGAL';",
          ["completed_road_length_km", "state_name"])

    add_q("indicdb-bn-015", "bn", "Bengali", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "পশ্চিমবঙ্গে গ্রাম পঞ্চায়েতগুলির জন্য মোট কত টাকা বরাদ্দ করা হয়েছিল?",
          "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'WEST BENGAL';",
          ["grant_allocated_inr", "state_name"])

    # =========================================================================
    # 7. ENGLISH (en) - 15 Queries
    # =========================================================================
    add_q("indicdb-en-001", "en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
          "What is the total number of farmer beneficiaries under PM-KISAN in Maharashtra?",
          "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
          ["farmer_beneficiaries", "amount_inr", "state_name"])

    add_q("indicdb-en-002", "en", "Latin", "Education", "ndap_education_stats", "hard",
          "Which district in Bihar had the lowest female literacy rate?",
          "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
          ["district_name", "female_literacy_rate", "state_name"])

    add_q("indicdb-en-003", "en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "hard",
          "How many mandays were generated under MGNREGA in Tamil Nadu by financial year?",
          "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' GROUP BY financial_year ORDER BY financial_year DESC;",
          ["total_mandays_generated", "state_name", "financial_year"])

    add_q("indicdb-en-004", "en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "easy",
          "What is the total number of Ayushman Bharat cards issued in Madhya Pradesh?",
          "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MADHYA PRADESH';",
          ["cards_issued", "state_name"])

    add_q("indicdb-en-005", "en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
          "What was the total production of Cotton in tonnes in Maharashtra?",
          "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND crop_name = 'COTTON';",
          ["production_tonnes", "state_name", "crop_name"])

    add_q("indicdb-en-006", "en", "Latin", "Education", "ndap_school_infrastructure", "easy",
          "How many schools in Pune district are equipped with computer labs?",
          "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
          ["schools_with_computer_labs", "state_name", "district_name"])

    add_q("indicdb-en-007", "en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
          "How many rural households in Madurai district have functional tap water connections?",
          "SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
          ["households_with_tap_connection", "state_name", "district_name"])

    add_q("indicdb-en-008", "en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
          "What is the total sales quantity of Urea fertilizer in Uttar Pradesh?",
          "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'UTTAR PRADESH' AND fertilizer_type = 'UREA';",
          ["sales_tonnes", "state_name", "fertilizer_type"])

    add_q("indicdb-en-009", "en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "medium",
          "How many rural houses were completed under PMAY in Rajasthan?",
          "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'RAJASTHAN';",
          ["houses_completed", "state_name"])

    add_q("indicdb-en-010", "en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
          "Which district in Maharashtra has the highest fully vaccinated children percentage?",
          "SELECT district_name, fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'MAHARASHTRA' ORDER BY fully_vaccinated_children_pct DESC LIMIT 1;",
          ["district_name", "fully_vaccinated_children_pct", "state_name"])

    add_q("indicdb-en-011", "en", "Latin", "Education", "ndap_higher_education_aishe", "easy",
          "What is the total number of chartered universities in Karnataka?",
          "SELECT university_count FROM ndap_higher_education_aishe WHERE state_name = 'KARNATAKA';",
          ["university_count", "state_name"])

    add_q("indicdb-en-012", "en", "Latin", "Healthcare", "ndap_maternal_child_mortality", "easy",
          "What is the maternal mortality ratio (MMR) recorded in Uttar Pradesh?",
          "SELECT maternal_mortality_ratio_mmr FROM ndap_maternal_child_mortality WHERE state_name = 'UTTAR PRADESH';",
          ["maternal_mortality_ratio_mmr", "state_name"])

    add_q("indicdb-en-013", "en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
          "What is the total length of completed rural roads under PMGSY in Andhra Pradesh?",
          "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'ANDHRA PRADESH';",
          ["completed_road_length_km", "state_name"])

    add_q("indicdb-en-014", "en", "Latin", "Agriculture", "ndap_soil_health_records", "easy",
          "How many Soil Health Cards were issued to farmers in Maharashtra?",
          "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'MAHARASHTRA';",
          ["cards_issued", "state_name"])

    add_q("indicdb-en-015", "en", "Latin", "Rural Development", "ndap_gram_panchayat_finance", "hard",
          "What is the total grant allocated and utilized by Gram Panchayats in Maharashtra?",
          "SELECT SUM(grant_allocated_inr) AS total_allocated, SUM(grant_utilized_inr) AS total_utilized FROM ndap_gram_panchayat_finance WHERE state_name = 'MAHARASHTRA';",
          ["grant_allocated_inr", "grant_utilized_inr", "state_name"])

    return queries


def main():
    print("Building and validating 105 IndicDB benchmark queries...")
    items = build_benchmark_items()
    print(f"Total compiled items: {len(items)}")

    # Verify execution against DuckDB sandbox
    sandbox = DuckDBSandbox()
    failed = 0
    for i, it in enumerate(items, start=1):
        sql = it["gold_sql"]
        res = sandbox.execute_query(sql)
        if not res or not res.get("columns"):
            print(f"[FAIL #{i}] {it['query_id']} SQL failed: {sql}")
            failed += 1

    if failed > 0:
        print(f"Validation FAILED with {failed} errors!")
        sys.exit(1)

    print(f"All {len(items)} queries executed successfully on authentic NDAP Parquet databases!")

    # Write output JSON
    out_path = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_expanded.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved expanded benchmark suite to: {out_path}")


if __name__ == "__main__":
    main()
