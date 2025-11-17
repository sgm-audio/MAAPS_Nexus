# Data Flow Architecture

## Overview
This document describes how data flows through the multi-agent system, from audio input through processing, analysis, optimization, and output.

## System-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Flow Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

External Input (DAW/Audio Interface)
         │
         ↓
┌────────────────────┐
│  DAW Control Agent │ ← Controls transport, tracks, routing
└────────┬───────────┘
         │ audio.input.received
         │ (AudioBuffer: PCM data, sample rate, channels)
         ↓
┌────────────────────┐
│ Audio Analysis     │ ← Extracts features (spectral, temporal, etc.)
│ Agent              │
└────────┬───────────┘
         │ audio.features.extracted
         │ (Features: spectrum, tempo, key, dynamics)
         ↓
┌────────────────────┐
│ Parameter          │ ← ML-based optimization suggestions
│ Optimization Agent │
└────────┬───────────┘
         │ optimization.suggestion.generated
         │ (Parameters: VST param values, confidence scores)
         ↓
┌────────────────────┐
│ VST Bridge Agent   │ ← Applies parameters to VST plugins
└────────┬───────────┘
         │ vst.parameter.changed
         │ (PluginState: param values, preset data)
         ↓
┌────────────────────┐
│ DAW Control Agent  │ ← Writes back to DAW
└────────┬───────────┘
         │
         ↓
External Output (DAW/Audio Interface)

         ╔═══════════════════════════════════╗
         ║    Cross-Cutting Concerns         ║
         ╚═══════════════════════════════════╝
                 ↓                   ↓
    ┌────────────────────┐  ┌─────────────────┐
    │ System Orchestrator│  │ Logging Monitor │
    │ Agent              │  │ Agent           │
    └────────────────────┘  └─────────────────┘
    - Workflow coordination  - Event logging
    - Error handling         - Metrics collection
    - State management       - Audit trails
```

## Data Types & Structures

### 1. Audio Data
```python
AudioBuffer = {
    "buffer_id": str,           # Unique identifier
    "sample_rate": int,         # 44100, 48000, etc.
    "channels": int,            # 1 (mono), 2 (stereo), etc.
    "bit_depth": int,           # 16, 24, 32
    "samples": np.ndarray,      # Raw PCM data
    "timestamp": float,         # DAW timeline position
    "duration_ms": float,       # Buffer duration
    "metadata": {
        "track_id": str,
        "track_name": str,
        "is_realtime": bool
    }
}
```

### 2. Audio Features
```python
AudioFeatures = {
    "buffer_id": str,           # Links to original audio
    "spectral": {
        "centroid": float,      # Spectral centroid (Hz)
        "rolloff": float,       # Spectral rolloff
        "flux": float,          # Spectral flux
        "bandwidth": float,     # Spectral bandwidth
        "mfcc": List[float]     # Mel-frequency cepstral coefficients
    },
    "temporal": {
        "tempo": float,         # BPM
        "beat_positions": List[float],
        "onset_strength": List[float],
        "zero_crossing_rate": float
    },
    "harmonic": {
        "key": str,             # Musical key (C, C#, D, etc.)
        "scale": str,           # Major/Minor
        "chroma": List[float],  # Chromagram
        "pitch_class": List[float]
    },
    "dynamic": {
        "rms": float,           # RMS energy
        "peak": float,          # Peak amplitude
        "dynamic_range": float, # dB range
        "loudness": float       # LUFS
    },
    "timestamp": float
}
```

### 3. Optimization Suggestions
```python
OptimizationSuggestion = {
    "suggestion_id": str,
    "buffer_id": str,           # Links to analyzed audio
    "target_plugin": str,       # VST plugin identifier
    "parameters": {
        "param_name": {
            "current_value": float,
            "suggested_value": float,
            "confidence": float,    # 0.0 to 1.0
            "reasoning": str
        }
    },
    "expected_outcome": str,
    "priority": str,            # high, medium, low
    "timestamp": float,
    "model_version": str
}
```

### 4. VST Plugin State
```python
VSTPluginState = {
    "plugin_id": str,
    "plugin_name": str,
    "vendor": str,
    "version": str,
    "parameters": {
        "param_id": {
            "name": str,
            "value": float,         # Normalized 0.0 to 1.0
            "display_value": str,   # Human-readable
            "unit": str,
            "is_automatable": bool
        }
    },
    "preset_data": bytes,       # Binary preset data
    "chunk_data": bytes,        # Plugin chunk data
    "timestamp": float
}
```

### 5. DAW Project State
```python
DAWProjectState = {
    "project_id": str,
    "project_name": str,
    "sample_rate": int,
    "tempo": float,
    "time_signature": str,
    "tracks": {
        "track_id": {
            "name": str,
            "type": str,            # audio, midi, instrument
            "volume": float,
            "pan": float,
            "mute": bool,
            "solo": bool,
            "plugins": List[str],   # Plugin IDs in chain
            "routing": {
                "input": str,
                "output": str
            }
        }
    },
    "transport": {
        "is_playing": bool,
        "is_recording": bool,
        "position": float,          # Seconds
        "loop_start": float,
        "loop_end": float
    }
}
```

### 6. System Events
```python
SystemEvent = {
    "event_id": str,
    "event_type": str,          # heartbeat, error, state_change
    "agent_id": str,
    "severity": str,            # info, warning, error, critical
    "data": dict,               # Event-specific data
    "timestamp": float,
    "correlation_id": str       # Links related events
}
```

### 7. Log Entry
```python
LogEntry = {
    "log_id": str,
    "timestamp": float,
    "level": str,               # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "agent_id": str,
    "message": str,
    "context": dict,            # Additional context
    "trace_id": str,            # Distributed tracing
    "metrics": {
        "cpu_percent": float,
        "memory_mb": float,
        "latency_ms": float
    }
}
```

## Data Flow Scenarios

### Scenario 1: Real-Time Audio Processing

```
Step 1: Audio Input
DAW Control Agent receives audio from DAW
├─> Converts to AudioBuffer format
├─> Publishes: audio.input.received
└─> Streams buffer to message bus (< 10ms latency)

