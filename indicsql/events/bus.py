"""
In-memory EventBus singleton for the IndicSQL multi-agent pipeline.
Supports synchronous publish, async-friendly publish, and per-query history.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Type

from indicsql.events.schemas import BaseEvent

logger = logging.getLogger(__name__)

# Handler type: any callable that accepts a BaseEvent subclass instance
EventHandler = Callable[[Any], None]


class _EventBus:
    """
    Lightweight publish/subscribe event bus.

    Usage:
        bus = EventBus  # singleton — import directly
        bus.subscribe(QueryInitiatedEvent, my_handler)
        bus.publish(QueryInitiatedEvent(query_id="q1", raw_query="..."))
    """

    def __init__(self) -> None:
        # event_type -> list of handlers
        self._subscribers: Dict[Type[BaseEvent], List[EventHandler]] = defaultdict(list)
        # Flat list of all emitted events, keyed by query_id for fast lookup
        self._history: List[BaseEvent] = []

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, event_type: Type[BaseEvent], handler: EventHandler) -> None:
        """Register *handler* to be called whenever *event_type* is published."""
        self._subscribers[event_type].append(handler)
        logger.debug("EventBus: subscribed %s → %s", event_type.__name__, handler)

    def unsubscribe(self, event_type: Type[BaseEvent], handler: EventHandler) -> None:
        """Remove a previously registered handler (no-op if not found)."""
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish(self, event: BaseEvent) -> None:
        """
        Synchronous publish: call all registered handlers in insertion order.
        Exceptions inside handlers are caught and logged so they never crash
        the pipeline.
        """
        self._history.append(event)
        for handler in self._subscribers.get(type(event), []):
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "EventBus handler %s raised: %s", handler, exc, exc_info=True
                )

    async def publish_async(self, event: BaseEvent) -> None:
        """
        Async-friendly publish: delegates to the synchronous path via
        run_in_executor so it can be safely awaited without blocking the
        event loop.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.publish, event)

    # ------------------------------------------------------------------
    # History / Introspection
    # ------------------------------------------------------------------

    def get_history(self, query_id: Optional[str] = None) -> List[BaseEvent]:
        """
        Return all recorded events, optionally filtered by *query_id*.
        """
        if query_id is None:
            return list(self._history)
        return [e for e in self._history if e.query_id == query_id]

    def clear_history(self) -> None:
        """Wipe the history buffer (useful in tests)."""
        self._history.clear()

    def reset(self) -> None:
        """Full reset: clear both subscribers and history (for test isolation)."""
        self._subscribers.clear()
        self._history.clear()


# ---- Module-level singleton ----
EventBus = _EventBus()
