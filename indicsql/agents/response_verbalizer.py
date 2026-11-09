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

    # 4. Generic schema-aware verbalization localized to detected language
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
