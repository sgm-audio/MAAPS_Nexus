# MAAPS Quick Reference Guide

**Multi-Agent Audio Processing System - Quick Commands & API Reference**

---

## Quick Start (30 seconds)

```python
from src.system import create_system

with create_system() as system:
    health = system.get_health()
    print(f"Health: {health['health_score']}%")
```

---

## System Operations

### Start/Stop System

```python
from src.system import create_system

# Method 1: Context Manager (Recommended)
with create_system() as system:
    # System auto-starts and auto-stops
    pass

# Method 2: Manual Control
system = create_system()
system.start()
# ... use system ...
system.stop()
```

### Check System Health

```python
health = system.get_health()

# Returns:
{
    'health_score': 100.0,           # Overall health (0-100)
    'agents_total': 5,               # Total agents
    'agents_healthy': 5,             # Healthy agents
    'system_uptime_seconds': 123.4,  # Uptime
    'message_bus_metrics': {...}     # Message bus stats
}
```

### Get Resource Metrics

```python
metrics = system.get_resource_metrics()

# Returns:
{
    'metrics': {
        'cpu_usage_percent': 25.3,
        'memory_usage_percent': 45.2,
        'gpu_usage_percent': 0.0,
        'disk_usage_percent': 58.1
    }
}
```

### List All Agents

```python
agents = system.get_all_agents()

# Returns list of:
{
    'agent_id': 'audio_enhancement_agent',
    'agent_name': 'Audio Enhancement & Restoration Agent',
    'state': 'running',
    'metrics': {...}
}
```

---

## Audio Processing

### Audio Enhancement

```python
import numpy as np

# Create test audio (440 Hz sine wave)
sample_rate = 44100
audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate))

# Enhance audio
result = system.enhance_audio(
    audio_data=audio.tolist(),
    sample_rate=44100,
    params={
        'noise_reduction_amount': 0.8,      # 0.0 - 1.0
        'declicking_sensitivity': 0.5,      # 0.0 - 1.0
        'declipping_threshold': 0.95,       # 0.0 - 1.0
        'preserve_transients': True
    }
)

# Returns:
{
    'enhanced_audio': [...],        # Enhanced audio data
    'sample_rate': 44100,
    'processing_time_ms': 123.4,
    'improvements': {...}
}
```

**Enhancement Parameters:**
- `noise_reduction_amount`: 0.0 (none) to 1.0 (maximum)
- `declicking_sensitivity`: 0.0 (off) to 1.0 (aggressive)
- `declipping_threshold`: 0.8 to 0.99 (detection threshold)
- `preserve_transients`: True/False (keep sharp attacks)

---

## Music Generation

### Generate Melody

```python
melody = system.generate_music(
    content_type='melody',
    musical_context={
        'key': 'C major',
        'tempo': 120.0,
        'time_signature': '4/4',
        'chord_progression': ['C', 'Am', 'F', 'G'],
        'length_bars': 8
    }
)

# Returns:
{
    'midi_data': {...},             # Generated MIDI
    'notes': [...],                 # Note events
    'generation_time_ms': 456.7
}
```

### Generate Other Content

```python
# Harmony
harmony = system.generate_music('harmony', musical_context)

# Drum Pattern
drums = system.generate_music('drums', musical_context)

# Bass Line
bass = system.generate_music('bass', musical_context)
```

**Musical Context Parameters:**
- `key`: 'C major', 'A minor', 'G major', etc.
- `tempo`: 60.0 - 200.0 BPM
- `time_signature`: '4/4', '3/4', '6/8', etc.
- `chord_progression`: List of chord names
- `length_bars`: 4, 8, 16, 32, etc.

---

## Metadata Management

### Extract Metadata

```python
metadata = system.extract_metadata(
    audio_data=audio.tolist(),
    sample_rate=44100,
    deep_analysis=True
)

# Returns:
{
    'musical_features': {
        'tempo': 120.0,
        'key': 'C major',
        'time_signature': '4/4',
        ...
    },
    'technical_features': {
        'sample_rate': 44100,
        'duration_seconds': 10.5,
        'peak_amplitude': 0.95,
        ...
    },
    'quality_metrics': {
        'signal_to_noise_ratio': 45.2,
        'dynamic_range': 12.3,
        ...
    }
}
```

### Search Metadata

```python
results = system.search_metadata(
    query="tempo:120 key:C",
    filters={
        'genre': 'pop',
        'min_duration': 180
    }
)
```

---

## Workflow Management

### Create Workflow

```python
from src.orchestration import create_audio_enhancement_workflow

# Define workflow
workflow_def = create_audio_enhancement_workflow(audio, sample_rate)

# Create and execute
workflow_id = system.create_workflow(workflow_def)
system.execute_workflow(workflow_id)

# Monitor progress
status = system.get_workflow_status(workflow_id)
print(f"Progress: {status['completed_steps']}/{status['total_steps']}")
```

### Workflow Status

```python
status = system.get_workflow_status(workflow_id)

# Returns:
{
    'workflow_id': 'wf_12345',
    'status': 'running',            # pending, running, completed, failed
    'completed_steps': 2,
    'total_steps': 5,
    'current_step': 'audio_analysis',
    'progress_percent': 40.0
}
```

---

## Configuration

### Environment Variables (.env)

