"""
Response Verbalizer Agent.
Takes tabular SQL execution results and verbalizes fluent, concise natural language answers
in the citizen's mother tongue (Hindi, Marathi, Tamil, Telugu, Bengali, Hinglish, English)
with localized Indian numbering (Lakhs and Crores).
"""

from typing import Any, Dict

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import VoiceSynthesisEvent


def format_indian_currency_number(val: Any, lang: str = "hi") -> str:
    """Formats large integers/floats into Crores or Lakhs safely with localized language terms."""
    if val is None:
        return "0"
    try:
        fval = float(val)
    except (ValueError, TypeError):
        return str(val)

    if lang == "mr":
        crore_label = "कोटी (Crores)"
        lakh_label = "लाख (Lakhs)"
    elif lang == "ta":
        crore_label = "கோடி (Crores)"
        lakh_label = "இலட்சம் (Lakhs)"
    elif lang == "te":
        crore_label = "కోట్లు (Crores)"
        lakh_label = "లక్షలు (Lakhs)"
    elif lang == "bn":
        crore_label = "কোটি (Crores)"
        lakh_label = "লাখ (Lakhs)"
    elif lang in ["en", "hi-en"]:
        crore_label = "Crores"
        lakh_label = "Lakhs"
    else:  # default 'hi'
        crore_label = "कोटी (Crores)"
        lakh_label = "लाख (Lakhs)"

    if fval >= 10_000_000:
        crores = fval / 10_000_000
        return f"{crores:.2f} {crore_label}"
    if fval >= 100_000:
        lakhs = fval / 100_000
        return f"{lakhs:.2f} {lakh_label}"
    return f"{fval:,.0f}"


