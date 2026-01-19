# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAAPS Nexus is a multi-agent audio processing system with two distinct architectures:

1. **Legacy System**: Message bus-based multi-agent system for audio enhancement, content generation, performance optimization, and metadata management (~7,000 lines of code, 65-70% complete)
2. **RL System (Primary)**: Reinforcement learning-based system using Ray cluster with competing agents coordinated via Hierarchical Goal Optimization (HGO) - the future direction of the project

**Important**: When asked to work on RL agents, focus on `src/agents/{critic_agent,eq_rl_agent,dynamics_rl_agent,hgo_coordinator}.py`. For legacy system work, focus on `src/agents/{audio_enhancement,content_generation,performance_optimization,metadata_management}_agent.py`.

## Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the RL System

**Standalone Test Mode** (no DAW required - recommended for initial testing):
```bash
python maaps_nexus_main.py --mode test --test-duration 10.0
```

**VST3 DAW Integration Mode** (requires VST3 plugin to be built and Python backend must be started FIRST):
```bash
# Step 1: Start Python backend first
python maaps_nexus_main.py --mode vst3 --buffer-size 512 --sample-rate 44100

# Step 2: Open DAW and load MAAPS Nexus VST3 plugin
```

Additional options:
- `--num-cpus 8`: Specify CPUs for Ray cluster
- `--use-pretrained`: Load pre-trained models from `--model-dir`
- `--model-dir ./models`: Model checkpoint directory

### Running the Legacy System

```bash
# Basic usage
python examples/basic_usage.py

# API server (development)
uvicorn api.main:app --reload

# API server (production)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
python tests/test_system.py

# Run with pytest
pytest tests/test_system.py

# Run live performance tests
pytest tests/test_live_effects_chain.py
pytest tests/test_live_looping.py
pytest tests/test_synchronization_clock.py
```

### VST3 Plugin Build (Optional)

```bash
cd vst3_plugin
mkdir build && cd build
cmake ..
cmake --build .
cmake --install .
```

Plugin installs to:
- Windows: `C:\Program Files\Common Files\VST3\`
- macOS: `~/Library/Audio/Plug-Ins/VST3/`
- Linux: `~/.vst3/`

### Code Quality

```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy src/
```

## Architecture

### RL System Architecture (Primary)

The RL system uses Ray for distributed computing with competing agents coordinated by HGO:

```
DAW (VST3) → Shared Memory → Python Multi-Agent System (Ray)
                                    ↓
                           Audio Ontology Manager
                                    ↓
                              Critic Agent (Judge)
                                    ↓
                    ┌───────────────┴───────────────┐
              EQ RL Agent                   Dynamics RL Agent
              (TD3, 8 bands)               (TD3, compression)
                    └───────────────┬───────────────┘
                                    ↓
                           HGO Coordinator (Mediator)
                                    ↓
                            Processed Audio
```

**Key Components:**

1. **Ray Cluster** (`src/infrastructure/ray_cluster.py`)
   - Distributed computing framework
   - Actor-based concurrency for real-time processing
   - Manages agent lifecycle and resources

2. **Audio Ontology** (`src/core/audio_ontology.py`)
   - Shared vocabulary for audio characteristics (Clarity, Warmth, Mud, Punch, etc.)
   - Frequency band mappings and attribute correlations
   - Goal system for optimization targets

3. **Critic Agent** (`src/agents/critic_agent.py`)
   - Neural network that evaluates audio quality
   - Predicts user satisfaction
   - Provides reward signals for RL training
   - **Build this first** - agents need feedback to learn

4. **EQ RL Agent** (`src/agents/eq_rl_agent.py`)
   - TD3 reinforcement learning agent
   - Controls 8 parametric EQ bands
   - Learns equalization strategies

5. **Dynamics RL Agent** (`src/agents/dynamics_rl_agent.py`)
   - TD3 reinforcement learning agent
   - Controls compression (threshold, ratio, attack, release, knee, makeup gain)
   - Competes with EQ agent

6. **HGO Coordinator** (`src/agents/hgo_coordinator.py`)
   - Resolves conflicts between agents using Hierarchical Goal Optimization
   - Determines execution order
   - Provides compromise solutions

7. **VST3 Wrapper** (`src/daw_integration/vst3_wrapper.py`)
   - Bridge between DAW and Python using shared memory
   - Lock-free ring buffers for <10ms latency
   - Platform-specific (Windows/Linux/macOS)

### Legacy Message Bus Architecture

The legacy system uses a publish-subscribe message bus:

```
Workflow Engine → Message Bus (Pub-Sub) → Agents
                                           ├─ Audio Enhancement Agent
                                           ├─ Content Generation Agent
                                           ├─ Performance Optimization Agent
                                           └─ Metadata Management Agent
