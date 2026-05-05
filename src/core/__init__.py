"""
Core module for the multi-agent system.
Provides foundational classes and utilities for agent communication.
"""

from .message_bus import MessageBus, get_message_bus
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
from .base_agent import BaseAgent, AgentState, AgentRegistry, get_agent_registry

__all__ = [
    # Message Bus
    "MessageBus",
    "get_message_bus",
    # Message Types
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
    # Base Agent
    "BaseAgent",
    "AgentState",
    "AgentRegistry",
    "get_agent_registry",
]
