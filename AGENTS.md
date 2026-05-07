# AGENTS.md

## System Overview
MAAPS Nexus has two architectures:
- **RL System (primary)**: Real-time mixing/mastering via RL agents, Ray distributed actors
- **Legacy System**: Offline audio enhancement/music generation, Pub-sub message bus, REST API

Entry points:
- RL System: `maaps_nexus_main.py`
- Legacy System: `examples/basic_usage.py` or API server
- DAW Integration: VST3/CLAP/ARA plugins (VST3 requires building C++ plugin)

## Key Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS; Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# On Linux, also install for shared-memory DAW integration:
pip install posix-ipc
```

### Testing
```bash
# Full test suite
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific suites (most commonly used)
pytest tests/test_rl_system.py
pytest tests/test_live_effects_chain.py
pytest tests/test_synthetic_integration.py
pytest tests/test_adaptive_latency.py

# Single test example
pytest tests/test_system.py::TestSystemBasics::test_system_creation
```

### Code Quality
```bash
# Format
black .

# Lint
flake8

# Type check (ignore missing imports for optional deps)
mypy src/ --ignore-missing-imports
```

### Running the System
```bash
# RL System - Standalone test (no DAW)
python maaps_nexus_main.py --mode test --test-duration 10.0

# RL System - VST3 DAW integration
python maaps_nexus_main.py --mode vst3 --buffer-size 512 --sample-rate 44100

# RL System - CLAP/ARA DAW integration
python maaps_nexus_main.py --mode clap --buffer-size 512 --sample-rate 44100
python maaps_nexus_main.py --mode ara  --buffer-size 512 --sample-rate 44100

# Legacy System examples
python examples/basic_usage.py

# Legacy API server
pip install -r requirements-api.txt
uvicorn api.main:app --reload

# Build VST3 plugin (optional)
cd vst3_plugin && mkdir -p build && cd build && cmake .. && cmake --build . && cmake --install .
```

## RL System Development
Primary focus. Agents are Ray actors coordinating via HGO (Hierarchical Goal Optimization).

### Adding an RL Agent
1. Create Ray actor in `src/agents/` using `@ray.remote` (see `eq_rl_agent.py` for TD3 pattern)
2. Implement `process_audio()`, `store_experience()`, `train_step()` using `AudioState` from `src/core/audio_ontology.py`
3. Register with HGO Coordinator in `maaps_nexus_main.py`
4. Target <10ms latency; profile with `tests/performance/`

### Key RL Components (`src/agents/`)
- `critic_agent.py`: Reward signal generator (build first)
- `eq_rl_agent.py`: 8-band EQ TD3 agent
- `dynamics_rl_agent.py`: Compression TD3 agent
- `hgo_coordinator.py`: Conflict resolution

## Legacy System Development
Secondary focus. Agents inherit from `BaseAgent` and communicate via message bus.

### Adding a Legacy Agent
1. Subclass `BaseAgent` from `src/core/base_agent.py`
2. Implement `setup()`, `handle_message(message)`, `teardown()`
3. Subscribe to topics in `setup()` and publish responses via `self.publish(...)`
4. Register in `src/orchestration/agent_coordinator.py → _create_core_agents()`

### Key Legacy Components
- `src/core/message_bus.py`: Pub-sub communication
- `src/core/base_agent.py`: Common agent lifecycle
- `src/orchestration/agent_coordinator.py`: Agent lifecycle management
- `api/main.py`: REST API server (FastAPI)

## Code Conventions
- **Imports**: stdlib → third-party → local (absolute: `from src.core.message_bus import MessageBus`)
- **Naming**: Classes=PascalCase, vars/functions=snake_case, constants=UPPER_SNAKE_CASE, private=_prefix
- **Type Hints**: Use for all signatures/attributes; `Optional[T]` for nullable; `dataclass` for simple data
- **Error Handling**: Specific exceptions; log with `logging`; try-except for I/O/network; custom domain exceptions
- **Documentation**: Triple-quoted docstrings; Args/Returns/Raises for public methods; sparse inline comments

## Performance & Safety
- **Latency Target**: <10ms for real-time audio processing (critical for RL system)
- **Parallelism**: Ray actors for RL system
- **Data Flow**: Minimize copying between agents
- **Security**: Never log secrets; validate inputs; use env vars for config; least privilege
- **State Management**: Enums for agent states; thread-safe patterns for shared state

## Important Files
- `src/nexus_system.py`: RL system orchestrator (Ray cluster, agent lifecycle, plugin IPC)
- `src/core/audio_ontology.py`: Shared attribute vocabulary (Clarity, Warmth, Punch, etc.)
- `src/daw_integration/streaming_plugin_wrapper.py`: VST3/CLAP shared-memory IPC bridge
- `src/daw_integration/ara_plugin_wrapper.py`: ARA2 host integration
- `src/infrastructure/ray_cluster.py`: Ray cluster initialization & resource management
- `src/utils/vertex_ai_integration.py`: Vertex AI integration
- `src/utils/llm_integration.py`: Multi-provider LLM (Anthropic/OpenAI/Ollama)

## Configuration
- Environment variables (copy `.env.example` to `.env`):
  - `VERTEX_PROJECT_ID`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional LLM integrations)
  - `AGENT_LOG_LEVEL`, `MESSAGE_BUS_MAX_QUEUE_SIZE`, `MAX_CPU_USAGE`, `MAX_MEMORY_USAGE`, `CACHE_MAX_SIZE_MB` (system tuning)