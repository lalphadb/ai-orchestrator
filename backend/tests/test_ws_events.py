"""
Unit tests for WebSocket Event Models (ws_events.py)
Tests Pydantic validation for all 8 event types.
"""

from datetime import datetime

import pytest
from app.models.ws_events import (WSCompleteEvent, WSConversationCreatedEvent,
                                  WSErrorEvent, WSEventBase, WSPhaseEvent,
                                  WSThinkingEvent, WSToolEvent,
                                  WSVerificationItemEvent, is_terminal_event,
                                  utcnow_iso)
from pydantic import ValidationError


class TestTimestampGeneration:
    """Test ISO 8601 timestamp generation."""

    def test_utcnow_iso_format(self):
        """✓ utcnow_iso generates valid ISO 8601 timestamp with Z suffix."""
        timestamp = utcnow_iso()
        assert timestamp.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(timestamp[:-1])

    def test_timestamp_auto_generation(self):
        """✓ Events auto-generate timestamp if not provided."""
        event = WSEventBase(type="test", run_id="run123")
        assert event.timestamp is not None
        assert event.timestamp.endswith("Z")


class TestWSEventBase:
    """Test base event validation."""

    def test_valid_base_event(self):
        """✓ Valid base event passes validation."""
        event = WSEventBase(
            type="thinking",
            timestamp="2026-01-28T10:30:00.000Z",
            run_id="a1b2c3d4",
            data={"message": "Testing"},
        )
        assert event.type == "thinking"
        assert event.run_id == "a1b2c3d4"
        assert event.data == {"message": "Testing"}

    def test_missing_type(self):
        """✓ Event without type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSEventBase(run_id="run123")
        assert "type" in str(exc_info.value)

    def test_missing_run_id(self):
        """✓ Event without run_id fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSEventBase(type="thinking")
        assert "run_id" in str(exc_info.value)

    def test_invalid_timestamp(self):
        """✓ Invalid ISO 8601 timestamp fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSEventBase(
                type="thinking",
                run_id="run123",
                timestamp="not-a-timestamp",
            )
        assert "Invalid ISO 8601 timestamp" in str(exc_info.value)

    def test_timestamp_without_z_suffix(self):
        """✓ Timestamp without Z suffix is accepted."""
        event = WSEventBase(
            type="thinking",
            run_id="run123",
            timestamp="2026-01-28T10:30:00.000",
        )
        assert event.timestamp == "2026-01-28T10:30:00.000"


class TestWSThinkingEvent:
    """Test thinking event validation."""

    def test_valid_thinking_event(self):
        """✓ Valid thinking event passes validation."""
        event = WSThinkingEvent(
            run_id="run123",
            data={"message": "Analyzing request..."},
        )
        assert event.type == "thinking"
        assert event.data["message"] == "Analyzing request..."

    def test_thinking_without_message(self):
        """✓ Thinking event without 'message' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSThinkingEvent(run_id="run123", data={"other": "value"})
        assert "message" in str(exc_info.value).lower()


class TestWSPhaseEvent:
    """Test phase event validation."""

    def test_valid_phase_event(self):
        """✓ Valid phase event passes validation."""
        event = WSPhaseEvent(
            run_id="run123",
            data={"phase": "spec", "status": "starting"},
        )
        assert event.type == "phase"
        assert event.data["phase"] == "spec"
        assert event.data["status"] == "starting"

    def test_phase_without_phase_key(self):
        """✓ Phase event without 'phase' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSPhaseEvent(run_id="run123", data={"status": "starting"})
        assert "phase" in str(exc_info.value).lower()

    def test_phase_without_status_key(self):
        """✓ Phase event without 'status' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSPhaseEvent(run_id="run123", data={"phase": "spec"})
        assert "status" in str(exc_info.value).lower()

    def test_invalid_phase_value(self):
        """✓ Invalid phase value fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSPhaseEvent(
                run_id="run123",
                data={"phase": "invalid_phase", "status": "starting"},
            )
        assert "Invalid phase" in str(exc_info.value)

    def test_invalid_status_value(self):
        """✓ Invalid status value fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSPhaseEvent(
                run_id="run123",
                data={"phase": "spec", "status": "invalid_status"},
            )
        assert "Invalid status" in str(exc_info.value)

    def test_all_valid_phases(self):
        """✓ All valid phases are accepted."""
        valid_phases = ["spec", "plan", "execute", "verify", "repair", "complete"]
        for phase in valid_phases:
            event = WSPhaseEvent(
                run_id="run123",
                data={"phase": phase, "status": "starting"},
            )
            assert event.data["phase"] == phase

    def test_all_valid_statuses(self):
        """✓ All valid statuses are accepted."""
        valid_statuses = ["starting", "in_progress", "complete", "failed"]
        for status in valid_statuses:
            event = WSPhaseEvent(
                run_id="run123",
                data={"phase": "spec", "status": status},
            )
            assert event.data["status"] == status


