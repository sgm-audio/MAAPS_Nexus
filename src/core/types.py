"""Compatibility shim: re-exports core message types under `src.core.types`.

Several modules in `src.agents.*` and `src.daw_integration` were authored
against `src.core.types`. The canonical location is `src.core.message_types`.
This module preserves the older import surface without duplicating definitions.
"""

from .message_types import (
    Message,
    Priority,
    MessageType,
    Topics,
    AudioBuffer,
    AudioFeatures,
    OptimizationSuggestion,
    VSTPluginState,
    DAWProjectState,
    SystemEvent,
    LogEntry,
)

__all__ = [
    "Message",
    "Priority",
    "MessageType",
    "Topics",
    "AudioBuffer",
    "AudioFeatures",
    "OptimizationSuggestion",
    "VSTPluginState",
    "DAWProjectState",
    "SystemEvent",
    "LogEntry",
]
