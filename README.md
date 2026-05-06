# Multi-Agent Audio Processing System

[![CI/CD](https://github.com/maaps/maaps/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/maaps/maaps/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)

A comprehensive, production-ready multi-agent system for advanced audio processing, AI-powered music generation, and intelligent project management.

## Overview

This system implements a sophisticated agent-based architecture for audio production workflows, featuring:

- **Audio Enhancement & Restoration Agent**: Advanced noise reduction, click removal, clipping restoration, and spectral repair
- **Content Generation & Gap Filling Agent**: AI-powered melody, harmony, drum pattern, and bass line generation
- **Performance & Resource Optimization Agent**: Real-time system monitoring, intelligent task scheduling, and cache management
- **Intelligent Metadata & Project Management Agent**: Comprehensive metadata extraction, version control, and semantic search
- **Workflow Orchestration Engine**: Complex multi-step workflow coordination with dependency management

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                   Workflow Engine                        │
│           (Multi-Step Workflow Coordination)             │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴──────────────┐
        │     Message Bus           │
        │  (Publish-Subscribe)      │
        └─┬─────────┬──────────┬───┘
          │         │          │
    ┌─────▼────┐ ┌──▼──────┐ ┌▼─────────┐
    │ Audio    │ │ Content │ │Performance│
    │Enhancement│ │Generation│ │Optimizer │
    └──────────┘ └─────────┘ └──────────┘
          │           │           │
          └───────────┴───────────┘
                      │
              ┌───────▼────────┐
              │   Metadata     │
              │   Management   │
              └────────────────┘
```

### Agent Communication

Agents communicate through a high-performance message bus using a publish-subscribe pattern with:
- Priority queuing (HIGH, MEDIUM, LOW)
- Request-response patterns
- Wildcard topic subscriptions
- Dead letter queuing for failed messages

## Quick Start

### Installation

```bash
# Clone the repository
cd agents

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src.system import create_system

# Create and start the system
system = create_system()
system.start()

# Enhance audio
import numpy as np

# Create test audio
sample_rate = 44100
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration))
audio = 0.5 * np.sin(2 * np.pi * 440 * t)

# Enhance
result = system.enhance_audio(
    audio_data=audio.tolist(),
    sample_rate=sample_rate,
    params={'noise_reduction_amount': 0.8}
)

# Generate music
musical_context = {
    'key': 'C major',
    'tempo': 120.0,
    'chord_progression': ['C', 'Am', 'F', 'G']
}

melody_result = system.generate_music(
    content_type='melody',
    musical_context=musical_context
)

# Clean up
system.stop()
```

### Running Examples

```bash
# Run all examples
python examples/basic_usage.py
```

### Running Tests

```bash
# Run test suite
python tests/test_system.py

