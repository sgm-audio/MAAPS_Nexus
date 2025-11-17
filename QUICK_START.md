# Quick Start Guide: Multi-Agent System Implementation

## Overview

This guide will help you quickly understand and implement the 7-agent architecture for audio processing and DAW integration.

## What You Have Now

### Architecture Documentation
- **`architecture/COMMUNICATION_ARCHITECTURE.md`** - Complete communication design with message bus, topics, and patterns
- **`architecture/DATA_FLOW_ARCHITECTURE.md`** - Data structures, flows, and processing scenarios
- **`architecture/README.md`** - Comprehensive architecture overview
- **`architecture/SYSTEM_DIAGRAMS.md`** - Visual diagrams using Mermaid

### Core Implementation
- **`src/core/message_bus.py`** - Thread-safe message bus with priority queuing
- **`src/core/message_types.py`** - All data structures and message types
- **`src/core/base_agent.py`** - Base agent class with lifecycle management
- **`src/core/__init__.py`** - Module exports

## Quick Start: Implementing Your First Agent

### Step 1: Create a Simple Agent

Create `src/agents/example_agent.py`:

```python
from src.core import BaseAgent, Topics, Message

class ExampleAgent(BaseAgent):
    def setup(self):
        """Called when agent starts"""
        # Subscribe to topics
        self.subscribe(Topics.AUDIO_INPUT_RECEIVED)
        self.log("INFO", "Example agent setup complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        if message.topic == Topics.AUDIO_INPUT_RECEIVED:
            self.log("INFO", f"Received audio buffer: {message.payload}")

            # Process the message
            # ... your logic here ...

            # Publish result
            self.publish(
                Topics.AUDIO_ANALYSIS_COMPLETE,
                {"status": "processed"}
            )

    def teardown(self):
        """Called when agent stops"""
        self.log("INFO", "Example agent shutting down")

# Create and start the agent
if __name__ == "__main__":
    agent = ExampleAgent("example-001", "Example Agent")
    agent.start()

    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
```

### Step 2: Run the Agent

```bash
python src/agents/example_agent.py
```

## Implementing the 7 Agents

### 1. DAW Control Interface Agent

**File**: `src/agents/daw_control.py`

**Key Responsibilities**:
```python
class DAWControlAgent(BaseAgent):
    def setup(self):
        self.subscribe(Topics.VST_PARAMETER_CHANGED)
        # Initialize DAW connection (Reaper API, etc.)

    def handle_message(self, message):
        if message.topic == Topics.VST_PARAMETER_CHANGED:
            # Update DAW with new parameters
            self.update_daw_parameters(message.payload)

    def capture_audio_buffer(self):
        # Capture audio from DAW
        # Publish to Topics.AUDIO_INPUT_RECEIVED
        pass
```

**Topics**:
- Publishes: `audio.input.received`, `daw.project.loaded`, `daw.transport.*`
- Subscribes: `vst.parameter.changed`

### 2. VST Bridge Manager Agent

**File**: `src/agents/vst_bridge.py`

**Key Responsibilities**:
```python
class VSTBridgeAgent(BaseAgent):
    def setup(self):
        self.subscribe(Topics.OPTIMIZATION_SUGGESTION_GENERATED)
        # Load VST plugins

    def handle_message(self, message):
        if message.topic == Topics.OPTIMIZATION_SUGGESTION_GENERATED:
            # Apply parameters to VST
            self.apply_vst_parameters(message.payload)

    def apply_vst_parameters(self, suggestion):
        # Apply parameters
        # Publish vst.parameter.changed
        pass
```

**Topics**:
- Publishes: `vst.plugin.loaded`, `vst.parameter.changed`, `vst.error.occurred`
- Subscribes: `optimization.suggestion.generated`

### 3. Audio Analysis Agent

**File**: `src/agents/audio_analysis.py`

