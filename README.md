# MAAPS Nexus

[![CI](https://github.com/SGM-Studios/MAAPS_Nexus/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/SGM-Studios/MAAPS_Nexus/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Multi-Agent Audio Processing System** — an AI-powered audio engine where competing reinforcement-learning agents collaborate through a shared ontology to make real-time mixing and mastering decisions, integrated directly into your DAW via VST3, CLAP, or ARA.

---

## Overview

MAAPS Nexus ships two complementary architectures that can be used independently or together:

| | RL System (primary) | Legacy System |
|---|---|---|
| **Purpose** | Real-time mixing & mastering via RL | Offline audio enhancement, music generation, metadata |
| **Communication** | Ray distributed actors | Pub-sub message bus |
| **Entry point** | `maaps_nexus_main.py` | `examples/basic_usage.py` / `api/main.py` |
| **DAW integration** | VST3 / CLAP / ARA plugin | REST API |

---

## RL System Architecture

The primary system uses [Ray](https://docs.ray.io) for distributed execution. Agents run as Ray actors and coordinate through a **Hierarchical Goal Optimization (HGO)** layer that resolves conflicts before any action is applied.

```
DAW (VST3 / CLAP / ARA)
        │  shared memory / IPC
        ▼
 Audio Ontology Manager        ← shared vocabulary
        │                         (Clarity, Warmth, Mud, Punch …)
        ▼
   Critic Agent                ← neural net that predicts user satisfaction
        │  reward signals
   ┌────┴────┐
EQ RL Agent  Dynamics RL Agent  ← TD3 agents that compete & learn
   └────┬────┘
        ▼
 HGO Coordinator               ← detects & resolves agent conflicts
        │
        ▼
  Processed Audio → DAW
```

### Key components

| Component | File | Description |
|---|---|---|
| System orchestrator | `src/nexus_system.py` | Manages Ray cluster, agent lifecycle, plugin IPC |
| Audio Ontology | `src/core/audio_ontology.py` | Shared attribute vocabulary (Clarity, Warmth, Punch, …) |
| Critic Agent | `src/agents/critic_agent.py` | Evaluates audio quality; generates reward signals |
| EQ RL Agent | `src/agents/eq_rl_agent.py` | TD3 agent controlling 8 parametric EQ bands |
| Dynamics RL Agent | `src/agents/dynamics_rl_agent.py` | TD3 agent controlling compression parameters |
| HGO Coordinator | `src/agents/hgo_coordinator.py` | Conflict detection & goal-hierarchy resolution |
| Streaming plugin | `src/daw_integration/streaming_plugin_wrapper.py` | VST3 / CLAP shared-memory IPC bridge |
| ARA plugin | `src/daw_integration/ara_plugin_wrapper.py` | ARA2 host integration |
| Ray cluster | `src/infrastructure/ray_cluster.py` | Cluster init & resource management |

---

## Quick Start

### Prerequisites

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

On Linux, also install `posix-ipc` for shared-memory DAW integration:

```bash
pip install posix-ipc
```

### Run standalone (no DAW required)

```bash
python maaps_nexus_main.py --mode test --test-duration 10.0
```

### Run with a DAW plugin

Start the Python backend **first**, then load the plugin in your DAW:

```bash
# Step 1 — start the backend (choose your plugin format)
python maaps_nexus_main.py --mode vst3 --buffer-size 512 --sample-rate 44100
python maaps_nexus_main.py --mode clap --buffer-size 512 --sample-rate 44100
python maaps_nexus_main.py --mode ara  --buffer-size 512 --sample-rate 44100

# Step 2 — load the corresponding plugin in Reaper / Bitwig / Logic / etc.
```

### Build the VST3 plugin (optional)

```bash
cd vst3_plugin
mkdir build && cd build
cmake ..
cmake --build .
cmake --install .
```

Plugin installs to the standard VST3 path for your OS.

### Additional CLI options

| Flag | Default | Description |
|---|---|---|
| `--num-cpus N` | auto | CPUs to allocate to the Ray cluster |
| `--buffer-size N` | 512 | Audio buffer size (samples) |
| `--sample-rate N` | 44100 | Sample rate (Hz) |
| `--model-dir PATH` | `./models` | Directory for RL model checkpoints |
| `--use-pretrained` | off | Load checkpoints from `--model-dir` on startup |
| `--test-duration N` | 10.0 | Duration for standalone test mode (seconds) |

---

## Legacy System

The message-bus system handles offline audio tasks exposed through a REST API.

```bash
# Run examples
python examples/basic_usage.py

# Start API server
pip install -r requirements-api.txt
uvicorn api.main:app --reload
```

### Legacy agents

| Agent | Description |
|---|---|
| Audio Enhancement | Noise reduction, click removal, clipping restoration |
| Content Generation | Melody, harmony, drum pattern, bass line generation |
| Performance Optimization | Resource monitoring, task scheduling, LRU cache |
| Metadata Management | Metadata extraction, semantic search, version control |
| Live Performance | Real-time effects chain, looping, MIDI control, sync clock |
| Transcription | Audio-to-MIDI, harmonic analysis, rhythm analysis |

---

## Development

### Environment variables

Copy `.env.example` to `.env` and fill in as needed:

```bash
# Optional — LLM integration
VERTEX_PROJECT_ID=your-gcp-project
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# System tuning (optional)
AGENT_LOG_LEVEL=INFO
MESSAGE_BUS_MAX_QUEUE_SIZE=10000
MAX_CPU_USAGE=85.0
MAX_MEMORY_USAGE=90.0
CACHE_MAX_SIZE_MB=500
```

### Testing

```bash
# Full test suite
pytest tests/

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Specific suites
pytest tests/test_rl_system.py
pytest tests/test_live_effects_chain.py
pytest tests/test_synthetic_integration.py
pytest tests/test_adaptive_latency.py
```

### Code quality

```bash
black .                              # format
flake8                               # lint
mypy src/ --ignore-missing-imports   # type check
```

### Adding an RL agent

1. Create a Ray actor class in `src/agents/` using `@ray.remote` — see `eq_rl_agent.py` for the TD3 pattern.
2. Define `process_audio()`, `store_experience()`, and `train_step()` using `AudioState` from `src/core/audio_ontology.py`.
3. Register with the HGO Coordinator in `maaps_nexus_main.py`.
4. Target < 10 ms total latency; profile with `tests/performance/`.

### Adding a legacy agent

1. Subclass `BaseAgent` from `src/core/base_agent.py`.
2. Implement `setup()`, `handle_message(message)`, `teardown()`.
3. Subscribe to topics in `setup()` and publish responses via `self.publish(...)`.
4. Register in `src/orchestration/agent_coordinator.py → _create_core_agents()`.

---

## Repository layout

```
MAAPS_Nexus/
├── maaps_nexus_main.py          # RL system entry point
├── src/
│   ├── nexus_system.py          # Main RL system orchestrator
│   ├── system.py                # Legacy system API
│   ├── core/
│   │   ├── audio_ontology.py    # Shared attribute vocabulary
│   │   ├── message_bus.py       # Pub-sub bus (legacy)
│   │   ├── base_agent.py        # Base class for legacy agents
│   │   ├── agent_factory.py     # Factory for legacy agents
│   │   ├── di_container.py      # Dependency injection
│   │   ├── common.py            # Shared utilities
│   │   └── exceptions.py        # Exception hierarchy
│   ├── agents/
│   │   ├── critic_agent.py      # RL: reward signal generator
│   │   ├── eq_rl_agent.py       # RL: 8-band EQ (TD3)
│   │   ├── dynamics_rl_agent.py # RL: compression (TD3)
│   │   ├── hgo_coordinator.py   # RL: conflict resolution
│   │   ├── audio_enhancement_agent.py
│   │   ├── content_generation_agent.py
│   │   ├── performance_optimization_agent.py
│   │   ├── metadata_management_agent.py
│   │   ├── live/                # Real-time performance agents
│   │   └── transcription/       # Audio-to-MIDI, harmonic analysis
│   ├── daw_integration/
│   │   ├── streaming_plugin_wrapper.py  # VST3 / CLAP IPC
│   │   └── ara_plugin_wrapper.py        # ARA2 integration
│   ├── infrastructure/
│   │   └── ray_cluster.py       # Ray cluster lifecycle
│   ├── orchestration/
│   │   ├── agent_coordinator.py # Legacy agent lifecycle
│   │   └── workflow_engine.py   # Multi-step workflow engine
│   └── utils/
│       ├── llm_integration.py   # Multi-provider LLM (Anthropic/OpenAI/Ollama)
│       └── vertex_ai_integration.py
├── api/                         # REST API (legacy system, FastAPI)
│   ├── main.py
│   └── routers/
├── tests/                       # Test suite
├── examples/                    # Legacy system examples
├── vst3_plugin/                 # VST3 C++ source
├── requirements.txt             # Core dependencies
├── requirements-api.txt         # API-layer dependencies
├── requirements-lint.txt        # CI lint dependencies
└── docker-compose.yml
```

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