# Or with pytest
pytest tests/
```

## Agent Capabilities

### 1. Audio Enhancement & Restoration Agent

**Topics:**
- `audio.enhancement.request` - Comprehensive enhancement
- `audio.noise.reduction.request` - Noise reduction only
- `audio.restoration.request` - Click/pop/clipping restoration
- `audio.superresolution.request` - Sample rate enhancement

**Features:**
- Adaptive spectral subtraction for noise reduction
- Click and pop detection and removal
- Digital clipping restoration
- Spectral artifact repair
- AI-powered super-resolution

**Example:**
```python
result = system.enhance_audio(
    audio_data=noisy_audio,
    sample_rate=44100,
    params={
        'noise_reduction_amount': 0.8,
        'declicking_sensitivity': 0.5,
        'declipping_threshold': 0.95
    }
)
```

### 2. Content Generation & Gap Filling Agent

**Topics:**
- `music.generation.melody.request` - Generate melodies
- `music.generation.harmony.request` - Generate harmony
- `music.generation.drums.request` - Generate drum patterns
- `music.generation.bass.request` - Generate bass lines
- `music.generation.arrangement.request` - Arrangement suggestions

**Features:**
- Melody generation with musical constraints
- Harmony generation with voice leading
- Genre-aware drum pattern synthesis
- Bass line generation from chord progressions
- Arrangement gap analysis

**Example:**
```python
melody_result = system.generate_music(
    content_type='melody',
    musical_context={
        'key': 'C major',
        'tempo': 120.0,
        'time_signature': '4/4',
        'chord_progression': ['C', 'Am', 'F', 'G'],
        'length_bars': 8
    }
)
```

### 3. Performance & Resource Optimization Agent

**Topics:**
- `system.resource.request` - Get resource metrics
- `system.task.schedule` - Schedule tasks
- `system.cache.get/set/clear` - Cache operations
- `system.performance.analyze` - Performance analysis
- `system.optimization.request` - Optimization requests

**Features:**
- Real-time CPU, memory, GPU monitoring
- Intelligent task scheduling with priorities
- LRU cache management
- Bottleneck detection
- Automated optimization recommendations

**Example:**
```python
# Get resource metrics
metrics = system.get_resource_metrics()
print(f"CPU: {metrics['metrics']['cpu_usage_percent']}%")
print(f"Memory: {metrics['metrics']['memory_usage_percent']}%")

# Get system health
health = system.get_health()
print(f"Health Score: {health['health_score']}%")
```

### 4. Intelligent Metadata & Project Management Agent

**Topics:**
- `metadata.extract.request` - Extract metadata
- `metadata.search.request` - Search metadata
- `project.create.request` - Create projects
- `project.version.create` - Version control
- `tags.generate.request` - Generate tags

**Features:**
- Comprehensive audio metadata extraction (musical, technical, quality)
- Intelligent tagging system
- Semantic search
- Project version control
- Collaboration support

**Example:**
```python
# Extract metadata
metadata_result = system.extract_metadata(
    audio_data=audio,
    sample_rate=44100,
    deep_analysis=True
)

# Search
search_result = system.search_metadata(
    query="tempo:120 key:C",
    filters={'genre': 'pop'}
)
```

### 5. Workflow Orchestration Engine

**Topics:**
- `workflow.create` - Create workflows
- `workflow.execute` - Execute workflows
- `workflow.status` - Get workflow status
- `workflow.cancel` - Cancel workflows

**Features:**
- Multi-step workflow definition
- Dependency management
- Automatic retries
- Progress tracking
- Result aggregation

**Example:**
```python
from src.orchestration import create_audio_enhancement_workflow

# Create workflow
workflow_def = create_audio_enhancement_workflow(audio, sample_rate)
workflow_id = system.create_workflow(workflow_def)

# Execute
system.execute_workflow(workflow_id)

# Monitor
status = system.get_workflow_status(workflow_id)
print(f"Progress: {status['completed_steps']}/{status['steps_total']}")
```

## Cross-Agent Workflows

### Example: Complete Audio Production Pipeline

```python
# 1. Extract metadata
metadata_result = system.extract_metadata(audio_data=audio, sample_rate=44100)

# 2. Enhance audio quality
enhancement_result = system.enhance_audio(audio_data=audio, sample_rate=44100)

# 3. Generate complementary musical elements
drums = system.generate_music('drums', musical_context)
bass = system.generate_music('bass', musical_context)

# 4. Re-extract metadata from enhanced audio
final_metadata = system.extract_metadata(
    audio_data=enhancement_result['enhanced_audio'],
    sample_rate=44100
)

# 5. Create project version
# ... (through metadata agent)
```

## System Configuration

### Environment Variables

```bash
# System settings
AGENT_LOG_LEVEL=INFO
MESSAGE_BUS_MAX_QUEUE_SIZE=10000

# Resource limits
MAX_CPU_USAGE=85.0
MAX_MEMORY_USAGE=90.0
CACHE_MAX_SIZE_MB=500

