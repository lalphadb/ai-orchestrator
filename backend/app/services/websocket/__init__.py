"""
WebSocket Services Package
Provides centralized EventEmitter for WebSocket event management.
"""

from .event_emitter import WSEventEmitter, event_emitter
from .exceptions import (InvalidEventStructure, RunNotFound,
                         TerminalAlreadySent, WebSocketClosed,
                         WSEventEmitterError)

__all__ = [
    "WSEventEmitterError",
    "TerminalAlreadySent",
    "InvalidEventStructure",
    "RunNotFound",
    "WebSocketClosed",
    "WSEventEmitter",
    "event_emitter",
]
