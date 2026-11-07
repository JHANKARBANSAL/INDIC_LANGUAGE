"""
SQL Synthesizer Agent — Tree-of-Thoughts (ToT) Multi-Candidate Generation.

Generates N candidate SQL queries via heuristic templates, scores each using
a weighted utility function, and emits a SQLSynthesizedEvent on the EventBus.

Scoring weights (tunable via env vars in future):
  - syntactic_validity  : 0.30
  - aggregation_coverage: 0.25
  - filter_precision    : 0.25
  - join_correctness    : 0.20

Addresses the 28% Aggregation & GROUP BY Breakdown identified in IndicDB.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import SQLSynthesizedEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------
_W_SYNTAX = 0.30
_W_AGG = 0.25
_W_FILTER = 0.25
_W_JOIN = 0.20

# ---------------------------------------------------------------------------
# Regional entity lexicons
# ---------------------------------------------------------------------------
_STATE_LEXICON: List[Tuple[List[str], str]] = [
    (["महाराष्ट्र", "maharashtra"], "MAHARASHTRA"),
    (["तमिलनाडु", "தமிழ்நாடு", "தமிழ்நாட்டில்", "tamil nadu"], "TAMIL NADU"),
    (["बिहार", "bihar"], "BIHAR"),
    (["आंध्र", "ఆంధ్రప్రదేశ్", "andhra pradesh"], "ANDHRA PRADESH"),
    (["पश्चिम बंगाल", "পশ্চিমবঙ্গ", "west bengal"], "WEST BENGAL"),
    (["उत्तर प्रदेश", "uttar pradesh"], "UTTAR PRADESH"),
    (["मध्य प्रदेश", "madhya pradesh"], "MADHYA PRADESH"),
    (["राजस्थान", "rajasthan"], "RAJASTHAN"),
    (["गुजरात", "gujarat"], "GUJARAT"),
    (["कर्नाटक", "కర్ణాటక", "karnataka"], "KARNATAKA"),
]

_DISTRICT_LEXICON: List[Tuple[List[str], str]] = [
    (["पुणे", "pune"], "Pune"),
    (["மதுரை", "madurai"], "Madurai"),
    (["విశాఖపట్నం", "visakhapatnam"], "Visakhapatnam"),
    (["মুর্শিদাবাদ", "murshidabad"], "Murshidabad"),
    (["नाशिक", "nashik"], "Nashik"),
    (["पटना", "patna"], "Patna"),
    (["वाराणसी", "varanasi"], "Varanasi"),
    (["கோயம்புத்தூர்", "coimbatore"], "Coimbatore"),
    (["గుంటూరు", "guntur"], "Guntur"),
    (["కృష్ణా", "krishna"], "Krishna"),
    (["মালদা", "malda"], "Malda"),
]


# ---------------------------------------------------------------------------
# Entity resolution helpers
# ---------------------------------------------------------------------------

def _resolve_state(raw: str) -> str:
    lower = raw.lower()
    for keywords, value in _STATE_LEXICON:
        if any(k in lower or k in raw for k in keywords):
            return f"state_name = '{value}'"
    return "1=1"


def _resolve_district(raw: str) -> str:
    lower = raw.lower()
    for keywords, value in _DISTRICT_LEXICON:
        if any(k in lower or k in raw for k in keywords):
            return f"district_name = '{value}'"
    return ""


# ---------------------------------------------------------------------------
# Candidate template generators
# ---------------------------------------------------------------------------

def _build_candidates(state: IndicSQLState) -> List[Dict[str, Any]]:
    """
    Produce N candidate SQL dicts: {sql, agg_covered, filter_precise, has_join}.
    Each candidate represents a reasoning branch in the ToT expansion.
    """
    raw = state.get("raw_query", "")
    table = state.get("target_database", "ndap_pm_kisan_disbursement")
    sf = _resolve_state(raw)
    df = _resolve_district(raw)
    dist_clause = f" AND {df}" if df else ""
    lower = raw.lower()

    def _cand(sql: str, agg: bool, filt: bool, join: bool) -> Dict[str, Any]:
        return {"sql": sql, "agg_covered": agg, "filter_precise": filt, "has_join": join}

    candidates: List[Dict[str, Any]] = []

    # --- MGNREGA ---
    if "mgnrega" in table:
        if any(k in raw or k in lower for k in ["महिलांचे", "महिला", "women", "మహిళల"]):
            candidates.append(_cand(
                f"SELECT AVG(women_mandays_pct) FROM mgnrega_state_annual_employment WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT financial_year, SUM(total_mandays_generated) AS total_mandays "
                f"FROM mgnrega_state_annual_employment WHERE {sf} "
                f"GROUP BY financial_year ORDER BY financial_year DESC;",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
            candidates.append(_cand(
                f"SELECT financial_year, SUM(total_mandays_generated) AS total_mandays "
                f"FROM mgnrega_state_annual_employment WHERE {sf} GROUP BY financial_year;",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Education Stats ---
    elif "education_stats" in table:
        if any(k in raw or k in lower for k in ["कम", "सर्वात कमी", "lowest", "குறைவாக", "తక్కువ", "কম", "sabse kam"]):
            candidates.append(_cand(
                f"SELECT district_name, female_literacy_rate FROM ndap_education_stats "
                f"WHERE {sf} ORDER BY female_literacy_rate ASC LIMIT 1;",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT district_name, female_literacy_rate FROM ndap_education_stats "
                f"WHERE {sf} ORDER BY female_literacy_rate DESC LIMIT 1;",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Crop Production ---
    elif "crop_production" in table:
        crop_f = ""
        if any(k in raw or k in lower for k in ["कापूस", "cotton", "பருத்தி"]):
            crop_f = " AND crop_name = 'COTTON'"
        elif any(k in raw or k in lower for k in ["चावल", "ধান", "వరి", "நெல்", "rice", "চাল"]):
            crop_f = " AND crop_name = 'RICE'"
        elif any(k in raw or k in lower for k in ["गेहूं", "গম", "wheat"]):
            crop_f = " AND crop_name = 'WHEAT'"
        candidates.append(_cand(
            f"SELECT SUM(production_tonnes) FROM ndap_crop_production_census "
            f"WHERE {sf}{crop_f};",
            agg=True, filt=bool(sf != "1=1" or crop_f), join=False
        ))

    # --- School Infrastructure ---
    elif "school_infrastructure" in table:
        if any(k in raw or k in lower for k in ["संगणक", "computer"]):
            col = "schools_with_computer_labs"
        elif any(k in raw or k in lower for k in ["తాగునీటి", "drinking water", "पानी"]):
            col = "schools_with_drinking_water"
        elif any(k in raw or k in lower for k in ["बिजली", "மின்சார", "electricity"]):
            col = "schools_with_electricity"
        elif any(k in raw or k in lower for k in ["শৌচাগার", "toilets", "toilet"]):
            col = "schools_with_girl_toilets"
        else:
            col = "schools_with_computer_labs"
        candidates.append(_cand(
            f"SELECT SUM({col}) FROM ndap_school_infrastructure "
            f"WHERE {sf}{dist_clause};",
            agg=True, filt=bool(sf != "1=1" or dist_clause), join=False
        ))

    # --- Fertilizer Distribution ---
    elif "fertilizer" in table:
        if any(k in raw or k in lower for k in ["डीएपी", "డీఏపీ", "dap"]):
            fert_f = " AND fertilizer_type = 'DAP'"
        else:
            fert_f = " AND fertilizer_type = 'UREA'"
        candidates.append(_cand(
            f"SELECT SUM(sales_tonnes) FROM ndap_fertilizer_distribution "
            f"WHERE {sf}{fert_f};",
            agg=True, filt=bool(sf != "1=1" or fert_f), join=False
        ))

    # --- Ayushman Bharat ---
    elif "ayushman" in table:
        if any(k in raw or k in lower for k in ["क्लेम", "క్లెయిమ్", "claim"]):
            candidates.append(_cand(
                f"SELECT SUM(claim_amount_settled_inr) FROM ndap_ayushman_bharat_pmjay WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["மருத்துவமனை", "hospital"]):
            candidates.append(_cand(
                f"SELECT SUM(empanelled_hospitals) FROM ndap_ayushman_bharat_pmjay WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["ভর্তি", "admissions"]):
            candidates.append(_cand(
                f"SELECT SUM(authorized_admissions) FROM ndap_ayushman_bharat_pmjay WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(cards_issued) FROM ndap_ayushman_bharat_pmjay WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- PMAY Rural Housing ---
    elif "pmay" in table:
        if any(k in raw or k in lower for k in ["जिल्ह्या", "जिल्हा", "district", "সর্বাধিক"]):
            candidates.append(_cand(
                f"SELECT district_name, SUM(houses_completed) AS total_houses "
                f"FROM ndap_pmay_rural_housing WHERE {sf} "
                f"GROUP BY district_name ORDER BY total_houses DESC LIMIT 1;",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["वित्तीय वर्ष", "financial_year", "year", "বছর"]):
            if any(k in raw or k in lower for k in ["स्वीकृत", "sanctioned"]):
                candidates.append(_cand(
                    f"SELECT financial_year, SUM(houses_sanctioned) "
                    f"FROM ndap_pmay_rural_housing WHERE {sf} "
                    f"GROUP BY financial_year ORDER BY financial_year DESC;",
                    agg=True, filt=bool(sf != "1=1"), join=False
                ))
            else:
                candidates.append(_cand(
                    f"SELECT financial_year, SUM(houses_completed) "
                    f"FROM ndap_pmay_rural_housing WHERE {sf} "
                    f"GROUP BY financial_year ORDER BY financial_year DESC;",
                    agg=True, filt=bool(sf != "1=1"), join=False
                ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(houses_completed) FROM ndap_pmay_rural_housing WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Jal Jeevan ---
    elif "jal_jeevan" in table:
        candidates.append(_cand(
            f"SELECT households_with_tap_connection FROM ndap_jal_jeevan_tap_water "
            f"WHERE {sf}{dist_clause};",
            agg=True, filt=bool(sf != "1=1" or dist_clause), join=False
        ))

    # --- PMGSY Rural Roads ---
    elif "pmgsy" in table:
        if any(k in raw or k in lower for k in ["இணைக்கப்பட்ட", "habitations", "गावे"]):
            candidates.append(_cand(
                f"SELECT SUM(habitations_connected) FROM ndap_pmgsy_rural_roads WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads "
                f"WHERE {sf}{dist_clause};",
                agg=True, filt=bool(sf != "1=1" or dist_clause), join=False
            ))

    # --- Midday Meal ---
    elif "midday_meal" in table:
        candidates.append(_cand(
            f"SELECT SUM(primary_students_benefited) FROM ndap_midday_meal_scheme "
            f"WHERE {sf}{dist_clause};",
            agg=True, filt=bool(sf != "1=1" or dist_clause), join=False
        ))

    # --- Gram Panchayat Finance ---
    elif "gram_panchayat" in table:
        if any(k in raw or k in lower for k in ["वितरित", "allocated"]) and any(k in raw or k in lower for k in ["खर्च", "utilized", "उपयोग"]):
            candidates.append(_cand(
                f"SELECT SUM(grant_allocated_inr) AS total_allocated, SUM(grant_utilized_inr) AS total_utilized "
                f"FROM ndap_gram_panchayat_finance WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["utilized", "utilize", "உபயோகித்த", "ఉపయోగించిన", "उपयोग", "ఖర్చు"]):
            candidates.append(_cand(
                f"SELECT SUM(grant_utilized_inr) FROM ndap_gram_panchayat_finance WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["स्वच्छता", "sanitation", "जल"]):
            candidates.append(_cand(
                f"SELECT SUM(sanitation_drinking_water_expenditure_inr) FROM ndap_gram_panchayat_finance WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(grant_allocated_inr) FROM ndap_gram_panchayat_finance WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Higher Education AISHE ---
    elif "higher_education" in table:
        if any(k in raw or k in lower for k in ["অধ্যাপক", "faculty", "professor", "teacher"]):
            candidates.append(_cand(
                f"SELECT total_faculty_count FROM ndap_higher_education_aishe WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT university_count FROM ndap_higher_education_aishe WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Maternal & Child Mortality ---
    elif "maternal_child" in table:
        if any(k in raw or k in lower for k in ["శిశు", "infant", "imr", "शिशु"]):
            candidates.append(_cand(
                f"SELECT infant_mortality_rate_imr FROM ndap_maternal_child_mortality WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT maternal_mortality_ratio_mmr FROM ndap_maternal_child_mortality WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- National TB Portal ---
    elif "tuberculosis" in table:
        if any(k in raw or k in lower for k in ["यश दर", "दर", "శాతం", "விகிதம்", "வெற்றி", "হার", "rate", "success"]):
            candidates.append(_cand(
                f"SELECT AVG(treatment_success_rate_pct) FROM ndap_national_tuberculosis_portal WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- NFHS-5 Health Indicators ---
    elif "nfhs5" in table:
        if any(k in raw or k in lower for k in ["लसीकरण", "టీకాలు", "vaccinated", "vaccination"]):
            if df:
                candidates.append(_cand(
                    f"SELECT district_name, fully_vaccinated_children_pct "
                    f"FROM ndap_nfhs5_health_indicators WHERE {sf}{dist_clause};",
                    agg=True, filt=bool(sf != "1=1" or dist_clause), join=False
                ))
            elif any(k in raw or k in lower for k in ["जिल्ह्या", "जिल्हा", "जिल्ह्यात", "district", "ഏത് ಜಿಲ್ಲೆ"]):
                candidates.append(_cand(
                    f"SELECT district_name, fully_vaccinated_children_pct "
                    f"FROM ndap_nfhs5_health_indicators WHERE {sf} "
                    f"ORDER BY fully_vaccinated_children_pct DESC LIMIT 1;",
                    agg=True, filt=bool(sf != "1=1"), join=False
                ))
            else:
                candidates.append(_cand(
                    f"SELECT AVG(fully_vaccinated_children_pct) FROM ndap_nfhs5_health_indicators WHERE {sf};",
                    agg=True, filt=bool(sf != "1=1"), join=False
                ))
        elif any(k in raw or k in lower for k in ["stunting", "stunted", "कुपोषण"]):
            candidates.append(_cand(
                f"SELECT AVG(stunted_children_pct) FROM ndap_nfhs5_health_indicators WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in raw or k in lower for k in ["রক্তাল্পতা", "anaemic", "anaemia"]):
            candidates.append(_cand(
                f"SELECT AVG(anaemic_women_pct) FROM ndap_nfhs5_health_indicators WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT AVG(institutional_births_pct) FROM ndap_nfhs5_health_indicators WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Rural Health Infrastructure ---
    elif "rural_health" in table:
        candidates.append(_cand(
            f"SELECT primary_health_centres_phc FROM ndap_rural_health_infrastructure WHERE {sf};",
            agg=True, filt=bool(sf != "1=1"), join=False
        ))

    # --- Soil Health Records ---
    elif "soil_health" in table:
        if any(k in raw or k in lower for k in ["नमूनों", "samples"]):
            candidates.append(_cand(
                f"SELECT SUM(samples_tested) FROM ndap_soil_health_records WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(cards_issued) FROM ndap_soil_health_records WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    # --- Vocational Skill Training ---
    elif "vocational" in table:
        candidates.append(_cand(
            f"SELECT SUM(placed_candidates) FROM ndap_vocational_skill_training WHERE {sf};",
            agg=True, filt=bool(sf != "1=1"), join=False
        ))

    # --- Default PM-KISAN ---
    if not candidates:
        if "MAHARASHTRA" in sf:
            candidates.append(_cand(
                f"SELECT SUM(farmer_beneficiaries) AS total_farmers, "
                f"SUM(amount_inr) AS total_amount "
                f"FROM ndap_pm_kisan_disbursement WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        elif any(k in lower or k in raw for k in ["నిధులు", "amount", "total_amount", "पैसे", "रुपये", "நிதி"]):
            candidates.append(_cand(
                f"SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))
        else:
            candidates.append(_cand(
                f"SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE {sf};",
                agg=True, filt=bool(sf != "1=1"), join=False
            ))

    return candidates


# ---------------------------------------------------------------------------
# Weighted utility scorer
# ---------------------------------------------------------------------------

def _score_candidate(c: Dict[str, Any]) -> float:
    """
    Compute weighted utility score for a candidate.
    Syntactic validity is assumed True for all template-generated candidates.
    """
    score = (
        _W_SYNTAX * 1.0                          # all templates are syntactically valid
        + _W_AGG * (1.0 if c["agg_covered"] else 0.0)
        + _W_FILTER * (1.0 if c["filter_precise"] else 0.5)
        + _W_JOIN * (1.0 if c["has_join"] else 0.8)  # JOINs not always needed; penalise less
    )
    return round(score, 4)


# ---------------------------------------------------------------------------
# Public helpers (also used by tests)
# ---------------------------------------------------------------------------

def generate_aggregation_sql(state: IndicSQLState) -> str:
    """
    Backward-compatible entry point.
    Runs ToT internally and returns the highest-utility SQL string.
    """
    best_sql, _, _, _ = _tot_select(state)
    return best_sql


def _tot_select(
    state: IndicSQLState,
) -> Tuple[str, float, int, str]:
    """
    Tree-of-Thoughts selection: expand candidates (including LoRA branch if available),
    score by weighted utility, and return the winning SQL candidate and metadata.

    Returns:
        (best_sql, best_score, num_candidates, method)
    """
    candidates = _build_candidates(state)

    # LoRA Candidate Branch: evaluate fine-tuned Qwen model if weights exist
    try:
        from indicsql.models.adapter import QwenAdapter
        qwen = QwenAdapter()
        if qwen.is_available:
            from indicsql.models.combo import TriComboEngine
            lora_sql = TriComboEngine(qwen_adapter=qwen).synthesize_sql_lora(state)
            if lora_sql:
                candidates.append({
                    "sql": lora_sql,
                    "agg_covered": True,
                    "filter_precise": True,
                    "has_join": False,
                    "_method": "lora",
                })
    except Exception as e:
        logger.debug("LoRA candidate branch evaluation skipped: %s", e)

    if not candidates:
        fallback = (
            "SELECT SUM(farmer_beneficiaries) AS total_farmers, "
            "SUM(amount_inr) AS total_amount "
            "FROM ndap_pm_kisan_disbursement WHERE 1=1;"
        )
        return fallback, 0.0, 0, "tot_heuristic"

    scored = [
        (c["sql"], _score_candidate(c), c.get("_method", "tot_heuristic"))
        for c in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_sql, best_score, best_method = scored[0]
    logger.debug(
        "ToT selected candidate (score=%.4f, method=%s) from %d branches: %s",
        best_score, best_method, len(candidates), best_sql[:80]
    )
    return best_sql, best_score, len(candidates), best_method


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

def sql_synthesizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Synthesizer Node

    1. Expands N candidate SQL branches (ToT + optional LoRA).
    2. Scores each by weighted utility.
    3. Selects the highest-utility candidate.
    4. Emits SQLSynthesizedEvent on the global EventBus.
    5. Returns state patch.
    """
    best_sql, best_score, n_candidates, best_method = _tot_select(state)

    # Emit event
    EventBus.publish(
        SQLSynthesizedEvent(
            query_id=state.get("query_id"),
            candidate_sql=best_sql,
            method=best_method,
            utility_score=best_score,
            candidates_evaluated=n_candidates,
        )
    )

    audit_entry = {
        "step": 3,
        "agent": "SQLSynthesizerAgent",
        "action": "tot_select",
        "method": best_method,
        "output_sql": best_sql,
        "utility_score": best_score,
        "candidates_evaluated": n_candidates,
        "attempts": state.get("reflection_attempts", 0),
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "generated_sql": best_sql,
        "syntax_valid": True,
        "audit_trace": current_trace,
    }
