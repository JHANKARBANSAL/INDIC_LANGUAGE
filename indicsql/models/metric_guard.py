"""
indicsql/models/metric_guard.py
AST-Based Metric & Aggregation Correctness Validator & Rewriter for IndicSQL.

Remediates Flaw 2 (Metric / Aggregation Correctness) by:
1. Extracting fine-grained multilingual metric and aggregation intent across 7 Indian languages.
2. Disambiguating domain-specific metric columns (e.g., samples_tested vs cards_issued,
   certified_candidates vs placed_candidates) based on explicit user intent.
3. Preserving and enforcing requested aggregation semantics (AVG for averages and rates,
   SUM for additive totals, MIN/ASC for superlatives) at the AST level using SQLGlot.
4. Pruning redundant dimension projections from pure scalar aggregate queries.
5. Strictly preserving valid queries with multiple aggregates, explicit grouping, joins,
   or intentional extrema.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Set

import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)


@dataclass
class MetricIntent:
    """Represents fine-grained metric and aggregation intent extracted from user query."""
    is_average: bool = False
    is_total: bool = False
    is_count: bool = False
    is_lowest: bool = False
    is_highest: bool = False
    is_soil_samples: bool = False
    is_soil_cards: bool = False
    is_vocational_certified: bool = False
    is_vocational_placed: bool = False
    has_grouping_intent: bool = False


# Known percentage/rate indicators across NDAP schemas
PERCENTAGE_RATE_COLUMNS: Set[str] = {
    "institutional_births_pct",
    "fully_vaccinated_children_pct",
    "stunted_children_pct",
    "anaemic_women_pct",
    "households_improved_sanitation_pct",
    "female_literacy_rate",
    "literacy_rate",
    "organic_carbon_pct",
}

# Additive measures across NDAP schemas where SUM is appropriate for totals
ADDITIVE_MEASURE_COLUMNS: Set[str] = {
    "completed_road_length_km",
    "total_mandays_generated",
    "amount_inr",
    "farmer_beneficiaries",
    "production_tonnes",
    "area_hectares",
    "quantity_metric_tonnes",
    "samples_tested",
    "cards_issued",
    "enrolled_candidates",
    "certified_candidates",
    "placed_candidates",
    "student_count",
    "meals_served",
    "schools_with_electricity",
    "schools_with_drinking_water",
    "schools_with_girl_toilets",
    "total_faculty_count",
    "total_notified_patients",
    "houses_completed",
    "funds_utilized_inr",
    "primary_health_centres_phc",
    "maternal_mortality_ratio",
    "infant_mortality_rate",
}


def extract_metric_intent(query: str) -> MetricIntent:
    """
    Extracts fine-grained metric and aggregation intent from citizen questions
    across English, Hinglish, Hindi, Marathi, Bengali, Tamil, and Telugu.
    """
    if not query or not query.strip():
        return MetricIntent()

    clean_q = query.split("\n")[0].strip()
    lower_q = clean_q.lower()
    intent = MetricIntent()

    # 1. Average / Mean Intent
    avg_patterns = [
        r'\b(?:average|avg|mean)\b',
        r'औसत', r'सरासरी', r'सरासरीने', r'গড়', r'সராசரி', r'சராசரியாக', r'సగటు', r'సరాసరి',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in avg_patterns):
        intent.is_average = True

    # 2. Total / Sum / Cumulative Intent
    total_patterns = [
        r'\b(?:total|cumulative|overall|all-time|overall\s+total)\b',
        r'कुल', r'योग', r'समग्र', r'एकूण', r'सर्व(?:\s+|$)', r'মোট', r'সর্বমোট',
        r'மொத்த', r'முழு', r'మొత్తం', r'మొత్తము',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in total_patterns):
        intent.is_total = True

    # 3. Lowest / Minimum Intent
    lowest_patterns = [
        r'\b(?:lowest|minimum|least|min|fewest|smallest)\b',
        r'\b(?:sabse\s*kam|sab\s*se\s*kam)\b',
        r'सबसे\s*कम', r'न्यूनतम', r'कम\s*से\s*कम',
        r'सर्वात\s*कमी', r'किमान', r'कमी',
        r'সবচেয়ে\s*কম', r'সর্বনিম্ন',
        r'மிகக்\s*குறைந்த', r'மிகக்\s*குறைவாக', r'குறைவான', r'குறைவாக', r'குறைந்தபட்ச', r'குறைந்த',
        r'అత్యల్పంగా', r'అత్యల్ప', r'కనిష్ట', r'తక్కువ',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in lowest_patterns):
        intent.is_lowest = True

    # 4. Highest / Maximum Intent
    highest_patterns = [
        r'\b(?:highest|maximum|most|max|peak|greatest)\b',
        r'सबसे\s*ज्यादा', r'अधिकतम', r'सर्वाधिक',
        r'सर्वात\s*जास्त', r'कमाल', r'जास्त',
        r'সবচেয়ে\s*বেশি', r'সর্বাধিক',
        r'மிக\s*அதிக', r'அதிகபட்ச', r'அதிகமாக',
        r'అత్యధికంగా', r'అత్యధిక', r'గరిష్ట',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in highest_patterns):
        intent.is_highest = True

    # 5. Soil Health Disambiguation: Samples Tested vs Cards Issued
    soil_samples_patterns = [
        r'\b(?:soil\s+sample|soil\s+samples|samples\s+test|samples\s+tested)\b',
        r'नमूनों\s*की\s*जांच', r'मिट्टी\s*के\s*नमूनों', r'नमूने', r'नमूनों',
        r'मातीचे\s*नमुने', r'नमुने\s*तपासण्यात',
        r'মাটির\s*নমুনা', r'নমুনা\s*পরীক্ষা',
        r'மண்\s*மாதிரிகள்', r'மாதிரிகள்',
        r'నేల\s*నమూనాలను', r'నేల\s*నమూనాలు', r'నమూనాలను',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in soil_samples_patterns):
        intent.is_soil_samples = True

    soil_cards_patterns = [
        r'\b(?:cards\s+issued|cards\s+distributed|health\s+cards\s+given|card\s+issued)\b',
        r'कार्ड\s*जारी', r'कार्ड\s*वितरित', r'कार्ड\s*वाटप',
        r'কার্ড\s*বিতরণ', r'কার্ড\s*ইস্যু',
        r'அட்டைகள்\s*வழங்கப்பட்டது', r'அட்டைகள்\s*கொடுக்கப்பட்டது',
        r'కార్డులు\s*జారీ', r'కార్డులు\s*పంపిణీ',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in soil_cards_patterns):
        intent.is_soil_cards = True

    # 6. Vocational Training Disambiguation: Certified vs Placed Candidates
    certified_patterns = [
        r'\b(?:certified|certification|certificate\s+holder|passed\s+exam)\b',
        r'प्रमाणित', r'प्रमाणपत्र', r'सनद',
        r'সনদপ্রাপ্ত', r'শংসাপত্র',
        r'சான்றிதழ்', r'சான்றிதழ்\s*பெற்றவர்கள்', r'தேர்ச்சி\s*பெற்று',
        r'సర్టిఫికేట్', r'సర్టిఫైడ్', r'ధృవీకరించబడిన',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in certified_patterns):
        intent.is_vocational_certified = True

    placed_patterns = [
        r'\b(?:placed|placement|employed|got\s+job|recruited)\b',
        r'रोजगार\s*मिला', r'रोजगार', r'नौकरी', r'प्लेसमेंट',
        r'চাকরি', r'নিয়োগ',
        r'வேலைவாய்ப்பு', r'வேலை\s*கிடைத்த',
        r'ఉపాధి', r'ఉద్యోగం',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in placed_patterns):
        intent.is_vocational_placed = True

    # 7. Grouping Intent
    grouping_patterns = [
        r'\b(?:each|every|per|breakdown|by\s+state|by\s+district|by\s+year|state-wise|district-wise|year-wise|wise)\b',
        r'वार', r'जिलेवार', r'राज्यवार', r'सालवार', r'प्रत्येक', r'हर\s*एक',
        r'जिल्हानिहाय', r'राज्यनिहाय',
        r'প্রতিটি', r'অনুসারে',
        r'ஒவ்வொரு', r'வரியாக',
        r'ప్రతి', r'వారీగా',
    ]
    if any(re.search(p, clean_q, re.IGNORECASE) for p in grouping_patterns):
        intent.has_grouping_intent = True

    return intent


def sanitize_metric_aggregations(
    sql: str,
    query: str,
    table_name: Optional[str] = None,
) -> str:
    """
    Validates and aligns metric columns and aggregation functions in the SQL AST
    against explicit citizen intent across all 7 supported Indian languages.
    """
    if not sql or not sql.strip():
        return sql

    intent = extract_metric_intent(query)

    try:
        tree = sqlglot.parse_one(sql.strip(), read="duckdb")
        if not tree:
            return sql
    except Exception as e:
        logger.warning("SQLGlot failed to parse query in MetricGuard (%s). Maintaining original: %s", e, sql)
        return sql

    modified = False

    # -------------------------------------------------------------------------
    # 1. Metric Column Disambiguation: Soil Health Records
    # -------------------------------------------------------------------------
    if table_name == "ndap_soil_health_records" and intent.is_soil_samples and not intent.is_soil_cards:
        for col in tree.find_all(exp.Column):
            if col.name.lower() == "cards_issued":
                logger.info("MetricGuard: Replaced cards_issued with samples_tested based on soil sample intent")
                col.replace(exp.Column(this=exp.to_identifier("samples_tested")))
                modified = True

    # -------------------------------------------------------------------------
    # 2. Metric Column Disambiguation: Vocational Skill Training
    # -------------------------------------------------------------------------
    if table_name == "ndap_vocational_skill_training" and intent.is_vocational_certified and not intent.is_vocational_placed:
        for col in tree.find_all(exp.Column):
            if col.name.lower() == "placed_candidates":
                logger.info("MetricGuard: Replaced placed_candidates with certified_candidates based on certification intent")
                col.replace(exp.Column(this=exp.to_identifier("certified_candidates")))
                modified = True

    # -------------------------------------------------------------------------
    # 2b. Metric Column Disambiguation: PM-Kisan Farmer Count vs Monetary Amount
    # -------------------------------------------------------------------------
    farmer_count_patterns = [
        r'\b(?:how\s+many\s+farmers|count\s+of\s+farmers|farmer\s+beneficiaries|number\s+of\s+farmers)\b',
        r'कितने\s*किसानों', r'किती\s*शेतकऱ्यांना', r'কতজন\s*কৃষক',
        r'எத்தனை\s*விவசாயிகள்', r'விவசாயிகளுக்கு',
        r'ఎంతమంది\s*రైతులకు', r'ఎంతమంది\s*రైతులు', r'రైతులకు',
    ]
    is_farmer_count = any(re.search(p, query, re.IGNORECASE) for p in farmer_count_patterns)
    if table_name == "ndap_pm_kisan_disbursement" and is_farmer_count:
        # If user explicitly asked for amount as well, preserve amount_inr
        is_amount_explicit = any(w in query.lower() for w in ['amount', 'disbursement', 'राशि', 'निधी', 'பணம்', 'డబ్బు'])
        if not is_amount_explicit:
            for col in tree.find_all(exp.Column):
                if col.name.lower() == "amount_inr":
                    logger.info("MetricGuard: Replaced amount_inr with farmer_beneficiaries based on farmer count intent")
                    col.replace(exp.Column(this=exp.to_identifier("farmer_beneficiaries")))
                    modified = True

    # -------------------------------------------------------------------------
    # 3. Superlative Direction & Projection Alignment
    # -------------------------------------------------------------------------
    if intent.is_lowest and not intent.is_highest:
        # Check if ORDER BY is present with DESC and change to ASC
        if tree.args.get("order"):
            order_node = tree.args["order"]
            for ordered in order_node.find_all(exp.Ordered):
                if ordered.args.get("desc"):
                    logger.info("MetricGuard: Corrected ORDER BY DESC to ASC based on lowest/minimum intent")
                    ordered.set("desc", False)
                    modified = True

        # Check if query asks for "lowest" of a measure (e.g. female_literacy_rate)
        # but model wrapped it in MAX()
        has_max = False
        new_selects = []
        for s in tree.selects:
            if isinstance(s, exp.Alias) and isinstance(s.this, exp.Max):
                inner_col = s.this.this
                new_selects.append(inner_col)
                has_max = True
            elif isinstance(s, exp.Max):
                inner_col = s.this
                new_selects.append(inner_col)
                has_max = True
            else:
                new_selects.append(s)

        if has_max:
            tree.set("expressions", new_selects)
            tree.set("group", None)
            # Find the measure column to order by
            measure_col = next((c.name for c in tree.find_all(exp.Column) if c.name.lower() in PERCENTAGE_RATE_COLUMNS), None)
            if measure_col:
                new_order = sqlglot.parse_one(f"SELECT 1 ORDER BY {measure_col} ASC").args["order"]
                tree.set("order", new_order)
                if not tree.args.get("limit"):
                    tree.set("limit", exp.Limit(expression=exp.Literal.number(1)))
                logger.info("MetricGuard: Transformed MAX(col) to col with ORDER BY %s ASC LIMIT 1 for lowest superlative", measure_col)
                modified = True

        # Check if query asks for "which district" with lowest/highest
        which_district_patterns = [
            r'\b(?:which\s+district|kis\s+district|kis\s+jile|kon\s+jela|enta\s+mavattam|ye\s+jilla)\b',
            r'किस\s*जिले', r'कोणत्या\s*जिल्ह्यात', r'எந்த\s*மாவட்டம்', r'மாவட்டம்\s*எது', r'ఏ\s*జిల్లా', r'কোন\s*জেলায়'
        ]
        is_which_district = any(re.search(p, query, re.IGNORECASE) for p in which_district_patterns)
        if is_which_district:
            # Find the measure column
            measure_col = next((c.name for c in tree.find_all(exp.Column) if c.name.lower() in PERCENTAGE_RATE_COLUMNS), None)
            if not measure_col:
                agg_node = next((n for n in tree.find_all((exp.Min, exp.Max, exp.Avg, exp.Sum)) if isinstance(n.this, exp.Column)), None)
                if agg_node:
                    measure_col = agg_node.this.name
            if not measure_col:
                measure_col = next((c.name for c in tree.find_all(exp.Column) if c.name.lower() not in {"district_name", "state_name", "reporting_year", "year"}), None)

            if measure_col:
                new_selects = [exp.Column(this=exp.to_identifier("district_name")), exp.Column(this=exp.to_identifier(measure_col))]
                tree.set("expressions", new_selects)
                tree.set("group", None)
                order_dir = "ASC" if intent.is_lowest else "DESC"
                new_order = sqlglot.parse_one(f"SELECT 1 ORDER BY {measure_col} {order_dir}").args["order"]
                tree.set("order", new_order)
                tree.set("limit", exp.Limit(expression=exp.Literal.number(1)))

                # Prune subquery equality filters in WHERE (e.g. col = (SELECT MIN(col)...))
                for eq in list(tree.find_all(exp.EQ)):
                    if list(eq.find_all(exp.Select)):
                        eq.replace(exp.true())

                logger.info(
                    "MetricGuard: Transformed query to district_name projection with ORDER BY %s %s LIMIT 1 for 'which district' question",
                    measure_col, order_dir
                )
                modified = True

    # -------------------------------------------------------------------------
    # 4. Aggregation Function Alignment: Average vs Total vs Peak
    # -------------------------------------------------------------------------
    # Scenario A: Explicit Average Intent
    if intent.is_average and not intent.is_total and not intent.is_highest:
        for node in list(tree.find_all((exp.Sum, exp.Max))):
            col_target = node.this
            logger.info("MetricGuard: Replaced %s with AVG(%s) based on explicit average intent", node.key.upper(), col_target.sql("duckdb"))
            node.replace(exp.Avg(this=col_target))
            modified = True

    # Scenario B: Rate/Percentage Indicator Summarization (e.g. institutional_births_pct in NFHS-5)
    elif (table_name == "ndap_nfhs5_health_indicators" or any(c.name.lower() in PERCENTAGE_RATE_COLUMNS for c in tree.find_all(exp.Column))) \
            and not intent.is_total and not intent.is_highest and not intent.is_lowest:
        for node in list(tree.find_all((exp.Sum, exp.Max))):
            col_target = node.this
            col_name = col_target.name.lower() if isinstance(col_target, exp.Column) else ""
            if col_name in PERCENTAGE_RATE_COLUMNS or col_name.endswith("_pct") or col_name.endswith("_rate"):
                logger.info("MetricGuard: Replaced %s on rate column %s with AVG()", node.key.upper(), col_name)
                node.replace(exp.Avg(this=col_target))
                modified = True

    # Scenario C: Explicit Total Intent on Additive Columns
    elif intent.is_total and not intent.is_highest and not intent.is_average:
        for node in list(tree.find_all(exp.Max)):
            col_target = node.this
            col_name = col_target.name.lower() if isinstance(col_target, exp.Column) else ""
            if col_name in ADDITIVE_MEASURE_COLUMNS or not col_name:
                logger.info("MetricGuard: Replaced MAX with SUM on additive column %s based on explicit total intent", col_name)
                node.replace(exp.Sum(this=col_target))
                modified = True

    # -------------------------------------------------------------------------
    # 5. Redundant Dimension Pruning in Pure Scalar Queries
    # -------------------------------------------------------------------------
    # If the user did NOT request grouping (no 'by district', 'each', etc.),
    # and the query is a scalar aggregate, prune non-aggregate dimension projections,
    # drop unrequested GROUP BY, and drop scalar ORDER BY/LIMIT.
    if not intent.has_grouping_intent and not intent.is_lowest and not intent.is_highest:
        has_agg = any(isinstance(c, (exp.Sum, exp.Avg, exp.Count, exp.Min, exp.Max)) for c in tree.find_all(exp.Expression))
        if has_agg and tree.args.get("group"):
            kept_selects = [
                s for s in tree.selects
                if any(isinstance(c, (exp.Sum, exp.Avg, exp.Count, exp.Min, exp.Max)) for c in s.walk())
            ]

            if kept_selects:
                # If multiple aggregates exist, keep the one matching intent if specific intent exists
                if intent.is_soil_samples and len(kept_selects) > 1:
                    samples_selects = [s for s in kept_selects if "samples_tested" in s.sql("duckdb").lower()]
                    if samples_selects:
                        kept_selects = samples_selects

                tree.set("expressions", kept_selects)
                tree.set("group", None)
                tree.set("order", None)
                tree.set("limit", None)
                logger.info("MetricGuard: Pruned unsolicited GROUP BY and non-aggregate dimensions from scalar aggregate query")
                modified = True

    # -------------------------------------------------------------------------
    # 6. Deduplicate Identical Aggregate Projections
    # -------------------------------------------------------------------------
    if len(tree.selects) > 1:
        seen_core_exprs = set()
        deduped_selects = []
        for s in tree.selects:
            core = s.this.sql("duckdb") if isinstance(s, exp.Alias) else s.sql("duckdb")
            if core not in seen_core_exprs:
                seen_core_exprs.add(core)
                deduped_selects.append(s)
        if len(deduped_selects) < len(tree.selects):
            logger.info("MetricGuard: Deduplicated identical aggregate projections")
            tree.set("expressions", deduped_selects)
            modified = True

    if not modified:
        return sql

    out_sql = tree.sql("duckdb")
    if not out_sql.endswith(";"):
        out_sql += ";"

    return out_sql
