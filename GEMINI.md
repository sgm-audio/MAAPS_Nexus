# MAAPS Nexus (Multi-Agent Audio Processing System)

## Project Overview

MAAPS Nexus is a comprehensive, production-ready system designed for advanced audio processing, AI-powered music generation, and intelligent project management. It employs a sophisticated agent-based architecture to orchestrate complex audio workflows, from noise reduction and restoration to creative content generation and metadata management.

## Tech Stack

*   **Language:** Python 3.9+
*   **Core Libraries:** `numpy`, `scipy`, `librosa`, `soundfile`, `pretty_midi`
*   **AI/ML Frameworks:** PyTorch (`torch`, `torchaudio`), Transformers (`transformers`)
*   **Architecture:**
    *   **Message Bus:** Publish-Subscribe pattern for inter-agent communication.
    *   **Agents:** Autonomous units for specific tasks (Enhancement, Generation, Optimization, Metadata).
    *   **Orchestration:** Workflow engine for managing dependencies and complex pipelines.
*   **GUI:** PySide6 (Qt for Python)
*   **Infrastructure:** Docker, Kubernetes (k8s), Google Cloud Vertex AI (for offloading heavy ML tasks).
*   **DAW Integration:** Reaper (via `reapy` and custom scripts).

## Project Structure

### Core Components (`src/`)
*   `src/system.py`: Main entry point for the system.
*   `src/core/`: Core infrastructure including `BaseAgent`, `MessageBus`, and message definitions.
*   `src/agents/`: Implementation of specific agents (e.g., `AudioEnhancementAgent`, `ContentGenerationAgent`).
*   `src/orchestration/`: Workflow engine and agent coordination logic.

### AI & Neural Stack (`neural_stack/`)
*   **"Titan" Stack:** High-fidelity neural audio processing environment.
*   **Components:**
    *   `titan_split.py`: Source separation using Meta's HT Demucs.
    *   `hallucinate_texture.py`: Texture generation using MusicGen.
    *   `auto_master.py`: Automated mastering using Spotify's `pedalboard`.
*   **Setup:** Requires a dedicated Conda environment (see `neural_stack/README.md`).

### SunoHydra (`SunoHydra/`)
*   A specialized module for translating raw technical audio tags into evocative, "human-readable" prompts for music generation models.

### User Interface (`gui/`)
*   A professional Windows GUI application built with PySide6.
*   **Entry Point:** `gui/main.py`.
*   **Features:** Dashboard, Effects Chain, Live Looping, Sync & Automation.

### API (`api/`)
*   Exposes system functionality via REST/WebSockets (likely FastAPI) for external integrations.

### Testing (`tests/`)
*   Comprehensive test suite using `pytest`.
*   Run with: `pytest tests/`

## Setup & Usage

### 1. Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# Install GUI dependencies
pip install -r requirements-gui.txt
```

### 2. Neural Stack Setup (Optional but Recommended)

For advanced AI features, set up the dedicated environment:

```bash
cd neural_stack
setup_neural_env.bat
```

### 3. Running the System

**Basic CLI/Script Usage:**
```python
from src.system import create_system
system = create_system()
system.start()
# ... perform operations ...
system.stop()
```

**Running the GUI:**
```bash
python gui/main.py
```

**Running Examples:**
```bash
python examples/basic_usage.py
```

## Development Conventions

*   **Agent Architecture:** All new functionality should be implemented as an Agent (`src/agents/`) inheriting from `BaseAgent`.
*   **Communication:** Agents must communicate *only* via the Message Bus (`self.subscribe`, `self.publish`).
*   **Configuration:** Use `config.json` for system-wide and agent-specific settings.
*   **Testing:** Write unit tests for new agents in `tests/`. Use mocks for heavy ML models during testing.

## Key Documentation Files

*   `README.md`: Main project overview and quick start.
*   `neural_stack/README.md`: Detailed instructions for the high-fidelity AI stack.
*   `GUI_PLAN.md`: Architecture and roadmap for the GUI.
*   `AGENTS.md`: Details on available agents and their capabilities.
*   `SunoHydra/prompts.md`: System prompt logic for the tag translator.
