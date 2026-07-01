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
from .di_container import (
    DIContainer,
    get_container,
    register_component,
    resolve_component,
)
from .common import (
    ThreadSafeMetrics,
    ProcessingWorker,
    ProcessingJob,
    Configuration,
    AgentLogger,
    timing_context,
    safe_json_serialize,
)
from .exceptions import (
    MAAPSException,
    AgentException,
    AgentNotFoundError,
    AgentStateError,
    MessageBusException,
    WorkflowException,
    AudioProcessingException,
    ErrorSeverity,
)

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
    # Dependency Injection
    "DIContainer",
    "get_container",
    "register_component",
    "resolve_component",
    # Common Utilities
    "ThreadSafeMetrics",
    "ProcessingWorker",
    "ProcessingJob",
    "Configuration",
    "AgentLogger",
    "timing_context",
    "safe_json_serialize",
    # Exceptions
    "MAAPSException",
    "AgentException",
    "AgentNotFoundError",
    "AgentStateError",
    "MessageBusException",
    "WorkflowException",
    "AudioProcessingException",
    "ErrorSeverity",
]


# Deferred import to avoid circular dependency
def __getattr__(name):
    if name == "AgentFactory":
        from .agent_factory import AgentFactory
        return AgentFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
