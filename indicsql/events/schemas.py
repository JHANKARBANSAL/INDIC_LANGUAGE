"""
Typed Event Schema Models for the IndicSQL pipeline.
Each event inherits from BaseEvent and captures a distinct pipeline milestone.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class BaseEvent:
    """Root event — all pipeline events inherit from this."""

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    query_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to plain dict for logging / metrics."""
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class QueryInitiatedEvent(BaseEvent):
    """Emitted by Supervisor when a new query enters the pipeline."""

    raw_query: str = ""
    detected_lang: str = ""
    detected_script: str = ""


@dataclass
class SchemaLinkedEvent(BaseEvent):
    """Emitted by SchemaLinker once relevant tables/columns are resolved."""

    target_table: str = ""
    matched_columns: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class SQLSynthesizedEvent(BaseEvent):
    """Emitted by SQLSynthesizer after candidate SQL is selected."""

    candidate_sql: str = ""
    method: str = "tot_heuristic"   # 'tot_heuristic' | 'lora'
    utility_score: float = 0.0
    candidates_evaluated: int = 1


@dataclass
class ExecutionCompletedEvent(BaseEvent):
    """Emitted by SandboxExecutor after DuckDB execution completes."""

    exit_code: int = 0
    row_count: int = 0
    execution_time_ms: float = 0.0
    success: bool = True


@dataclass
class ReflectionTriggeredEvent(BaseEvent):
    """Emitted by the ReflectionHealer when a retry loop is initiated."""

    error_message: str = ""
    attempt_number: int = 1


@dataclass
class VoiceSynthesisEvent(BaseEvent):
    """Emitted by ResponseVerbalizer when TTS verbalization is produced."""

    verbalized_text: str = ""
    char_count: int = 0