```

**Core Components:**

- **Message Bus** (`src/core/message_bus.py`): Thread-safe pub-sub with priority queuing (HIGH/MEDIUM/LOW), wildcard topic subscriptions, dead letter queue
- **Base Agent** (`src/core/base_agent.py`): Base class for all agents with setup/handle_message/teardown lifecycle
- **Agent Coordinator** (`src/orchestration/agent_coordinator.py`): Manages agent lifecycle
- **Workflow Engine** (`src/orchestration/workflow_engine.py`): Multi-step workflow coordination

**Agents:**
- Audio Enhancement: Noise reduction, click removal, clipping restoration
- Content Generation: Melody, harmony, drum, bass generation
- Performance Optimization: Resource monitoring, task scheduling, caching
- Metadata Management: Metadata extraction, search, version control
- Live Performance: Real-time effects, looping, MIDI control, synchronization

## Development Workflow

### Adding New RL Agents

1. Create agent class in `src/agents/` using `@ray.remote` decorator
2. Implement TD3 or other RL algorithm (see `eq_rl_agent.py` as reference)
3. Define state/action spaces compatible with `AudioState` from audio_ontology
4. Implement `process_audio()`, `store_experience()`, `train_step()` methods
5. Register with HGO Coordinator in `maaps_nexus_main.py` with priority level
6. Ensure <10ms latency for real-time processing (profile with `tests/performance/`)

### Adding New Legacy Agents

1. Create class in `src/agents/` inheriting from `BaseAgent` (see `src/core/base_agent.py`)
2. Implement lifecycle methods: `setup()`, `handle_message(message: Message)`, `teardown()`
3. Subscribe to relevant topics in `setup()` using `self.subscribe("topic.name")`
4. Publish responses using `self.publish(Message(topic="response.topic", payload={...}))`
5. Register in `src/orchestration/agent_coordinator.py` in `_create_core_agents()`
6. Export in `src/agents/__init__.py`
7. Add tests in `tests/test_system.py`

### Training RL Models

The Critic agent must be trained first with user satisfaction labels:
```python
critic.train_step(audio_samples, ontology_states, satisfaction_labels)
```

RL agents train automatically during use via reward signals from Critic. Accelerate training by processing many audio frames in standalone mode.

### API Development

The REST API (`api/main.py`) provides HTTP endpoints for the legacy system:
- Audio processing
- Music generation
- Metadata extraction
- System health monitoring

Routers are organized in `api/routers/`:
- `audio.py`: Audio enhancement endpoints
- `effects.py`: Effects processing
- `looping.py`: Live looping
- `metadata.py`: Metadata operations
- `system.py`: System management

## Key Patterns

### RL System Execution Flow

1. Audio arrives from DAW via shared memory
2. EQ and Dynamics agents propose actions (parallel execution via Ray)
3. HGO Coordinator detects conflicts and resolves via goal hierarchy
4. Approved actions are executed
5. Critic evaluates result and provides reward
6. Agents store experience and periodically train (every 100 frames)
7. Processed audio returns to DAW

### Message Bus Communication

Agents communicate via topics with wildcards supported:
```python
# Subscribe
self.subscribe("audio.enhancement.request")
self.subscribe("audio.*")  # Wildcard

