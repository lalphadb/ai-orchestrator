"""
WebSocket Event Emitter Exceptions
Custom exceptions for terminal event tracking and validation.
"""


class WSEventEmitterError(Exception):
    """Base exception for EventEmitter errors."""

    pass


class TerminalAlreadySent(WSEventEmitterError):
    """
    Raised when attempting to send a second terminal event for a run.
    INVARIANT: Exactly ONE terminal event (complete OR error) per run.
    """

    def __init__(self, run_id: str, previous_type: str, attempted_type: str):
        self.run_id = run_id
        self.previous_type = previous_type
        self.attempted_type = attempted_type
        super().__init__(
            f"Terminal event already sent for run '{run_id}': "
            f"previous={previous_type}, attempted={attempted_type}"
        )


class InvalidEventStructure(WSEventEmitterError):
    """Raised when event fails Pydantic validation."""

    pass


class RunNotFound(WSEventEmitterError):
    """Raised when attempting to emit event for unknown run_id."""

    pass


class WebSocketClosed(WSEventEmitterError):
    """Raised when attempting to emit to closed WebSocket."""

    pass
