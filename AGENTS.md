# AGENTS.md

This file provides guidance for agentic coding agents working in the MAAPS Nexus repository.

## Build/Lint/Test Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/macOS

# Install dependencies
pip install -r requirements.txt
```

### Testing Commands
```bash
# Run all tests
pytest tests/

# Run single test file
pytest tests/test_system.py
python tests/test_system.py

# Run specific test class/method
pytest tests/test_system.py::TestSystemBasics
pytest tests/test_system.py::TestSystemBasics::test_system_creation

# Run live performance tests
pytest tests/test_live_effects_chain.py
pytest tests/test_live_looping.py
pytest tests/test_synchronization_clock.py

# Run integration tests with synthetic data
pytest tests/test_synthetic_integration.py

# Run adaptive latency protection tests
pytest tests/test_adaptive_latency.py

# Run tests with coverage report
pytest tests/ --cov=src --cov-report=html
```

### Code Quality Commands
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy src/
```

### Running the System
```bash
# RL System (Standalone test mode)
python maaps_nexus_main.py --mode test --test-duration 10.0

# RL System (VST3 DAW integration)
python maaps_nexus_main.py --mode vst3 --buffer-size 512 --sample-rate 44100

# Legacy System
python examples/basic_usage.py

# API server
uvicorn api.main:app --reload
```

## Code Style Guidelines

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports third
- Use absolute imports for local modules: `from src.core.message_bus import MessageBus`
- Group related imports together

### Type Hints
- Use type hints for all function signatures and class attributes
- Import from `typing` module: `Dict`, `List`, `Optional`, `Tuple`, `Union`
- Use `Optional[T]` for nullable values
- Use `dataclass` for simple data containers

### Naming Conventions
- **Classes**: PascalCase (e.g., `BaseAgent`, `CriticNetwork`)
- **Functions/Variables**: snake_case (e.g., `process_audio`, `satisfaction_score`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_LATENCY_MS`)
- **Private members**: prefix with underscore (e.g., `_state`, `_process_internal`)
- **Agent IDs**: lowercase with underscores (e.g., `critic_agent`, `eq_rl_agent`)

### Error Handling
- Use specific exception types rather than generic `Exception`
- Log errors with appropriate level using `logging` module
- Use try-except blocks for external dependencies (file I/O, network calls)
- Raise custom exceptions for domain-specific errors

### Documentation
- Use triple quotes for module and class docstrings
- Document all public methods with Args, Returns, Raises sections
- Use inline comments sparingly - prefer self-documenting code
- Include type hints in docstrings for clarity

### Agent Development Patterns
- **RL Agents**: Use `@ray.remote` decorator, inherit from base patterns in `eq_rl_agent.py`
- **Legacy Agents**: Inherit from `BaseAgent`, implement `setup()`, `handle_message()`, `teardown()`
- **State Management**: Use enums for agent states, thread-safe patterns for shared state
- **Communication**: Use message bus topics with wildcards, follow request-response pattern

### Performance Constraints
- Target <10ms latency for real-time audio processing
- Use Ray actors for parallel processing in RL system
- Minimize data copying between agents
- Profile with `tests/performance/` tools

### Testing Patterns
- Use `unittest.TestCase` for test classes
- Implement `setUpClass`/`tearDownClass` for expensive setup
- Use synthetic data generators from `tests/utils/`
- Test both success and failure scenarios
- Include integration tests for multi-agent workflows

### Security Best Practices
- Never log secrets, API keys, or sensitive data
- Use environment variables for configuration
- Validate all external inputs
- Follow principle of least privilege

### File Organization
- Keep related functionality in same module
- Use `__init__.py` to control imports
- Separate public API from internal implementation
- Follow existing directory structure patterns

## Architecture Notes

### RL System Components
- **Critic Agent**: Must be built first - provides reward signals
- **EQ/Dynamics Agents**: Use TD3 algorithm, compete via HGO
- **HGO Coordinator**: Mediates conflicts between agents
- **Ray Cluster**: Distributed computing foundation

### Legacy System Components
- **Message Bus**: Pub-sub communication with priority queuing
- **Base Agent**: Common lifecycle and communication patterns
- **Workflow Engine**: Multi-step orchestration

### Integration Points
- VST3 plugin uses shared memory for <10ms latency
- Vertex AI integration via `src/utils/vertex_ai_integration.py`
- API layer provides HTTP endpoints for legacy system

Remember: The RL system is the primary focus, legacy system is secondary.