**Key Responsibilities**:
```python
import librosa
import numpy as np
from src.core import AudioFeatures, SpectralFeatures

class AudioAnalysisAgent(BaseAgent):
    def setup(self):
        self.subscribe(Topics.AUDIO_INPUT_RECEIVED)

    def handle_message(self, message):
        if message.topic == Topics.AUDIO_INPUT_RECEIVED:
            features = self.extract_features(message.payload)
            self.publish(
                Topics.AUDIO_FEATURES_EXTRACTED,
                features.__dict__
            )

    def extract_features(self, audio_buffer):
        # Extract spectral features using librosa
        samples = audio_buffer['samples']
        sr = audio_buffer['sample_rate']

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=samples, sr=sr)
        mfcc = librosa.feature.mfcc(y=samples, sr=sr)

        # Temporal features
        tempo, beats = librosa.beat.beat_track(y=samples, sr=sr)

        # Create AudioFeatures object
        # Return complete feature set
        pass
```

**Topics**:
- Publishes: `audio.features.extracted`, `audio.analysis.complete`
- Subscribes: `audio.input.received`

### 4. Parameter Optimization Agent

**File**: `src/agents/parameter_optimization.py`

**Key Responsibilities**:
```python
import tensorflow as tf  # or PyTorch

class ParameterOptimizationAgent(BaseAgent):
    def setup(self):
        self.subscribe(Topics.AUDIO_FEATURES_EXTRACTED)
        self.subscribe(Topics.OPTIMIZATION_PREFERENCE_LEARNED)
        # Load ML model
        self.model = self.load_model()

    def handle_message(self, message):
        if message.topic == Topics.AUDIO_FEATURES_EXTRACTED:
            suggestions = self.generate_suggestions(message.payload)
            self.publish(
                Topics.OPTIMIZATION_SUGGESTION_GENERATED,
                suggestions.__dict__
            )

    def generate_suggestions(self, features):
        # Use ML model to generate parameter suggestions
        # Return OptimizationSuggestion
        pass

    def load_model(self):
        # Load trained ML model
        pass
```

**Topics**:
- Publishes: `optimization.suggestion.generated`, `optimization.model.updated`
- Subscribes: `audio.features.extracted`, `optimization.preference.learned`

### 5. System Orchestrator Agent

**File**: `src/agents/system_orchestrator.py`

**Key Responsibilities**:
```python
class SystemOrchestratorAgent(BaseAgent):
    def setup(self):
        # Subscribe to all system events
        self.subscribe("system.*")
        self.subscribe("*.error.*")

        # Track agent states
        self.agent_states = {}

    def handle_message(self, message):
        if message.topic == Topics.SYSTEM_HEARTBEAT:
            self.update_agent_state(message.payload)

        elif message.topic == Topics.SYSTEM_ERROR_CRITICAL:
            self.handle_critical_error(message.payload)

    def update_agent_state(self, data):
        agent_id = data['agent_id']
        self.agent_states[agent_id] = {
            'last_heartbeat': data['timestamp'],
            'metrics': data['metrics']
        }

    def handle_critical_error(self, error_data):
        # Coordinate error recovery
        # Alert other agents if needed
        pass
```

**Topics**:
- Publishes: All `system.*` topics
- Subscribes: All agent heartbeats, all error topics

### 6. Logging Monitor Agent

**File**: `src/agents/logging_monitor.py`

**Key Responsibilities**:
```python
import psycopg2  # PostgreSQL
from datetime import datetime

class LoggingMonitorAgent(BaseAgent):
    def setup(self):
        # Subscribe to all log and system topics
        self.subscribe("log.*")
        self.subscribe("system.*")

        # Connect to database
        self.db = self.connect_database()

    def handle_message(self, message):
        # Store log entry in database
        self.persist_log(message)

        # Update metrics
        if message.topic == Topics.LOG_METRICS_PERFORMANCE:
            self.update_metrics(message.payload)

    def persist_log(self, message):
        # Insert into database
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO system_logs (agent_id, level, message, context)
            VALUES (%s, %s, %s, %s)
        """, (
            message.sender,
            message.payload.get('level'),
            message.payload.get('message'),
            json.dumps(message.payload.get('context'))
        ))
        self.db.commit()

    def connect_database(self):
        # PostgreSQL connection
        return psycopg2.connect(
            host="localhost",
            database="agents_db",
            user="agent_user",
            password="password"
        )
```

**Topics**:
- Publishes: `log.metrics.performance`
- Subscribes: All `log.*` and `system.*` topics

### 7. System Logging Monitor Agent

This appears to be a duplicate of #6. You may want to merge these or differentiate their roles (e.g., one for application logs, one for system metrics).

## Running All Agents Together

### Option 1: Single Process (Development)

Create `src/run_all.py`:

