"""
WebSocket Event Emitter with Terminal Guarantee
Centralized emission point enforcing WebSocket invariants.

INVARIANTS (from CLAUDE.md):
- Every event MUST include: type, timestamp (ISO 8601), run_id
- Every run MUST terminate with EXACTLY ONE terminal event: complete OR error
- No run can remain indefinitely in RUNNING state

Architecture:
- WSEventEmitter: Single emission point with automatic validation
- RunLifecycleTracker: Tracks terminal events per run (idempotency)
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import WebSocket
from pydantic import ValidationError

from app.core.config import settings
from app.models.ws_events import (WSCompleteEvent, WSConversationCreatedEvent,
                                  WSErrorEvent, WSEvent, WSEventBase,
                                  WSPhaseEvent, WSThinkingEvent, WSToolEvent,
                                  WSVerificationItemEvent, is_terminal_event)
from app.services.websocket.exceptions import (InvalidEventStructure,
                                               TerminalAlreadySent,
                                               WebSocketClosed)

logger = logging.getLogger(__name__)


class EventQueue:
    """
    Queue d'events WebSocket pour anti-perte en cas de déconnexion (CRQ-P1-5).

    Fonctionnement:
    - Buffer events si WebSocket fermé
    - Replay events à reconnexion
    - TTL + quota pour éviter memory leak
    """

    def __init__(self):
        self._queues: Dict[str, List[Dict[str, Any]]] = {}  # run_id -> [events]
        self._timestamps: Dict[str, datetime] = {}  # run_id -> création queue
        self._lock = asyncio.Lock()

    async def enqueue(self, run_id: str, event: Dict[str, Any]) -> None:
        """Ajouter event dans la queue pour ce run"""
        if not settings.ENABLE_EVENT_QUEUE:
            return

        async with self._lock:
            # Créer queue si nécessaire
            if run_id not in self._queues:
                self._queues[run_id] = []
                self._timestamps[run_id] = datetime.now(timezone.utc)

            # Ajouter event (avec limite quota)
            if len(self._queues[run_id]) < settings.EVENT_QUEUE_MAX_SIZE:
                self._queues[run_id].append(event)
            else:
                # Queue pleine → purger plus ancien
                self._queues[run_id].pop(0)
                self._queues[run_id].append(event)
                logger.warning(f"Event queue full for run {run_id}, purged oldest")

    async def get_events(self, run_id: str, clear: bool = True) -> List[Dict[str, Any]]:
        """Récupérer tous events en attente pour ce run"""
        if not settings.ENABLE_EVENT_QUEUE:
            return []

        async with self._lock:
            events = self._queues.get(run_id, []).copy()
            if clear and run_id in self._queues:
                self._queues[run_id].clear()
            return events

    async def has_events(self, run_id: str) -> bool:
        """Vérifier si des events en attente"""
        if not settings.ENABLE_EVENT_QUEUE:
            return False

        async with self._lock:
            return run_id in self._queues and len(self._queues[run_id]) > 0

    async def cleanup_expired(self) -> int:
        """Purger queues expirées (TTL dépassé)"""
        if not settings.ENABLE_EVENT_QUEUE:
            return 0

        now = datetime.now(timezone.utc)
        ttl_delta = timedelta(minutes=settings.EVENT_QUEUE_TTL_MINUTES)
        expired = []

        async with self._lock:
            for run_id, timestamp in self._timestamps.items():
                if now - timestamp > ttl_delta:
                    expired.append(run_id)

            for run_id in expired:
                del self._queues[run_id]
                del self._timestamps[run_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired event queues")
        return len(expired)

    async def clear_run(self, run_id: str) -> None:
        """Nettoyer queue pour ce run"""
        async with self._lock:
            if run_id in self._queues:
                del self._queues[run_id]
            if run_id in self._timestamps:
                del self._timestamps[run_id]


class RunLifecycleTracker:
    """
    Tracks run lifecycle to enforce exactly-one terminal event per run.
    Thread-safe using asyncio locks.
    """

    def __init__(self):
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def start_run(self, run_id: str) -> None:
        """Register new run as RUNNING."""
        async with self._global_lock:
            self._runs[run_id] = {
                "status": "RUNNING",
                "started_at": datetime.now(timezone.utc),
                "terminal_event": None,
            }
            self._locks[run_id] = asyncio.Lock()
            logger.info(f"Run lifecycle started: {run_id}")

    async def mark_terminal(self, run_id: str, event_type: str) -> bool:
        """
        Mark terminal event sent for run.
        Returns True if this is the first terminal, False if already sent.
        Thread-safe: Only one of N concurrent calls will succeed.
        """
        # Acquire run-specific lock
        async with self._global_lock:
            if run_id not in self._locks:
                logger.warning(f"Attempted to mark terminal for unknown run: {run_id}")
                return False
            lock = self._locks[run_id]

        async with lock:
            if run_id not in self._runs:
                return False

            run_state = self._runs[run_id]

            # Check if terminal already sent
            if run_state["terminal_event"] is not None:
                previous_type = run_state["terminal_event"]
                logger.warning(
                    f"Terminal event already sent for run '{run_id}': "
                    f"previous={previous_type}, attempted={event_type}"
                )
                return False

            # Mark terminal sent
            run_state["status"] = "TERMINAL"
            run_state["terminal_event"] = event_type
            run_state["terminal_at"] = datetime.now(timezone.utc)

            logger.info(f"Run lifecycle terminal: {run_id} → {event_type}")
            return True

    async def is_terminal_sent(self, run_id: str) -> bool:
        """Check if terminal event already sent for run."""
        if run_id not in self._runs:
            return False
        return self._runs[run_id]["terminal_event"] is not None

    async def get_status(self, run_id: str) -> Optional[str]:
        """Get current run status (RUNNING or TERMINAL)."""
        if run_id not in self._runs:
            return None
        return self._runs[run_id]["status"]

    async def cleanup_run(self, run_id: str, delay: int = 300) -> None:
        """
        Cleanup run state after delay (default 5 minutes).
        Prevents memory leak from long-lived tracker.
        """
        await asyncio.sleep(delay)
        async with self._global_lock:
            if run_id in self._runs:
                del self._runs[run_id]
            if run_id in self._locks:
                del self._locks[run_id]
            logger.debug(f"Run lifecycle cleaned up: {run_id}")

    async def get_all_running(self) -> list[str]:
        """Get all runs currently in RUNNING state (for debugging/monitoring)."""
        return [run_id for run_id, state in self._runs.items() if state["status"] == "RUNNING"]


class WSEventEmitter:
    """
    Centralized WebSocket event emitter.
    Enforces invariants: type, timestamp, run_id, terminal guarantee.
    """

    def __init__(self):
        self.lifecycle_tracker = RunLifecycleTracker()
        self.event_queue = EventQueue()  # CRQ-P1-5

    async def emit(
        self,
        websocket: WebSocket,
        event_type: str,
        run_id: str,
        data: Dict[str, Any],
        validate: Optional[bool] = None,
    ) -> bool:
        """
        Emit event with automatic invariant enforcement.

        Args:
            websocket: WebSocket connection
            event_type: Event type (thinking, phase, tool, etc.)
            run_id: Run identifier
            data: Event payload
            validate: Override validation (default: uses WS_STRICT_VALIDATION setting)

        Returns:
            True if event sent successfully, False otherwise

        Raises:
            InvalidEventStructure: If validation enabled and event invalid
            WebSocketClosed: If WebSocket connection closed
        """
        # Determine validation mode
        if validate is None:
            validate = settings.WS_STRICT_VALIDATION

        # v7 mode: bypass EventEmitter (legacy format)
        if settings.WS_MODE == "v7":
            return await self._emit_legacy(websocket, event_type, data)

        # Construct event model based on type
        try:
            event_data = {
                "type": event_type,
                "run_id": run_id,
                "data": data,
            }

            # Validate against Pydantic schema if enabled
            if validate:
                event = self._validate_event(event_type, event_data)
            else:
                # Compat mode: Auto-inject timestamp without full validation
                event = WSEventBase(**event_data)

            # Send to WebSocket (CRQ-P1-5: avec queue fallback)
            await self._send_to_websocket(websocket, event.model_dump(), run_id)

            logger.debug(f"Event emitted: {event_type} for run {run_id}")
            return True

        except ValidationError as e:
            logger.error(f"Event validation failed: {event_type} - {e}")
            if validate:
                raise InvalidEventStructure(f"Event validation failed: {e}")
            return False

        except Exception as e:
            logger.error(f"Failed to emit event: {event_type} - {e}", exc_info=True)
            # CRQ-2026-0203-001: Enhanced error context for terminal event failures
            if is_terminal_event(event_type):
                logger.error(
                    f"CRITICAL: Terminal event '{event_type}' failed for run {run_id}. "
                    f"Run will remain stuck in RUNNING state. Data: {data}"
                )
            return False

    async def emit_terminal(
        self,
        websocket: WebSocket,
        event_type: str,
        run_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Emit terminal event with idempotency guarantee.
        INVARIANT: Exactly ONE terminal event per run.

        Args:
            websocket: WebSocket connection
            event_type: Terminal event type (complete or error)
            run_id: Run identifier
            data: Event payload

        Returns:
            True if event sent (first terminal), False if already sent

        Raises:
            TerminalAlreadySent: If terminal already sent (when enforcement enabled)
        """
        if not is_terminal_event(event_type):
            logger.warning(f"emit_terminal called with non-terminal event: {event_type}")
            return await self.emit(websocket, event_type, run_id, data)

        # Check terminal enforcement
        if settings.WS_TERMINAL_ENFORCEMENT:
            # Mark terminal (idempotent)
            success = await self.lifecycle_tracker.mark_terminal(run_id, event_type)
            if not success:
                if await self.lifecycle_tracker.is_terminal_sent(run_id):
                    previous = self.lifecycle_tracker._runs[run_id]["terminal_event"]
                    raise TerminalAlreadySent(run_id, previous, event_type)
                logger.warning(f"Failed to mark terminal for unknown run: {run_id}")
                return False

        # Emit terminal event
        # 🔍 DEBUG: Log before emit
        logger.info(f"[DEBUG EventEmitter] Emitting terminal event '{event_type}' for run {run_id}")
        logger.info(f"[DEBUG EventEmitter] Data keys: {list(data.keys())}")
        logger.info(f"[DEBUG EventEmitter] Has response: {'response' in data}")
        if "response" in data:
            logger.info(
                f"[DEBUG EventEmitter] Response length: {len(data['response']) if data['response'] else 0}"
            )

        result = await self.emit(websocket, event_type, run_id, data)

        # 🔍 DEBUG: Log after emit
        logger.info(f"[DEBUG EventEmitter] Terminal event sent: {result}")

        # Schedule cleanup after 5 minutes
        if result:
            asyncio.create_task(self.lifecycle_tracker.cleanup_run(run_id, delay=300))

        return result

    def _validate_event(self, event_type: str, event_data: Dict[str, Any]) -> WSEvent:
        """Validate event against specific Pydantic model."""
        event_classes = {
            "thinking": WSThinkingEvent,
            "phase": WSPhaseEvent,
            "tool": WSToolEvent,
            "verification_item": WSVerificationItemEvent,
            "complete": WSCompleteEvent,
            "error": WSErrorEvent,
            "conversation_created": WSConversationCreatedEvent,
        }

        event_class = event_classes.get(event_type, WSEventBase)
        return event_class(**event_data)

    async def _send_to_websocket(
        self, websocket: WebSocket, event_dict: Dict[str, Any], run_id: Optional[str] = None
    ) -> None:
        """
        Send event to WebSocket with error handling.
        CRQ-P1-5: Si WebSocket fermé et queue activée → buffer event.
        """
        try:
            await websocket.send_json(event_dict)
        except RuntimeError as e:
            if "WebSocket is not connected" in str(e):
                # CRQ-P1-5: Buffer dans queue si activé
                if settings.ENABLE_EVENT_QUEUE and run_id:
                    await self.event_queue.enqueue(run_id, event_dict)
                    logger.info(
                        f"WebSocket closed, event buffered in queue for run {run_id} "
                        f"(type: {event_dict.get('type')})"
                    )
                    return  # Ne pas lever exception, event buffered
                raise WebSocketClosed("WebSocket connection closed")
            raise

    async def _emit_legacy(
        self, websocket: WebSocket, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """
        Emit event in v7 legacy format (no run_id, no timestamp validation).
        Used when WS_MODE="v7" for backward compatibility.
        """
        legacy_event = {"type": event_type, "data": data}
        try:
            await websocket.send_json(legacy_event)
            logger.debug(f"Legacy event emitted: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit legacy event: {event_type} - {e}")
            return False

    async def get_queued_events(self, run_id: str, clear: bool = True) -> List[Dict[str, Any]]:
        """
        Récupérer events en attente pour un run (CRQ-P1-5).
        Utilisé par API /api/v1/ws/events/{run_id} pour replay.
        """
        return await self.event_queue.get_events(run_id, clear=clear)

    async def has_queued_events(self, run_id: str) -> bool:
        """Vérifier si des events en attente (CRQ-P1-5)"""
        return await self.event_queue.has_events(run_id)


# Singleton instance
event_emitter = WSEventEmitter()
