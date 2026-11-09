#!/usr/bin/env python3
"""
scripts/build_unseen_140_benchmark.py
Synthesizes a brand new, unseen 140-query evaluation suite (20 queries x 7 languages).
Ensures 100% executable gold SQL validated directly against DuckDB parquet stores.

Domains Covered:
1. Agriculture (PM-Kisan, Crop Production, Fertilizers, Mandi Prices)
2. Rural Development (MGNREGA, PMAY Housing, PMGSY Roads, Jal Jeevan Mission, Panchayat Finance)
3. Education (School Infrastructure, AISHE Higher Education, Midday Meal, Literacy)
4. Healthcare & Nutrition (Ayushman Bharat, NFHS-5 Indicators, Rural Health, TB Portal, Mortality)
5. Skills & Livelihood (Vocational Training, Soil Health)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import duckdb
from indicsql.sandbox.duckdb_engine import DuckDBSandbox

OUTPUT_FILE = REPO_ROOT / "data" / "benchmarks" / "indicdb_unseen_suite_140.json"


def build_and_verify_unseen_suite():
    sandbox = DuckDBSandbox()

    # Base templates (20 diverse question archetypes across all 20 NDAP databases)
    # Each template defines (domain, table, columns, difficulty, gold_sql_template)
    # and natural language queries in all 7 languages.
    archetypes = [
        # Archetype 1: PM-Kisan State Beneficiaries
        {
            "domain": "Agriculture",
            "target_table": "ndap_pm_kisan_disbursement",
            "target_columns": ["farmer_beneficiaries", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'RAJASTHAN';",
            "queries": {
                "en": "How many total farmer beneficiaries received PM-Kisan support in Rajasthan?",
                "hi-en": "Rajasthan me PM-Kisan ke under total kitne farmers ko benefit mila?",
                "hi": "राजस्थान में पीएम-किसान के तहत कुल कितने किसानों को लाभ मिला?",
                "mr": "राजस्थानमध्ये पीएम-किसान योजनेचा लाभ एकूण किती शेतकऱ्यांना मिळाला?",
                "bn": "রাজস্থানে পিএম-কিষাণ প্রকল্পে মোট কতজন কৃষক সুবিধা পেয়েছেন?",
                "ta": "ராஜஸ்தானில் பிஎம்-கிசான் திட்டத்தின் கீழ் பயனடைந்த மொத்த விவசாயிகள் எத்தனை பேர்?",
                "te": "రాజస్థాన్‌లో పీఎం-కిసాన్ పథకం ద్వారా మొత్తం ఎంతమంది రైతులకు లబ్ధి చేకూరింది?",
            }
        },
        # Archetype 2: Crop Production by Commodity
        {
            "domain": "Agriculture",
            "target_table": "ndap_crop_production_census",
            "target_columns": ["production_tonnes", "crop_name", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT SUM(production_tonnes) AS total_production FROM ndap_crop_production_census WHERE state_name = 'GUJARAT' AND crop_name = 'SOYBEAN';",
            "queries": {
                "en": "What was the total production of soybean in Gujarat in tonnes?",
                "hi-en": "Gujarat me soybean crop ka total production kitna hua?",
                "hi": "गुजरात में सोयाबीन का कुल उत्पादन कितने टन हुआ?",
                "mr": "गुजरातमध्ये सोयाबीनचे एकूण उत्पादन किती टन झाले?",
                "bn": "গুজরাটে সয়াবিনের মোট উৎপাদন কত মেট্রিক টন হয়েছে?",
                "ta": "குஜராத்தில் சோயாபீனின் மொத்த உற்பத்தி எத்தனை டன்கள்?",
                "te": "గుజరాత్‌లో సోయాబీన్ మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
            }
        },
        # Archetype 3: Crop Area in Hectares
        {
            "domain": "Agriculture",
            "target_table": "ndap_crop_production_census",
            "target_columns": ["area_hectares", "crop_name", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT SUM(area_hectares) AS total_area FROM ndap_crop_production_census WHERE state_name = 'PUNJAB' AND crop_name = 'WHEAT';",
            "queries": {
                "en": "What is the total cultivation area of wheat in Punjab in hectares?",
                "hi-en": "Punjab me wheat cultivation ka total area kitne hectares hai?",
                "hi": "पंजाब में गेहूं की खेती का कुल क्षेत्रफल कितने हेक्टेयर है?",
                "mr": "पंजाबमध्ये गव्हाची लागवड किती हेक्टर क्षेत्रावर झाली?",
                "bn": "পাঞ্জাবে গমের মোট চাষের এলাকা কত হেক্টর?",
                "ta": "பஞ்சாபில் கோதுமை சாகுபடி பரப்பளவு எத்தனை ஹெக்டேர்?",
                "te": "పంజాబ్‌లో గోధుమ సాగు విస్తీర్ణం ఎన్ని హెక్టార్లు?",
            }
        },
        # Archetype 4: Fertilizer Sales
        {
            "domain": "Agriculture",
            "target_table": "ndap_fertilizer_distribution",
            "target_columns": ["sales_tonnes", "fertilizer_type", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT SUM(sales_tonnes) AS total_sales FROM ndap_fertilizer_distribution WHERE state_name = 'UTTAR PRADESH' AND fertilizer_type = 'DAP';",
            "queries": {
                "en": "What were the total sales of DAP fertilizer in Uttar Pradesh in tonnes?",
                "hi-en": "Uttar Pradesh me DAP fertilizer ki total sales kitni tonnes hui?",
                "hi": "उत्तर प्रदेश में डीएपी खाद की कुल बिक्री कितने टन हुई?",
                "mr": "उत्तर प्रदेशात डीएपी खताची एकूण विक्री किती टन झाली?",
                "bn": "উত্তর প্রদেশে ডিএপি সারের মোট বিক্রি কত মেট্রিক টন?",
                "ta": "உத்தரபிரதேசத்தில் டிஏபி உரத்தின் மொத்த விற்பனை எத்தனை டன்கள்?",
                "te": "ఉత్తరప్రదేశ్‌లో డీఏపీ ఎరువుల మొత్తం అమ్మకాలు ఎన్ని టన్నులు?",
            }
        },
        # Archetype 5: Mandi Max Price
        {
            "domain": "Agriculture",
            "target_table": "ndap_mandi_commodity_prices",
            "target_columns": ["modal_price_inr", "commodity", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';",
            "queries": {
                "en": "What was the average mandi price of wheat in Maharashtra?",
                "hi-en": "Maharashtra ki mandis me wheat ka average price kya raha?",
                "hi": "महाराष्ट्र की मंडियों में गेहूं का औसत मॉडल भाव क्या रहा?",
                "mr": "महाराष्ट्रातील बाजार समित्यांमध्ये गव्हाचा सरासरी भाव काय होता?",
                "bn": "মহারাষ্ট্রের বাজারগুলিতে গমের গড় মূল্য কত ছিল?",
                "ta": "மகாராஷ்டிரா சந்தைகளில் கோதுமையின் சராசரி மாதிரி விலை என்ன?",
                "te": "మహారాష్ట్ర మార్కెట్లలో గోధుమల సగటు ధర ఎంత?",
            }
        },
        # Archetype 6: MGNREGA Total Mandays Generated
        {
            "domain": "Rural Development",
            "target_table": "mgnrega_state_annual_employment",
            "target_columns": ["total_mandays_generated", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';",
            "queries": {
                "en": "How many total mandays were generated under MGNREGA in Bihar?",
                "hi-en": "Bihar me MGNREGA scheme me total kitne mandays generate hue?",
                "hi": "बिहार में मनरेगा योजना के तहत कुल कितने कार्य दिवस उत्पन्न किए गए?",
                "mr": "बिहारमध्ये मनरेगा अंतर्गत एकूण किती मनुष्य दिन रोजगार निर्माण झाला?",
                "bn": "বিহারে ১০০ দিনের কাজের প্রকল্পে মোট কত কর্মদিবস তৈরি হয়েছে?",
                "ta": "பீகாரில் மகாத்மா காந்தி ஊரக வேலை திட்டத்தில் உருவாக்கப்பட்ட மொத்த மனித வேலை நாட்கள் எத்தனை?",
                "te": "బీహార్‌లో ఉపాధి హామీ పథకం కింద ఎన్ని పనిదినాలు కల్పించబడ్డాయి?",
            }
        },
        # Archetype 7: PMAY Houses Completed
        {
            "domain": "Rural Development",
            "target_table": "ndap_pmay_rural_housing",
            "target_columns": ["houses_completed", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(houses_completed) AS total_houses FROM ndap_pmay_rural_housing WHERE state_name = 'ODISHA';",
            "queries": {
                "en": "How many rural houses were completed under PMAY in Odisha?",
                "hi-en": "Odisha me PMAY Gramin ke under total kitne houses complete hue?",
                "hi": "ओडिशा में पीएम आवास योजना ग्रामीण के तहत कुल कितने घर पूरे हुए?",
                "mr": "ओडिशामध्ये पीएम आवास ग्रामीण अंतर्गत एकूण किती घरे पूर्ण झाली?",
                "bn": "ওড়িশায় গ্রামীণ আবাস যোজনায় মোট কতগুলি বাড়ি তৈরি সম্পন্ন হয়েছে?",
                "ta": "ஒடிசாவில் பிரதம மந்திரி ஊரக குடியிருப்பு திட்டத்தில் கட்டி முடிக்கப்பட்ட வீடுகள் எத்தனை?",
                "te": "ఒడిశాలో పీఎంఏవై గ్రామీణ పథకం కింద పూర్తయిన మొత్తం ఇళ్ళు ఎన్ని?",
            }
        },
        # Archetype 8: PMGSY Road Length in KM
        {
            "domain": "Rural Development",
            "target_table": "ndap_pmgsy_rural_roads",
            "target_columns": ["completed_road_length_km", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';",
            "queries": {
                "en": "What is the total length of rural roads completed in Madhya Pradesh under PMGSY?",
                "hi-en": "Madhya Pradesh me PMGSY ke under total kitne km road construct hui?",
                "hi": "मध्य प्रदेश में पीएमजीएसवाई के तहत कुल कितने किलोमीटर सड़क का निर्माण हुआ?",
                "mr": "मध्य प्रदेशात पीएमजीएसवाय अंतर्गत एकूण किती किलोमीटर रस्त्यांचे बांधकाम पूर्ण झाले?",
                "bn": "মধ্যপ্রদেশে গ্রামীণ সড়ক যোজনায় মোট কত কিলোমিটার রাস্তা তৈরি হয়েছে?",
                "ta": "மத்தியப் பிரதேசத்தில் கிராமப்புற சாலை திட்டத்தில் முடிக்கப்பட்ட மொத்த சாலை நீளம் எத்தனை கி.மீ?",
                "te": "మధ్యప్రదేశ్‌లో గ్రామీణ రహదారుల పథకం కింద నిర్మించిన మొత్తం రోడ్ల పొడవు ఎన్ని కి.మీ?",
            }
        },
        # Archetype 9: Jal Jeevan Mission Tap Water Connections
        {
            "domain": "Water & Sanitation",
            "target_table": "ndap_jal_jeevan_tap_water",
            "target_columns": ["households_with_tap_connection", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(households_with_tap_connection) AS total_connections FROM ndap_jal_jeevan_tap_water WHERE state_name = 'TELANGANA';",
            "queries": {
                "en": "How many rural households have tap water connections under Jal Jeevan Mission in Telangana?",
                "hi-en": "Telangana me Jal Jeevan Mission ke under kitne households ko tap water connection mila?",
                "hi": "तेलंगाना में जल जीवन मिशन के तहत कुल कितने ग्रामीण परिवारों को नल जल कनेक्शन मिला?",
                "mr": "तेलंगणामध्ये जल जीवन मिशन अंतर्गत एकूण किती कुटुंबांना नळजोडणी मिळाली?",
                "bn": "তেলেঙ্গানায় জল জীবন মিশনে মোট কতগুলি গ্রামীণ পরিবারে ট্যাপ সংযোগ রয়েছে?",
                "ta": "தெலுங்கானாவில் ஜல் ஜீவன் திட்டத்தின் கீழ் குழாய் குடிநீர் இணைப்பு பெற்ற மொத்த கிராமப்புற குடும்பங்கள் எத்தனை?",
                "te": "తెలంగాణలో జల్ జీవన్ మిషన్ కింద కుళాయి కనెక్షన్లు పొందిన మొత్తం గ్రామీణ గృహాలు ఎన్ని?",
            }
        },
        # Archetype 10: Education Stats Female Literacy Rate by District
        {
            "domain": "Education",
            "target_table": "ndap_education_stats",
            "target_columns": ["female_literacy_rate", "district_name", "state_name"],
            "difficulty": "hard",
            "gold_sql": "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;",
            "queries": {
                "en": "Which district in Bihar recorded the lowest female literacy rate?",
                "hi-en": "Bihar ke kis district me female literacy rate sabse kam record hua?",
                "hi": "बिहार के किस जिले में सबसे कम महिला साक्षरता दर दर्ज की गई?",
                "mr": "बिहारमधील कोणत्या जिल्ह्यात महिला साक्षरतेचे प्रमाण सर्वात कमी नोंदवले गेले?",
                "bn": "বিহারের কোন জেলায় মহিলা সাক্ষরতার হার সবচেয়ে কম রেকর্ড করা হয়েছে?",
                "ta": "பீகாரில் பெண் கல்வியறிவு விகிதம் மிகக் குறைவாக பதிவான மாவட்டம் எது?",
                "te": "బీహార్‌లో మహిళా అక్షరాస్యత రేటు అత్యల్పంగా నమోదైన జిల్లా ఏది?",
            }
        },
        # Archetype 11: School Infrastructure with Computer Labs
        {
            "domain": "Education",
            "target_table": "ndap_school_infrastructure",
            "target_columns": ["schools_with_computer_labs", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(schools_with_computer_labs) AS total_schools FROM ndap_school_infrastructure WHERE state_name = 'KERALA';",
            "queries": {
                "en": "How many schools in Kerala have functional computer labs?",
                "hi-en": "Kerala me computer lab facility wale total kitne schools hain?",
                "hi": "केरल में कंप्यूटर लैब की सुविधा वाले कुल कितने स्कूल हैं?",
                "mr": "केरळमध्ये संगणक प्रयोगशाळा सुविधा असलेल्या एकूण शाळांची संख्या किती?",
                "bn": "কেরালাতে কম্পিউটার ল্যাব সুবিধা থাকা স্কুলের মোট সংখ্যা কত?",
                "ta": "கேரளாவில் கணினி ஆய்வக வசதி கொண்ட மொத்த பள்ளிகள் எத்தனை?",
                "te": "కేరళలో కంప్యూటర్ ల్యాబ్ సదుపాయం ఉన్న పాఠశాలల మొత్తం సంఖ్య ఎంత?",
            }
        },
        # Archetype 12: School Electricity Facility by District
        {
            "domain": "Education",
            "target_table": "ndap_school_infrastructure",
            "target_columns": ["schools_with_electricity", "district_name", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
            "queries": {
                "en": "How many schools in Pune district have electricity facility?",
                "hi-en": "Pune district me electricity facility wale schools kitne hain?",
                "hi": "पुणे जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?",
                "mr": "पुणे जिल्ह्यातील वीज सुविधा असलेल्या शाळांची संख्या किती आहे?",
                "bn": "পুনে জেলায় বিদ্যুৎ সংযোগ থাকা স্কুলের সংখ্যা কত?",
                "ta": "புனே மாவட்டத்தில் மின்சார வசதி கொண்ட பள்ளிகள் எத்தனை?",
                "te": "పుణే జిల్లాలో విద్యుత్ సదుపాయం ఉన్న పాఠశాలల సంఖ్య ఎంత?",
            }
        },
        # Archetype 13: AISHE Higher Education Faculty Count
        {
            "domain": "Education",
            "target_table": "ndap_higher_education_aishe",
            "target_columns": ["total_faculty_count", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';",
            "queries": {
                "en": "What is the total number of college faculty members in Tamil Nadu?",
                "hi-en": "Tamil Nadu me higher education me total kitne faculty members hain?",
                "hi": "तमिलनाडु में उच्च शिक्षा संस्थानों में कुल कितने शिक्षक कार्यरत हैं?",
                "mr": "तामिळनाडूमध्ये उच्च शिक्षण संस्थांमध्ये एकूण किती प्राध्यापक कार्यरत आहेत?",
                "bn": "তামিলনাড়ুতে উচ্চশিক্ষা প্রতিষ্ঠানগুলিতে মোট কতজন শিক্ষক রয়েছেন?",
                "ta": "தமிழ்நாட்டில் உள்ள கல்லூரிகளில் பணிபுரியும் மொத்த பேராசிரியர்களின் எண்ணிக்கை என்ன?",
                "te": "తమిళనాడులోని కళాశాలల్లో మొత్తం ఎంతమంది అధ్యాపకులు పనిచేస్తున్నారు?",
            }
        },
        # Archetype 14: Midday Meal Primary Students Benefited
        {
            "domain": "Education & Nutrition",
            "target_table": "ndap_midday_meal_scheme",
            "target_columns": ["primary_students_benefited", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(primary_students_benefited) AS total_students FROM ndap_midday_meal_scheme WHERE state_name = 'WEST BENGAL';",
            "queries": {
                "en": "How many primary school children benefited from the Midday Meal Scheme in West Bengal?",
                "hi-en": "West Bengal me Midday Meal scheme se kitne primary school students ko labh mila?",
                "hi": "पश्चिम बंगाल में मध्याह्न भोजन योजना से लाभान्वित प्राथमिक छात्रों की कुल संख्या कितनी है?",
                "mr": "पश्चिम बंगालमध्ये माध्यान्ह भोजन योजनेचा लाभ मिळालेल्या प्राथमिक विद्यार्थ्यांची संख्या किती?",
                "bn": "পশ্চিমবঙ্গে মিড ডে মিল প্রকল্পের সুবিধাভোগী প্রাথমিক শিক্ষার্থীদের সংখ্যা কত?",
                "ta": "மேற்கு வங்கத்தில் மதிய உணவுத் திட்டத்தால் பயனடைந்த தொடக்கப்பள்ளி மாணவர்கள் எத்தனை பேர்?",
                "te": "పశ్చిమ బెంగాల్‌లో మధ్యాహ్న భోజన పథకం ద్వారా ప్రయోజనం పొందిన ప్రాథమిక విద్యార్థులు ఎంతమంది?",
            }
        },
        # Archetype 15: Ayushman Bharat PM-JAY Cards Issued
        {
            "domain": "Healthcare",
            "target_table": "ndap_ayushman_bharat_pmjay",
            "target_columns": ["cards_issued", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(cards_issued) AS total_cards FROM ndap_ayushman_bharat_pmjay WHERE state_name = 'ASSAM';",
            "queries": {
                "en": "How many Ayushman Bharat PM-JAY cards were issued in Assam?",
                "hi-en": "Assam me Ayushman Bharat PM-JAY ke total kitne cards issue hue?",
                "hi": "असम में आयुष्मान भारत पीएम-जय के तहत कुल कितने कार्ड जारी किए गए?",
                "mr": "आसाममध्ये आयुष्मान भारत योजनेअंतर्गत एकूण किती कार्ड्स जारी करण्यात आली?",
                "bn": "আসামে আয়ুষ্মান ভারত প্রকল্পে মোট কতগুলি কার্ড ইস্যু করা হয়েছে?",
                "ta": "அசாமில் ஆயுஷ்மான் பாரத் திட்டத்தின் கீழ் வழங்கப்பட்ட மொத்த அட்டைகள் எத்தனை?",
                "te": "అస్సాంలో ఆయుష్మాన్ భారత్ పథకం కింద జారీ చేసిన మొత్తం కార్డుల సంఖ్య ఎంత?",
            }
        },
        # Archetype 16: Rural Health Infrastructure PHC Count
        {
            "domain": "Healthcare",
            "target_table": "ndap_rural_health_infrastructure",
            "target_columns": ["primary_health_centres_phc", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
            "queries": {
                "en": "How many primary health centres (PHCs) are operational in Haryana?",
                "hi-en": "Haryana me total kitne primary health centres (PHC) chal rahe hain?",
                "hi": "हरियाणा में कुल कितने प्राथमिक स्वास्थ्य केंद्र संचालित हैं?",
                "mr": "हरियाणामध्ये एकूण किती प्राथमिक आरोग्य केंद्रे कार्यरत आहेत?",
                "bn": "হরিয়ানায় মোট কতগুলি প্রাথমিক স্বাস্থ্য কেন্দ্র চালু রয়েছে?",
                "ta": "ஹரியானாவில் செயல்படும் மொத்த ஆரம்ப சுகாதார நிலையங்கள் எத்தனை?",
                "te": "హర్యానాలో పనిచేస్తున్న మొత్తం ప్రాథమిక ఆరోగ్య కేంద్రాల సంఖ్య ఎంత?",
            }
        },
        # Archetype 17: National TB Portal Notified Patients
        {
            "domain": "Healthcare",
            "target_table": "ndap_national_tuberculosis_portal",
            "target_columns": ["total_notified_patients", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
            "queries": {
                "en": "What is the total number of TB patients notified in Karnataka?",
                "hi-en": "Karnataka me Nikshay portal par total kitne TB patients notify hue?",
                "hi": "कर्नाटक में निक्षय पोर्टल पर कुल कितने टीबी के मरीज अधिसूचित किए गए?",
                "mr": "कर्नाटकात एकूण किती क्षयरोग रुग्णांची नोंद करण्यात आली?",
                "bn": "কর্ণাটকে মোট কতজন যক্ষ্মা রোগী সরকারিভাবে নথিভুক্ত হয়েছেন?",
                "ta": "கர்நாடகாவில் பதிவு செய்யப்பட்ட மொத்த காசநோய் நோயாளிகள் எத்தனை பேர்?",
                "te": "కర్ణాటకలో నోటిఫై చేయబడిన మొత్తం టీబీ రోగుల సంఖ్య ఎంత?",
            }
        },
        # Archetype 18: NFHS-5 Institutional Deliveries Percentage
        {
            "domain": "Healthcare",
            "target_table": "ndap_nfhs5_health_indicators",
            "target_columns": ["institutional_births_pct", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';",
            "queries": {
                "en": "What is the average percentage of institutional deliveries in Andhra Pradesh according to NFHS-5?",
                "hi-en": "NFHS-5 ke according Andhra Pradesh me institutional delivery ka average percentage kya hai?",
                "hi": "एनएफएचएस-5 के अनुसार आंध्र प्रदेश में संस्थागत प्रसव का औसत प्रतिशत क्या है?",
                "mr": "एनएफएचएस-५ नुसार आंध्र प्रदेशात संस्थात्मक प्रसूतीचे सरासरी प्रमाण किती टक्के आहे?",
                "bn": "এনএফএইচএস-৫ অনুসারে অন্ধ্রপ্রদেশে প্রাতিষ্ঠানিক প্রসবের গড় হার কত শতাংশ?",
                "ta": "தேசிய குடும்ப சுகாதார ஆய்வின்படி ஆந்திராவில் மருத்துவமனைகளில் நிகழ்ந்த பிரசவங்களின் சராசரி சதவீதம் என்ன?",
                "te": "ఎన్ఎఫ్ హెచ్ ఎస్-5 ప్రకారం ఆంధ్రప్రదేశ్‌లో సంస్థాగత ప్రసవాల సగటు శాతం ఎంత?",
            }
        },
        # Archetype 19: Soil Health Samples Tested
        {
            "domain": "Agriculture",
            "target_table": "ndap_soil_health_records",
            "target_columns": ["samples_tested", "district_name", "state_name"],
            "difficulty": "medium",
            "gold_sql": "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';",
            "queries": {
                "en": "How many soil samples were tested in Coimbatore district under Soil Health Card Scheme?",
                "hi-en": "Coimbatore district me Soil Health Card yojana ke under kitne soil samples test hue?",
                "hi": "कोयंबटूर जिले में मृदा स्वास्थ्य कार्ड योजना के तहत कितने मिट्टी के नमूनों की जांच की गई?",
                "mr": "कोईम्बतूर जिल्ह्यात मृदा आरोग्य पत्रिका अंतर्गत मातीचे किती नमुने तपासण्यात आले?",
                "bn": "কোয়েম্বাটোর জেলায় সয়েল হেলথ কার্ড প্রকল্পের অধীনে কতগুলি মাটির নমুনা পরীক্ষা করা হয়েছে?",
                "ta": "கோயம்புத்தூர் மாவட்டத்தில் ஆய்வு செய்யப்பட்ட மண் மாதிரிகள் எத்தனை?",
                "te": "కోయంబత్తూర్ జిల్లాలో సాయిల్ హెల్త్ కార్డ్ పథకం కింద ఎన్ని నేల నమూనాలను పరీక్షించారు?",
            }
        },
        # Archetype 20: Vocational Skill Certified Candidates
        {
            "domain": "Skill Development",
            "target_table": "ndap_vocational_skill_training",
            "target_columns": ["certified_candidates", "state_name"],
            "difficulty": "easy",
            "gold_sql": "SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';",
            "queries": {
                "en": "How many candidates received skill certification under vocational training in Jharkhand?",
                "hi-en": "Jharkhand me vocational skill training ke under total kitne candidates certified hue?",
                "hi": "झारखंड में व्यावसायिक कौशल प्रशिक्षण के तहत कुल कितने उम्मीदवार प्रमाणित हुए?",
                "mr": "झारखंडमध्ये व्यावसायिक कौशल्य प्रशिक्षणांतर्गत एकूण किती उमेदवार प्रमाणित झाले?",
                "bn": "ঝাড়খণ্ডে বৃত্তিমূলক দক্ষতা প্রশিক্ষণের অধীনে মোট কতজন প্রার্থী সনদপ্রাপ্ত হয়েছেন?",
                "ta": "ஜார்கண்டில் தொழிற்கல்வி திறன் பயிற்சியில் தேர்ச்சி பெற்று சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?",
                "te": "జార్ఖండ్‌లో వృత్తి విద్యా నైపుణ్య శిక్షణ కింద సర్టిఫికేట్ పొందిన మొత్తం అభ్యర్థులు ఎంతమంది?",
            }
        },
    ]

    print("=" * 80)
    print("Synthesizing and Validating Brand New 140-Query Unseen Evaluation Suite")
    print("=" * 80)

    languages = ["en", "hi-en", "hi", "mr", "bn", "ta", "te"]
    script_map = {
        "en": "Latin",
        "hi-en": "Latin",
        "hi": "Devanagari",
        "mr": "Devanagari",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
    }

    full_instances = []
    failed_sql = 0

    for arch_idx, arch in enumerate(archetypes, 1):
        gold_sql = arch["gold_sql"]
        # Validate that the gold SQL runs on DuckDB parquet stores
        res = sandbox.execute_query(gold_sql)
        if not res or res.get("rows") is None:
            print(f"❌ SQL Verification FAILED on archetype {arch_idx}: {gold_sql}")
            failed_sql += 1
            continue

        rows = res.get("rows", [])
        if not rows or rows[0][0] is None:
            print(f"⚠️ Warning: Query returned None/empty: {gold_sql}")

        for lang in languages:
            q_id = f"unseen-{lang}-{arch_idx:03d}"
            q_text = arch["queries"][lang]
            instance = {
                "query_id": q_id,
                "query": q_text,
                "language": lang,
                "script": script_map[lang],
                "domain": arch["domain"],
                "target_table": arch["target_table"],
                "gold_sql": gold_sql,
                "difficulty": arch["difficulty"],
                "target_columns": arch["target_columns"],
            }
            full_instances.append(instance)

    if failed_sql > 0:
        print(f"Aborting: {failed_sql} SQL templates failed DuckDB validation.")
        return False

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_instances, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully created and validated {len(full_instances)} queries in {OUTPUT_FILE}")
    print(f"Distribution: {len(full_instances) // len(languages)} queries per language across 7 languages.")
    return True


if __name__ == "__main__":
    build_and_verify_unseen_suite()