Step 2: Feature Extraction
Audio Analysis Agent receives AudioBuffer
├─> Performs FFT, spectral analysis
├─> Extracts temporal features (tempo, beats)
├─> Computes dynamic range metrics
├─> Creates AudioFeatures object
└─> Publishes: audio.features.extracted (< 50ms from input)

Step 3: Parameter Optimization
Parameter Optimization Agent receives AudioFeatures
├─> Loads ML model for target VST
├─> Generates parameter suggestions
├─> Calculates confidence scores
├─> Creates OptimizationSuggestion
└─> Publishes: optimization.suggestion.generated (< 20ms)

Step 4: VST Parameter Application
VST Bridge Agent receives OptimizationSuggestion
├─> Validates parameter ranges
├─> Applies parameters to VST plugin
├─> Captures new VSTPluginState
└─> Publishes: vst.parameter.changed (< 5ms)

Step 5: DAW Update
DAW Control Agent receives VSTPluginState
├─> Updates DAW project state
├─> Confirms parameter changes
└─> Total latency: < 100ms end-to-end
```

### Scenario 2: Batch Processing

```
Step 1: Project Load
DAW Control Agent loads project
├─> Parses project file
├─> Creates DAWProjectState
├─> Publishes: daw.project.loaded
└─> System Orchestrator coordinates initialization

Step 2: Batch Analysis
For each audio track:
  ├─> DAW Control extracts audio buffer
  ├─> Audio Analysis processes entire track
  ├─> Results aggregated by System Orchestrator
  └─> Progress reported to Logging Monitor

Step 3: Optimization Run
Parameter Optimization Agent processes all tracks
├─> Generates suggestions for each plugin instance
├─> Applies suggestions in batch
├─> VST Bridge updates all plugins
└─> Final state persisted by DAW Control