```python
from src.core import get_agent_registry
from src.agents.daw_control import DAWControlAgent
from src.agents.vst_bridge import VSTBridgeAgent
from src.agents.audio_analysis import AudioAnalysisAgent
from src.agents.parameter_optimization import ParameterOptimizationAgent
from src.agents.system_orchestrator import SystemOrchestratorAgent
from src.agents.logging_monitor import LoggingMonitorAgent

def main():
    registry = get_agent_registry()

    # Create all agents
    agents = [
        DAWControlAgent("daw-001", "DAW Control"),
        VSTBridgeAgent("vst-001", "VST Bridge"),
        AudioAnalysisAgent("audio-001", "Audio Analysis"),
        ParameterOptimizationAgent("param-001", "Parameter Optimization"),
        SystemOrchestratorAgent("orch-001", "System Orchestrator"),
        LoggingMonitorAgent("log-001", "Logging Monitor")
    ]

    # Register all agents
    for agent in agents:
        registry.register(agent)

    # Start all agents
    registry.start_all()

    print("All agents started. Press Ctrl+C to stop.")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all agents...")
        registry.stop_all()
        print("All agents stopped.")

if __name__ == "__main__":
    main()
```

Run:
```bash
python src/run_all.py
```

### Option 2: Separate Processes (Production)

Run each agent in its own terminal:

```bash
# Terminal 1
python -m src.agents.daw_control

# Terminal 2
python -m src.agents.vst_bridge

# Terminal 3
python -m src.agents.audio_analysis

# Terminal 4
python -m src.agents.parameter_optimization

# Terminal 5
python -m src.agents.system_orchestrator

# Terminal 6
python -m src.agents.logging_monitor
```

## Testing Communication

Create `src/test_communication.py`:

```python
from src.core import get_message_bus, Message, Topics, Priority
import time

def test_pub_sub():
    bus = get_message_bus()

    # Subscriber callback
    received_messages = []

    def on_message(msg):
        received_messages.append(msg)
        print(f"Received: {msg.topic} - {msg.payload}")

    # Subscribe
    bus.subscribe(Topics.AUDIO_INPUT_RECEIVED, "test-agent", on_message)

    # Publish
    message = Message(
        topic=Topics.AUDIO_INPUT_RECEIVED,
        sender="test-publisher",
        payload={"data": "test"},
        priority=Priority.HIGH
    )

    bus.publish(message)

    # Wait for delivery
    time.sleep(0.5)

    assert len(received_messages) == 1
    print("✓ Publish-subscribe test passed")

if __name__ == "__main__":
    test_pub_sub()
```

## Next Steps

1. **Implement Core Agents**: Start with DAW Control and Audio Analysis
2. **Test Communication**: Verify message flow between agents
3. **Add ML Models**: Implement parameter optimization logic
4. **Setup Database**: Create PostgreSQL schema for logging
5. **Performance Testing**: Benchmark message throughput and latency
6. **Add Monitoring**: Set up Grafana dashboards

## Dependencies

Install required packages:

```bash
pip install numpy
pip install librosa
pip install psycopg2-binary
pip install tensorflow  # or pytorch
```

## Useful Commands

```bash
# Run tests
python -m pytest tests/

# Check message bus metrics
python -c "from src.core import get_message_bus; print(get_message_bus().get_metrics())"

# Monitor logs
tail -f logs/system.log

# Check database
psql agents_db -c "SELECT COUNT(*) FROM system_logs;"
```

## Troubleshooting

### Message Not Delivered
1. Check that agent is subscribed to the correct topic
2. Verify message bus is running
3. Check for topic wildcards matching

### High Latency
1. Check queue depths: `bus.get_metrics()`
2. Verify priority levels are appropriate
3. Look for slow subscribers blocking dispatcher

### Agent Not Starting
1. Check logs for error messages
2. Verify all dependencies are imported
3. Ensure message bus is started before agents

## Resources

- [Communication Architecture](architecture/COMMUNICATION_ARCHITECTURE.md)
- [Data Flow Architecture](architecture/DATA_FLOW_ARCHITECTURE.md)
- [Architecture Overview](architecture/README.md)
- [System Diagrams](architecture/SYSTEM_DIAGRAMS.md)

## Support

For questions or issues, refer to the architecture documentation or check the logs in the Logging Monitor agent's database.
