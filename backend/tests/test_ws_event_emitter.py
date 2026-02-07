"""
Unit tests for WebSocket EventEmitter (event_emitter.py)
Tests terminal idempotency, concurrent terminals, validation, compat mode.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from app.services.websocket.event_emitter import (RunLifecycleTracker,
                                                  WSEventEmitter)
from app.services.websocket.exceptions import (InvalidEventStructure,
                                               TerminalAlreadySent)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = MagicMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def event_emitter():
    """Create fresh EventEmitter instance."""
    return WSEventEmitter()


@pytest.fixture
def lifecycle_tracker():
    """Create fresh RunLifecycleTracker instance."""
    return RunLifecycleTracker()


class TestRunLifecycleTracker:
    """Test RunLifecycleTracker lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_run(self, lifecycle_tracker):
        """✓ Starting run registers it as RUNNING."""
        await lifecycle_tracker.start_run("run123")
        status = await lifecycle_tracker.get_status("run123")
        assert status == "RUNNING"

    @pytest.mark.asyncio
    async def test_mark_terminal_first_time(self, lifecycle_tracker):
        """✓ First terminal mark succeeds."""
        await lifecycle_tracker.start_run("run123")
        success = await lifecycle_tracker.mark_terminal("run123", "complete")
        assert success is True

        status = await lifecycle_tracker.get_status("run123")
        assert status == "TERMINAL"

        is_sent = await lifecycle_tracker.is_terminal_sent("run123")
        assert is_sent is True

    @pytest.mark.asyncio
    async def test_mark_terminal_second_time_fails(self, lifecycle_tracker):
        """✓ Second terminal mark fails (idempotency)."""
        await lifecycle_tracker.start_run("run123")
        await lifecycle_tracker.mark_terminal("run123", "complete")

        # Attempt second terminal
        success = await lifecycle_tracker.mark_terminal("run123", "error")
        assert success is False

    @pytest.mark.asyncio
    async def test_mark_terminal_unknown_run(self, lifecycle_tracker):
        """✓ Marking terminal for unknown run fails."""
        success = await lifecycle_tracker.mark_terminal("unknown", "complete")
        assert success is False

    @pytest.mark.asyncio
    async def test_concurrent_terminal_marks(self, lifecycle_tracker):
        """✓ Concurrent terminal marks - only 1 of N succeeds."""
        await lifecycle_tracker.start_run("run123")

        # Launch 10 concurrent terminal marks
        tasks = [lifecycle_tracker.mark_terminal("run123", "complete") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Exactly 1 should succeed
        assert sum(results) == 1
        assert results.count(True) == 1
        assert results.count(False) == 9

    @pytest.mark.asyncio
    async def test_get_all_running(self, lifecycle_tracker):
        """✓ get_all_running returns only RUNNING runs."""
        await lifecycle_tracker.start_run("run1")
        await lifecycle_tracker.start_run("run2")
        await lifecycle_tracker.start_run("run3")

        running = await lifecycle_tracker.get_all_running()
        assert len(running) == 3
        assert "run1" in running

        # Mark one terminal
        await lifecycle_tracker.mark_terminal("run2", "complete")
        running = await lifecycle_tracker.get_all_running()
        assert len(running) == 2
        assert "run2" not in running

    @pytest.mark.asyncio
    async def test_cleanup_run(self, lifecycle_tracker):
        """✓ Cleanup removes run state after delay."""
        await lifecycle_tracker.start_run("run123")
        await lifecycle_tracker.mark_terminal("run123", "complete")

        # Cleanup with minimal delay
        await lifecycle_tracker.cleanup_run("run123", delay=0.01)

        status = await lifecycle_tracker.get_status("run123")
        assert status is None


class TestWSEventEmitter:
    """Test WSEventEmitter event emission."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_valid_thinking_event(self, mock_settings, event_emitter, mock_websocket):
        """✓ Emit valid thinking event."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        success = await event_emitter.emit(
            mock_websocket,
            "thinking",
            "run123",
            {"message": "Analyzing..."},
        )

        assert success is True
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "thinking"
        assert call_args["run_id"] == "run123"
        assert call_args["data"]["message"] == "Analyzing..."
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_valid_phase_event(self, mock_settings, event_emitter, mock_websocket):
        """✓ Emit valid phase event."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        success = await event_emitter.emit(
            mock_websocket,
            "phase",
            "run123",
            {"phase": "spec", "status": "starting"},
        )

        assert success is True
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["data"]["phase"] == "spec"
        assert call_args["data"]["status"] == "starting"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_invalid_event_with_validation(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """✓ Emit invalid event with validation raises exception."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        with pytest.raises(InvalidEventStructure):
            await event_emitter.emit(
                mock_websocket,
                "thinking",
                "run123",
                {"missing": "message"},  # Missing required 'message' key
            )

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_invalid_event_without_validation(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """✓ Emit invalid event without validation succeeds (compat mode)."""
        mock_settings.WS_MODE = "compat"
        mock_settings.WS_STRICT_VALIDATION = False

        success = await event_emitter.emit(
            mock_websocket,
            "thinking",
            "run123",
            {"missing": "message"},
            validate=False,
        )

        # Should succeed without validation
        assert success is True

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_terminal_first_time(self, mock_settings, event_emitter, mock_websocket):
        """✓ First terminal emission succeeds."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        await event_emitter.lifecycle_tracker.start_run("run123")

        success = await event_emitter.emit_terminal(
            mock_websocket,
            "complete",
            "run123",
            {"message": "Done"},
        )

        assert success is True
        is_sent = await event_emitter.lifecycle_tracker.is_terminal_sent("run123")
        assert is_sent is True

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_terminal_second_time_raises(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """✓ Second terminal emission raises TerminalAlreadySent."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        await event_emitter.lifecycle_tracker.start_run("run123")
        await event_emitter.emit_terminal(mock_websocket, "complete", "run123", {"message": "Done"})

        # Attempt second terminal
        with pytest.raises(TerminalAlreadySent) as exc_info:
            await event_emitter.emit_terminal(
                mock_websocket, "error", "run123", {"message": "Failed"}
            )

        assert exc_info.value.run_id == "run123"
        assert exc_info.value.previous_type == "complete"
        assert exc_info.value.attempted_type == "error"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_terminal_concurrent(self, mock_settings, event_emitter, mock_websocket):
        """✓ Concurrent terminal emissions - only 1 succeeds, rest raise."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = True

        await event_emitter.lifecycle_tracker.start_run("run123")

        # Launch 10 concurrent terminal emissions
        async def emit_with_exception_handling():
            try:
                return await event_emitter.emit_terminal(
                    mock_websocket, "complete", "run123", {"message": "Done"}
                )
            except TerminalAlreadySent:
                return False

        tasks = [emit_with_exception_handling() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Exactly 1 should succeed
        assert sum(results) == 1

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_terminal_without_enforcement(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """✓ Terminal emission without enforcement allows multiple terminals."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True
        mock_settings.WS_TERMINAL_ENFORCEMENT = False

        success1 = await event_emitter.emit_terminal(
            mock_websocket, "complete", "run123", {"message": "Done"}
        )
        success2 = await event_emitter.emit_terminal(
            mock_websocket, "error", "run123", {"message": "Failed"}
        )

        # Both should succeed when enforcement disabled
        assert success1 is True
        assert success2 is True

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_legacy_mode(self, mock_settings, event_emitter, mock_websocket):
        """✓ Legacy mode (v7) emits without run_id/timestamp."""
        mock_settings.WS_MODE = "v7"

        success = await event_emitter.emit(
            mock_websocket,
            "thinking",
            "run123",  # run_id ignored in v7
            {"message": "Analyzing..."},
        )

        assert success is True
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "thinking"
        assert call_args["data"]["message"] == "Analyzing..."
        # Should NOT have run_id in v7 mode
        assert "run_id" not in call_args

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_emit_all_event_types(self, mock_settings, event_emitter, mock_websocket):
        """✓ Emit all event types successfully."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        event_tests = [
            ("thinking", {"message": "Thinking..."}),
            ("phase", {"phase": "spec", "status": "starting"}),
            ("tool", {"tool": "bash", "status": "success"}),
            ("verification_item", {"name": "tests", "passed": True}),
            ("conversation_created", {"conversation_id": "conv123"}),
        ]

        for event_type, data in event_tests:
            success = await event_emitter.emit(
                mock_websocket, event_type, f"run_{event_type}", data
            )
            assert success is True, f"Failed to emit {event_type}"

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_websocket_closed_handling(self, mock_settings, event_emitter, mock_websocket):
        """✓ Handle WebSocket closed gracefully."""
        mock_settings.WS_MODE = "v8"
        mock_settings.WS_STRICT_VALIDATION = True

        # Simulate WebSocket closed
        mock_websocket.send_json.side_effect = RuntimeError("WebSocket is not connected")

        # Should return False, not crash
        success = await event_emitter.emit(
            mock_websocket, "thinking", "run123", {"message": "Test"}
        )
        assert success is False


class TestCompatibilityMode:
    """Test backward compatibility modes."""

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_compat_mode_emits_v8_structure(
        self, mock_settings, event_emitter, mock_websocket
    ):
        """✓ Compat mode emits v8 structure with optional validation."""
        mock_settings.WS_MODE = "compat"
        mock_settings.WS_STRICT_VALIDATION = True

        success = await event_emitter.emit(
            mock_websocket,
            "thinking",
            "run123",
            {"message": "Analyzing..."},
        )

        assert success is True
        call_args = mock_websocket.send_json.call_args[0][0]
        # Should have v8 structure
        assert "type" in call_args
        assert "run_id" in call_args
        assert "timestamp" in call_args
        assert "data" in call_args

    @pytest.mark.asyncio
    @patch("app.services.websocket.event_emitter.settings")
    async def test_v7_mode_rollback(self, mock_settings, event_emitter, mock_websocket):
        """✓ v7 mode provides rollback capability."""
        mock_settings.WS_MODE = "v7"

        # Should emit legacy format
        success = await event_emitter.emit(
            mock_websocket, "thinking", "run123", {"message": "Test"}
        )

        assert success is True
        call_args = mock_websocket.send_json.call_args[0][0]
        # Should NOT have v8 structure
        assert "run_id" not in call_args
        assert "timestamp" not in call_args