# Database
METADATA_DB_PATH=metadata.db
```

### Agent Configuration

Create `config.json`:
```json
{
  "system": {
    "monitoring_interval": 1.0,
    "health_check_interval": 5.0
  },
  "audio_enhancement": {
    "default_noise_reduction": 0.8,
    "max_processing_time": 300
  },
  "content_generation": {
    "default_temperature": 0.8,
    "max_generation_bars": 32
  },
  "performance": {
    "cache_size_mb": 500,
    "task_scheduler_algorithm": "resource_aware"
  },
  "metadata": {
    "deep_analysis_default": true,
    "search_index_size": 10000
  }
}
```

## Performance Optimization

### Best Practices

1. **Use Workflows for Complex Tasks**: Leverage the workflow engine for multi-step processes
2. **Enable Caching**: Cache frequently accessed data to reduce redundant processing
3. **Monitor Resources**: Regularly check system health and resource usage
4. **Batch Operations**: Process multiple files together when possible
5. **Tune Agent Parameters**: Adjust enhancement, generation, and optimization parameters based on your needs

### Scalability

- **Horizontal Scaling**: Deploy multiple agent instances behind a load balancer
- **Vertical Scaling**: Increase CPU/Memory/GPU resources for individual agents
- **Cloud Deployment**: Deploy to cloud platforms (AWS, Azure, GCP) for elastic scaling

## Troubleshooting

### Common Issues

**Issue**: Agents fail to start
```python
# Check system health
health = system.get_health()
print(health)

# Check specific agent
status = system.get_agent_status('audio_enhancement_agent')
print(status)
```

**Issue**: High CPU/Memory usage
```python
# Get resource metrics
metrics = system.get_resource_metrics()

# Analyze performance
# Reduce concurrent tasks or increase resources
```

**Issue**: Workflow execution timeout
```python
# Increase workflow step timeout
workflow_def['steps'][0]['timeout'] = 120.0  # 2 minutes
```

## Development

### Project Structure

```
agents/
├── src/
│   ├── core/                 # Core infrastructure
│   │   ├── base_agent.py     # Base agent class
│   │   ├── message_bus.py    # Message bus
│   │   └── message_types.py  # Message definitions
│   ├── agents/               # Agent implementations
│   │   ├── audio_enhancement_agent.py
│   │   ├── content_generation_agent.py
│   │   ├── performance_optimization_agent.py
│   │   └── metadata_management_agent.py
│   ├── orchestration/        # Workflow orchestration
│   │   ├── workflow_engine.py
│   │   └── agent_coordinator.py
│   └── system.py             # Main system interface
├── examples/                 # Usage examples
│   └── basic_usage.py
├── tests/                    # Test suite
│   └── test_system.py
├── architecture/             # Architecture documentation
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

### Adding New Agents

1. **Create Agent Class**:
```python
from src.core import BaseAgent, Message

class MyNewAgent(BaseAgent):
    def setup(self):
        self.subscribe("my.topic")

    def handle_message(self, message: Message):
        # Process message
        pass

    def teardown(self):
        # Cleanup
        pass
```

2. **Register in Coordinator**:
```python
# In src/orchestration/agent_coordinator.py
from ..agents import MyNewAgent

def _create_core_agents(self):
    agents_to_create = [
        # ... existing agents
        MyNewAgent()
    ]
```

3. **Export in __init__.py**:
```python
# In src/agents/__init__.py
from .my_new_agent import MyNewAgent

__all__ = [
    # ... existing agents
    'MyNewAgent',
]
```

## API Reference

See inline documentation in source files for detailed API reference.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Code of Conduct](CODE_OF_CONDUCT.md) and feel free to submit issues or pull requests.

## Support

For issues, questions, or contributions, please open an issue on the project repository.

## Acknowledgments

Built with:
- librosa - Audio analysis
- NumPy/SciPy - Numerical computing
- pretty_midi - MIDI manipulation
- psutil - System monitoring

---

**Multi-Agent Audio Processing System** - Professional-grade audio production automation
