"""
Ollama Client for Local Neural Inference in IndicSQL.
Enables fast, privacy-preserving, local Text-to-SQL synthesis using models
like Qwen-2.5-Coder / Qwen-2.5 on Apple Silicon or local hardware.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from indicsql.core.config import settings
from indicsql.schema.phonetic import transliterate_indic_to_latin

logger = logging.getLogger(__name__)

from indicsql.models.temporal_guard import (
    extract_temporal_intent,
    has_temporal_intent,
    prune_unrequested_temporal_filters,
    sanitize_temporal_predicates,
)
from indicsql.models.metric_guard import sanitize_metric_aggregations


class OllamaClient:
    """Wrapper for Ollama API providing zero-cost local LLM inference."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 45.0,
    ):
        self.base_url = (base_url or getattr(settings, "ollama_host", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or getattr(settings, "ollama_model", "qwen2.5:3b")
        self.timeout = timeout
        self._is_active: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """Checks if local Ollama daemon is active and responsive."""
        if self._is_active is not None:
            return self._is_active
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                models = [m.get("name", "") for m in r.json().get("models", [])]
                # If exact model isn't found, pick first available qwen or mistral
                if self.model_name not in models and any("qwen" in m for m in models):
                    self.model_name = next(m for m in models if "qwen" in m)
                elif self.model_name not in models and models:
                    self.model_name = models[0]
                self._is_active = True
                return True
        except Exception:
            pass
        self._is_active = False
        return False

    def list_models(self) -> List[str]:
        """Returns list of downloaded Ollama model tags."""
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            if r.status_code == 200:
                return [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def generate_sql(
        self,
        query: str,
        table_name: str,
        table_schema: Dict[str, Any],
        language: str = "en",
        canonical_entities: Optional[Dict[str, str]] = None,
        target_columns: Optional[List[str]] = None,
        error_feedback: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> Optional[str]:
        """
        Synthesizes a DuckDB SQL query dynamically from schema DDL and natural language.
        If error_feedback is provided, guides the model to reflect and fix the query.
        """
        cols_desc = []
        for col, col_desc in table_schema.get("columns", {}).items():
            cols_desc.append(f"  - {col}: {col_desc}")
        columns_text = "\n".join(cols_desc)

        entity_hints = ""
        if canonical_entities:
            hints = [f"{k}='{v}'" for k, v in canonical_entities.items() if v]
            if hints:
                entity_hints = f"\nEntity Hints (Use exact database literal values): {', '.join(hints)}"

        column_hints = ""
        if target_columns:
            valid_targets = [c for c in target_columns if c in table_schema.get("columns", {})]
            if valid_targets:
                column_hints = f"\nTarget Metric Columns Identified by Schema Linker: {', '.join(valid_targets)}"

        system_prompt = (
            "You are an expert Text-to-SQL engineer synthesizing queries for Indian Government (NDAP) databases.\n"
            "Generate a single valid, deterministic DuckDB SQL query for the requested question.\n"
            "Rules:\n"
            "1. Output ONLY the raw executable SQL query ending with a semicolon. Do not wrap in markdown or explanations.\n"
            "2. Table values for state_name (e.g. 'MAHARASHTRA', 'PUNJAB', 'ANDHRA PRADESH') and crop_name are stored in UPPERCASE. In ndap_mandi_commodity_prices, commodity is Title Case ('Wheat', 'Rice', 'Tomato'). District names are Title Case exactly as given in Entity Hints.\n"
            "3. Include WHERE conditions ONLY for the columns explicitly provided in Entity Mappings or explicitly mentioned in the question.\n"
            "4. Do NOT add any extra columns or conditions to the WHERE clause.\n"
            "5. Use standard DuckDB aggregate functions: SUM(), AVG(), MIN(), MAX(), COUNT().\n"
            "   - If the citizen asks for average, mean, or rate (e.g. 'average', 'avg', 'औसत', 'सरासरी', 'சராசரி', 'సగటు', 'গড়'), or asks to summarize a percentage/rate indicator column (such as institutional_births_pct) or commodity price, use AVG(). NEVER use SUM() or MAX() when average or rate is requested.\n"
            "   - If the citizen asks for total, cumulative, or sum (e.g. 'total', 'sum', 'कुल', 'एकूण', 'మొత్తం', 'மொத்த', 'মোট'), use SUM(). NEVER use MAX() when a total or cumulative figure is requested.\n"
            "6. If the question mentions 'महिला', 'பெண்', 'స్త్రీ' or 'female', select female columns (e.g. female_literacy_rate), never male.\n"
            "7. If the citizen asks for both beneficiaries/farmers and amount/disbursement, select both SUM(farmer_beneficiaries) and SUM(amount_inr).\n"
            "8. If the question asks for count of people, farmers, or beneficiaries (e.g. 'किती शेतकऱ्यांना', 'कितने किसानों', 'लाभार्थी', 'விவசாயிகள்', 'பயனாளிகள்', 'లబ్ధిదారులు', 'ఎంతమంది రైతులకు', 'ఎంతమంది', 'రైతులు', 'কতজন কৃষক'), aggregate beneficiary/farmer count columns (e.g. SUM(farmer_beneficiaries)), NOT monetary amount.\n"
            "9. In soil health records (ndap_soil_health_records), if the question asks for soil samples tested (e.g. 'soil samples', 'नमूनों की जांच', 'मातीचे नमुने', 'மண் மாதிரிகள்', 'நேல నమూనాలు', 'মাটির নমুনা'), select SUM(samples_tested). ONLY select SUM(cards_issued) when the question specifically asks for cards distributed/issued (e.g. 'cards', 'कार्ड', 'அட்டைகள்', 'కార్డులు').\n"
            "10. In vocational skill training (ndap_vocational_skill_training), if the question asks for certified or passed candidates (e.g. 'certified', 'प्रमाणित', 'সনদপ্রাপ্ত', 'சான்றிதழ் பெற்றவர்கள்', 'సర్టిఫైడ్'), select SUM(certified_candidates). If it asks for placed or employed candidates, select SUM(placed_candidates).\n"
            "11. Never include GROUP BY unless the citizen question explicitly asks for a breakdown by district, year, or state.\n"
            "12. If the question asks for 'lowest', 'least', 'min', 'sabse kam', 'कमी', 'குறைவாக', 'అత్యల్పంగా', 'সবচেয়ে কম', use 'ORDER BY column ASC LIMIT 1', NEVER MAX or DESC. When the question asks 'which district' (e.g. 'किस जिले', 'कोणत्या जिल्ह्यात', 'எந்த மாவட்டம்', 'ఏ జిల్లా', 'কোন জেলায়'), project district_name (and the metric column), NOT state_name.\n"
            "13. Unless the citizen question explicitly specifies a year, academic year, or time frame, NEVER add WHERE filters on temporal columns (reporting_year, academic_year, financial_year, survey_year, cycle_year). Calculate cumulative lifetime totals across all records."
        )

        repair_prompt = ""
        if error_feedback and previous_sql:
            repair_prompt = (
                f"\n\n[SELF-HEALING REFLECTION]\n"
                f"Your previous query was:\n{previous_sql}\n"
                f"It failed execution with error:\n{error_feedback}\n"
                f"Please fix the error and rewrite the query to be completely valid."
            )

        latin_bridge = transliterate_indic_to_latin(query)
        phonetic_hint = f" (Phonetic: \"{latin_bridge}\")" if latin_bridge and latin_bridge.lower() != query.lower() else ""

        user_prompt = (
            f"Table Name: {table_name}\n"
            f"Table Description: {table_schema.get('description', '')}\n"
            f"Table Schema Columns:\n{columns_text}\n"
            f"{entity_hints}"
            f"{column_hints}\n\n"
            f"Citizen Question ({language}): \"{query}\"{phonetic_hint}\n"
            f"{repair_prompt}\n\n"
            f"SQL Query:"
        )

        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        try:
            r = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.05,
                        "stop": ["<|im_end|>", "<|endoftext|>"],
                    },
                },
                timeout=self.timeout,
            )
            if r.status_code == 200:
                raw_response = r.json().get("response", "").strip()
                return self._clean_sql(raw_response, table_name, query, canonical_entities=canonical_entities)
        except Exception as e:
            logger.warning(f"Ollama generation failed ({self.model_name}): {e}")
            return None

        return None

    def _clean_sql(
        self,
        text: str,
        table_name: str,
        query: str = "",
        canonical_entities: Optional[Dict[str, str]] = None,
    ) -> str:
        """Strips markdown code blocks, explanations, hallucinations, and ensures valid semicolon."""
        # Strip markdown ```sql ... ```
        if "```" in text:
            match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
            else:
                text = text.replace("```sql", "").replace("```", "").strip()

        text = text.replace("；", ";")
        # Remove explanatory leading/trailing lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        sql_lines = []
        for line in lines:
            # If line is conversational
            if any(line.lower().startswith(p) for p in ["here is", "this query", "the query", "note:"]):
                continue
            sql_lines.append(line)

        cleaned = " ".join(sql_lines).strip()
        if ";" in cleaned:
            cleaned = cleaned[:cleaned.index(";") + 1]
        elif not cleaned.endswith(";"):
            cleaned += ";"

        # Remove stray trailing closing parentheses if count is unbalanced
        while cleaned.endswith(");") and cleaned.count(")") > cleaned.count("("):
            cleaned = cleaned[:-2] + ";"
        while cleaned.endswith(")") and cleaned.count(")") > cleaned.count("("):
            cleaned = cleaned[:-1]

        # Prune unrequested hallucinations common in smaller 3B models
        q_lower = query.lower()
        if "season" not in q_lower and "kharif" not in q_lower and "rabi" not in q_lower and "हंगाम" not in q_lower:
            cleaned = re.sub(r"\s+AND\s+season\s*(?:=|\bIS\b)\s*[^;]+?(?=\s+AND|\s*;|$)", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s+WHERE\s+season\s*(?:=|\bIS\b)\s*[^;]+?\s+AND\s+", " WHERE ", cleaned, flags=re.IGNORECASE)

        # Prune unrequested temporal filters using AST-based predicate validator
        cleaned = sanitize_temporal_predicates(cleaned, query, table_name=table_name)

        # Enforce metric and aggregation correctness using AST-based metric guard
        cleaned = sanitize_metric_aggregations(cleaned, query, table_name=table_name)

        # Remove invalid ORDER BY on scalar aggregate queries without GROUP BY
        c_up = cleaned.upper()
        if any(agg in c_up for agg in ["SUM(", "AVG(", "COUNT("]) and "GROUP BY" not in c_up:
            cleaned = re.sub(r"\s+ORDER\s+BY\s+[^;]+(?=;|$)", "", cleaned, flags=re.IGNORECASE)

        # Enforce canonical entity alignment to prevent hallucinated states or misspelled districts
        if canonical_entities is not None:
            c_dist = canonical_entities.get("district_name")
            if c_dist:
                cleaned = re.sub(r"district_name\s*=\s*'[^']+'", f"district_name = '{c_dist}'", cleaned, flags=re.IGNORECASE)
            else:
                # If citizen question has no district mention, prune any hallucinated district_name in WHERE clause
                cleaned = re.sub(r"\s+AND\s+district_name\s*(?:=|\bIS\b|\bIN\b|\bLIKE\b)\s*(\([^)]*\)|'[^']*'|[^;]+?)(?=\s+AND|\s+GROUP\s+BY|\s+ORDER\s+BY|\s*;|$)", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\s+WHERE\s+district_name\s*(?:=|\bIS\b|\bIN\b|\bLIKE\b)\s*(\([^)]*\)|'[^']*'|[^;]+?)\s+AND\s+", " WHERE ", cleaned, flags=re.IGNORECASE)

            c_state = canonical_entities.get("state_name")
            if c_state:
                cleaned = re.sub(r"state_name\s*=\s*'[^']+'", f"state_name = '{c_state}'", cleaned, flags=re.IGNORECASE)
            for comm_key in ["crop_name", "fertilizer_type", "commodity"]:
                c_comm = canonical_entities.get(comm_key) or canonical_entities.get("commodity")
                if c_comm:
                    if table_name == "ndap_mandi_commodity_prices" and comm_key == "commodity":
                        c_val = c_comm.title()
                    else:
                        c_val = c_comm
                    cleaned = re.sub(rf"{comm_key}\s*=\s*'[^']+'", f"{comm_key} = '{c_val}'", cleaned, flags=re.IGNORECASE)

        # Remove unrequested GROUP BY ONLY when query is a pure scalar aggregate without non-aggregated projected columns
        c_up = cleaned.upper()
        if "GROUP BY" in c_up:
            grouping_keywords = ["each", "every", "by state", "by district", "by year", "wise", "वार", "வரியாக", "వారీగా", "অনুসারে"]
            if not any(k in q_lower for k in grouping_keywords):
                select_clause = cleaned[:c_up.find("FROM")] if "FROM" in c_up else ""
                # If there are non-aggregate columns projected, GROUP BY is required by SQL syntax
                has_plain_col = any(
                    col in select_clause.lower()
                    for col in ["district_name", "state_name", "crop_name", "commodity", "financial_year"]
                )
                if not has_plain_col:
                    cleaned = re.sub(r"\s+GROUP\s+BY\s+[^;]+?(?=\s+ORDER\s+BY|\s*;|$)", "", cleaned, flags=re.IGNORECASE)

        return cleaned