```bash
# System
AGENT_LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
MAX_WORKER_THREADS=8              # 1-32

# Resources
MAX_CPU_USAGE_PERCENT=85.0        # 50-95
MAX_MEMORY_USAGE_PERCENT=90.0     # 50-95
CACHE_MAX_SIZE_MB=500             # 100-2000

# Performance
ENABLE_GPU=false                  # true/false
```

### Agent Configuration (config.json)

```json
{
  "agents": {
    "audio_enhancement": {
      "processing_threads": 4,
      "default_params": {
        "noise_reduction_amount": 0.8
      }
    },
    "content_generation": {
      "default_params": {
        "temperature": 0.8,
        "creativity_level": "medium"
      }
    },
    "performance_optimization": {
      "cache": {
        "max_size_mb": 500,
        "eviction_policy": "lru"
      }
    }
  }
}
```

---

## Testing & Validation

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test class
pytest tests/test_system.py::TestSystemBasics -v

# Specific test
pytest tests/test_system.py::TestSystemBasics::test_01_system_startup -v
```

### Run Examples

```bash
# All examples
python examples/basic_usage.py

# Individual examples in Python:
from examples.basic_usage import example_1_basic_system_startup
example_1_basic_system_startup()
```

---

## Command Line Utilities

### System Health Check

```bash
python -c "from src.system import create_system; s=create_system(); s.start(); print('Health:', s.get_health()['health_score']); s.stop()"
```

### Quick Test

```bash
# Start system and check all agents
python -c "
from src.system import create_system
s = create_system()
s.start()
print('Agents:', len(s.get_all_agents()))
s.stop()
"
```

### Resource Monitor

```bash
# Check current resource usage
python -c "
from src.system import create_system
s = create_system()
s.start()
m = s.get_resource_metrics()
print(f\"CPU: {m['metrics']['cpu_usage_percent']}%\")
print(f\"Memory: {m['metrics']['memory_usage_percent']}%\")
s.stop()
"
```

---

## Troubleshooting Quick Fixes

### System Won't Start

```python
# 1. Check imports
from src.system import create_system  # Should work

# 2. Check dependencies
import librosa  # Should work

# 3. Verify config
import json
with open('config.json') as f:
    config = json.load(f)
print("Config OK")
```

### Agent Failures

```python
system.start()

# Check which agents failed
agents = system.get_all_agents()
for agent in agents:
    if agent['state'] != 'running':
        print(f"Failed: {agent['agent_name']}")
        print(f"State: {agent['state']}")
```

### Memory Issues

```python
# Reduce cache size in config.json
{
  "agents": {
    "performance_optimization": {
      "cache": {
        "max_size_mb": 250  # Reduced from 500
      }
    }
  }
}
```

---

## File Locations

| File/Directory | Purpose | Location |
|----------------|---------|----------|
| System Code | Core implementation | `src/` |
| Configuration | Environment variables | `.env` |
| Configuration | Agent settings | `config.json` |
| Database | Metadata storage | `data/metadata.db` |
| Logs | System logs | `logs/system.log` |
| Tests | Test suite | `tests/` |
| Examples | Usage examples | `examples/` |
| Docs | Documentation | `*.md` files |

---

## API Response Times (Typical)

| Operation | Average | Notes |
|-----------|---------|-------|
| System Startup | 2-3s | All agents |
| Health Check | <50ms | Lightweight |
| Audio Enhancement | 1-3s | Per 1s audio |
| Music Generation | 0.5-2s | Per 8 bars |
| Metadata Extract | 0.5-1s | Per file |
| Workflow Create | <100ms | Setup only |

---

## Common Workflows

### Basic Audio Processing

```python
with create_system() as system:
    # 1. Load audio
    audio_data = [...]  # Your audio

    # 2. Enhance
    enhanced = system.enhance_audio(audio_data, 44100)

    # 3. Extract metadata
    metadata = system.extract_metadata(enhanced['enhanced_audio'], 44100)

    # 4. Done!
    print(f"Processed {metadata['technical_features']['duration_seconds']}s")
```

### Music Production Pipeline

```python
with create_system() as system:
    context = {
        'key': 'C major',
        'tempo': 120.0,
        'chord_progression': ['C', 'Am', 'F', 'G']
    }

    # Generate components
    melody = system.generate_music('melody', context)
    harmony = system.generate_music('harmony', context)
    drums = system.generate_music('drums', context)
    bass = system.generate_music('bass', context)

    # Combine and enhance...
```

---

## Health Monitoring Script

```python
import time
from src.system import create_system

system = create_system()
system.start()

try:
    while True:
        health = system.get_health()
        metrics = system.get_resource_metrics()

        print(f"\nHealth: {health['health_score']}%")
        print(f"CPU: {metrics['metrics']['cpu_usage_percent']:.1f}%")
        print(f"Memory: {metrics['metrics']['memory_usage_percent']:.1f}%")
        print(f"Agents: {health['agents_healthy']}/{health['agents_total']}")

        if health['health_score'] < 80:
            print("WARNING: Low health score!")

        time.sleep(30)  # Check every 30 seconds

except KeyboardInterrupt:
    system.stop()
```

---

## Version Info

```python
# Get system version
print("MAAPS v1.0.0")

# Check agent versions
agents = system.get_all_agents()
for agent in agents:
    print(f"{agent['agent_name']}: v1.0.0")
```

---

**MAAPS Quick Reference v1.0.0**
For complete documentation, see: `DEPLOYMENT.md`