Step 4: Reporting
Logging Monitor Agent generates report
├─> Aggregates all changes made
├─> Computes performance metrics
├─> Creates audit trail
└─> Exports summary
```

### Scenario 3: User Preference Learning

```
Step 1: User Adjustment
DAW Control detects manual parameter change
├─> Captures user action
├─> Retrieves current AudioFeatures
├─> Publishes: optimization.preference.learned

Step 2: Model Update
Parameter Optimization Agent receives preference
├─> Links parameter change to audio features
├─> Updates ML model with new training data
├─> Re-trains model incrementally
└─> Publishes: optimization.model.updated

Step 3: Validation
System Orchestrator validates model performance
├─> Requests test predictions
├─> Compares with user preferences
├─> Approves or rejects model update
└─> Logs results via Logging Monitor
```

## Data Persistence

### What Gets Persisted

| Data Type | Persistence | Retention | Location |
|-----------|------------|-----------|----------|
| Audio Buffers | Temporary | Session only | Memory/Temp files |
| Audio Features | Permanent | 90 days | Database |
| Optimization Suggestions | Permanent | 90 days | Database |
| VST Plugin States | Permanent | Indefinite | DAW project + DB |
| User Preferences | Permanent | Indefinite | Database |
| ML Model Checkpoints | Permanent | Last 10 versions | File system |
| System Events | Permanent | 30 days | Database |
| Log Entries | Permanent | Info: 7 days, Error: 90 days | Database |
| Performance Metrics | Permanent | 30 days | Time-series DB |

### Database Schema

```sql
-- Audio Features Table
CREATE TABLE audio_features (
    feature_id UUID PRIMARY KEY,
    buffer_id UUID,
    track_id UUID,
    timestamp TIMESTAMP,
    spectral_data JSONB,
    temporal_data JSONB,
    harmonic_data JSONB,
    dynamic_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Optimization History Table
CREATE TABLE optimization_history (
    suggestion_id UUID PRIMARY KEY,
    feature_id UUID REFERENCES audio_features(feature_id),
    plugin_id VARCHAR,
    parameters JSONB,
    applied BOOLEAN,
    user_accepted BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Preferences Table
CREATE TABLE user_preferences (
    preference_id UUID PRIMARY KEY,
    user_id UUID,
    feature_id UUID REFERENCES audio_features(feature_id),
    plugin_id VARCHAR,
    parameter_name VARCHAR,
    parameter_value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System Logs Table
CREATE TABLE system_logs (
    log_id UUID PRIMARY KEY,
    agent_id VARCHAR,
    level VARCHAR,
    message TEXT,
    context JSONB,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Data Volume Estimates

### Real-Time Processing (48kHz, 512-sample buffers)
- Buffer rate: ~93 buffers/second
- Audio data throughput: ~180 KB/s per channel
- Feature data: ~2 KB per buffer = ~186 KB/s
- Optimization suggestions: ~10/second = ~5 KB/s
- Total data rate: ~370 KB/s per audio track

### Storage Requirements (per hour of audio)
- Audio features: ~670 MB
- Optimization history: ~18 MB
- System logs (info): ~50 MB
- Performance metrics: ~100 MB
- Total: ~840 MB per hour per track

## Performance Budgets

| Operation | Target Latency | Max Latency |
|-----------|----------------|-------------|
| Audio buffer → Features | 50ms | 100ms |
| Features → Suggestion | 20ms | 50ms |
| Suggestion → VST update | 5ms | 10ms |
| End-to-end (audio → VST) | 100ms | 200ms |
| Message dispatch | 1ms | 5ms |
| Database write | 10ms | 50ms |
| Database read (cache hit) | 1ms | 10ms |
| Model inference | 15ms | 30ms |

## Data Security & Privacy

### Sensitive Data
- User preferences: Encrypted at rest
- Audio buffers: Not persisted (memory only)
- VST plugin states: Encrypted if contains presets

### Access Control
- Agents can only access data they need
- Database queries are permission-checked
- Message bus validates sender/receiver permissions

### Data Anonymization
- Feature extraction removes identifying information
- Logs sanitize file paths and user names
- Metrics aggregated before external reporting
