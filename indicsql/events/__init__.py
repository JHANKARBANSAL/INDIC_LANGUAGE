"""
IndicSQL Event System.
Typed event models and in-memory pub/sub bus for the multi-agent pipeline.
"""

from indicsql.events.bus import EventBus
from indicsql.events.schemas import (
    BaseEvent,
    ExecutionCompletedEvent,
    QueryInitiatedEvent,
    ReflectionTriggeredEvent,
    SchemaLinkedEvent,
    SQLSynthesizedEvent,
    VoiceSynthesisEvent,
)

__all__ = [
    "BaseEvent",
    "QueryInitiatedEvent",
    "SchemaLinkedEvent",
    "SQLSynthesizedEvent",
    "ExecutionCompletedEvent",
    "ReflectionTriggeredEvent",
    "VoiceSynthesisEvent",
    "EventBus",
]
