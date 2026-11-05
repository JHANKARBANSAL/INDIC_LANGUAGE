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


def format_indian_currency_number(val: float) -> str:
    """Formats large integers/floats into Crores or Lakhs."""
    if val >= 10_000_000:
        crores = val / 10_000_000
        return f"{crores:.2f} कोटी (Crores)"
    if val >= 100_000:
        lakhs = val / 100_000
        return f"{lakhs:.2f} लाख (Lakhs)"
    return f"{val:,.0f}"


def verbalize_tabular_result(state: IndicSQLState) -> str:
    """Produces the localized natural language explanation."""
    res = state.get("execution_result")
    err = state.get("execution_error")
    lang = state.get("detected_lang", "en")

    if err or not res:
        if lang == "hi":
            return f"माफ़ कीजिए, डेटाबेस में आपके प्रश्न का सटीक उत्तर नहीं मिल सका। (त्रुटि: {err or 'कोई डेटा नहीं'})"
        elif lang == "mr":
            return f"क्षमस्व, डेटाबेसमध्ये आपल्या प्रश्नाचे उत्तर सापडू शकले नाही. (त्रुटी: {err or 'डेटा उपलब्ध नाही'})"
        return f"Unable to retrieve data for query. (Reason: {err or 'Empty result set'})"

    rows = res.get("rows", [])
    if not rows:
        return "डेटाबेस में कोई रिकॉर्ड नहीं मिला। (No matching records found in database)."

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
        mandays_fmt = format_indian_currency_number(float(mandays))
        if lang == "ta":
            return f"மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் மொத்தம் {mandays_fmt} மனித வேலை நாட்கள் உருவாக்கப்பட்டுள்ளன."
        elif lang == "hi":
            return f"मनरेगा योजना के तहत कुल {mandays_fmt} कार्य दिवस (Mandays) उत्पन्न किए गए।"
        elif lang == "mr":
            return f"मनरेगा योजनेअंतर्गत एकूण {mandays_fmt} मनुष्य दिन रोजगार निर्माण करण्यात आला."
        else:
            return f"Under MGNREGA, a total of {mandays:,} person-days (mandays) were generated."

    # 3. PM-KISAN Farmers & Disbursement
    if "total_farmers" in columns or "farmer_beneficiaries" in columns:
        farmers_idx = (
            columns.index("total_farmers")
            if "total_farmers" in columns
            else columns.index("farmer_beneficiaries")
        )
        farmers = row[farmers_idx]
        farmers_fmt = format_indian_currency_number(float(farmers))
        amount_part = ""
        if "total_amount" in columns or "amount_inr" in columns:
            amt_idx = (
                columns.index("total_amount")
                if "total_amount" in columns
                else columns.index("amount_inr")
            )
            amt = row[amt_idx]
            amt_fmt = format_indian_currency_number(float(amt))
            amount_part = (
                f", आणि ₹{amt_fmt} ची रक्कम थेट वितरित करण्यात आली"
                if lang == "mr"
                else f", और कुल ₹{amt_fmt} की राशि हस्तांतरित की गई"
            )

        if lang == "mr":
            return f"पीएम-किसान योजनेअंतर्गत एकूण {farmers_fmt} शेतकऱ्यांना लाभ मिळाला{amount_part}."
        elif lang == "hi":
            return f"पीएम-किसान योजना के तहत कुल {farmers_fmt} किसानों को लाभ प्राप्त हुआ{amount_part}."
        elif lang == "hi-en":
            return f"PM-KISAN yojana ke tahat total {farmers_fmt} farmers ko labh mila."
        else:
            return (
                f"Under PM-KISAN, a total of {farmers:,} farmers received direct benefit transfers."
            )

    # Generic schema-aware verbalization
    items_desc = []
    for col, val in zip(res.get("columns", []), row):
        if isinstance(val, (int, float)):
            val_str = format_indian_currency_number(float(val))
        else:
            val_str = str(val)
        items_desc.append(f"{col}: {val_str}")

    return f"डेटाबेस परिणाम ({len(rows)} रेकॉर्ड): " + ", ".join(items_desc)


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
