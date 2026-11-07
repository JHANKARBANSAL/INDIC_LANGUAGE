#!/usr/bin/env python3
"""
Comprehensive Pan-India 280-Query IndicDB Benchmark Suite Generator.
Constructs and strictly validates 280 diverse evaluation instances
(40 queries x 7 Indic/English languages = 280 queries)
covering all 36 States & Union Territories of India across 20 authentic NDAP databases.

Validates each query against DuckDBSandbox to guarantee 100% execution validity.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.sandbox.duckdb_engine import DuckDBSandbox


def build_pan_india_280_items():
    queries = []

    def add(qid, lang, script, domain, table, difficulty, query_text, gold_sql, cols):
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
    # 1. HINDI (hi) - 40 Queries
    # =========================================================================
    # Agriculture & PM-KISAN
    add("indicdb-hi-001", "hi", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "उत्तर प्रदेश में कुल कितने किसानों को पीएम-किसान का लाभ मिला?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-hi-002", "hi", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
        "बिहार में पीएम-किसान के तहत कुल कितनी धनराशि वितरित की गई?",
        "SELECT SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'BIHAR';",
        ["amount_inr", "state_name"])
    add("indicdb-hi-003", "hi", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "पंजाब में गेहूं का कुल उत्पादन कितने टन हुआ?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'PUNJAB' AND crop_name = 'WHEAT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-hi-004", "hi", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "मध्य प्रदेश में सोयाबीन की खेती का कुल क्षेत्रफल कितने हेक्टेयर है?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'MADHYA PRADESH' AND crop_name = 'SOYBEAN';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-hi-005", "hi", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "हरियाणा में यूरिया खाद की कुल बिक्री कितनी हुई?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'HARYANA' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-hi-006", "hi", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "easy",
        "राजस्थान में डीएपी खाद की कुल आवश्यकता कितने टन थी?",
        "SELECT SUM(requirement_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'RAJASTHAN' AND fertilizer_type = 'DAP';",
        ["requirement_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-hi-007", "hi", "Devanagari", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "उत्तर प्रदेश की मंडियों में गेहूं का औसत मॉडल मूल्य क्या रहा?",
        "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'UTTAR PRADESH' AND commodity = 'Wheat';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-hi-008", "hi", "Devanagari", "Agriculture", "ndap_soil_health_records", "easy",
        "हिमाचल प्रदेश में कुल कितने मृदा स्वास्थ्य कार्ड जारी किए गए?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'HIMACHAL PRADESH';",
        ["cards_issued", "state_name"])

    # Education & Literacy
    add("indicdb-hi-009", "hi", "Devanagari", "Education", "ndap_education_stats", "hard",
        "बिहार के किस जिले में महिला साक्षरता दर सबसे कम है?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-hi-010", "hi", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
        "उत्तराखंड में बिजली सुविधा वाले कुल कितने स्कूल हैं?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'UTTARAKHAND';",
        ["schools_with_electricity", "state_name"])
    add("indicdb-hi-011", "hi", "Devanagari", "Education", "ndap_school_infrastructure", "medium",
        "दिल्ली में कंप्यूटर लैब वाले स्कूलों की कुल संख्या क्या है?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'DELHI';",
        ["schools_with_computer_labs", "state_name"])
    add("indicdb-hi-012", "hi", "Devanagari", "Education", "ndap_midday_meal_scheme", "medium",
        "झारखंड में मध्याह्न भोजन योजना से लाभान्वित प्राथमिक छात्रों की कुल संख्या कितनी है?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'JHARKHAND';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-hi-013", "hi", "Devanagari", "Education", "ndap_higher_education_aishe", "easy",
        "मध्य प्रदेश में कुल कितने पंजीकृत कॉलेज हैं?",
        "SELECT SUM(college_count) FROM ndap_higher_education_aishe WHERE state_name = 'MADHYA PRADESH';",
        ["college_count", "state_name"])

    # Healthcare
    add("indicdb-hi-014", "hi", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "उत्तर प्रदेश में आयुष्मान भारत के तहत कुल कितने कार्ड जारी किए गए?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'UTTAR PRADESH';",
        ["cards_issued", "state_name"])
    add("indicdb-hi-015", "hi", "Devanagari", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "छत्तीसगढ़ में कुल कितने प्राथमिक स्वास्थ्य केंद्र संचालित हैं?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'CHHATTISGARH';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-hi-016", "hi", "Devanagari", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "बिहार में टीबी के कुल कितने मरीज अधिसूचित किए गए?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'BIHAR';",
        ["total_notified_patients", "state_name"])
    add("indicdb-hi-017", "hi", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
        "राजस्थान में संस्थागत प्रसव का औसत प्रतिशत क्या है?",
        "SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'RAJASTHAN';",
        ["institutional_births_pct", "state_name"])
    add("indicdb-hi-018", "hi", "Devanagari", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "मध्य प्रदेश में मातृ मृत्यु अनुपात एमएमआर कितना दर्ज किया गया?",
        "SELECT AVG(maternal_mortality_ratio_mmr) FROM ndap_maternal_child_mortality WHERE state_name = 'MADHYA PRADESH';",
        ["maternal_mortality_ratio_mmr", "state_name"])

    # Rural Development & Infrastructure
    add("indicdb-hi-019", "hi", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "उत्तर प्रदेश में मनरेगा के तहत कुल कितने मानव दिवस सृजित किए गए?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'UTTAR PRADESH';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-hi-020", "hi", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "बिहार में मनरेगा के तहत कुल मजदूरी व्यय कितना हुआ?",
        "SELECT SUM(total_wage_expenditure_inr) FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';",
        ["total_wage_expenditure_inr", "state_name"])
    add("indicdb-hi-021", "hi", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "मध्य प्रदेश में प्रधानमंत्री आवास योजना के कितने घर पूरे हुए?",
        "SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE state_name = 'MADHYA PRADESH';",
        ["houses_completed", "state_name"])
    add("indicdb-hi-022", "hi", "Devanagari", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "राजस्थान में पीएमजीएसवाई के तहत कुल कितनी सड़क लंबाई पूरी हुई?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'RAJASTHAN';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-hi-023", "hi", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "हरियाणा में नल जल कनेक्शन वाले कुल ग्रामीण परिवार कितने हैं?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'HARYANA';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-hi-024", "hi", "Devanagari", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "उत्तराखंड में ग्राम पंचायतों को कुल कितना अनुदान आवंटित किया गया?",
        "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'UTTARAKHAND';",
        ["grant_allocated_inr", "state_name"])
    add("indicdb-hi-025", "hi", "Devanagari", "Skill Development", "ndap_vocational_skill_training", "easy",
        "दिल्ली में व्यावसायिक प्रशिक्षण के तहत प्रमाणित उम्मीदवारों की कुल संख्या क्या है?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'DELHI';",
        ["certified_candidates", "state_name"])

    # UTs & Border States in Hindi
    add("indicdb-hi-026", "hi", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "जम्मू और कश्मीर में पीएम-किसान योजना के कुल कितने लाभार्थी हैं?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'JAMMU AND KASHMIR';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-hi-027", "hi", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "लद्दाख में आयुष्मान भारत के तहत कुल कितने अस्पताल सूचीबद्ध हैं?",
        "SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'LADAKH';",
        ["empanelled_hospitals", "state_name"])
    add("indicdb-hi-028", "hi", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
        "चंडीगढ़ में कुल कितने सरकारी और सहायता प्राप्त स्कूल हैं?",
        "SELECT SUM(total_schools) FROM ndap_school_infrastructure WHERE state_name = 'CHANDIGARH';",
        ["total_schools", "state_name"])
    add("indicdb-hi-029", "hi", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "असम में चावल का कुल उत्पादन कितने टन दर्ज किया गया?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ASSAM' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-hi-030", "hi", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "गोवा में नल जल कवरेज का औसत प्रतिशत क्या है?",
        "SELECT AVG(tap_connection_coverage_pct) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'GOA';",
        ["tap_connection_coverage_pct", "state_name"])

    # Multi-condition & Grouped Analytics
    add("indicdb-hi-031", "hi", "Devanagari", "Education", "ndap_school_infrastructure", "hard",
        "उत्तर प्रदेश के किस जिले में लड़कियों के शौचालय वाले स्कूल सबसे अधिक हैं?",
        "SELECT district_name, SUM(schools_with_girl_toilets) AS total_toilets FROM ndap_school_infrastructure WHERE state_name = 'UTTAR PRADESH' GROUP BY district_name ORDER BY total_toilets DESC LIMIT 1;",
        ["district_name", "schools_with_girl_toilets", "state_name"])
    add("indicdb-hi-032", "hi", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
        "बिहार में कुपोषित बच्चों के सबसे अधिक प्रतिशत वाले 3 जिले कौन से हैं?",
        "SELECT district_name, stunted_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'BIHAR' ORDER BY stunted_children_pct DESC LIMIT 3;",
        ["district_name", "stunted_children_pct", "state_name"])
    add("indicdb-hi-033", "hi", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "hard",
        "पंजाब में किस जिले में सबसे अधिक यूरिया बिक्री हुई?",
        "SELECT district_name, SUM(sales_tonnes) AS urea_sales FROM ndap_fertilizer_distribution WHERE state_name = 'PUNJAB' AND fertilizer_type = 'UREA' GROUP BY district_name ORDER BY urea_sales DESC LIMIT 1;",
        ["district_name", "sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-hi-034", "hi", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "झारखंड में पीएमएवाई के तहत कुल कितनी धनराशि हस्तांतरित की गई?",
        "SELECT SUM(funds_transferred_inr) FROM ndap_pmay_rural_housing WHERE state_name = 'JHARKHAND';",
        ["funds_transferred_inr", "state_name"])
    add("indicdb-hi-035", "hi", "Devanagari", "Skill Development", "ndap_vocational_skill_training", "medium",
        "उत्तर प्रदेश में कृषि क्षेत्र कौशल परिषद में कुल कितने उम्मीदवार नामांकित हुए?",
        "SELECT SUM(enrolled_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'UTTAR PRADESH' AND sector_skill_council = 'Agriculture';",
        ["enrolled_candidates", "state_name", "sector_skill_council"])
    add("indicdb-hi-036", "hi", "Devanagari", "Agriculture", "ndap_soil_health_records", "easy",
        "हरियाणा में जांचे गए कुल नमूनों की संख्या क्या है?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'HARYANA';",
        ["samples_tested", "state_name"])
    add("indicdb-hi-037", "hi", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "छत्तीसगढ़ में आयुष्मान भारत योजना के तहत कुल स्वीकृत क्लेम राशि कितनी है?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'CHHATTISGARH';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-hi-038", "hi", "Devanagari", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "हिमाचल प्रदेश में पीएमजीएसवाई से जुड़ी कुल बस्तियों की संख्या क्या है?",
        "SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE state_name = 'HIMACHAL PRADESH';",
        ["habitations_connected", "state_name"])
    add("indicdb-hi-039", "hi", "Devanagari", "Agriculture", "ndap_crop_production_census", "easy",
        "उत्तराखंड में कुल फसल उत्पादन कितने टन हुआ?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'UTTARAKHAND';",
        ["production_tonnes", "state_name"])
    add("indicdb-hi-040", "hi", "Devanagari", "Education", "ndap_education_stats", "easy",
        "दिल्ली के स्कूलों में कुल कितने छात्र नामांकित हैं?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'DELHI';",
        ["student_count", "state_name"])

    # =========================================================================
    # 2. MARATHI (mr) - 40 Queries
    # =========================================================================
    add("indicdb-mr-001", "mr", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "महाराष्ट्रात पीएम-किसान योजनेचा लाभ एकूण किती शेतकऱ्यांना मिळाला?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-mr-002", "mr", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "महाराष्ट्रात कापूस पिकाचे एकूण उत्पादन किती टन झाले?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND crop_name = 'COTTON';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-mr-003", "mr", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "महाराष्ट्रात ऊसाची लागवड किती हेक्टर क्षेत्रावर झाली?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND crop_name = 'SUGARCANE';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-mr-004", "mr", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
        "पुणे जिल्ह्यातील शाळांमध्ये संगणक प्रयोगशाळा किती आहेत?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-mr-005", "mr", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "महाराष्ट्रात आयुष्यमान भारत अंतर्गत किती क्लेम रक्कम मंजूर झाली?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MAHARASHTRA';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-mr-006", "mr", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "महाराष्ट्रातील कोणत्या जिल्ह्यात प्रधानमंत्री आवास योजनेअंतर्गत सर्वाधिक घरे पूर्ण झाली?",
        "SELECT district_name, SUM(houses_completed) AS total_completed FROM ndap_pmay_rural_housing WHERE state_name = 'MAHARASHTRA' GROUP BY district_name ORDER BY total_completed DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-mr-007", "mr", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "महाराष्ट्रात युरिया खताची एकूण विक्री किती टन झाली?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'MAHARASHTRA' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-mr-008", "mr", "Devanagari", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "महाराष्ट्रातील बाजार समित्यांमध्ये कांद्याचा सरासरी भाव काय राहिला?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Onion';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-mr-009", "mr", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "महाराष्ट्रात मनरेगा योजनेअंतर्गत एकूण किती मनुष्य दिन रोजगार निर्माण झाला?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'MAHARASHTRA';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-mr-010", "mr", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
        "महाराष्ट्रात सर्वात कमी बाल कुपोषण प्रमाण कोणत्या जिल्ह्यात आहे?",
        "SELECT district_name, stunted_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'MAHARASHTRA' ORDER BY stunted_children_pct ASC LIMIT 1;",
        ["district_name", "stunted_children_pct", "state_name"])
    add("indicdb-mr-011", "mr", "Devanagari", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "महाराष्ट्रात एकूण किती प्राथमिक आरोग्य केंद्र (PHC) कार्यरत आहेत?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'MAHARASHTRA';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-mr-012", "mr", "Devanagari", "Education", "ndap_education_stats", "medium",
        "नागपूर जिल्ह्यातील एकूण विद्यार्थी संख्या किती आहे?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'MAHARASHTRA' AND district_name = 'Nagpur';",
        ["student_count", "state_name", "district_name"])
    add("indicdb-mr-013", "mr", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "महाराष्ट्रात नळजोडणी मिळालेल्या एकूण ग्रामीण कुटुंबांची संख्या काय आहे?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'MAHARASHTRA';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-mr-014", "mr", "Devanagari", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "महाराष्ट्रात ग्रामीण रस्ते योजनेअंतर्गत किती किमी लांबीचे रस्ते बांधून पूर्ण झाले?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'MAHARASHTRA';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-mr-015", "mr", "Devanagari", "Skill Development", "ndap_vocational_skill_training", "medium",
        "महाराष्ट्रात ऑटोमोटिव्ह क्षेत्रात किती उमेदवारांना रोजगार मिळाला?",
        "SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'MAHARASHTRA' AND sector_skill_council = 'Automotive';",
        ["placed_candidates", "state_name", "sector_skill_council"])
    add("indicdb-mr-016", "mr", "Devanagari", "Education", "ndap_school_infrastructure", "medium",
        "नाशिक जिल्ह्यातील पिण्याचे पाणी सुविधा असलेल्या शाळांची संख्या किती?",
        "SELECT SUM(schools_with_drinking_water) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Nashik';",
        ["schools_with_drinking_water", "state_name", "district_name"])
    add("indicdb-mr-017", "mr", "Devanagari", "Agriculture", "ndap_soil_health_records", "easy",
        "महाराष्ट्रात तपासलेल्या माती नमुन्यांची एकूण संख्या किती?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'MAHARASHTRA';",
        ["samples_tested", "state_name"])
    add("indicdb-mr-018", "mr", "Devanagari", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "महाराष्ट्रात टीबी उपचारांचा यशस्वी दर किती टक्के आहे?",
        "SELECT AVG(treatment_success_rate_pct) FROM ndap_national_tuberculosis_portal WHERE state_name = 'MAHARASHTRA';",
        ["treatment_success_rate_pct", "state_name"])
    add("indicdb-mr-019", "mr", "Devanagari", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "महाराष्ट्रातील ग्रामपंचायतींनी वापरलेला एकूण निधी किती रुपये आहे?",
        "SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'MAHARASHTRA';",
        ["grant_utilized_inr", "state_name"])
    add("indicdb-mr-020", "mr", "Devanagari", "Education", "ndap_midday_meal_scheme", "medium",
        "महाराष्ट्रात शालेय पोषण आहारासाठी किती मेट्रिक टन अन्नधान्य वाटप झाले?",
        "SELECT SUM(foodgrains_allocated_mt) FROM ndap_midday_meal_scheme WHERE state_name = 'MAHARASHTRA';",
        ["foodgrains_allocated_mt", "state_name"])

    # Additional pan-India queries in Marathi
    add("indicdb-mr-021", "mr", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "गुजरातमध्ये भुईमुगाचे एकूण उत्पादन किती टन झाले?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'GUJARAT' AND crop_name = 'GROUNDNUT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-mr-022", "mr", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "गोवा राज्यात पीएम-किसानचे एकूण लाभार्थी शेतकरी किती आहेत?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'GOA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-mr-023", "mr", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "कर्नाटक राज्यात किती रुग्णालये आयुष्यमान भारत योजनेत समाविष्ट आहेत?",
        "SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'KARNATAKA';",
        ["empanelled_hospitals", "state_name"])
    add("indicdb-mr-024", "mr", "Devanagari", "Education", "ndap_higher_education_aishe", "easy",
        "महाराष्ट्रात एकूण विद्यापीठांची संख्या किती आहे?",
        "SELECT SUM(university_count) FROM ndap_higher_education_aishe WHERE state_name = 'MAHARASHTRA';",
        ["university_count", "state_name"])
    add("indicdb-mr-025", "mr", "Devanagari", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "मध्य प्रदेशात डीएपी खताची एकूण विक्री किती टन झाली?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'MADHYA PRADESH' AND fertilizer_type = 'DAP';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-mr-026", "mr", "Devanagari", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "महाराष्ट्रात मनरेगा अंतर्गत महिलांचे मनुष्य दिन प्रमाण किती टक्के आहे?",
        "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'MAHARASHTRA';",
        ["women_mandays_pct", "state_name"])
    add("indicdb-mr-027", "mr", "Devanagari", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "महाराष्ट्रात किती समुदाय आरोग्य केंद्र (CHC) आहेत?",
        "SELECT SUM(community_health_centres_chc) FROM ndap_rural_health_infrastructure WHERE state_name = 'MAHARASHTRA';",
        ["community_health_centres_chc", "state_name"])
    add("indicdb-mr-028", "mr", "Devanagari", "Education", "ndap_school_infrastructure", "easy",
        "ठाणे जिल्ह्यात एकूण शाळांची संख्या किती आहे?",
        "SELECT SUM(total_schools) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Thane';",
        ["total_schools", "state_name", "district_name"])
    add("indicdb-mr-029", "mr", "Devanagari", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "महाराष्ट्रात अर्भक मृत्यू दर आयएमआर किती नोंदवला गेला?",
        "SELECT AVG(infant_mortality_rate_imr) FROM ndap_maternal_child_mortality WHERE state_name = 'MAHARASHTRA';",
        ["infant_mortality_rate_imr", "state_name"])
    add("indicdb-mr-030", "mr", "Devanagari", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "महाराष्ट्रात टोमॅटोचा किमान भाव काय होता?",
        "SELECT MIN(min_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Tomato';",
        ["min_price_inr", "state_name", "commodity"])
    add("indicdb-mr-031", "mr", "Devanagari", "Rural Development", "ndap_jal_jeevan_tap_water", "hard",
        "महाराष्ट्रात हर घर जल प्रमाणित गावे सर्वाधिक कोणत्या जिल्ह्यात आहेत?",
        "SELECT district_name, SUM(villages_certified_har_ghar_jal) AS total_villages FROM ndap_jal_jeevan_tap_water WHERE state_name = 'MAHARASHTRA' GROUP BY district_name ORDER BY total_villages DESC LIMIT 1;",
        ["district_name", "villages_certified_har_ghar_jal", "state_name"])
    add("indicdb-mr-032", "mr", "Devanagari", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
        "कोल्हापूर जिल्ह्यात पीएम-किसानचे किती लाभार्थी शेतकरी आहेत?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA' AND district_name = 'Kolhapur';",
        ["farmer_beneficiaries", "state_name", "district_name"])
    add("indicdb-mr-033", "mr", "Devanagari", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "औरंगाबाद जिल्ह्यात आयुष्यमान कार्ड किती जारी झाले?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'MAHARASHTRA' AND district_name = 'Aurangabad';",
        ["cards_issued", "state_name", "district_name"])
    add("indicdb-mr-034", "mr", "Devanagari", "Education", "ndap_education_stats", "hard",
        "महाराष्ट्रात सर्वात जास्त महिला साक्षरता दर कोणत्या जिल्ह्यात आहे?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'MAHARASHTRA' ORDER BY female_literacy_rate DESC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-mr-035", "mr", "Devanagari", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "सोलापूर जिल्ह्यात किती घरे मंजूर झाली?",
        "SELECT SUM(houses_sanctioned) FROM ndap_pmay_rural_housing WHERE state_name = 'MAHARASHTRA' AND district_name = 'Solapur';",
        ["houses_sanctioned", "state_name", "district_name"])
    add("indicdb-mr-036", "mr", "Devanagari", "Skill Development", "ndap_vocational_skill_training", "easy",
        "महाराष्ट्रात आरोग्य सेवा क्षेत्रात किती विद्यार्थी प्रशिक्षित झाले?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'MAHARASHTRA' AND sector_skill_council = 'Healthcare';",
        ["certified_candidates", "state_name", "sector_skill_council"])
    add("indicdb-mr-037", "mr", "Devanagari", "Agriculture", "ndap_crop_production_census", "medium",
        "नागपूर जिल्ह्यात कापसाचे उत्पादन किती झाले?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'MAHARASHTRA' AND district_name = 'Nagpur' AND crop_name = 'COTTON';",
        ["production_tonnes", "state_name", "district_name", "crop_name"])
    add("indicdb-mr-038", "mr", "Devanagari", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "महाराष्ट्रात ग्रामीण रस्ते प्रकल्पावर एकूण किती खर्च झाला?",
        "SELECT SUM(total_expenditure_inr) FROM ndap_pmgsy_rural_roads WHERE state_name = 'MAHARASHTRA';",
        ["total_expenditure_inr", "state_name"])
    add("indicdb-mr-039", "mr", "Devanagari", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "पुणे जिल्ह्यात बालकांचे पूर्ण लसीकरण किती टक्के झाले?",
        "SELECT fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
        ["fully_vaccinated_children_pct", "state_name", "district_name"])
    add("indicdb-mr-040", "mr", "Devanagari", "Agriculture", "ndap_soil_health_records", "easy",
        "महाराष्ट्रात जारी केलेल्या मृदा आरोग्य पत्रिकांची संख्या किती?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'MAHARASHTRA';",
        ["cards_issued", "state_name"])

    # =========================================================================
    # 3. TAMIL (ta) - 40 Queries
    # =========================================================================
    add("indicdb-ta-001", "ta", "Tamil", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "தமிழ்நாட்டில் பிஎம்-கிசான் திட்டத்தின் கீழ் பயனடைந்த மொத்த விவசாயிகள் எத்தனை பேர்?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'TAMIL NADU';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-ta-002", "ta", "Tamil", "Agriculture", "ndap_crop_production_census", "medium",
        "தமிழ்நாட்டில் நெல் பயிரின் மொத்த உற்பத்தி எத்தனை டன்கள்?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'TAMIL NADU' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-ta-003", "ta", "Tamil", "Agriculture", "ndap_crop_production_census", "medium",
        "தமிழ்நாட்டில் கரும்பு சாகுபடி பரப்பளவு எத்தனை ஹெக்டேர்?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'TAMIL NADU' AND crop_name = 'SUGARCANE';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-ta-004", "ta", "Tamil", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "தமிழ்நாட்டில் மகாத்மா காந்தி வேலைவாய்ப்பு திட்டத்தில் உருவாக்கப்பட்ட மனித வேலை நாட்கள் எத்தனை?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-ta-005", "ta", "Tamil", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "தமிழ்நாட்டில் ஆயுஷ்மான் பாரத் திட்டத்தின் கீழ் வழங்கப்பட்ட மொத்த அட்டைகள் எத்தனை?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'TAMIL NADU';",
        ["cards_issued", "state_name"])
    add("indicdb-ta-006", "ta", "Tamil", "Education", "ndap_school_infrastructure", "easy",
        "மதுரை மாவட்டத்தில் கணினி ஆய்வகம் உள்ள பள்ளிகள் எத்தனை?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-ta-007", "ta", "Tamil", "Education", "ndap_education_stats", "hard",
        "தமிழ்நாட்டில் பெண் எழுத்தறிவு விகிதம் அதிகமாக உள்ள மாவட்டம் எது?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'TAMIL NADU' ORDER BY female_literacy_rate DESC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-ta-008", "ta", "Tamil", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "தமிழ்நாட்டில் யூரியா உரத்தின் மொத்த விற்பனை எத்தனை டன்?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'TAMIL NADU' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-ta-009", "ta", "Tamil", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "கோயம்புத்தூர் மாவட்டத்தில் முழுமையாக தடுப்பூசி போடப்பட்ட குழந்தைகளின் சதவீதம் என்ன?",
        "SELECT fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';",
        ["fully_vaccinated_children_pct", "state_name", "district_name"])
    add("indicdb-ta-010", "ta", "Tamil", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "தமிழ்நாட்டில் பிரதம மந்திரி ஆவாஸ் யோஜனா திட்டத்தில் அதிக வீடுகள் கட்டப்பட்ட மாவட்டம் எது?",
        "SELECT district_name, SUM(houses_completed) AS total_houses FROM ndap_pmay_rural_housing WHERE state_name = 'TAMIL NADU' GROUP BY district_name ORDER BY total_houses DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-ta-011", "ta", "Tamil", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "தமிழ்நாட்டில் குடிநீர் குழாய் இணைப்பு பெற்றுள்ள கிராமப்புற குடும்பங்கள் எத்தனை?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-ta-012", "ta", "Tamil", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "தமிழ்நாட்டில் மொத்தம் எத்தனை ஆரம்ப சுகாதார நிலையங்கள் (PHC) உள்ளன?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'TAMIL NADU';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-ta-013", "ta", "Tamil", "Education", "ndap_midday_meal_scheme", "medium",
        "தமிழ்நாட்டில் மதிய உணவு திட்டத்தால் பயனடைந்த தொடக்கப்பள்ளி மாணவர்கள் எத்தனை பேர்?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'TAMIL NADU';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-ta-014", "ta", "Tamil", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "தமிழ்நாட்டில் முடிக்கப்பட்ட கிராமப்புற சாலைகளின் மொத்த நீளம் என்ன?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'TAMIL NADU';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-ta-015", "ta", "Tamil", "Skill Development", "ndap_vocational_skill_training", "easy",
        "தமிழ்நாட்டில் தொழிற்பயிற்சி முடித்து சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'TAMIL NADU';",
        ["certified_candidates", "state_name"])
    add("indicdb-ta-016", "ta", "Tamil", "Agriculture", "ndap_soil_health_records", "easy",
        "தமிழ்நாட்டில் வழங்கப்பட்ட மண் வள அட்டைகளின் எண்ணிக்கை என்ன?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU';",
        ["cards_issued", "state_name"])
    add("indicdb-ta-017", "ta", "Tamil", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "தமிழ்நாடு சந்தைகளில் நெல்லின் சராசரி மாதிரி விலை என்ன?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'TAMIL NADU' AND commodity = 'Rice';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-ta-018", "ta", "Tamil", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "தமிழ்நாட்டில் அறிவிக்கப்பட்ட காசநோயாளிகளின் மொத்த எண்ணிக்கை என்ன?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'TAMIL NADU';",
        ["total_notified_patients", "state_name"])
    add("indicdb-ta-019", "ta", "Tamil", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "தமிழ்நாட்டில் கிராம ஊராட்சிகளுக்கு ஒதுக்கப்பட்ட மொத்த நிதி என்ன?",
        "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'TAMIL NADU';",
        ["grant_allocated_inr", "state_name"])
    add("indicdb-ta-020", "ta", "Tamil", "Education", "ndap_higher_education_aishe", "easy",
        "தமிழ்நாட்டில் உள்ள மொத்த கல்லூரிகளின் எண்ணிக்கை என்ன?",
        "SELECT SUM(college_count) FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';",
        ["college_count", "state_name"])
    # 21 to 40 Tamil pan-India
    add("indicdb-ta-021", "ta", "Tamil", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "புதுச்சேரியில் பிஎம்-கிசான் திட்டத்தின் மொத்த பயனாளிகள் எத்தனை பேர்?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'PUDUCHERRY';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-ta-022", "ta", "Tamil", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "கேரளாவில் பிஎம்-கிசான் நிதி பெற்ற விவசாயிகள் எத்தனை பேர்?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'KERALA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-ta-023", "ta", "Tamil", "Education", "ndap_school_infrastructure", "easy",
        "சேலம் மாவட்டத்தில் மாணவிகளுக்கு கழிப்பறை வசதி கொண்ட பள்ளிகள் எத்தனை?",
        "SELECT SUM(schools_with_girl_toilets) FROM ndap_school_infrastructure WHERE state_name = 'TAMIL NADU' AND district_name = 'Salem';",
        ["schools_with_girl_toilets", "state_name", "district_name"])
    add("indicdb-ta-024", "ta", "Tamil", "Agriculture", "ndap_crop_production_census", "medium",
        "ஈரோடு மாவட்டத்தில் நிலக்கடலை உற்பத்தி எத்தனை டன்?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'TAMIL NADU' AND district_name = 'Erode' AND crop_name = 'GROUNDNUT';",
        ["production_tonnes", "state_name", "district_name", "crop_name"])
    add("indicdb-ta-025", "ta", "Tamil", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "தமிழ்நாட்டில் தாய்மார்கள் இறப்பு விகிதம் (MMR) என்ன?",
        "SELECT AVG(maternal_mortality_ratio_mmr) FROM ndap_maternal_child_mortality WHERE state_name = 'TAMIL NADU';",
        ["maternal_mortality_ratio_mmr", "state_name"])
    add("indicdb-ta-026", "ta", "Tamil", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "தமிழ்நாட்டில் ஊரக வேலைவாய்ப்பு திட்டத்தில் பெண்களின் பங்கு எத்தனை சதவீதம்?",
        "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU';",
        ["women_mandays_pct", "state_name"])
    add("indicdb-ta-027", "ta", "Tamil", "Education", "ndap_education_stats", "easy",
        "சென்னை மாவட்டத்தில் பதிவு செய்யப்பட்ட மொத்த மாணவர்கள் எத்தனை?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'TAMIL NADU' AND district_name = 'Chennai';",
        ["student_count", "state_name", "district_name"])
    add("indicdb-ta-028", "ta", "Tamil", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "திருச்சிராப்பள்ளி மாவட்டத்தில் டிஏபி உரத் தேவை எத்தனை டன்?",
        "SELECT SUM(requirement_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'TAMIL NADU' AND district_name = 'Tiruchirappalli' AND fertilizer_type = 'DAP';",
        ["requirement_tonnes", "state_name", "district_name", "fertilizer_type"])
    add("indicdb-ta-029", "ta", "Tamil", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "தமிழ்நாட்டில் அனுமதிக்கப்பட்ட மொத்த மருத்துவ சேர்க்கைகள் எத்தனை?",
        "SELECT SUM(authorized_admissions) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'TAMIL NADU';",
        ["authorized_admissions", "state_name"])
    add("indicdb-ta-030", "ta", "Tamil", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "தமிழ்நாட்டில் ஹர் கர் ஜல் சான்றிதழ் பெற்ற மொத்த கிராமங்கள் எத்தனை?",
        "SELECT SUM(villages_certified_har_ghar_jal) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TAMIL NADU';",
        ["villages_certified_har_ghar_jal", "state_name"])
    add("indicdb-ta-031", "ta", "Tamil", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "திருநெல்வேலி மாவட்டத்தில் மருத்துவமனைகளில் நிகழ்ந்த பிரசவங்களின் சதவீதம் என்ன?",
        "SELECT institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'TAMIL NADU' AND district_name = 'Tirunelveli';",
        ["institutional_births_pct", "state_name", "district_name"])
    add("indicdb-ta-032", "ta", "Tamil", "Education", "ndap_school_infrastructure", "easy",
        "தமிழ்நாட்டில் மின்சார வசதி கொண்ட மொத்த பள்ளிகள் எத்தனை?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'TAMIL NADU';",
        ["schools_with_electricity", "state_name"])
    add("indicdb-ta-033", "ta", "Tamil", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "மதுரை மாவட்டத்தில் பிரதம மந்திரி வீட்டு வசதி திட்டத்தில் மாற்றப்பட்ட நிதி எவ்வளவு?",
        "SELECT SUM(funds_transferred_inr) FROM ndap_pmay_rural_housing WHERE state_name = 'TAMIL NADU' AND district_name = 'Madurai';",
        ["funds_transferred_inr", "state_name", "district_name"])
    add("indicdb-ta-034", "ta", "Tamil", "Skill Development", "ndap_vocational_skill_training", "medium",
        "தமிழ்நாட்டில் விவசாய திறன் பயிற்சிக்காக சேர்ந்தவர்கள் எத்தனை பேர்?",
        "SELECT SUM(enrolled_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'TAMIL NADU' AND sector_skill_council = 'Agriculture';",
        ["enrolled_candidates", "state_name", "sector_skill_council"])
    add("indicdb-ta-035", "ta", "Tamil", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "தமிழ்நாட்டில் வெங்காயத்தின் அதிகபட்ச விலை என்ன?",
        "SELECT MAX(max_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'TAMIL NADU' AND commodity = 'Onion';",
        ["max_price_inr", "state_name", "commodity"])
    add("indicdb-ta-036", "ta", "Tamil", "Agriculture", "ndap_soil_health_records", "easy",
        "கோயம்புத்தூர் மாவட்டத்தில் ஆய்வு செய்யப்பட்ட மண் மாதிரிகள் எத்தனை?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';",
        ["samples_tested", "state_name", "district_name"])
    add("indicdb-ta-037", "ta", "Tamil", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "தமிழ்நாட்டில் கிராமப்புற சாலை திட்டத்தில் இணைக்கப்பட்ட மொத்த குடியிருப்புகள் எத்தனை?",
        "SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE state_name = 'TAMIL NADU';",
        ["habitations_connected", "state_name"])
    add("indicdb-ta-038", "ta", "Tamil", "Education", "ndap_higher_education_aishe", "easy",
        "தமிழ்நாட்டில் உள்ள மொத்த கல்லூரி ஆசிரியர்கள் எண்ணிக்கை என்ன?",
        "SELECT SUM(total_faculty_count) FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';",
        ["total_faculty_count", "state_name"])
    add("indicdb-ta-039", "ta", "Tamil", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "தமிழ்நாட்டில் சமூக சுகாதார மையங்களில் உள்ள சிறப்பு மருத்துவர்கள் எத்தனை பேர்?",
        "SELECT SUM(specialists_at_chc) FROM ndap_rural_health_infrastructure WHERE state_name = 'TAMIL NADU';",
        ["specialists_at_chc", "state_name"])
    add("indicdb-ta-040", "ta", "Tamil", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "தமிழ்நாட்டில் ஊரக வேலைவாய்ப்பு திட்டத்தின் மொத்த ஊதியச் செலவு என்ன?",
        "SELECT SUM(total_wage_expenditure_inr) FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU';",
        ["total_wage_expenditure_inr", "state_name"])

    # =========================================================================
    # 4. TELUGU (te) - 40 Queries
    # =========================================================================
    add("indicdb-te-001", "te", "Telugu", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "ఆంధ్రప్రదేశ్‌లో పీఎం-కిసాన్ పథకం ద్వారా ఎంతమంది రైతులకు లబ్ధి చేకూరింది?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'ANDHRA PRADESH';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-te-002", "te", "Telugu", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "తెలంగాణలో పీఎం-కిసాన్ లబ్ధిదారుల సంఖ్య ఎంత?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'TELANGANA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-te-003", "te", "Telugu", "Agriculture", "ndap_crop_production_census", "medium",
        "ఆంధ్రప్రదేశ్‌లో వరి పంట మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ANDHRA PRADESH' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-te-004", "te", "Telugu", "Agriculture", "ndap_crop_production_census", "medium",
        "తెలంగాణలో పత్తి సాగు విస్తీర్ణం ఎన్ని హెక్టార్లు?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'TELANGANA' AND crop_name = 'COTTON';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-te-005", "te", "Telugu", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "ఆంధ్రప్రదేశ్‌లో ఉపాధి హామీ పథకం కింద ఎన్ని పనిదినాలు కల్పించబడ్డాయి?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'ANDHRA PRADESH';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-te-006", "te", "Telugu", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "ఆంధ్రప్రదేశ్‌లో ఆయుష్మాన్ భారత్ కింద క్లెయిమ్ అయిన మొత్తం సొమ్ము ఎంత?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'ANDHRA PRADESH';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-te-007", "te", "Telugu", "Education", "ndap_school_infrastructure", "easy",
        "విశాఖపట్నం జిల్లాలో కంప్యూటర్ ల్యాబ్‌లు ఉన్న పాఠశాలలు ఎన్ని?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Visakhapatnam';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-te-008", "te", "Telugu", "Education", "ndap_education_stats", "hard",
        "ఆంధ్రప్రదేశ్‌లో అతి తక్కువ స్త్రీ అక్షరాస్యత రేటు ఉన్న జిల్లా ఏది?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'ANDHRA PRADESH' ORDER BY female_literacy_rate ASC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-te-009", "te", "Telugu", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "గుంటూరు జిల్లాలో యూరియా ఎరువు అమ్మకాలు ఎన్ని టన్నులు?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Guntur' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "district_name", "fertilizer_type"])
    add("indicdb-te-010", "te", "Telugu", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "విజయవాడ లేదా కృష్ణా ప్రాంతంలో ఆసుపత్రి ప్రసవాల శాతం ఎంత?",
        "SELECT institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Vijayawada';",
        ["institutional_births_pct", "state_name", "district_name"])
    add("indicdb-te-011", "te", "Telugu", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "ఆంధ్రప్రదేశ్‌లో పీఎంఏవై గ్రామీణ పథకం కింద అత్యధిక ఇళ్లు నిర్మించిన జిల్లా ఏది?",
        "SELECT district_name, SUM(houses_completed) AS total_houses FROM ndap_pmay_rural_housing WHERE state_name = 'ANDHRA PRADESH' GROUP BY district_name ORDER BY total_houses DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-te-012", "te", "Telugu", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "ఆంధ్రప్రదేశ్‌లో కుళాయి నీటి కనెక్షన్లు ఉన్న గ్రామీణ కుటుంబాల సంఖ్య ఎంత?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'ANDHRA PRADESH';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-te-013", "te", "Telugu", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "తెలంగాణలో మొత్తం ప్రాథమిక ఆరోగ్య కేంద్రాలు (PHC) ఎన్ని ఉన్నాయి?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'TELANGANA';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-te-014", "te", "Telugu", "Education", "ndap_midday_meal_scheme", "medium",
        "ఆంధ్రప్రదేశ్‌లో మధ్యాహ్న భోజన పథకం వల్ల ప్రయోజనం పొందిన విద్యార్థులు ఎంతమంది?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'ANDHRA PRADESH';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-te-015", "te", "Telugu", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "తెలంగాణలో పీఎమ్‌జీఎస్‌వై కింద పూర్తయిన రోడ్ల పొడవు ఎంత?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'TELANGANA';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-te-016", "te", "Telugu", "Skill Development", "ndap_vocational_skill_training", "easy",
        "ఆంధ్రప్రదేశ్‌లో నైపుణ్య శిక్షణ పూర్తి చేసుకున్న వారి సంఖ్య ఎంత?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'ANDHRA PRADESH';",
        ["certified_candidates", "state_name"])
    add("indicdb-te-017", "te", "Telugu", "Agriculture", "ndap_soil_health_records", "easy",
        "ఆంధ్రప్రదేశ్‌లో రైతులకు పంపిణీ చేసిన సాయిల్ హెల్త్ కార్డులు ఎన్ని?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'ANDHRA PRADESH';",
        ["cards_issued", "state_name"])
    add("indicdb-te-018", "te", "Telugu", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "తెలంగాణ మార్కెట్లలో మొక్కజొన్న సగటు ధర ఎంత?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'TELANGANA' AND commodity = 'Maize';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-te-019", "te", "Telugu", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "ఆంధ్రప్రదేశ్‌లో క్షయవ్యాధి నిర్ధారణ అయిన రోగుల సంఖ్య ఎంత?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'ANDHRA PRADESH';",
        ["total_notified_patients", "state_name"])
    add("indicdb-te-020", "te", "Telugu", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "ఆంధ్రప్రదేశ్‌లో గ్రామ పంచాయతీలు ఉపయోగించిన మొత్తం నిధులు ఎన్ని?",
        "SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'ANDHRA PRADESH';",
        ["grant_utilized_inr", "state_name"])
    # 21 to 40 Telugu
    add("indicdb-te-021", "te", "Telugu", "Agriculture", "ndap_crop_production_census", "medium",
        "కర్నూలు జిల్లాలో వేరుశనగ ఉత్పత్తి ఎన్ని టన్నులు?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Kurnool' AND crop_name = 'GROUNDNUT';",
        ["production_tonnes", "state_name", "district_name", "crop_name"])
    add("indicdb-te-022", "te", "Telugu", "Education", "ndap_higher_education_aishe", "easy",
        "ఆంధ్రప్రదేశ్‌లో మొత్తం విశ్వవిద్యాలయాల సంఖ్య ఎంత?",
        "SELECT SUM(university_count) FROM ndap_higher_education_aishe WHERE state_name = 'ANDHRA PRADESH';",
        ["university_count", "state_name"])
    add("indicdb-te-023", "te", "Telugu", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "నెల్లూరు జిల్లాలో జారీ చేసిన ఆయుష్మాన్ కార్డులు ఎన్ని?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Nellore';",
        ["cards_issued", "state_name", "district_name"])
    add("indicdb-te-024", "te", "Telugu", "Education", "ndap_school_infrastructure", "easy",
        "తిరుపతి జిల్లాలో బాలికల మరుగుదొడ్లు ఉన్న పాఠశాలలు ఎన్ని?",
        "SELECT SUM(schools_with_girl_toilets) FROM ndap_school_infrastructure WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Tirupati';",
        ["schools_with_girl_toilets", "state_name", "district_name"])
    add("indicdb-te-025", "te", "Telugu", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "ఆంధ్రప్రదేశ్‌లో ఉపాధి హామీ పథకంలో మహిళల భాగస్వామ్యం శాతం ఎంత?",
        "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'ANDHRA PRADESH';",
        ["women_mandays_pct", "state_name"])
    add("indicdb-te-026", "te", "Telugu", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "తెలంగాణలో డీఏపీ ఎరువుల మొత్తం అమ్మకాలు ఎన్ని టన్నులు?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'TELANGANA' AND fertilizer_type = 'DAP';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-te-027", "te", "Telugu", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "ఆంధ్రప్రదేశ్‌లో శిశు మరణాల రేటు (IMR) ఎంత?",
        "SELECT AVG(infant_mortality_rate_imr) FROM ndap_maternal_child_mortality WHERE state_name = 'ANDHRA PRADESH';",
        ["infant_mortality_rate_imr", "state_name"])
    add("indicdb-te-028", "te", "Telugu", "Education", "ndap_education_stats", "easy",
        "కడప జిల్లాలో మొత్తం విద్యార్థుల సంఖ్య ఎంత?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Kadapa';",
        ["student_count", "state_name", "district_name"])
    add("indicdb-te-029", "te", "Telugu", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "ఆంధ్రప్రదేశ్‌లో ట్యాప్ వాటర్ కవరేజ్ సగటు శాతం ఎంత?",
        "SELECT AVG(tap_connection_coverage_pct) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'ANDHRA PRADESH';",
        ["tap_connection_coverage_pct", "state_name"])
    add("indicdb-te-030", "te", "Telugu", "Agriculture", "ndap_soil_health_records", "easy",
        "తెలంగాణలో పరీక్షించిన నేల నమూనాల సంఖ్య ఎంత?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'TELANGANA';",
        ["samples_tested", "state_name"])
    add("indicdb-te-031", "te", "Telugu", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "గుంటూరు జిల్లాలో సంపూర్ణ టీకాలు వేయించుకున్న పిల్లల శాతం ఎంత?",
        "SELECT fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH' AND district_name = 'Guntur';",
        ["fully_vaccinated_children_pct", "state_name", "district_name"])
    add("indicdb-te-032", "te", "Telugu", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "తెలంగాణలో మంజూరైన పీఎంఏవై ఇళ్ల సంఖ్య ఎంత?",
        "SELECT SUM(houses_sanctioned) FROM ndap_pmay_rural_housing WHERE state_name = 'TELANGANA';",
        ["houses_sanctioned", "state_name"])
    add("indicdb-te-033", "te", "Telugu", "Skill Development", "ndap_vocational_skill_training", "medium",
        "ఆంధ్రప్రదేశ్‌లో ఐటీ రంగంలో ఉపాధి పొందిన అభ్యర్థులు ఎంతమంది?",
        "SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'ANDHRA PRADESH' AND sector_skill_council = 'IT-ITeS';",
        ["placed_candidates", "state_name", "sector_skill_council"])
    add("indicdb-te-034", "te", "Telugu", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "ఆంధ్రప్రదేశ్‌లో మిర్చి గరిష్ట ధర ఎంత నమోదైంది?",
        "SELECT MAX(max_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'ANDHRA PRADESH' AND commodity = 'Chilli';",
        ["max_price_inr", "state_name", "commodity"])
    add("indicdb-te-035", "te", "Telugu", "Education", "ndap_school_infrastructure", "easy",
        "తెలంగాణలో విద్యుత్ సౌకర్యం ఉన్న పాఠశాలల సంఖ్య ఎంత?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'TELANGANA';",
        ["schools_with_electricity", "state_name"])
    add("indicdb-te-036", "te", "Telugu", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "ఆంధ్రప్రదేశ్‌లో పీహెచ్‌సీలలో పనిచేస్తున్న వైద్యుల సంఖ్య ఎంత?",
        "SELECT SUM(doctors_at_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'ANDHRA PRADESH';",
        ["doctors_at_phc", "state_name"])
    add("indicdb-te-037", "te", "Telugu", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "ఆంధ్రప్రదేశ్‌లో గ్రామీణ రోడ్ల ప్రాజెక్టుల మొత్తం వ్యయం ఎంత?",
        "SELECT SUM(total_expenditure_inr) FROM ndap_pmgsy_rural_roads WHERE state_name = 'ANDHRA PRADESH';",
        ["total_expenditure_inr", "state_name"])
    add("indicdb-te-038", "te", "Telugu", "Agriculture", "ndap_crop_production_census", "easy",
        "ఆంధ్రప్రదేశ్‌లో మొత్తం పంటల ఉత్పత్తి ఎన్ని టన్నులు?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ANDHRA PRADESH';",
        ["production_tonnes", "state_name"])
    add("indicdb-te-039", "te", "Telugu", "Education", "ndap_midday_meal_scheme", "medium",
        "తెలంగాణలో మధ్యాహ్న భోజన పథకానికి కేటాయించిన ఆహార ధాన్యాలు ఎన్ని మెట్రిక్ టన్నులు?",
        "SELECT SUM(foodgrains_allocated_mt) FROM ndap_midday_meal_scheme WHERE state_name = 'TELANGANA';",
        ["foodgrains_allocated_mt", "state_name"])
    add("indicdb-te-040", "te", "Telugu", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "తెలంగాణలో క్షయ వ్యాధి చికిత్స విజయవంతమైన శాతం ఎంత?",
        "SELECT AVG(treatment_success_rate_pct) FROM ndap_national_tuberculosis_portal WHERE state_name = 'TELANGANA';",
        ["treatment_success_rate_pct", "state_name"])

    # =========================================================================
    # 5. BENGALI (bn) - 40 Queries
    # =========================================================================
    add("indicdb-bn-001", "bn", "Bengali", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "পশ্চিমবঙ্গে মোট কতজন কৃষক পিএম-কিষানের সুবিধা পেয়েছেন?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'WEST BENGAL';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-bn-002", "bn", "Bengali", "Agriculture", "ndap_crop_production_census", "medium",
        "পশ্চিমবঙ্গে ধান ফসলের মোট উৎপাদন কত টন হয়েছে?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'WEST BENGAL' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-bn-003", "bn", "Bengali", "Agriculture", "ndap_crop_production_census", "medium",
        "পশ্চিমবঙ্গে পাটের মোট চাষের এলাকা কত হেক্টর?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'WEST BENGAL' AND crop_name = 'JUTE';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-bn-004", "bn", "Bengali", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "পশ্চিমবঙ্গে ১০০ দিনের কাজের প্রকল্পে মোট কত কর্মদিবস তৈরি হয়েছে?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'WEST BENGAL';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-bn-005", "bn", "Bengali", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "পশ্চিমবঙ্গে আয়ুষ্মান ভারত প্রকল্পে মোট কত টাকা নিষ্পত্তি হয়েছে?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'WEST BENGAL';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-bn-006", "bn", "Bengali", "Education", "ndap_school_infrastructure", "easy",
        "কলকাতা জেলায় কম্পিউটার ল্যাব থাকা স্কুলের সংখ্যা কত?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'WEST BENGAL' AND district_name = 'Kolkata';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-bn-007", "bn", "Bengali", "Education", "ndap_education_stats", "hard",
        "পশ্চিমবঙ্গের কোন জেলায় নারী সাক্ষরতার হার সবচেয়ে কম?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'WEST BENGAL' ORDER BY female_literacy_rate ASC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-bn-008", "bn", "Bengali", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "মুর্শিদাবাদ জেলায় ইউরিয়া সারের মোট বিক্রি কত টন?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'WEST BENGAL' AND district_name = 'Murshidabad' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "district_name", "fertilizer_type"])
    add("indicdb-bn-009", "bn", "Bengali", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "হাওড়া জেলায় শিশুদের সম্পূর্ণ টিকাকরণের হার কত শতাংশ?",
        "SELECT fully_vaccinated_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'WEST BENGAL' AND district_name = 'Howrah';",
        ["fully_vaccinated_children_pct", "state_name", "district_name"])
    add("indicdb-bn-010", "bn", "Bengali", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "পশ্চিমবঙ্গে প্রধানমন্ত্রী আবাস যোজনায় সর্বাধিক বাড়ি তৈরি হয়েছে কোন জেলায়?",
        "SELECT district_name, SUM(houses_completed) AS total_houses FROM ndap_pmay_rural_housing WHERE state_name = 'WEST BENGAL' GROUP BY district_name ORDER BY total_houses DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-bn-011", "bn", "Bengali", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "পশ্চিমবঙ্গে নলবাহিত পানীয় জলের সংযোগ পাওয়া গ্রামীণ পরিবারের সংখ্যা কত?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'WEST BENGAL';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-bn-012", "bn", "Bengali", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "পশ্চিমবঙ্গে মোট কতগুলি প্রাথমিক স্বাস্থ্য কেন্দ্র (PHC) রয়েছে?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'WEST BENGAL';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-bn-013", "bn", "Bengali", "Education", "ndap_midday_meal_scheme", "medium",
        "পশ্চিমবঙ্গে মিড-ডে মিল স্কিমে মোট কতজন প্রাথমিক ছাত্র উপকৃত হয়েছে?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'WEST BENGAL';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-bn-014", "bn", "Bengali", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "পশ্চিমবঙ্গে প্রধানমন্ত্রী গ্রাম সড়ক যোজনায় সম্পূর্ণ রাস্তার দৈর্ঘ্য কত?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'WEST BENGAL';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-bn-015", "bn", "Bengali", "Skill Development", "ndap_vocational_skill_training", "easy",
        "পশ্চিমবঙ্গে বৃত্তিমূলক প্রশিক্ষণে শংসাপত্রপ্রাপ্ত প্রার্থীর সংখ্যা কত?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'WEST BENGAL';",
        ["certified_candidates", "state_name"])
    add("indicdb-bn-016", "bn", "Bengali", "Agriculture", "ndap_soil_health_records", "easy",
        "পশ্চিমবঙ্গে মোট বিলিকৃত মৃত্তিকা স্বাস্থ্য কার্ডের সংখ্যা কত?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'WEST BENGAL';",
        ["cards_issued", "state_name"])
    add("indicdb-bn-017", "bn", "Bengali", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "পশ্চিমবঙ্গের বাজারে আলুর গড় মডেল দর কত ছিল?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'WEST BENGAL' AND commodity = 'Potato';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-bn-018", "bn", "Bengali", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "পশ্চিমবঙ্গে মোট নোটিফাইড যক্ষ্মা রোগীর সংখ্যা কত?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'WEST BENGAL';",
        ["total_notified_patients", "state_name"])
    add("indicdb-bn-019", "bn", "Bengali", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "পশ্চিমবঙ্গের গ্রাম পঞ্চায়েতগুলিতে ব্যবহৃত মোট অনুদান কত টাকা?",
        "SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'WEST BENGAL';",
        ["grant_utilized_inr", "state_name"])
    add("indicdb-bn-020", "bn", "Bengali", "Education", "ndap_higher_education_aishe", "easy",
        "পশ্চিমবঙ্গে মোট কলেজের সংখ্যা কত?",
        "SELECT SUM(college_count) FROM ndap_higher_education_aishe WHERE state_name = 'WEST BENGAL';",
        ["college_count", "state_name"])
    # 21 to 40 Bengali (East & North-East coverage)
    add("indicdb-bn-021", "bn", "Bengali", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "ত্রিপুরা রাজ্যে পিএম-কিষানের মোট সুবিধাভোগী কৃষক কতজন?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'TRIPURA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-bn-022", "bn", "Bengali", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "ওড়িশা রাজ্যে পিএম-কিষান প্রকল্পে মোট কতজন কৃষক উপকৃত হয়েছেন?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'ODISHA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-bn-023", "bn", "Bengali", "Education", "ndap_school_infrastructure", "easy",
        "দার্জিলিং জেলায় বিদ্যুৎ সুবিধা থাকা স্কুলের সংখ্যা কত?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'WEST BENGAL' AND district_name = 'Darjeeling';",
        ["schools_with_electricity", "state_name", "district_name"])
    add("indicdb-bn-024", "bn", "Bengali", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "উত্তর ২৪ পরগনা জেলায় কতগুলি আয়ুষ্মান কার্ড ইস্যু করা হয়েছে?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'WEST BENGAL' AND district_name = 'North 24 Parganas';",
        ["cards_issued", "state_name", "district_name"])
    add("indicdb-bn-025", "bn", "Bengali", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "পশ্চিমবঙ্গে ১০০ দিনের কাজে মহিলাদের কর্মদিবসের অনুপাত কত শতাংশ?",
        "SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE state_name = 'WEST BENGAL';",
        ["women_mandays_pct", "state_name"])
    add("indicdb-bn-026", "bn", "Bengali", "Education", "ndap_education_stats", "easy",
        "হুগলী জেলায় মোট ছাত্রছাত্রীর সংখ্যা কত?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'WEST BENGAL' AND district_name = 'Hooghly';",
        ["student_count", "state_name", "district_name"])
    add("indicdb-bn-027", "bn", "Bengali", "Agriculture", "ndap_crop_production_census", "medium",
        "নদিয়া জেলায় মোট ফসল উৎপাদন কত মেট্রিক টন?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'WEST BENGAL' AND district_name = 'Nadia';",
        ["production_tonnes", "state_name", "district_name"])
    add("indicdb-bn-028", "bn", "Bengali", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "পশ্চিমবঙ্গে মাতৃমৃত্যু অনুপাত এমএমআর কত নথিভুক্ত হয়েছে?",
        "SELECT AVG(maternal_mortality_ratio_mmr) FROM ndap_maternal_child_mortality WHERE state_name = 'WEST BENGAL';",
        ["maternal_mortality_ratio_mmr", "state_name"])
    add("indicdb-bn-029", "bn", "Bengali", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "পশ্চিমবঙ্গে জল জীবন মিশনে হর ঘর জল প্রত্যয়িত মোট গ্রামের সংখ্যা কত?",
        "SELECT SUM(villages_certified_har_ghar_jal) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'WEST BENGAL';",
        ["villages_certified_har_ghar_jal", "state_name"])
    add("indicdb-bn-030", "bn", "Bengali", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "পশ্চিমবঙ্গে ডিএপি সারের মোট বিক্রি কত টন?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'WEST BENGAL' AND fertilizer_type = 'DAP';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-bn-031", "bn", "Bengali", "Skill Development", "ndap_vocational_skill_training", "medium",
        "পশ্চিমবঙ্গে কৃষি সংক্রান্ত দক্ষতা প্রকল্পে কতজন প্রার্থী ভর্তি হয়েছেন?",
        "SELECT SUM(enrolled_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'WEST BENGAL' AND sector_skill_council = 'Agriculture';",
        ["enrolled_candidates", "state_name", "sector_skill_council"])
    add("indicdb-bn-032", "bn", "Bengali", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "মুর্শিদাবাদ জেলায় রক্তাল্পতায় ভোগা মহিলাদের হার কত শতাংশ?",
        "SELECT anaemic_women_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'WEST BENGAL' AND district_name = 'Murshidabad';",
        ["anaemic_women_pct", "state_name", "district_name"])
    add("indicdb-bn-033", "bn", "Bengali", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "পশ্চিমবঙ্গে মোট কতগুলি বাড়ি অনুমোদিত হয়েছে?",
        "SELECT SUM(houses_sanctioned) FROM ndap_pmay_rural_housing WHERE state_name = 'WEST BENGAL';",
        ["houses_sanctioned", "state_name"])
    add("indicdb-bn-034", "bn", "Bengali", "Education", "ndap_school_infrastructure", "easy",
        "পশ্চিমবঙ্গে পানীয় জলের সুবিধা থাকা স্কুলের সংখ্যা কত?",
        "SELECT SUM(schools_with_drinking_water) FROM ndap_school_infrastructure WHERE state_name = 'WEST BENGAL';",
        ["schools_with_drinking_water", "state_name"])
    add("indicdb-bn-035", "bn", "Bengali", "Agriculture", "ndap_soil_health_records", "easy",
        "পশ্চিমবঙ্গে মোট কতগুলি মাটির নমুনা পরীক্ষা করা হয়েছে?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'WEST BENGAL';",
        ["samples_tested", "state_name"])
    add("indicdb-bn-036", "bn", "Bengali", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "পশ্চিমবঙ্গে প্রাথমিক স্বাস্থ্য কেন্দ্রে কর্মরত মোট চিকিৎসকের সংখ্যা কত?",
        "SELECT SUM(doctors_at_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'WEST BENGAL';",
        ["doctors_at_phc", "state_name"])
    add("indicdb-bn-037", "bn", "Bengali", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "পশ্চিমবঙ্গে গ্রামীণ রাস্তা প্রকল্পে মোট ব্যয় কত টাকা?",
        "SELECT SUM(total_expenditure_inr) FROM ndap_pmgsy_rural_roads WHERE state_name = 'WEST BENGAL';",
        ["total_expenditure_inr", "state_name"])
    add("indicdb-bn-038", "bn", "Bengali", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "পশ্চিমবঙ্গের পাইকারি বাজারে পেঁয়াজের সর্বোচ্চ দর কত উঠেছে?",
        "SELECT MAX(max_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'WEST BENGAL' AND commodity = 'Onion';",
        ["max_price_inr", "state_name", "commodity"])
    add("indicdb-bn-039", "bn", "Bengali", "Education", "ndap_higher_education_aishe", "easy",
        "পশ্চিমবঙ্গে উচ্চশিক্ষায় নিযুক্ত মোট শিক্ষকের সংখ্যা কত?",
        "SELECT SUM(total_faculty_count) FROM ndap_higher_education_aishe WHERE state_name = 'WEST BENGAL';",
        ["total_faculty_count", "state_name"])
    add("indicdb-bn-040", "bn", "Bengali", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "পশ্চিমবঙ্গে যক্ষ্মা নির্মূল প্রকল্পে ডিবিটি পুষ্টি সহায়তা বাবদ মোট কত টাকা দেওয়া হয়েছে?",
        "SELECT SUM(dbt_nutritional_amount_inr) FROM ndap_national_tuberculosis_portal WHERE state_name = 'WEST BENGAL';",
        ["dbt_nutritional_amount_inr", "state_name"])

    # =========================================================================
    # 6. HINGLISH (hi-en) - 40 Queries
    # =========================================================================
    add("indicdb-hien-001", "hi-en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "Maharashtra me total kitne farmers ko PM-Kisan ka labh mila?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-hien-002", "hi-en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
        "Uttar Pradesh me PM-Kisan yojana me total kitna amount distribute hua?",
        "SELECT SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH';",
        ["amount_inr", "state_name"])
    add("indicdb-hien-003", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "Punjab me wheat ka total production kitne tonnes hua?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'PUNJAB' AND crop_name = 'WHEAT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-hien-004", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "Madhya Pradesh me soybean cultivation ka total area kitne hectares hai?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'MADHYA PRADESH' AND crop_name = 'SOYBEAN';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-hien-005", "hi-en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "Haryana me urea fertilizer ki total sales kitni tonnes hui?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'HARYANA' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-hien-006", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "Gujarat me groundnut crop ka total production kitna hua?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'GUJARAT' AND crop_name = 'GROUNDNUT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-hien-007", "hi-en", "Latin", "Education", "ndap_education_stats", "hard",
        "Bihar ke kis district me female literacy rate sabse kam hai?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-hien-008", "hi-en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "Pune district ke schools me kitni computer labs hain?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-hien-009", "hi-en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "Rajasthan me Ayushman Bharat ke under total kitne cards issue hue?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'RAJASTHAN';",
        ["cards_issued", "state_name"])
    add("indicdb-hien-010", "hi-en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
        "Bihar me stunted children ka highest percentage kis district me hai?",
        "SELECT district_name, stunted_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'BIHAR' ORDER BY stunted_children_pct DESC LIMIT 1;",
        ["district_name", "stunted_children_pct", "state_name"])
    add("indicdb-hien-011", "hi-en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "Uttar Pradesh me MGNREGA ke under total kitne mandays generate hue?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'UTTAR PRADESH';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-hien-012", "hi-en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "Madhya Pradesh me PMAY rural scheme me sabse zyada houses kis district me complete hue?",
        "SELECT district_name, SUM(houses_completed) AS total_completed FROM ndap_pmay_rural_housing WHERE state_name = 'MADHYA PRADESH' GROUP BY district_name ORDER BY total_completed DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-hien-013", "hi-en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "Haryana me kitne rural households ko tap water connection mila?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'HARYANA';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-hi-en-014", "hi-en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "Rajasthan me PMGSY ke under completed road length kitne km hai?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'RAJASTHAN';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-hien-015", "hi-en", "Latin", "Skill Development", "ndap_vocational_skill_training", "easy",
        "Delhi me vocational training me kitne candidates certified hue?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'DELHI';",
        ["certified_candidates", "state_name"])
    add("indicdb-hien-016", "hi-en", "Latin", "Agriculture", "ndap_soil_health_records", "easy",
        "Himachal Pradesh me total kitne soil health cards issue kiye gaye?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'HIMACHAL PRADESH';",
        ["cards_issued", "state_name"])
    add("indicdb-hien-017", "hi-en", "Latin", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "Maharashtra ki mandis me onion ka average modal price kya raha?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Onion';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-hien-018", "hi-en", "Latin", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "Uttar Pradesh me total notified TB patients kitne hain?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'UTTAR PRADESH';",
        ["total_notified_patients", "state_name"])
    add("indicdb-hien-019", "hi-en", "Latin", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "Uttarakhand me gram panchayats ko kitna grant allocate hua?",
        "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'UTTARAKHAND';",
        ["grant_allocated_inr", "state_name"])
    add("indicdb-hien-020", "hi-en", "Latin", "Education", "ndap_higher_education_aishe", "easy",
        "Karnataka me total colleges ka count kitna hai?",
        "SELECT SUM(college_count) FROM ndap_higher_education_aishe WHERE state_name = 'KARNATAKA';",
        ["college_count", "state_name"])
    # 21 to 40 Hinglish
    add("indicdb-hien-021", "hi-en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "Jammu and Kashmir me PM-Kisan ke total beneficiary farmers kitne hain?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'JAMMU AND KASHMIR';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-hien-022", "hi-en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "Ladakh me kitne hospitals Ayushman Bharat ke under empanelled hain?",
        "SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'LADAKH';",
        ["empanelled_hospitals", "state_name"])
    add("indicdb-hien-023", "hi-en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "Chandigarh me total schools kitne hain?",
        "SELECT SUM(total_schools) FROM ndap_school_infrastructure WHERE state_name = 'CHANDIGARH';",
        ["total_schools", "state_name"])
    add("indicdb-hien-024", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "Assam me rice production kitne tonnes hua?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ASSAM' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-hien-025", "hi-en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "Goa me average tap water coverage percentage kitna hai?",
        "SELECT AVG(tap_connection_coverage_pct) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'GOA';",
        ["tap_connection_coverage_pct", "state_name"])
    add("indicdb-hien-026", "hi-en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "Bihar me MGNREGA wages par total expenditure kitna hua?",
        "SELECT SUM(total_wage_expenditure_inr) FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';",
        ["total_wage_expenditure_inr", "state_name"])
    add("indicdb-hien-027", "hi-en", "Latin", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "Chhattisgarh me total kitne Primary Health Centres (PHC) hain?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'CHHATTISGARH';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-hien-028", "hi-en", "Latin", "Education", "ndap_midday_meal_scheme", "medium",
        "Jharkhand me Midday meal scheme se kitne primary students benefit hue?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'JHARKHAND';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-hien-029", "hi-en", "Latin", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "Madhya Pradesh me Maternal Mortality Ratio (MMR) kitna report hua?",
        "SELECT AVG(maternal_mortality_ratio_mmr) FROM ndap_maternal_child_mortality WHERE state_name = 'MADHYA PRADESH';",
        ["maternal_mortality_ratio_mmr", "state_name"])
    add("indicdb-hien-030", "hi-en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "Rajasthan me DAP fertilizer ki requirement kitne tonnes thi?",
        "SELECT SUM(requirement_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'RAJASTHAN' AND fertilizer_type = 'DAP';",
        ["requirement_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-hien-031", "hi-en", "Latin", "Skill Development", "ndap_vocational_skill_training", "medium",
        "Maharashtra me Automotive sector me kitne candidates placed hue?",
        "SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'MAHARASHTRA' AND sector_skill_council = 'Automotive';",
        ["placed_candidates", "state_name", "sector_skill_council"])
    add("indicdb-hien-032", "hi-en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "Uttarakhand me electricity facility wale schools kitne hain?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'UTTARAKHAND';",
        ["schools_with_electricity", "state_name"])
    add("indicdb-hien-033", "hi-en", "Latin", "Agriculture", "ndap_soil_health_records", "easy",
        "Haryana me tested soil samples ki total count kitni hai?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'HARYANA';",
        ["samples_tested", "state_name"])
    add("indicdb-hien-034", "hi-en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "Chhattisgarh me claim settled amount kitna hai?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'CHHATTISGARH';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-hien-035", "hi-en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "Jharkhand me PMAY funds transfer amount kitna hai?",
        "SELECT SUM(funds_transferred_inr) FROM ndap_pmay_rural_housing WHERE state_name = 'JHARKHAND';",
        ["funds_transferred_inr", "state_name"])
    add("indicdb-hien-036", "hi-en", "Latin", "Education", "ndap_education_stats", "easy",
        "Delhi schools me total enrolled students kitne hain?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'DELHI';",
        ["student_count", "state_name"])
    add("indicdb-hien-037", "hi-en", "Latin", "Agriculture", "ndap_crop_production_census", "easy",
        "Uttarakhand me total crop production kitne tonnes hua?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'UTTARAKHAND';",
        ["production_tonnes", "state_name"])
    add("indicdb-hien-038", "hi-en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "Rajasthan me institutional births percentage kitna hai?",
        "SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'RAJASTHAN';",
        ["institutional_births_pct", "state_name"])
    add("indicdb-hien-039", "hi-en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "Himachal Pradesh me PMGSY road network se kitni habitations connect hui?",
        "SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE state_name = 'HIMACHAL PRADESH';",
        ["habitations_connected", "state_name"])
    add("indicdb-hien-040", "hi-en", "Latin", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "UP mandis me wheat ka average price kya raha?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'UTTAR PRADESH' AND commodity = 'Wheat';",
        ["modal_price_inr", "state_name", "commodity"])

    # =========================================================================
    # 7. ENGLISH (en) - 40 Queries (Baseline Ground Truth)
    # =========================================================================
    add("indicdb-en-001", "en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "What is the total number of farmer beneficiaries under PM-KISAN in Maharashtra?",
        "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-en-002", "en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "medium",
        "What is the total amount disbursed under PM-KISAN in Uttar Pradesh?",
        "SELECT SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH';",
        ["amount_inr", "state_name"])
    add("indicdb-en-003", "en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "What is the total production of wheat in Punjab in tonnes?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'PUNJAB' AND crop_name = 'WHEAT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-en-004", "en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "What is the total cultivation area of soybean in Madhya Pradesh in hectares?",
        "SELECT SUM(area_hectares) FROM ndap_crop_production_census WHERE state_name = 'MADHYA PRADESH' AND crop_name = 'SOYBEAN';",
        ["area_hectares", "state_name", "crop_name"])
    add("indicdb-en-005", "en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "What were the total sales of urea fertilizer in Haryana in tonnes?",
        "SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'HARYANA' AND fertilizer_type = 'UREA';",
        ["sales_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-en-006", "en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "What was the total production of groundnut in Gujarat in tonnes?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'GUJARAT' AND crop_name = 'GROUNDNUT';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-en-007", "en", "Latin", "Education", "ndap_education_stats", "hard",
        "Which district in Bihar recorded the lowest female literacy rate?",
        "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
        ["district_name", "female_literacy_rate", "state_name"])
    add("indicdb-en-008", "en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "How many schools in Pune district have computer labs?",
        "SELECT SUM(schools_with_computer_labs) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
        ["schools_with_computer_labs", "state_name", "district_name"])
    add("indicdb-en-009", "en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "How many Ayushman cards were issued in Rajasthan?",
        "SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'RAJASTHAN';",
        ["cards_issued", "state_name"])
    add("indicdb-en-010", "en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "hard",
        "Which district in Bihar has the highest percentage of stunted children?",
        "SELECT district_name, stunted_children_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'BIHAR' ORDER BY stunted_children_pct DESC LIMIT 1;",
        ["district_name", "stunted_children_pct", "state_name"])
    add("indicdb-en-011", "en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "easy",
        "What is the total number of person-days generated under MGNREGA in Uttar Pradesh?",
        "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'UTTAR PRADESH';",
        ["total_mandays_generated", "state_name"])
    add("indicdb-en-012", "en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "hard",
        "Which district in Madhya Pradesh completed the highest number of houses under PMAY?",
        "SELECT district_name, SUM(houses_completed) AS total_completed FROM ndap_pmay_rural_housing WHERE state_name = 'MADHYA PRADESH' GROUP BY district_name ORDER BY total_completed DESC LIMIT 1;",
        ["district_name", "houses_completed", "state_name"])
    add("indicdb-en-013", "en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "easy",
        "How many rural households in Haryana have tap water connections?",
        "SELECT SUM(households_with_tap_connection) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'HARYANA';",
        ["households_with_tap_connection", "state_name"])
    add("indicdb-en-014", "en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "easy",
        "What is the total completed road length under PMGSY in Rajasthan in kilometers?",
        "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'RAJASTHAN';",
        ["completed_road_length_km", "state_name"])
    add("indicdb-en-015", "en", "Latin", "Skill Development", "ndap_vocational_skill_training", "easy",
        "What is the count of certified candidates in vocational skill training in Delhi?",
        "SELECT SUM(certified_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'DELHI';",
        ["certified_candidates", "state_name"])
    add("indicdb-en-016", "en", "Latin", "Agriculture", "ndap_soil_health_records", "easy",
        "How many soil health cards were issued in Himachal Pradesh?",
        "SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE state_name = 'HIMACHAL PRADESH';",
        ["cards_issued", "state_name"])
    add("indicdb-en-017", "en", "Latin", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "What was the average modal price of onion in Maharashtra mandis?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Onion';",
        ["modal_price_inr", "state_name", "commodity"])
    add("indicdb-en-018", "en", "Latin", "Healthcare", "ndap_national_tuberculosis_portal", "medium",
        "What is the total number of notified tuberculosis patients in Uttar Pradesh?",
        "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'UTTAR PRADESH';",
        ["total_notified_patients", "state_name"])
    add("indicdb-en-019", "en", "Latin", "Rural Development", "ndap_gram_panchayat_finance", "medium",
        "What is the total grant allocated to gram panchayats in Uttarakhand?",
        "SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE state_name = 'UTTARAKHAND';",
        ["grant_allocated_inr", "state_name"])
    add("indicdb-en-020", "en", "Latin", "Education", "ndap_higher_education_aishe", "easy",
        "What is the total number of colleges in Karnataka?",
        "SELECT SUM(college_count) FROM ndap_higher_education_aishe WHERE state_name = 'KARNATAKA';",
        ["college_count", "state_name"])
    # 21 to 40 English (Coverage of remaining states/UTs)
    add("indicdb-en-021", "en", "Latin", "Agriculture", "ndap_pm_kisan_disbursement", "easy",
        "How many farmer beneficiaries received PM-KISAN in Jammu and Kashmir?",
        "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'JAMMU AND KASHMIR';",
        ["farmer_beneficiaries", "state_name"])
    add("indicdb-en-022", "en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "How many hospitals are empanelled under Ayushman Bharat in Ladakh?",
        "SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'LADAKH';",
        ["empanelled_hospitals", "state_name"])
    add("indicdb-en-023", "en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "What is the total count of schools in Chandigarh?",
        "SELECT SUM(total_schools) FROM ndap_school_infrastructure WHERE state_name = 'CHANDIGARH';",
        ["total_schools", "state_name"])
    add("indicdb-en-024", "en", "Latin", "Agriculture", "ndap_crop_production_census", "medium",
        "What was the total rice production in Assam in tonnes?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'ASSAM' AND crop_name = 'RICE';",
        ["production_tonnes", "state_name", "crop_name"])
    add("indicdb-en-025", "en", "Latin", "Rural Development", "ndap_jal_jeevan_tap_water", "medium",
        "What is the average tap water coverage percentage in Goa?",
        "SELECT AVG(tap_connection_coverage_pct) FROM ndap_jal_jeevan_tap_water WHERE state_name = 'GOA';",
        ["tap_connection_coverage_pct", "state_name"])
    add("indicdb-en-026", "en", "Latin", "Rural Development", "mgnrega_state_annual_employment", "medium",
        "What is the total wage expenditure under MGNREGA in Bihar?",
        "SELECT SUM(total_wage_expenditure_inr) FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';",
        ["total_wage_expenditure_inr", "state_name"])
    add("indicdb-en-027", "en", "Latin", "Healthcare", "ndap_rural_health_infrastructure", "easy",
        "How many Primary Health Centres (PHC) are operational in Chhattisgarh?",
        "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'CHHATTISGARH';",
        ["primary_health_centres_phc", "state_name"])
    add("indicdb-en-028", "en", "Latin", "Education", "ndap_midday_meal_scheme", "medium",
        "How many primary students benefited from the Midday Meal Scheme in Jharkhand?",
        "SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme WHERE state_name = 'JHARKHAND';",
        ["primary_students_benefited", "state_name"])
    add("indicdb-en-029", "en", "Latin", "Healthcare", "ndap_maternal_child_mortality", "medium",
        "What was the recorded Maternal Mortality Ratio (MMR) in Madhya Pradesh?",
        "SELECT AVG(maternal_mortality_ratio_mmr) FROM ndap_maternal_child_mortality WHERE state_name = 'MADHYA PRADESH';",
        ["maternal_mortality_ratio_mmr", "state_name"])
    add("indicdb-en-030", "en", "Latin", "Agriculture", "ndap_fertilizer_distribution", "medium",
        "What was the total DAP requirement in Rajasthan in tonnes?",
        "SELECT SUM(requirement_tonnes) FROM ndap_fertilizer_distribution WHERE state_name = 'RAJASTHAN' AND fertilizer_type = 'DAP';",
        ["requirement_tonnes", "state_name", "fertilizer_type"])
    add("indicdb-en-031", "en", "Latin", "Skill Development", "ndap_vocational_skill_training", "medium",
        "How many candidates were placed in the Automotive sector in Maharashtra?",
        "SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE state_name = 'MAHARASHTRA' AND sector_skill_council = 'Automotive';",
        ["placed_candidates", "state_name", "sector_skill_council"])
    add("indicdb-en-032", "en", "Latin", "Education", "ndap_school_infrastructure", "easy",
        "How many schools in Uttarakhand have electricity facility?",
        "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'UTTARAKHAND';",
        ["schools_with_electricity", "state_name"])
    add("indicdb-en-033", "en", "Latin", "Agriculture", "ndap_soil_health_records", "easy",
        "What is the total number of tested soil samples in Haryana?",
        "SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE state_name = 'HARYANA';",
        ["samples_tested", "state_name"])
    add("indicdb-en-034", "en", "Latin", "Healthcare", "ndap_ayushman_bharat_pmjay", "medium",
        "What is the total claim settled amount under PMJAY in Chhattisgarh?",
        "SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'CHHATTISGARH';",
        ["claim_amount_settled_inr", "state_name"])
    add("indicdb-en-035", "en", "Latin", "Rural Development", "ndap_pmay_rural_housing", "medium",
        "What is the total fund transferred under PMAY rural housing in Jharkhand?",
        "SELECT SUM(funds_transferred_inr) FROM ndap_pmay_rural_housing WHERE state_name = 'JHARKHAND';",
        ["funds_transferred_inr", "state_name"])
    add("indicdb-en-036", "en", "Latin", "Education", "ndap_education_stats", "easy",
        "What is the total student count enrolled in Delhi schools?",
        "SELECT SUM(student_count) FROM ndap_education_stats WHERE state_name = 'DELHI';",
        ["student_count", "state_name"])
    add("indicdb-en-037", "en", "Latin", "Agriculture", "ndap_crop_production_census", "easy",
        "What was the total crop production in Uttarakhand in tonnes?",
        "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'UTTARAKHAND';",
        ["production_tonnes", "state_name"])
    add("indicdb-en-038", "en", "Latin", "Healthcare", "ndap_nfhs5_health_indicators", "medium",
        "What is the institutional births percentage in Rajasthan?",
        "SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE state_name = 'RAJASTHAN';",
        ["institutional_births_pct", "state_name"])
    add("indicdb-en-039", "en", "Latin", "Rural Development", "ndap_pmgsy_rural_roads", "medium",
        "How many habitations were connected under PMGSY in Himachal Pradesh?",
        "SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE state_name = 'HIMACHAL PRADESH';",
        ["habitations_connected", "state_name"])
    add("indicdb-en-040", "en", "Latin", "Agriculture", "ndap_mandi_commodity_prices", "medium",
        "What was the average modal price of wheat in Uttar Pradesh mandis?",
        "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'UTTAR PRADESH' AND commodity = 'Wheat';",
        ["modal_price_inr", "state_name", "commodity"])

    return queries


def main():
    print("=" * 75)
    print("🇮🇳 Generating & Validating Pan-India 280-Query IndicDB Benchmark Suite")
    print("=" * 75)

    items = build_pan_india_280_items()
    print(f"Total Queries Defined: {len(items)}")

    # Verify distribution
    from collections import Counter
    counts = Counter(it["language"] for it in items)
    for lang, c in counts.items():
        print(f"  • {lang.upper():<6}: {c} queries")

    # Strict Validation against DuckDB Sandbox
    print("\n🔍 Validating all 280 Gold SQL queries against authentic DuckDB stores...")
    sandbox = DuckDBSandbox()
    failed = 0
    for i, it in enumerate(items, start=1):
        sql = it["gold_sql"]
        res = sandbox.execute_query(sql)
        if not res or res.get("row_count", 0) == 0:
            print(f"[FAIL #{i:03d}] {it['query_id']} ({it['language']}) returned empty result! SQL: {sql}")
            failed += 1
        elif res.get("execution_error"):
            print(f"[FAIL #{i:03d}] {it['query_id']} execution error: {res['execution_error']}! SQL: {sql}")
            failed += 1

    if failed > 0:
        print(f"\n❌ Validation FAILED with {failed} errors! Fix queries before exporting.")
        sys.exit(1)

    print(f"\n✅ All {len(items)} queries executed flawlessly with authentic non-empty row results on DuckDB!")

    out_path = REPO_ROOT / "data" / "benchmarks" / "indicdb_eval_suite_pan_india_280.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"📁 Benchmark Suite exported successfully to:\n   {out_path}")
    print("=" * 75)


if __name__ == "__main__":
    main()

