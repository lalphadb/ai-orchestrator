"""
Tests pour CRQ-P1-5: Event Queue WebSocket (anti-perte déconnexion)
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from app.core.config import settings
from app.services.websocket.event_emitter import EventQueue, WSEventEmitter


class TestEventQueue:
    """Tests pour EventQueue (buffer anti-perte)"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup et restauration des settings"""
        original_enable_event_queue = settings.ENABLE_EVENT_QUEUE
        original_max_size = settings.EVENT_QUEUE_MAX_SIZE
        original_ttl = settings.EVENT_QUEUE_TTL_MINUTES
        yield
        settings.ENABLE_EVENT_QUEUE = original_enable_event_queue
        settings.EVENT_QUEUE_MAX_SIZE = original_max_size
        settings.EVENT_QUEUE_TTL_MINUTES = original_ttl

    @pytest.mark.asyncio
    async def test_enqueue_event_when_enabled(self):
        """Event doit être bufferisé si flag ON"""
        settings.ENABLE_EVENT_QUEUE = True

        queue = EventQueue()
        event = {"type": "thinking", "run_id": "test-run", "data": {"message": "test"}}

        await queue.enqueue("test-run", event)

        # Vérifier event dans queue
        assert await queue.has_events("test-run")
        events = await queue.get_events("test-run", clear=False)
        assert len(events) == 1
        assert events[0]["type"] == "thinking"

    @pytest.mark.asyncio
    async def test_enqueue_disabled_when_flag_off(self):
        """Event ne doit PAS être bufferisé si flag OFF (backward compat)"""
        settings.ENABLE_EVENT_QUEUE = False

        queue = EventQueue()
        event = {"type": "thinking", "run_id": "test-run", "data": {"message": "test"}}

        await queue.enqueue("test-run", event)

        # Queue doit rester vide
        assert not await queue.has_events("test-run")

    @pytest.mark.asyncio
    async def test_get_events_clears_queue(self):
        """get_events(clear=True) doit vider la queue"""
        settings.ENABLE_EVENT_QUEUE = True

        queue = EventQueue()
        await queue.enqueue("test-run", {"type": "event1"})
        await queue.enqueue("test-run", {"type": "event2"})

        # Récupérer avec clear=True
        events = await queue.get_events("test-run", clear=True)
        assert len(events) == 2

        # Queue doit être vide
        assert not await queue.has_events("test-run")

    @pytest.mark.asyncio
    async def test_get_events_preserves_queue_if_no_clear(self):
        """get_events(clear=False) doit préserver la queue"""
        settings.ENABLE_EVENT_QUEUE = True

        queue = EventQueue()
        await queue.enqueue("test-run", {"type": "event1"})

        # Récupérer sans clear
        events = await queue.get_events("test-run", clear=False)
        assert len(events) == 1

        # Queue doit toujours contenir l'event
        assert await queue.has_events("test-run")

    @pytest.mark.asyncio
    async def test_queue_quota_enforcement(self):
        """Queue doit purger plus ancien si quota dépassé"""
        settings.ENABLE_EVENT_QUEUE = True
        settings.EVENT_QUEUE_MAX_SIZE = 3  # Limite à 3 events

        queue = EventQueue()

        # Ajouter 4 events (dépasse quota)
        for i in range(4):
            await queue.enqueue("test-run", {"type": f"event{i}", "index": i})

        events = await queue.get_events("test-run", clear=False)

        # Doit contenir seulement les 3 derniers (event1, event2, event3)
        assert len(events) == 3
        assert events[0]["index"] == 1  # event0 purgé
        assert events[2]["index"] == 3

    @pytest.mark.asyncio
    async def test_cleanup_expired_queues(self):
        """Cleanup doit purger queues expirées (TTL)"""
        settings.ENABLE_EVENT_QUEUE = True
        settings.EVENT_QUEUE_TTL_MINUTES = 1  # TTL 1 minute

        queue = EventQueue()
        await queue.enqueue("test-run", {"type": "event1"})

        # Simuler expiration (modifier timestamp manuellement)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        queue._timestamps["test-run"] = old_time

        # Cleanup
        cleaned = await queue.cleanup_expired()

        # Queue expirée doit être purgée
        assert cleaned == 1
        assert not await queue.has_events("test-run")

    @pytest.mark.asyncio
    async def test_clear_run_removes_queue(self):
        """clear_run doit supprimer complètement la queue d'un run"""
        settings.ENABLE_EVENT_QUEUE = True

        queue = EventQueue()
        await queue.enqueue("test-run", {"type": "event1"})

        await queue.clear_run("test-run")

        # Queue doit être supprimée
        assert not await queue.has_events("test-run")


class TestWSEventEmitterWithQueue:
    """Tests pour intégration queue dans WSEventEmitter"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup et restauration des settings"""
        original_enable_event_queue = settings.ENABLE_EVENT_QUEUE
        yield
        settings.ENABLE_EVENT_QUEUE = original_enable_event_queue

    @pytest.mark.asyncio
    async def test_websocket_closed_buffers_event_when_enabled(self):
        """Event doit être bufferisé si WebSocket fermé et flag ON"""
        settings.ENABLE_EVENT_QUEUE = True
        settings.WS_STRICT_VALIDATION = False  # Désactiver validation pour test

        emitter = WSEventEmitter()

        # Mock WebSocket qui lève RuntimeError (fermé)
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=RuntimeError("WebSocket is not connected"))

        # Tenter d'émettre event (ne doit PAS lever exception)
        result = await emitter.emit(mock_ws, "thinking", "test-run", {"message": "test"})

        # Emit doit réussir (event bufferisé)
        assert result is True

        # Event doit être dans la queue
        assert await emitter.has_queued_events("test-run")
        events = await emitter.get_queued_events("test-run", clear=False)
        assert len(events) == 1
        assert events[0]["type"] == "thinking"

    @pytest.mark.asyncio
    async def test_websocket_closed_raises_when_queue_disabled(self):
        """Exception doit être levée si WebSocket fermé et flag OFF"""
        settings.ENABLE_EVENT_QUEUE = False
        settings.WS_STRICT_VALIDATION = False

        emitter = WSEventEmitter()

        # Mock WebSocket fermé
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=RuntimeError("WebSocket is not connected"))

        # Tenter d'émettre event (doit échouer)
        result = await emitter.emit(mock_ws, "thinking", "test-run", {"message": "test"})

        # Emit doit échouer (pas de buffering)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_queued_events_returns_buffered_events(self):
        """get_queued_events doit retourner tous events bufferisés"""
        settings.ENABLE_EVENT_QUEUE = True
        settings.WS_STRICT_VALIDATION = False

        emitter = WSEventEmitter()

        # Mock WebSocket fermé
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=RuntimeError("WebSocket is not connected"))

        # Émettre 3 events (tous bufferisés)
        await emitter.emit(mock_ws, "thinking", "test-run", {"msg": "1"})
        await emitter.emit(mock_ws, "tool", "test-run", {"msg": "2"})
        await emitter.emit(mock_ws, "phase", "test-run", {"msg": "3"})

        # Récupérer events
        events = await emitter.get_queued_events("test-run", clear=True)

        assert len(events) == 3
        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "tool"
        assert events[2]["type"] == "phase"

        # Queue doit être vide après clear
        assert not await emitter.has_queued_events("test-run")
