"""
Message type definitions for the multi-agent system.
Defines standardized data structures for all inter-agent communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class Priority(Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MessageType(Enum):
    """Types of messages in the system"""
    EVENT = "event"
    REQUEST = "request"
    RESPONSE = "response"
    STREAM = "stream"


@dataclass
class Message:
    """Base message structure for all inter-agent communication"""
    topic: str
    sender: str
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    message_type: MessageType = MessageType.EVENT
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "sender": self.sender,
            "priority": self.priority.value,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id
        }


@dataclass
class AudioBuffer:
    """Audio data structure"""
    buffer_id: str
    sample_rate: int
    channels: int
    bit_depth: int
    samples: Any  # numpy array
    timestamp: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpectralFeatures:
    """Spectral audio features"""
    centroid: float
    rolloff: float
    flux: float
    bandwidth: float
    mfcc: List[float]


@dataclass
class TemporalFeatures:
    """Temporal audio features"""
    tempo: float
    beat_positions: List[float]
    onset_strength: List[float]
    zero_crossing_rate: float


@dataclass
class HarmonicFeatures:
    """Harmonic audio features"""
    key: str
    scale: str
    chroma: List[float]
    pitch_class: List[float]


@dataclass
class DynamicFeatures:
    """Dynamic audio features"""
    rms: float
    peak: float
    dynamic_range: float
    loudness: float


@dataclass
class AudioFeatures:
    """Complete audio feature set"""
    buffer_id: str
    spectral: SpectralFeatures
    temporal: TemporalFeatures
    harmonic: HarmonicFeatures
    dynamic: DynamicFeatures
    timestamp: float


@dataclass
class ParameterSuggestion:
    """Individual parameter optimization suggestion"""
    current_value: float
    suggested_value: float
    confidence: float
    reasoning: str


@dataclass
class OptimizationSuggestion:
    """VST parameter optimization suggestion"""
    suggestion_id: str
    buffer_id: str
    target_plugin: str
    parameters: Dict[str, ParameterSuggestion]
    expected_outcome: str
    priority: Priority
    timestamp: float
    model_version: str


@dataclass
class VSTParameter:
    """VST plugin parameter"""
    name: str
    value: float
    display_value: str
    unit: str
    is_automatable: bool


@dataclass
class VSTPluginState:
    """VST plugin state"""
    plugin_id: str
    plugin_name: str
    vendor: str
    version: str
    parameters: Dict[str, VSTParameter]
    preset_data: Optional[bytes] = None
    chunk_data: Optional[bytes] = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class TrackInfo:
    """DAW track information"""
    name: str
    track_type: str
    volume: float
    pan: float
    mute: bool
    solo: bool
    plugins: List[str]
    routing: Dict[str, str]


@dataclass
class TransportState:
    """DAW transport state"""
    is_playing: bool
    is_recording: bool
    position: float
    loop_start: Optional[float] = None
    loop_end: Optional[float] = None


@dataclass
class DAWProjectState:
    """Complete DAW project state"""
    project_id: str
    project_name: str
    sample_rate: int
    tempo: float
    time_signature: str
    tracks: Dict[str, TrackInfo]
    transport: TransportState


@dataclass
class SystemEvent:
    """System-level event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    agent_id: str = ""
    severity: str = "info"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    correlation_id: Optional[str] = None


@dataclass
class LogEntry:
    """Log entry structure"""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    level: str = "INFO"
    agent_id: str = ""
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)


# Topic constants
class Topics:
    """Standardized topic names"""

    # Audio processing topics
    AUDIO_INPUT_RECEIVED = "audio.input.received"
    AUDIO_ANALYSIS_STARTED = "audio.analysis.started"
    AUDIO_ANALYSIS_COMPLETE = "audio.analysis.complete"
    AUDIO_FEATURES_EXTRACTED = "audio.features.extracted"

    # VST plugin topics
    VST_PLUGIN_LOADED = "vst.plugin.loaded"
    VST_PARAMETER_CHANGED = "vst.parameter.changed"
    VST_PARAMETER_OPTIMIZED = "vst.parameter.optimized"
    VST_STATE_SAVED = "vst.state.saved"
    VST_ERROR_OCCURRED = "vst.error.occurred"

    # DAW control topics
    DAW_TRANSPORT_PLAY = "daw.transport.play"
    DAW_TRANSPORT_STOP = "daw.transport.stop"
    DAW_TRANSPORT_RECORD = "daw.transport.record"
    DAW_PROJECT_LOADED = "daw.project.loaded"
    DAW_TRACK_CREATED = "daw.track.created"

    # Optimization topics
    OPTIMIZATION_SUGGESTION_GENERATED = "optimization.suggestion.generated"
    OPTIMIZATION_PREFERENCE_LEARNED = "optimization.preference.learned"
    OPTIMIZATION_MODEL_UPDATED = "optimization.model.updated"

    # System topics
    SYSTEM_AGENT_STARTED = "system.agent.started"
    SYSTEM_AGENT_STOPPED = "system.agent.stopped"
    SYSTEM_ERROR_CRITICAL = "system.error.critical"
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_METRICS_COLLECTED = "system.metrics.collected"

    # Logging topics
    LOG_EVENT_INFO = "log.event.info"
    LOG_EVENT_WARNING = "log.event.warning"
    LOG_EVENT_ERROR = "log.event.error"
    LOG_METRICS_PERFORMANCE = "log.metrics.performance"
    LOG_AUDIT_ACTION = "log.audit.action"

    # Workflow topics
    WORKFLOW_CREATE = "workflow.create"
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_STATUS = "workflow.status"

    # Enhancement & Generation topics
    AUDIO_ENHANCEMENT_REQUEST = "audio.enhancement.request"
    MUSIC_GEN_MELODY_REQ = "music.generation.melody.request"
    MUSIC_GEN_HARMONY_REQ = "music.generation.harmony.request"
    MUSIC_GEN_DRUMS_REQ = "music.generation.drums.request"
    MUSIC_GEN_BASS_REQ = "music.generation.bass.request"

    # Metadata topics
    METADATA_EXTRACT_REQ = "metadata.extract.request"
    METADATA_SEARCH_REQ = "metadata.search.request"

    # Resource topics
    SYSTEM_RESOURCE_REQ = "system.resource.request"


class Timeouts:
    """Standardized timeout values in seconds"""
    SHORT = 5.0
    MEDIUM = 30.0
    LONG = 60.0
    VERY_LONG = 120.0