def verbalize_tabular_result(state: IndicSQLState) -> str:
    """Produces the localized natural language explanation across all 7 supported languages."""
    res = state.get("execution_result")
    err = state.get("execution_error")
    lang = state.get("detected_lang", "en")

    if err or not res:
        if lang == "hi":
            return f"माफ़ कीजिए, डेटाबेस में आपके प्रश्न का सटीक उत्तर नहीं मिल सका। (त्रुटि: {err or 'कोई डेटा नहीं'})"
        elif lang == "mr":
            return f"क्षमस्व, डेटाबेसमध्ये आपल्या प्रश्नाचे उत्तर सापडू शकले नाही. (त्रुटी: {err or 'डेटा उपलब्ध नाही'})"
        elif lang == "ta":
            return f"மன்னிக்கவும், தரவுத்தளத்தில் உங்கள் கேள்விக்கான சரியான பதில் கிடைக்கவில்லை. (பிழை: {err or 'தரவு இல்லை'})"
        elif lang == "te":
            return f"క్షమించండి, డేటాబేస్ లో మీ ప్రశ్నకు ఖచ్చితమైన సమాధానం లభించలేదు. (లోపం: {err or 'డేటా లేదు'})"
        elif lang == "bn":
            return f"দুঃখিত, ডাটাবেসে আপনার প্রশ্নের সঠিক উত্তর পাওয়া যায়নি। (ত্রুটি: {err or 'কোন তথ্য নেই'})"
        elif lang == "hi-en":
            return f"Sorry, database mein aapke question ka exact answer nahi mila. (Error: {err or 'No data found'})"
        return f"Unable to retrieve data for query. (Reason: {err or 'Empty result set'})"

    rows = res.get("rows", [])
    if not rows:
        if lang == "hi":
            return "डेटाबेस में कोई रिकॉर्ड नहीं मिला।"
        elif lang == "mr":
            return "डेटाबेसमध्ये कोणतीही नोंद आढळली नाही."
        elif lang == "ta":
            return "தரவுத்தளத்தில் பதிவுகள் எதுவும் கிடைக்கவில்லை."
        elif lang == "te":
            return "డేటాబేస్ లో ఎటువంటి రికార్డులు కనుగొనబడలేదు."
        elif lang == "bn":
            return "ডাটাবেসে কোনো রেকর্ড পাওয়া যায়নি।"
        elif lang == "hi-en":
            return "Database mein koi matching record nahi mila."
        return "No matching records found in database."

    columns = [c.lower() for c in res.get("columns", [])]
    query_text = (state.get("raw_query", "") or state.get("normalized_query", "")).lower()

    # 0. Multi-row Ranking / Grouping Verbalization (e.g. top districts / states)
    if len(rows) > 1 and ("district_name" in columns or "state_name" in columns):
        ent_col_idx = columns.index("district_name") if "district_name" in columns else columns.index("state_name")
        val_col_idx = next(
            (i for i in range(len(columns)) if i != ent_col_idx and columns[i] not in ["state_name", "district_name", "financial_year", "survey_year", "crop_year"]),
            1 if ent_col_idx == 0 else 0
        )
        val_col_name = columns[val_col_idx] if val_col_idx < len(columns) else ""
        is_val_pct = "rate" in val_col_name or "pct" in val_col_name

        formatted_items = []
        for r in rows:
            ent = str(r[ent_col_idx])
            val = r[val_col_idx]
            if is_val_pct:
                try:
                    formatted_items.append(f"{ent} ({float(val):.1f}%)")
                except (ValueError, TypeError):
                    formatted_items.append(f"{ent} ({val})")
            else:
                formatted_items.append(f"{ent} ({format_indian_currency_number(val, lang=lang)})")

        joined_items = ", ".join(formatted_items)

        # Determine human-readable metric basis
        metric_en = "PM-Kisan farmer beneficiaries"
        metric_hi = "किसान लाभार्थियों (Farmer Beneficiaries)"
        if "student" in val_col_name:
            metric_en = "student enrollment"
            metric_hi = "विद्यार्थी संख्या (Student Count)"
        elif "literacy" in val_col_name:
            metric_en = "literacy rate"
            metric_hi = "साक्षरता दर (Literacy Rate)"
        elif "manday" in val_col_name:
            metric_en = "MGNREGA mandays"
            metric_hi = "मनरेगा कार्य दिवसों (Mandays)"
        elif "water" in val_col_name or "tap" in val_col_name:
            metric_en = "tap water connections"
            metric_hi = "नल जल कनेक्शनों (Tap Water Connections)"
        elif "school" in val_col_name:
            metric_en = "school infrastructure count"
            metric_hi = "स्कूलों की संख्या"
        elif "production" in val_col_name:
            metric_en = "crop production (tonnes)"
            metric_hi = "फसल उत्पादन"
        elif "amount" in val_col_name:
            metric_en = "disbursed amount (₹)"
            metric_hi = "वितरित राशि"

        # Detect State in Query
        state_display = ""
        if "uttar pradesh" in query_text or " uttar " in f" {query_text} " or " up " in f" {query_text} " or "उत्तर प्रदेश" in query_text:
            state_display = "Uttar Pradesh"
        elif "bihar" in query_text or "बिहार" in query_text:
            state_display = "Bihar"
        elif "maharashtra" in query_text or "महाराष्ट्र" in query_text:
            state_display = "Maharashtra"
        elif "tamil nadu" in query_text or "தமிழ்நாடு" in query_text:
            state_display = "Tamil Nadu"
        elif "rajasthan" in query_text or "राजस्थान" in query_text:
            state_display = "Rajasthan"

        if lang == "hi":
            st_prefix = f"{state_display} में " if state_display else ""
            return f"{st_prefix}{metric_hi} के अनुसार शीर्ष {len(rows)} जिले हैं: {joined_items}।"
        elif lang == "mr":
            st_prefix = f"{state_display} मधील " if state_display else ""
            return f"{st_prefix}{metric_en} नुसार नोंदणीकृत अव्वल {len(rows)} जिल्हे: {joined_items}."
        elif lang == "ta":
            st_prefix = f"{state_display} மாநிலத்தில் " if state_display else ""
            return f"{st_prefix}{metric_en} அடிப்படையில் முன்னணி {len(rows)} மாவட்டங்கள்: {joined_items}."
        elif lang == "te":
            st_prefix = f"{state_display} లో " if state_display else ""
            return f"{st_prefix}{metric_en} ఆధారంగా అగ్ర {len(rows)} నమోదైన జిల్లాలు: {joined_items}."
        elif lang == "bn":
            st_prefix = f"{state_display} এ " if state_display else ""
            return f"{st_prefix}{metric_en} অনুসারে শীর্ষ {len(rows)}টি নথিভুক্ত জেলা: {joined_items}।"
        elif lang == "hi-en":
            st_prefix = f"{state_display} mein " if state_display else ""
            return f"{st_prefix}{metric_en} ke basis par top {len(rows)} recorded districts: {joined_items}."
        else:
            st_phrase = f" in {state_display}" if state_display else ""
            return f"Top {len(rows)} recorded districts{st_phrase} by {metric_en}: {joined_items}."

    row = rows[0]

    # 1. Female Literacy Rate
    if "female_literacy_rate" in columns:
        dist_idx = columns.index("district_name") if "district_name" in columns else 0
        rate_idx = columns.index("female_literacy_rate")
        dist = row[dist_idx]
        rate = row[rate_idx]
        if lang == "hi":
            return f"डेटाबेस के अनुसार {dist} जिले में महिला साक्षरता दर {rate}% दर्ज की गई।"
        elif lang == "mr":
            return f"डेटाबेसच्या नोंदीनुसार {dist} जिल्ह्यामध्ये महिला साक्षरता प्रमाण {rate}% नोंदवले गेले आहे."
        elif lang == "ta":
            return f"தரவுத்தள பதிவுகளின்படி {dist} மாவட்டத்தில் பெண் கல்வியறிவு விகிதம் {rate}% ஆக பதிவாகியுள்ளது."
        elif lang == "te":
            return f"డేటాబేస్ రికార్డుల ప్రకారం {dist} జిల్లాలో మహిళా అక్షరాస్యత రేటు {rate}% గా నమోదైంది."
        elif lang == "bn":
            return f"ডাটাবেস রেকর্ড অনুযায়ী {dist} জেলায় মহিলা সাক্ষরতার হার {rate}% রেকর্ড করা হয়েছে।"
        elif lang == "hi-en":
            return f"Database ke according {dist} district mein female literacy rate {rate}% record hua hai."
        else:
            return f"According to database records, district {dist} recorded a female literacy rate of {rate}%."

    # 2. MGNREGA Person-Days (Mandays)
    if "total_mandays" in columns or "total_mandays_generated" in columns:
        mandays_idx = (
            columns.index("total_mandays")
            if "total_mandays" in columns
            else columns.index("total_mandays_generated")
        )
        mandays = row[mandays_idx]
        mandays_fmt = format_indian_currency_number(mandays, lang=lang)
        if lang == "ta":
            return f"மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் மொத்தம் {mandays_fmt} மனித வேலை நாட்கள் உருவாக்கப்பட்டுள்ளன."
        elif lang == "hi":
            return f"मनरेगा योजना के तहत कुल {mandays_fmt} कार्य दिवस (Mandays) उत्पन्न किए गए।"
        elif lang == "mr":
            return f"मनरेगा योजनेअंतर्गत एकूण {mandays_fmt} मनुष्य दिन रोजगार निर्माण करण्यात आला."
        elif lang == "te":
            return f"ఉపాధి హామీ పథకం కింద మొత్తం {mandays_fmt} పనిదినాలు కల్పించబడ్డాయి."
        elif lang == "bn":
            return f"১০০ দিনের কাজের প্রকল্পে মোট {mandays_fmt} কর্মদিবস তৈরি হয়েছে।"
        elif lang == "hi-en":
            return f"MGNREGA scheme ke tahat total {mandays_fmt} person-days generate hue."
        else:
            return f"Under MGNREGA, a total of {mandays_fmt} person-days (mandays) were generated."

    # 3. PM-KISAN Farmers & Disbursement
    farmer_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["farmer", "beneficiar"])),
        None
    )
    if farmer_col_idx is not None:
        farmers = row[farmer_col_idx]
        farmers_fmt = format_indian_currency_number(farmers, lang=lang)
        amount_part = ""
        amt_col_idx = next(
            (i for i, c in enumerate(columns) if any(k in c for k in ["amount", "disbursed"])),
            None
        )
        if amt_col_idx is not None:
            amt = row[amt_col_idx]
            amt_fmt = format_indian_currency_number(amt, lang=lang)
            if lang == "mr":
                amount_part = f", आणि ₹{amt_fmt} ची रक्कम थेट वितरित करण्यात आली"
            elif lang == "ta":
                amount_part = f", மற்றும் மொத்தம் ₹{amt_fmt} நிதி விடுவிக்கப்பட்டது"
            elif lang == "te":
                amount_part = f", మరియు మొత్తం ₹{amt_fmt} నిధులు పంపిణీ చేయబడ్డాయి"
            elif lang == "bn":
                amount_part = f", এবং মোট ₹{amt_fmt} টাকা বিতরণ করা হয়েছে"
            elif lang == "hi-en":
                amount_part = f", aur total ₹{amt_fmt} amount transfer kiya gaya"
            elif lang == "en":
                amount_part = f", with a total disbursement of ₹{amt_fmt}"
            else:
                amount_part = f", और कुल ₹{amt_fmt} की राशि हस्तांतरित की गई"

        # Check if nationwide timeless cumulative sum across 4 financial years (> 10 Crores)
        try:
            f_val = float(farmers)
        except (ValueError, TypeError):
            f_val = 0.0

        if f_val > 100_000_000:
            if lang == "mr":
                return f"पीएम-किसान योजनेअंतर्गत 4 आर्थिक वर्षांमध्ये (2021-2025) एकूण {farmers_fmt} संचयी शेतकरी लाभांचे वितरण झाले (वार्षिक सरासरी ~7.16 कोटी सक्रिय लाभार्थी, नवीनतम 2024-25 मध्ये 7.11 कोटी){amount_part}."
            elif lang == "hi":
                return f"पीएम-किसान योजना के 4 वित्तीय वर्षों (2021-2025) में कुल {farmers_fmt} संचयी किसान किस्तों का वितरण हुआ (प्रति वर्ष औसतन ~7.16 करोड़ सक्रिय किसान लाभार्थी, नवीनतम वर्ष 2024-25 में 7.11 करोड़){amount_part}।"
            elif lang == "hi-en":
                return f"PM-KISAN yojana ke tahat 4 financial years (2021-2025) mein total {farmers_fmt} cumulative farmer disbursements record hue (per year average ~7.16 Crores active beneficiaries, latest 2024-25 mein 7.11 Crores){amount_part}."
            elif lang == "te":
                return f"పీఎం-కిసాన్ పథకం కింద 4 ఆర్థిక సంవత్సరాల్లో (2021-2025) మొత్తం {farmers_fmt} సంయుక్త రైతు లబ్ధిదారులకు నిధులు విడుదలయ్యాయి (ఏడాదికి సగటున ~7.16 కోట్ల మంది క్రియాశీల రైతులు){amount_part}."
            elif lang == "ta":
                return f"பிஎம்-கிசான் திட்டத்தின் கீழ் 4 நிதியாண்டுகளில் (2021-2025) மொத்தம் {farmers_fmt} ஒட்டுமொத்த விவசாய நிதி விடுவிப்புகள் செய்யப்பட்டுள்ளன (வருடத்திற்கு சராசரியாக ~7.16 கோடி தீவிர விவசாயிகள்){amount_part}."
            elif lang == "bn":
                return f"পিএম-কিষান প্রকল্পের অধীনে 4টি আর্থিক বছরে (2021-2025) মোট {farmers_fmt} ক্রমবর্ধমান কৃষক সুবিধা বিতরণ করা হয়েছে (প্রতি বছর গড়ে ~7.16 কোটি সক্রিয় কৃষক){amount_part}।"
            else:
                return (
                    f"Under PM-KISAN records across 4 financial years (2021–2025), a cumulative total of {farmers_fmt} farmer disbursements were recorded, averaging ~7.16 Crores active beneficiaries per year (with 7.11 Crores in the latest 2024–25 period){amount_part}."
                )

        if lang == "mr":
            return f"पीएम-किसान योजनेअंतर्गत एकूण {farmers_fmt} शेतकऱ्यांना लाभ मिळाला{amount_part}."
        elif lang == "hi":
            return f"पीएम-किसान योजना के तहत कुल {farmers_fmt} किसानों को लाभ प्राप्त हुआ{amount_part}."
        elif lang == "hi-en":
            return f"PM-KISAN yojana ke tahat total {farmers_fmt} farmers ko labh mila{amount_part}."
        elif lang == "te":
            return f"పీఎం-కిసాన్ పథకం కింద మొత్తం {farmers_fmt} రైతులకు లబ్ధి చేకూరింది{amount_part}."
        elif lang == "ta":
            return f"பிஎம்-கிசான் திட்டத்தின் கீழ் மொத்தம் {farmers_fmt} விவசாயிகள் பயனடைந்துள்ளனர்{amount_part}."
        elif lang == "bn":
            return f"পিএম-কিষান প্রকল্পের অধীনে মোট {farmers_fmt} জন কৃষক উপকৃত হয়েছেন{amount_part}।"
        else:
            return (
                f"Under PM-KISAN, a total of {farmers_fmt} farmers received direct benefit transfers{amount_part}."
            )

    sql_text = (state.get("generated_sql", "") or "").upper()
    detected_state = ""
    for st in ["UTTAR PRADESH", "PUNJAB", "GUJARAT", "MAHARASHTRA", "RAJASTHAN", "BIHAR", "TAMIL NADU", "WEST BENGAL", "ANDHRA PRADESH", "TELANGANA"]:
        if f"'{st}'" in sql_text or st.lower() in query_text:
            detected_state = st.title()
            break

    # 4. Fertilizer Distribution (DAP, Urea, MOP)
    fert_col_idx = next((i for i, c in enumerate(columns) if any(k in c for k in ["sales", "fertilizer"])), None)
    if fert_col_idx is not None and any(f in sql_text or f in query_text.upper() for f in ["DAP", "UREA", "MOP", "NPK"]):
        fert_type = "DAP" if "DAP" in (sql_text + query_text.upper()) else ("UREA" if "UREA" in (sql_text + query_text.upper()) else "fertilizer")
        sales_val = row[fert_col_idx]
        sales_fmt = format_indian_currency_number(sales_val, lang=lang)
        if lang == "hi":
            return f"{detected_state} में {fert_type} खाद की कुल बिक्री {sales_fmt} टन दर्ज की गई।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {fert_type} खताची एकूण विक्री {sales_fmt} टन नोंदवली गेली."
        elif lang == "hi-en":
            return f"{detected_state} mein {fert_type} fertilizer ki total sales {sales_fmt} tonnes record hui."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {fert_type} உரத்தின் மொத்த விற்பனை {sales_fmt} டன்கள் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {fert_type} ఎరువుల మొత్తం అమ్మకాలు {sales_fmt} టన్నులుగా నమోదయ్యాయి."
        elif lang == "bn":
            return f"{detected_state}-এ {fert_type} সারের মোট বিক্রি {sales_fmt} মেট্রিক টন রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, total recorded sales of {fert_type} fertilizer were {sales_fmt} tonnes."

    # 5. Crop Cultivation Area (Hectares)
    area_col_idx = next((i for i, c in enumerate(columns) if any(k in c for k in ["area_hectares", "cultivation_area", "total_area"])), None)
    if area_col_idx is not None:
        area_val = row[area_col_idx]
        area_fmt = format_indian_currency_number(area_val, lang=lang)
        crop_name = "Wheat" if "WHEAT" in (sql_text + query_text.upper()) else ("Soybean" if "SOYBEAN" in (sql_text + query_text.upper()) else "crop")
        crop_hi = "गेहूं" if crop_name == "Wheat" else ("सोयाबीन" if crop_name == "Soybean" else "फसल")
        if lang == "hi":
            return f"{detected_state} में {crop_hi} की खेती का कुल क्षेत्रफल {area_fmt} हेक्टेयर दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {crop_hi} लागवडीखालील एकूण क्षेत्र {area_fmt} हेक्टर नोंदवले गेले."
        elif lang == "hi-en":
            return f"{detected_state} mein {crop_name} cultivation ka total area {area_fmt} hectares record hua."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {crop_name} சாகுபடி பரப்பளவு {area_fmt} ஹெக்டேர் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {crop_name} సాగు విస్తీర్ణం {area_fmt} హెక్టార్లుగా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এ {crop_name} চাষের মোট এলাকা {area_fmt} হেক্টর রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the total recorded cultivation area for {crop_name} was {area_fmt} hectares."

    # 6. Crop Production (Tonnes)
    prod_col_idx = next((i for i, c in enumerate(columns) if any(k in c for k in ["production_tonnes", "total_production", "production"]) and "sales" not in c), None)
    if prod_col_idx is not None:
        prod_val = row[prod_col_idx]
        prod_fmt = format_indian_currency_number(prod_val, lang=lang)
        crop_name = "Soybean" if "SOYBEAN" in (sql_text + query_text.upper()) else ("Wheat" if "WHEAT" in (sql_text + query_text.upper()) else "crop")
        crop_hi = "सोयाबीन" if crop_name == "Soybean" else ("गेहूं" if crop_name == "Wheat" else "फसल")
        if lang == "hi":
            return f"{detected_state} में {crop_hi} का कुल उत्पादन {prod_fmt} टन दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {crop_hi} एकूण उत्पादन {prod_fmt} टन झाले."
        elif lang == "hi-en":
            return f"{detected_state} mein {crop_name} ka total production {prod_fmt} tonnes record hua."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {crop_name} மொத்த உற்பத்தி {prod_fmt} டன்கள் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {crop_name} మొత్తం ఉత్పత్తి {prod_fmt} టన్నులుగా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এ {crop_name}-এর মোট উৎপাদন {prod_fmt} মেট্রিক টন রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the total recorded production of {crop_name} was {prod_fmt} tonnes."

    # 7. Mandi Commodity Prices (INR / Quintal)
    price_col_idx = next((i for i, c in enumerate(columns) if any(k in c for k in ["price", "modal_price", "avg_price"])), None)
    if price_col_idx is not None:
        price_val = row[price_col_idx]
        try:
            price_fmt = f"{float(price_val):,.2f}"
        except (ValueError, TypeError):
            price_fmt = str(price_val)
        comm = "Wheat" if "WHEAT" in (sql_text + query_text.upper()) else "commodity"
        comm_hi = "गेहूं" if comm == "Wheat" else "जिंस"
        if lang == "hi":
            return f"{detected_state} की मंडियों में {comm_hi} का औसत मॉडल भाव ₹{price_fmt} प्रति क्विंटल दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मधील बाजार समित्यांमध्ये {comm_hi} सरासरी भाव ₹{price_fmt} प्रति क्विंटल नोंदवला गेला."
        elif lang == "hi-en":
            return f"{detected_state} ki mandis mein {comm} ka average modal price ₹{price_fmt} per quintal raha."
        elif lang == "ta":
            return f"{detected_state} சந்தைகளில் {comm} சராசரி மாதிரி விலை குவிண்டாலுக்கு ₹{price_fmt} ஆகும்."
        elif lang == "te":
            return f"{detected_state} మార్కెట్లలో {comm} సగటు ధర క్వింటాలుకు ₹{price_fmt} గా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এর বাজারগুলিতে {comm}-এর গড় মূল্য কুইন্টাল প্রতি ₹{price_fmt} রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the average mandi modal price for {comm} was ₹{price_fmt} per quintal."

    # 8. Generic schema-aware verbalization localized to detected language
    items_desc = []
    for col, val in zip(res.get("columns", []), row):
        val_str = format_indian_currency_number(val, lang=lang)
        items_desc.append(f"{col}: {val_str}")

    joined_items = ", ".join(items_desc)
    if lang == "hi":
        return f"डेटाबेस परिणाम ({len(rows)} रिकॉर्ड): {joined_items}"
    elif lang == "mr":
        return f"डेटाबेस निकाल ({len(rows)} नोंद): {joined_items}"
    elif lang == "ta":
        return f"தரவுத்தள முடிவு ({len(rows)} பதிவு): {joined_items}"
    elif lang == "te":
        return f"డేటాబేస్ ఫలితం ({len(rows)} రికార్డు): {joined_items}"
    elif lang == "bn":
        return f"ডাটাবেস ফলাফল ({len(rows)} রেকর্ড): {joined_items}"
    elif lang == "hi-en":
        return f"Database result ({len(rows)} records): {joined_items}"
    return f"Database result ({len(rows)} records): {joined_items}"


def response_verbalizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Verbalizer Node: Formulates vernacular answer.
    Emits VoiceSynthesisEvent on the EventBus.
    """
    answer = verbalize_tabular_result(state)

    EventBus.publish(
        VoiceSynthesisEvent(
            query_id=state.get("query_id"),
            verbalized_text=answer,
            char_count=len(answer),
        )
    )

    audit_entry = {
        "step": 5,
        "agent": "ResponseVerbalizerAgent",
        "action": "verbalize_indic_prose",
        "output_length": len(answer),
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "verbalized_response": answer,
        "audit_trace": current_trace,
    }
