"""
Exception hierarchy for the multi-agent system.

Provides standardized error handling with:
- Domain-specific exception types
- Error context and metadata
- Error chaining for debugging
- HTTP status code mapping for API layer
"""

from typing import Dict, Any, Optional
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for prioritization and handling."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MAAPSException(Exception):
    """
    Base exception for all MAAPS system errors.

    Provides standardized error information including:
    - Error code for programmatic handling
    - Severity level
    - Contextual metadata
    - HTTP status code mapping
    """

    error_code: str = "MAAPS_ERROR"
    severity: ErrorSeverity = ErrorSeverity.ERROR
    http_status: int = 500

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        error_dict = {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
        }

        if self.cause:
            error_dict["cause"] = str(self.cause)

        return error_dict

    def __str__(self) -> str:
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


# Agent-specific exceptions
class AgentException(MAAPSException):
    """Base exception for agent-related errors."""

    error_code = "AGENT_ERROR"

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message, details, cause)
        self.agent_id = agent_id
        if agent_id:
            self.details["agent_id"] = agent_id


class AgentNotFoundError(AgentException):
    """Raised when an agent cannot be found."""

    error_code = "AGENT_NOT_FOUND"
    http_status = 404
    severity = ErrorSeverity.WARNING


class AgentStateError(AgentException):
    """Raised when an agent is in an invalid state."""

    error_code = "AGENT_STATE_ERROR"
    http_status = 409
    severity = ErrorSeverity.ERROR


class AgentInitializationError(AgentException):
    """Raised when agent initialization fails."""

    error_code = "AGENT_INIT_ERROR"
    http_status = 500
    severity = ErrorSeverity.CRITICAL


class AgentTimeoutError(AgentException):
    """Raised when an agent operation times out."""

    error_code = "AGENT_TIMEOUT"
    http_status = 504
    severity = ErrorSeverity.WARNING


# Message Bus exceptions
class MessageBusException(MAAPSException):
    """Base exception for message bus errors."""

    error_code = "MESSAGE_BUS_ERROR"


class MessageDeliveryError(MessageBusException):
    """Raised when message delivery fails."""

    error_code = "MESSAGE_DELIVERY_FAILED"
    http_status = 503
    severity = ErrorSeverity.ERROR


class MessageQueueFullError(MessageBusException):
    """Raised when message queue is full."""

    error_code = "MESSAGE_QUEUE_FULL"
    http_status = 503
    severity = ErrorSeverity.WARNING


class SubscriptionError(MessageBusException):
    """Raised when subscription operation fails."""

    error_code = "SUBSCRIPTION_ERROR"
    http_status = 400
    severity = ErrorSeverity.WARNING


# Workflow exceptions
class WorkflowException(MAAPSException):
    """Base exception for workflow-related errors."""

    error_code = "WORKFLOW_ERROR"


class WorkflowNotFoundError(WorkflowException):
    """Raised when a workflow cannot be found."""

    error_code = "WORKFLOW_NOT_FOUND"
    http_status = 404
    severity = ErrorSeverity.WARNING


class WorkflowExecutionError(WorkflowException):
    """Raised when workflow execution fails."""

    error_code = "WORKFLOW_EXECUTION_FAILED"
    http_status = 500
    severity = ErrorSeverity.ERROR


class WorkflowStepError(WorkflowException):
    """Raised when a workflow step fails."""

    error_code = "WORKFLOW_STEP_FAILED"
    http_status = 500
    severity = ErrorSeverity.ERROR

    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        step_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message, details, cause)
        self.workflow_id = workflow_id
        self.step_id = step_id
        if workflow_id:
            self.details["workflow_id"] = workflow_id
        if step_id:
            self.details["step_id"] = step_id


class CircularDependencyError(WorkflowException):
    """Raised when workflow has circular dependencies."""

    error_code = "CIRCULAR_DEPENDENCY"
    http_status = 400
    severity = ErrorSeverity.ERROR


# Audio processing exceptions
class AudioProcessingException(MAAPSException):
    """Base exception for audio processing errors."""

    error_code = "AUDIO_PROCESSING_ERROR"


class AudioValidationError(AudioProcessingException):
    """Raised when audio data validation fails."""

    error_code = "AUDIO_VALIDATION_FAILED"
    http_status = 400
    severity = ErrorSeverity.WARNING


class AudioEnhancementError(AudioProcessingException):
    """Raised when audio enhancement fails."""

    error_code = "AUDIO_ENHANCEMENT_FAILED"
    http_status = 500
    severity = ErrorSeverity.ERROR


class UnsupportedAudioFormatError(AudioProcessingException):
    """Raised when audio format is not supported."""

    error_code = "UNSUPPORTED_AUDIO_FORMAT"
    http_status = 415
    severity = ErrorSeverity.WARNING


# Resource exceptions
class ResourceException(MAAPSException):
    """Base exception for resource-related errors."""

    error_code = "RESOURCE_ERROR"


class ResourceExhaustedError(ResourceException):
    """Raised when system resources are exhausted."""

    error_code = "RESOURCE_EXHAUSTED"
    http_status = 503
    severity = ErrorSeverity.CRITICAL


class ResourceNotAvailableError(ResourceException):
    """Raised when a required resource is not available."""

    error_code = "RESOURCE_NOT_AVAILABLE"
    http_status = 503
    severity = ErrorSeverity.WARNING


class ConfigurationException(MAAPSException):
    """Base exception for configuration errors."""

    error_code = "CONFIGURATION_ERROR"
    http_status = 400
    severity = ErrorSeverity.ERROR


class ValidationException(MAAPSException):
    """Base exception for validation errors."""

    error_code = "VALIDATION_ERROR"
    http_status = 400
    severity = ErrorSeverity.WARNING


def handle_exception(exception: Exception) -> MAAPSException:
    """
    Convert a generic exception to a MAAPSException.

    Args:
        exception: The exception to convert

    Returns:
        A MAAPSException instance
    """
    if isinstance(exception, MAAPSException):
        return exception

    return MAAPSException(message=str(exception), cause=exception)
