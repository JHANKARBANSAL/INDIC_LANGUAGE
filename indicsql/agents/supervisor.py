"""
Query Supervisor & Script Router Agent.
Analyzes input query, detects script and language, manages state transitions, and routes tasks.
"""

import unicodedata
from typing import Any, Dict

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import QueryInitiatedEvent


def detect_indic_script(text: str) -> str:
    """
    Detects the Unicode script of the input text based on character Unicode blocks.
    Supports Devanagari, Bengali, Tamil, Telugu, and Latin (Hinglish/English).
    """
    for ch in text:
        name = unicodedata.name(ch, "")
        if "DEVANAGARI" in name:
            return "Devanagari"
        if "BENGALI" in name:
            return "Bengali"
        if "TAMIL" in name:
            return "Tamil"
        if "TELUGU" in name:
            return "Telugu"
    return "Latin"


def identify_language_code(text: str, script: str) -> str:
    """
    Identifies the language code ('hi', 'bn', 'ta', 'te', 'mr', 'hi-en', 'en').
    """
    if script == "Tamil":
        return "ta"
    if script == "Telugu":
        return "te"
    if script == "Bengali":
        return "bn"
    if script == "Devanagari":
        # Heuristic check for Marathi specific characters (like ळ) or words
        marathi_markers = {"ळ", "आहे", "किती", "शेतकऱ्यांना", "महाराष्ट्रात", "उत्पादन", "शाळांमध्ये", "झाले"}
        if any(m in text for m in marathi_markers):
            return "mr"
        return "hi"

    # For Latin script: Distinguish Hinglish vs English
    hinglish_markers = {
        "kitne",
        "kisko",
        "pichle",
        "saal",
        "me",
        "mein",
        "ka",
        "ki",
        "ke",
        "hai",
        "kya",
        "yojana",
    }
    words = set(text.lower().split())
    if words.intersection(hinglish_markers):
        return "hi-en"
    return "en"


def supervisor_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Supervisor Agent node: Ingests raw query, identifies language & script,
    initializes audit trace and canonical query.
    Emits QueryInitiatedEvent on the EventBus.
    """
    raw_query = state.get("raw_query", "").strip()
    script = detect_indic_script(raw_query)
    lang = identify_language_code(raw_query, script)

    EventBus.publish(
        QueryInitiatedEvent(
            query_id=state.get("query_id"),
            raw_query=raw_query,
            detected_lang=lang,
            detected_script=script,
        )
    )

    audit_entry = {
        "step": 1,
        "agent": "SupervisorRouter",
        "action": "normalize_and_detect",
        "detected_script": script,
        "detected_language": lang,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "detected_script": script,
        "detected_lang": lang,
        "canonical_query": raw_query,
        "reflection_attempts": state.get("reflection_attempts", 0),
        "audit_trace": current_trace,
    }
