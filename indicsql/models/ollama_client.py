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

logger = logging.getLogger(__name__)


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
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            if r.status_code == 200:
                models = [m.get("name", "") for m in r.json().get("models", [])]
                # If exact model isn't found, pick first available qwen or mistral
                if self.model_name not in models and any("qwen" in m for m in models):
                    self.model_name = next(m for m in models if "qwen" in m)
                elif self.model_name not in models and models:
                    self.model_name = models[0]
                return True
        except Exception:
            pass
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
                entity_hints = f"\nEntity Hints (Use exact database values in UPPERCASE): {', '.join(hints)}"

        system_prompt = (
            "You are an expert Text-to-SQL engineer synthesizing queries for Indian Government (NDAP) databases.\n"
            "Generate a single valid, deterministic DuckDB SQL query for the requested question.\n"
            "Rules:\n"
            "1. Output ONLY the raw executable SQL query ending with a semicolon. Do not wrap in markdown or explanations.\n"
            "2. Table values for state_name (e.g. 'MAHARASHTRA', 'PUNJAB', 'BIHAR') and categories (e.g. 'WHEAT', 'COTTON', 'UREA', 'DAP') are stored in UPPERCASE.\n"
            "3. Include WHERE conditions ONLY for the columns explicitly provided in Entity Mappings or explicitly mentioned in the question.\n"
            "4. Do NOT add any extra columns or conditions to the WHERE clause.\n"
            "5. Use standard DuckDB aggregate functions: SUM(), AVG(), MIN(), MAX(), COUNT().\n"
            "6. If the question mentions 'महिला', 'பெண்', 'స్త్రీ' or 'female', select female columns (e.g. female_literacy_rate), never male.\n"
            "7. If the citizen asks for both beneficiaries/farmers and amount/disbursement, select both SUM(farmer_beneficiaries) and SUM(amount_inr).\n"
            "8. If the question asks only for count of people/farmers/beneficiaries (e.g. 'किती शेतकऱ्यांना', 'कितने किसानों', 'लाभार्थी', 'பயனாளிகள்', 'లబ్ధిదారులు'), aggregate beneficiary/farmer count columns (e.g. farmer_beneficiaries), not monetary amount."
        )

        repair_prompt = ""
        if error_feedback and previous_sql:
            repair_prompt = (
                f"\n\n[SELF-HEALING REFLECTION]\n"
                f"Your previous query was:\n{previous_sql}\n"
                f"It failed execution with error:\n{error_feedback}\n"
                f"Please fix the error and rewrite the query to be completely valid."
            )

        user_prompt = (
            f"Table Name: {table_name}\n"
            f"Table Description: {table_schema.get('description', '')}\n"
            f"Table Schema Columns:\n{columns_text}\n"
            f"{entity_hints}\n\n"
            f"Citizen Question ({language}): \"{query}\"\n"
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
                return self._clean_sql(raw_response, table_name, query)
        except Exception as e:
            logger.warning(f"Ollama generation failed ({self.model_name}): {e}")
            return None

        return None

    def _clean_sql(self, text: str, table_name: str, query: str = "") -> str:
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

        # Prune unrequested hallucinations common in smaller 3B models
        q_lower = query.lower()
        if "season" not in q_lower and "kharif" not in q_lower and "rabi" not in q_lower and "हंगाम" not in q_lower:
            cleaned = re.sub(r"\s+AND\s+season\s*(?:=|\bIS\b)\s*[^;]+?(?=\s+AND|\s*;|$)", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s+WHERE\s+season\s*(?:=|\bIS\b)\s*[^;]+?\s+AND\s+", " WHERE ", cleaned, flags=re.IGNORECASE)

        # Remove invalid ORDER BY on scalar aggregate queries without GROUP BY
        c_up = cleaned.upper()
        if any(agg in c_up for agg in ["SUM(", "AVG(", "COUNT("]) and "GROUP BY" not in c_up:
            cleaned = re.sub(r"\s+ORDER\s+BY\s+[^;]+(?=;|$)", "", cleaned, flags=re.IGNORECASE)

        return cleaned