# Publish
self.publish(Message(
    topic="audio.enhancement.response",
    payload={"enhanced_audio": audio},
    priority=Priority.HIGH
))
```

### Request-Response Pattern

For synchronous operations:
```python
response = self.request(
    topic="system.resource.request",
    payload={},
    timeout=5.0
)
```

## Important Constraints

### Real-Time Processing
- Target latency: <10ms total (VST3 wrapper ~2ms, agent processing ~5-8ms)
- Use Ray actors for parallel processing
- Minimize data copying between agents
- Profile with `tests/performance/` tools

### RL Training
- Critic agent MUST be trained before RL agents can learn effectively
- Agents learn online during processing - no separate training phase required
- Save checkpoints periodically (`system.save_models()`)
- Exploration noise decreases over time

### Vertex AI Integration
- LLM integration via `src/utils/` (supports Vertex AI, Anthropic, OpenAI, Ollama)
- Requires `VERTEX_PROJECT_ID` environment variable
- See `SETUP_VERTEX_AI.md` for configuration
- Test with `python test_vertex_ai.py`

## File Structure

```
MAAPS_Nexus/
├── maaps_nexus_main.py                    # RL system entry point
├── src/
│   ├── infrastructure/
│   │   └── ray_cluster.py                # Ray cluster initialization
│   ├── core/
│   │   ├── audio_ontology.py            # Shared audio vocabulary (Clarity, Warmth, etc.)
│   │   ├── message_bus.py               # Pub-sub messaging (legacy)
│   │   ├── message_types.py             # Message definitions (legacy)
│   │   └── base_agent.py                # Base class for legacy agents
│   ├── agents/
│   │   ├── critic_agent.py              # RL: Evaluates audio quality, provides rewards
│   │   ├── eq_rl_agent.py               # RL: 8-band EQ with TD3
│   │   ├── dynamics_rl_agent.py         # RL: Compression with TD3
│   │   ├── hgo_coordinator.py           # RL: Conflict resolution mediator
│   │   ├── audio_enhancement_agent.py   # Legacy: Noise reduction, declicking
│   │   ├── content_generation_agent.py  # Legacy: Melody, harmony, drums
│   │   ├── performance_optimization_agent.py  # Legacy: Resource monitoring
│   │   ├── metadata_management_agent.py # Legacy: Metadata extraction, search
│   │   ├── live/                        # Legacy: Real-time performance agents
│   │   └── transcription/               # Legacy: Audio-to-MIDI, harmonic analysis
│   ├── daw_integration/
│   │   └── vst3_wrapper.py              # Shared memory bridge to DAW
│   ├── orchestration/
│   │   ├── agent_coordinator.py         # Legacy: Agent lifecycle management
│   │   └── workflow_engine.py           # Legacy: Multi-step workflows
│   ├── system.py                        # Legacy: High-level system API
│   └── utils/
│       ├── vertex_ai_integration.py     # Vertex AI (Claude/Gemini)
│       └── llm_integration.py           # Multi-provider LLM support
├── api/                                  # REST API (legacy system, ~40% complete)
│   ├── main.py                          # FastAPI application
│   ├── routers/                         # Endpoint routers (mostly stubs)
│   └── schemas/                         # Request/response schemas
├── tests/
│   ├── test_system.py                   # Basic system tests
│   ├── test_live_*.py                   # Live performance tests
│   └── performance/                     # Benchmarking tools
├── examples/
│   └── basic_usage.py                   # Legacy system examples
├── vst3_plugin/                         # VST3 C++ plugin (shared memory IPC)
└── [Documentation files]                # *.md files in root
```

## Testing Strategy

**Current Test Coverage: ~25% (needs significant expansion)**

- Unit tests for individual agents (see `tests/test_system.py`)
- Integration tests for multi-agent workflows (limited)
- Performance benchmarks in `tests/performance/`
- Live performance tests: `test_live_effects_chain.py`, `test_live_looping.py`, `test_synchronization_clock.py`
- Run tests: `pytest tests/` or `python tests/test_system.py`

**Testing Priority**: The legacy system needs extensive test coverage expansion (see `LEGACY_SYSTEM_COMPLETION_FRAMEWORK.md` for details).

## Environment Variables

Create `.env` file (copy from `.env.example`):
```bash
# Vertex AI Configuration (optional - for LLM integration)
VERTEX_PROJECT_ID=your-project-id
VERTEX_LOCATION=us-central1
VERTEX_MODEL=claude-3-5-sonnet@20241022

