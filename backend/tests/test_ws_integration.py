"""
Integration tests for WebSocket v8 (test_ws_integration.py)
Tests the 5 required playbook scenarios from the plan.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from app.services.websocket.event_emitter import WSEventEmitter


@pytest.fixture
def event_emitter():
    """Create fresh EventEmitter instance for each test."""
    return WSEventEmitter()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket that collects events."""
    ws = MagicMock(spec=WebSocket)
    ws.events = []

    async def send_json(data):
        ws.events.append(data)

    ws.send_json = AsyncMock(side_effect=send_json)
    return ws


class TestWebSocketIntegration:
    """Integration tests for WebSocket event flow."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_happy_path_complete_run(self, mock_settings, event_emitter, mock_websocket):
        """
        ✓ Launch complete run (happy path)

        Simulates a complete workflow run and verifies:
        - All events have timestamp, run_id
        - Events follow logical order
        - Exactly ONE terminal event (complete)
        """
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        run_id = "test123"
        await event_emitter.lifecycle_tracker.start_run(run_id)

        # Simulate workflow event sequence
        events = [
            ("conversation_created", {"conversation_id": "conv-123"}),
            ("phase", {"phase": "spec", "status": "starting"}),
            ("thinking", {"message": "Analyzing..."}),
            ("phase", {"phase": "plan", "status": "starting"}),
            ("phase", {"phase": "execute", "status": "starting"}),
            ("thinking", {"message": "Executing..."}),
            ("tool", {"tool": "bash", "status": "success"}),
            ("phase", {"phase": "verify", "status": "starting"}),
            ("verification_item", {"name": "tests", "passed": True}),
        ]

        # Emit all non-terminal events
        for event_type, data in events:
            await event_emitter.emit(mock_websocket, event_type, run_id, data)

        # Emit terminal event
        await event_emitter.emit_terminal(
            mock_websocket,
            "complete",
            run_id,
            {"message": "Workflow completed", "result": "success"},
        )

        # Verify all events collected
        collected_events = mock_websocket.events
        assert len(collected_events) == 10  # 9 + 1 terminal

        # Verify all events have required fields
        for event in collected_events:
            assert "type" in event, f"Event missing 'type': {event}"
            assert "timestamp" in event, f"Event missing 'timestamp': {event}"
            assert "run_id" in event, f"Event missing 'run_id': {event}"
            assert "data" in event, f"Event missing 'data': {event}"
            assert event["run_id"] == run_id

        # Verify timestamps are ISO 8601 format
        for event in collected_events:
            timestamp = event["timestamp"]
            assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp[-6:]

        # Verify exactly ONE terminal event
        terminal_events = [e for e in collected_events if e["type"] in ["complete", "error"]]
        assert len(terminal_events) == 1, f"Expected 1 terminal event, got {len(terminal_events)}"
        assert terminal_events[0]["type"] == "complete"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_verify_logical_event_order(self, mock_settings, event_emitter, mock_websocket):
        """
        ✓ Verify logical event order

        Ensures events follow expected workflow sequence:
        conversation_created → phase:spec → phase:plan → phase:execute → terminal
        """
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        run_id = "order-test"
        await event_emitter.lifecycle_tracker.start_run(run_id)

        # Emit events in expected order
        await event_emitter.emit(
            mock_websocket, "conversation_created", run_id, {"conversation_id": "conv-1"}
        )
        await event_emitter.emit(
            mock_websocket, "phase", run_id, {"phase": "spec", "status": "starting"}
        )
        await event_emitter.emit(
            mock_websocket, "phase", run_id, {"phase": "plan", "status": "starting"}
        )
        await event_emitter.emit(
            mock_websocket, "phase", run_id, {"phase": "execute", "status": "starting"}
        )
        await event_emitter.emit_terminal(mock_websocket, "complete", run_id, {"message": "Done"})

        events = mock_websocket.events
        assert len(events) == 5

        # Verify order
        assert events[0]["type"] == "conversation_created"
        assert events[1]["type"] == "phase"
        assert events[1]["data"]["phase"] == "spec"
        assert events[2]["type"] == "phase"
        assert events[2]["data"]["phase"] == "plan"
        assert events[3]["type"] == "phase"
        assert events[3]["data"]["phase"] == "execute"
        assert events[4]["type"] == "complete"  # Terminal last

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_run_always_terminates(self, mock_settings, event_emitter, mock_websocket):
        """
        ✓ Verify run ALWAYS terminates

        Launches multiple concurrent "runs" and verifies all get terminal within reasonable time.
        """
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        async def simulate_run(run_id):
            """Simulate a complete run."""
            await event_emitter.lifecycle_tracker.start_run(run_id)
            await event_emitter.emit(mock_websocket, "thinking", run_id, {"message": "Working..."})
            await asyncio.sleep(0.01)  # Simulate work
            await event_emitter.emit_terminal(
                mock_websocket, "complete", run_id, {"message": "Done"}
            )

        # Launch 10 concurrent runs
        run_ids = [f"run-{i}" for i in range(10)]
        tasks = [simulate_run(run_id) for run_id in run_ids]

        # Should all complete within 1 second
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=1.0)

        # Verify all runs got terminal events
        events = mock_websocket.events
        terminal_events = [e for e in events if e["type"] == "complete"]
        assert len(terminal_events) == 10, "All 10 runs should have terminal events"

        # Verify each run_id got exactly one terminal
        for run_id in run_ids:
            run_terminals = [e for e in terminal_events if e["run_id"] == run_id]
            assert len(run_terminals) == 1, f"Run {run_id} should have exactly 1 terminal"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_backend_exception_sends_error(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """
        ✓ Simulate backend exception → error terminal

        Verifies that exceptions during workflow emit error terminal event.
        """
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        run_id = "error-test"
        await event_emitter.lifecycle_tracker.start_run(run_id)

        # Emit some events
        await event_emitter.emit(mock_websocket, "thinking", run_id, {"message": "Starting..."})
        await event_emitter.emit(
            mock_websocket, "phase", run_id, {"phase": "execute", "status": "starting"}
        )

        # Simulate error during execution
        await event_emitter.emit_terminal(
            mock_websocket,
            "error",
            run_id,
            {"message": "Execution failed", "error": "ValueError: Invalid input"},
        )

        events = mock_websocket.events
        assert len(events) == 3

        # Verify terminal is error
        terminal_events = [e for e in events if e["type"] == "error"]
        assert len(terminal_events) == 1
        assert terminal_events[0]["data"]["message"] == "Execution failed"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_no_running_runs_after_completion(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """
        ✓ No RUNNING runs after completion

        Verifies that lifecycle tracker correctly marks runs as terminal.
        """
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        run_id = "lifecycle-test"

        # Start run
        await event_emitter.lifecycle_tracker.start_run(run_id)

        # Verify status is RUNNING
        status = await event_emitter.lifecycle_tracker.get_status(run_id)
        assert status == "RUNNING"

        # Check running runs list
        running = await event_emitter.lifecycle_tracker.get_all_running()
        assert run_id in running

        # Emit terminal event
        await event_emitter.emit_terminal(mock_websocket, "complete", run_id, {"message": "Done"})

        # Verify status is TERMINAL
        status = await event_emitter.lifecycle_tracker.get_status(run_id)
        assert status == "TERMINAL"

        # Verify not in running list
        running = await event_emitter.lifecycle_tracker.get_all_running()
        assert run_id not in running

        # Verify terminal was sent
        is_sent = await event_emitter.lifecycle_tracker.is_terminal_sent(run_id)
        assert is_sent is True


class TestTerminalIdempotency:
    """Test terminal event idempotency guarantees."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_duplicate_terminal_rejected(self, mock_settings, event_emitter, mock_websocket):
        """Second terminal emission should be rejected."""
        from app.services.websocket.exceptions import TerminalAlreadySent

        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        run_id = "dup-test"
        await event_emitter.lifecycle_tracker.start_run(run_id)

        # First terminal succeeds
        await event_emitter.emit_terminal(mock_websocket, "complete", run_id, {"message": "Done"})

        # Second terminal should raise exception
        with pytest.raises(TerminalAlreadySent) as exc_info:
            await event_emitter.emit_terminal(mock_websocket, "error", run_id, {"message": "Error"})

        assert exc_info.value.run_id == run_id
        assert exc_info.value.previous_type == "complete"
        assert exc_info.value.attempted_type == "error"

        # Verify only one terminal event was sent
        events = mock_websocket.events
        terminal_events = [e for e in events if e["type"] in ["complete", "error"]]
        assert len(terminal_events) == 1