class TestWSToolEvent:
    """Test tool event validation."""

    def test_valid_tool_event(self):
        """✓ Valid tool event passes validation."""
        event = WSToolEvent(
            run_id="run123",
            data={"tool": "bash", "status": "success", "output": "Done"},
        )
        assert event.type == "tool"
        assert event.data["tool"] == "bash"
        assert event.data["status"] == "success"

    def test_tool_without_tool_key(self):
        """✓ Tool event without 'tool' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSToolEvent(run_id="run123", data={"status": "success"})
        assert "tool" in str(exc_info.value).lower()

    def test_tool_without_status_key(self):
        """✓ Tool event without 'status' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSToolEvent(run_id="run123", data={"tool": "bash"})
        assert "status" in str(exc_info.value).lower()


class TestWSVerificationItemEvent:
    """Test verification item event validation."""

    def test_valid_verification_item_event(self):
        """✓ Valid verification item event passes validation."""
        event = WSVerificationItemEvent(
            run_id="run123",
            data={"name": "tests", "passed": True, "message": "All tests passed"},
        )
        assert event.type == "verification_item"
        assert event.data["name"] == "tests"
        assert event.data["passed"] is True

    def test_verification_item_without_name(self):
        """✓ Verification item without 'name' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSVerificationItemEvent(run_id="run123", data={"passed": True})
        assert "name" in str(exc_info.value).lower()

    def test_verification_item_without_passed(self):
        """✓ Verification item without 'passed' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSVerificationItemEvent(run_id="run123", data={"name": "tests"})
        assert "passed" in str(exc_info.value).lower()

    def test_verification_item_passed_not_boolean(self):
        """✓ Verification item with non-boolean 'passed' fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSVerificationItemEvent(
                run_id="run123",
                data={"name": "tests", "passed": "yes"},
            )
        assert "boolean" in str(exc_info.value).lower()


class TestWSCompleteEvent:
    """Test complete (terminal) event validation."""

    def test_valid_complete_event(self):
        """✓ Valid complete event passes validation."""
        event = WSCompleteEvent(
            run_id="run123",
            data={"message": "Task completed successfully"},
        )
        assert event.type == "complete"
        assert event.data["message"] == "Task completed successfully"

    def test_complete_event_default_data(self):
        """✓ Complete event has default data if not provided."""
        event = WSCompleteEvent(run_id="run123")
        assert event.data["message"] == "Run completed successfully"


class TestWSErrorEvent:
    """Test error (terminal) event validation."""

    def test_valid_error_event(self):
        """✓ Valid error event passes validation."""
        event = WSErrorEvent(
            run_id="run123",
            data={"message": "Execution failed", "error": "ValueError"},
        )
        assert event.type == "error"
        assert event.data["message"] == "Execution failed"

    def test_error_without_message(self):
        """✓ Error event without 'message' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSErrorEvent(run_id="run123", data={"error": "ValueError"})
        assert "message" in str(exc_info.value).lower()


class TestWSConversationCreatedEvent:
    """Test conversation created event validation."""

    def test_valid_conversation_created_event(self):
        """✓ Valid conversation created event passes validation."""
        event = WSConversationCreatedEvent(
            run_id="run123",
            data={"conversation_id": "conv-12345"},
        )
        assert event.type == "conversation_created"
        assert event.data["conversation_id"] == "conv-12345"

    def test_conversation_created_without_conversation_id(self):
        """✓ Conversation created without 'conversation_id' key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WSConversationCreatedEvent(run_id="run123", data={})
        assert "conversation_id" in str(exc_info.value).lower()


class TestTerminalEventHelpers:
    """Test terminal event helper functions."""

    def test_is_terminal_event_complete(self):
        """✓ 'complete' is recognized as terminal event."""
        assert is_terminal_event("complete") is True

    def test_is_terminal_event_error(self):
        """✓ 'error' is recognized as terminal event."""
        assert is_terminal_event("error") is True

    def test_is_terminal_event_non_terminal(self):
        """✓ Non-terminal event types return False."""
        assert is_terminal_event("thinking") is False
        assert is_terminal_event("phase") is False
        assert is_terminal_event("tool") is False
        assert is_terminal_event("verification_item") is False
        assert is_terminal_event("conversation_created") is False