# Alternative: Direct Anthropic API
# ANTHROPIC_API_KEY=your-api-key
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Alternative: OpenAI
# OPENAI_API_KEY=your-api-key
# OPENAI_MODEL=gpt-4

# Alternative: Ollama (local)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama2

# System settings (optional)
AGENT_LOG_LEVEL=INFO
MESSAGE_BUS_MAX_QUEUE_SIZE=10000

# Resource limits (optional)
MAX_CPU_USAGE=85.0
MAX_MEMORY_USAGE=90.0
CACHE_MAX_SIZE_MB=500
```

**Note**: See `SETUP_VERTEX_AI.md` for complete Vertex AI configuration guide, including authentication setup.

## Common Pitfalls

1. **Running VST3 mode without starting Python backend first** - Always start `maaps_nexus_main.py` before loading the VST3 plugin
2. **Not training Critic agent** - RL agents need reward signals to learn
3. **Exceeding latency budget** - Profile carefully, use smaller buffer sizes if needed
4. **Ray cluster issues on Windows** - Consider using WSL2 if Ray has problems
5. **Shared memory not found** - On Linux, install `posix-ipc`: `pip install posix-ipc`
6. **Forgetting to activate venv** - Always activate before running

## Dependencies

Core dependencies (see `requirements.txt`):
- `ray[default]==2.9.0`: Distributed computing for RL system
- `torch>=2.0.0`: Deep learning for RL agents
- `librosa==0.11.0`: Audio analysis
- `numpy==2.3.4`: Numerical computing
- `scipy==1.16.3`: Scientific computing
- `psutil==7.1.3`: System monitoring
- `anthropic[vertex]>=0.40.0`: Vertex AI integration (optional)
- `google-cloud-aiplatform>=1.71.1`: Vertex AI platform (optional)
- `fastapi`: REST API framework (legacy system)
- `music21==9.9.1`: Music theory analysis (legacy)
- `pretty-midi==0.2.11`: MIDI manipulation (legacy)
- `pytest==9.0.1`: Testing framework

**Platform-specific**:
- Linux/macOS: Install `posix-ipc>=1.1.1` for shared memory support
- Windows: Ray may have issues; consider using WSL2

## Important Documentation Files

- **`README.md`**: Overview of legacy message bus system
- **`MULTI_AGENT_AUDIO_SYSTEM_README.md`**: Detailed RL system architecture and usage
- **`LEGACY_SYSTEM_COMPLETION_FRAMEWORK.md`**: Legacy system completion status (65-70% done)
- **`SETUP_VERTEX_AI.md`**: Complete Vertex AI integration guide
- **`VERTEX_AI_QUICKSTART.md`**: Quick start for Vertex AI
- **`API_GUIDE.md`**: REST API documentation (legacy system)
- **`LIVE_PERFORMANCE_AGENTS.md`**: Real-time performance system documentation
- **`MUSICAL_ANALYSIS_TRANSCRIPTION.md`**: Audio transcription features
- **`DEPLOYMENT_GUIDE.md`**: Production deployment instructions
