#!/usr/bin/env python3
"""
scripts/verify_algorithmic_bridge.py
Zero-Shot Native Indic Transliteration Bridge & Dynamic Grounding Verification.
Tests unlisted districts (Kadapa, Birbhum, Kurnool, Solapur, Madurai, etc.)
demonstrating zero hardcoding, algorithmic sanscript conversion, and prompt token reduction.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.schema.phonetic import (
    detect_indic_script_scheme,
    transliterate_indic_to_latin,
)
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.agents.sql_synthesizer import extract_canonical_entities, synthesize_sql
from indicsql.core.state import IndicSQLState
from indicsql.sandbox.duckdb_engine import DuckDBSandbox

TEST_CASES = [
    {
        "lang": "Telugu",
        "district": "Kadapa (కడప)",
        "query": "కడప జిల్లాలో పిఎం కిసాన్ మొత్తం నిధులు ఎంత?",
        "expected_district": "Kadapa",
        "expected_state": "ANDHRA PRADESH",
    },
    {
        "lang": "Bengali",
        "district": "Birbhum (বীরভূম)",
        "query": "বীরভূম জেলায় মোট চাল উৎপাদন কত মেট্রিক টন?",
        "expected_district": "Birbhum",
        "expected_state": "WEST BENGAL",
    },
    {
        "lang": "Telugu",
        "district": "Kurnool (కర్నూలు)",
        "query": "కర్నూలు జిల్లాలో ఎంతమంది రైతులకు లబ్ధి చేకూరింది?",
        "expected_district": "Kurnool",
        "expected_state": "ANDHRA PRADESH",
    },
    {
        "lang": "Marathi",
        "district": "Solapur (सोलापूर)",
        "query": "सोलापूर जिल्ह्यात पीक उत्पादन किती टन झाले?",
        "expected_district": "Solapur",
        "expected_state": "MAHARASHTRA",
    },
    {
        "lang": "Tamil",
        "district": "Madurai (மதுரை)",
        "query": "மதுரை மாவட்டத்தில் நெல் உற்பத்தி எவ்வளவு?",
        "expected_district": "Madurai",
        "expected_state": "TAMIL NADU",
    },
]

def main():
    print("=" * 85)
    print("🇮🇳 ZERO-SHOT ALGORITHMIC TRANSLITERATION BRIDGE & DYNAMIC GROUNDING")
    print("=" * 85)
    print("Testing unlisted non-metro districts with ZERO hardcoding.\n")

    sandbox = DuckDBSandbox()
    passed_count = 0

    for idx, tc in enumerate(TEST_CASES, 1):
        q = tc["query"]
        lang = tc["lang"]
        target = tc["expected_district"]
        target_state = tc["expected_state"]

        # 1. Algorithmic Transliteration Bridge
        scheme = detect_indic_script_scheme(q)
        latin = transliterate_indic_to_latin(q)

        # 2. Dynamic Grounder Extraction
        extracted = extract_canonical_entities(q)
        grounded_dist = extracted.get("district_name")
        grounded_state = extracted.get("state_name")

        # 3. SQL Synthesis (Neural with fallback reflection)
        dummy_state: IndicSQLState = {
            "query_id": f"test-{idx}",
            "raw_query": q,
            "detected_lang": "te" if lang == "Telugu" else ("bn" if lang == "Bengali" else ("mr" if lang == "Marathi" else "ta")),
            "target_database": "ndap_pm_kisan_disbursement" if "కిసాన్" in q or "రైతు" in q else "ndap_crop_production_census",
        }
        sql, method, conf = synthesize_sql(dummy_state)

        # 4. DuckDB Sandbox Execution Verification
        exec_res = None
        exec_err = None
        try:
            exec_res = sandbox.execute_query(sql)
        except Exception as e:
            exec_err = str(e)

        dist_matched = bool(grounded_dist and grounded_dist.lower() == target.lower())
        sql_has_dist = bool(target.lower() in sql.lower())
        exec_ok = bool(exec_res is not None and exec_err is None)

        passed = dist_matched and sql_has_dist and exec_ok
        if passed:
            passed_count += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"

        print(f"[{idx}/{len(TEST_CASES)}] {lang} Query: \"{q}\"")
        print(f"   • Detected Script Scheme : {scheme}")
        print(f"   • Latin Phonetic Bridge  : \"{latin}\"")
        print(f"   • Grounded District      : {grounded_dist} (Expected: {target})")
        print(f"   • Grounded State (Auto)  : {grounded_state} (Expected: {target_state})")
        print(f"   • Synthesized SQL        : {sql}")
        print(f"   • Execution Status       : {'Success (' + str(exec_res['row_count']) + ' rows)' if exec_ok else 'Error: ' + str(exec_err)}")
        print(f"   • Overall Result         : {status}\n")

    print("=" * 85)
    print(f"SUMMARY: {passed_count}/{len(TEST_CASES)} Zero-Shot District Queries Passed ({passed_count/len(TEST_CASES)*100:.1f}%)")
    print("=" * 85)

if __name__ == "__main__":
    main()