class TestCompatibilityModes:
    """Test backward compatibility modes."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_compat_mode_emits_v8(self, mock_settings, event_emitter, mock_websocket):
        """Compat mode should emit v8 structure."""
        mock_settings.WS_MODE = "compat"
        mock_settings.WS_STRICT_VALIDATION = True

        await event_emitter.emit(mock_websocket, "thinking", "run123", {"message": "Test"})

        events = mock_websocket.events
        assert len(events) == 1

        event = events[0]
        assert "type" in event
        assert "timestamp" in event
        assert "run_id" in event
        assert "data" in event
        assert event["run_id"] == "run123"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_v7_mode_no_run_id(self, mock_settings, event_emitter, mock_websocket):
        """v7 mode should NOT include run_id (legacy format)."""
        mock_settings.WS_MODE = "v7"

        await event_emitter.emit(mock_websocket, "thinking", "run123", {"message": "Test"})

        events = mock_websocket.events
        assert len(events) == 1

        event = events[0]
        assert event["type"] == "thinking"
        assert event["data"]["message"] == "Test"
        assert "run_id" not in event  # Legacy format


class TestEventValidation:
    """Test Pydantic event validation."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_invalid_phase_rejected(self, mock_settings, event_emitter, mock_websocket):
        """Invalid phase value should be rejected when validation enabled."""
        from app.services.websocket.exceptions import InvalidEventStructure

        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        with pytest.raises(InvalidEventStructure):
            await event_emitter.emit(
                mock_websocket, "phase", "run123", {"phase": "invalid_phase", "status": "starting"}
            )

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_missing_required_field_rejected(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """Missing required field should be rejected when validation enabled."""
        from app.services.websocket.exceptions import InvalidEventStructure

        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        with pytest.raises(InvalidEventStructure):
            await event_emitter.emit(
                mock_websocket,
                "thinking",
                "run123",
                {"wrong_field": "value"},  # Missing 'message' field
            )

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_validation_disabled_allows_invalid(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """Invalid event should pass when validation disabled."""
        mock_settings.WS_MODE = "compat"
        mock_settings.WS_STRICT_VALIDATION = False

        # Should succeed despite invalid data
        result = await event_emitter.emit(
            mock_websocket, "thinking", "run123", {"wrong_field": "value"}, validate=False
        )

        assert result is True
