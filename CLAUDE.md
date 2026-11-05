# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**Sonic Mind Forge** - A comprehensive monorepo containing multiple interconnected projects for audio production, AI-powered creativity, and cognitive creative systems. This is a multi-project repository with distinct applications that can be developed and deployed independently or as an integrated platform.

### Project Structure

```
X:\Sonic Mind\
├── src/                          # MAAPS - Multi-Agent Audio Processing System (Python)
├── api/                          # MAAPS REST API (FastAPI)
├── frontend/maaps-ui/            # MAAPS Web UI (React/Vite)
├── sonic-mind-forge-platform/    # Main marketing & platform hub (Next.js)
├── mindwave-ai-complete/         # AI mixing application monorepo (Node.js + Python)
├── ai-audio-mix-partner/         # AI audio mixing partner (React + Gemini AI)
├── Apex/                         # APEX DAW - Professional audio interface (Python/PyQt6)
├── MarkerMatic/                  # Console/DAW marker synchronization (Python)
├── Social Content Engine/        # Social media content generation
├── Long-Short-Content-Engine/    # Video content repurposing
├── wordpress/                    # WordPress installation
├── examples/                     # Usage examples
├── tests/                        # Test suites
└── architecture/                 # Architecture documentation
```

---

# 1. MAAPS - Multi-Agent Audio Processing System

The core Python-based distributed system for advanced audio processing, AI-powered music generation, and intelligent DAW integration.

## Development Commands

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install API dependencies
pip install -r requirements-api.txt

# Install performance testing dependencies
pip install -r requirements-performance.txt
```

### Running the System
```bash
# Start the complete system (development mode)
python -m src.system

# Run basic usage examples
python examples/basic_usage.py

# Run live performance demo
python examples/live_performance_demo.py

# Run transcription integration demo
python examples/transcription_integration_demo.py
```

### Running the API
```bash
# Development server with hot reload
uvicorn api.main:app --reload

# Production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Access documentation
# Interactive docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
python tests/test_system.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run performance tests
python tests/performance/load_test.py
python tests/performance/benchmark.py
python tests/performance/stress_test.py
```

### Development Tools
```bash
# Format code
black src/ tests/ api/

# Lint code
flake8 src/ tests/ api/

# Type checking
mypy src/ tests/ api/
```

## Architecture

### Core Design Pattern
MAAPS uses a **distributed multi-agent architecture** with:
- **Message Bus**: Thread-safe pub-sub message bus for asynchronous agent communication
- **Agent Registry**: Centralized agent lifecycle management
- **Event-Driven**: All inter-agent communication via message topics (no direct dependencies)
- **Workflow Engine**: Orchestrates complex multi-step processing pipelines

### Agent Communication Flow
```
DAW Control → Message Bus → Audio Analysis → Parameter Optimization → VST Bridge
                  ↓                              ↓
          System Orchestrator              Logging Monitor
```

Agents communicate ONLY through the message bus using topic subscriptions. Never add direct agent-to-agent method calls.

### Core Components

#### 1. Message Bus (`src/core/message_bus.py`)
- Singleton pattern with thread-safe operations
- Priority queuing (HIGH, MEDIUM, LOW)
- Wildcard topic subscriptions (e.g., `"system.*"`)
- Request-response pattern support
- Dead letter queue for failed messages
- Metrics collection for monitoring

#### 2. Base Agent (`src/core/base_agent.py`)
All agents inherit from `BaseAgent` and must implement:
- `setup()`: Initialize agent, subscribe to topics
- `handle_message(message)`: Process incoming messages
- `teardown()`: Cleanup on shutdown

#### 3. Message Types (`src/core/message_types.py`)
Complete data structures and message types. Use existing dataclasses; don't create ad-hoc dictionaries for structured data.

#### 4. Agent Coordinator (`src/orchestration/agent_coordinator.py`)
- Creates and manages all agents
- Handles system initialization and shutdown
- Provides health checks and agent status

#### 5. Workflow Engine (`src/orchestration/workflow_engine.py`)
- Coordinates multi-step workflows with dependencies
- Automatic retries and error handling
- Progress tracking and result aggregation

### Agent Responsibilities

**Core Agents** (`src/agents/`):
- `audio_enhancement_agent.py`: Noise reduction, click removal, clipping restoration
- `content_generation_agent.py`: AI melody, harmony, drum, bass generation
- `performance_optimization_agent.py`: Resource monitoring, task scheduling, caching
- `metadata_management_agent.py`: Metadata extraction, search, project versioning

**Live Performance Agents** (`src/agents/live/`):
- `realtime_audio_io_agent.py`: Low-latency audio I/O
- `midi_control_agent.py`: MIDI event handling
- `synchronization_clock_agent.py`: Timing synchronization
- `performance_automation_agent.py`: Real-time parameter automation
- `live_mixing_dynamics_agent.py`: Dynamic audio mixing
- `live_effects_chain_agent.py`: Real-time effects processing
- `live_looping_agent.py`: Loop recording and playback

**Transcription Agents** (`src/agents/transcription/`):
- `musical_analysis_agent.py`: Musical structure analysis
- `audio_to_midi_agent.py`: Audio to MIDI conversion
- `tablature_generation_agent.py`: Guitar/bass tab generation
- `harmonic_analysis_agent.py`: Chord and key detection
- `rhythm_analysis_agent.py`: Tempo and beat analysis
- `multitrack_coordinator_agent.py`: Multi-track coordination

## Message Topics

### Topic Naming Convention
Topics use dot notation: `<domain>.<entity>.<action>[.<qualifier>]`

Examples:
- `audio.input.received`
- `audio.features.extracted`
- `optimization.suggestion.generated`
- `system.error.critical`
- `log.metrics.performance`

### Subscription Patterns
```python
# Exact topic
self.subscribe("audio.input.received")

# Wildcard (all system topics)
self.subscribe("system.*")

# Multiple levels
self.subscribe("audio.*.request")
```

### Message Priority
- **HIGH**: Errors, transport control, critical state changes (< 5ms latency target)
- **MEDIUM**: Analysis results, optimization suggestions (< 10ms latency target)
- **LOW**: Metrics, heartbeats, info logs (< 50ms latency target)

## Adding New Agents

1. **Create Agent Class** in `src/agents/`:
```python
from src.core import BaseAgent, Message

class MyNewAgent(BaseAgent):
    def setup(self):
        # Subscribe to topics
        self.subscribe("my.topic")
        self.log("INFO", "Agent initialized")

    def handle_message(self, message: Message):
        # Process message based on topic
        if message.topic == "my.topic":
            # Handle message
            self.publish("my.result", {"data": result})

    def teardown(self):
        # Cleanup resources
        pass
```

2. **Register in Coordinator** (`src/orchestration/agent_coordinator.py`):
```python
from ..agents import MyNewAgent

def _create_core_agents(self):
    agents_to_create = [
        # ... existing agents
        MyNewAgent("my-agent-001", "My New Agent")
    ]
```

3. **Export in `__init__.py`**:
```python
from .my_new_agent import MyNewAgent
__all__ = ['MyNewAgent', ...]
```

4. **Document Topics**: Update `architecture/COMMUNICATION_ARCHITECTURE.md` with new topics

## API Structure

The REST API (`api/`) wraps the agent system:
- `main.py`: FastAPI application entry point with system initialization
- `routers/`: API endpoint implementations
  - `audio.py`: Audio processing endpoints
  - `metadata.py`: Metadata operations
  - `system.py`: System health and metrics
  - `effects.py`: Effects processing
  - `looping.py`: Looping controls
  - `sync.py`: Synchronization
  - `automation.py`: Automation controls
- `dependencies.py`: Authentication middleware (`get_current_user`, `get_optional_user`)
- `auth.py`: JWT authentication (login, verify)
- `websocket.py`: WebSocket support for real-time updates

### System Initialization Pattern

The API uses a dependency injection pattern to ensure the system is initialized:

```python
# api/main.py provides get_system_dep() dependency
from api.main import get_system_dep

@router.get("/endpoint")
async def my_endpoint(sys=Depends(get_system_dep)):
    # sys is guaranteed to be initialized MultiAgentSystem
    result = sys.some_method()
    return result
```

The system is initialized on FastAPI startup event and validated before each request using `get_system_dep()`. This prevents NoneType errors from uninitialized system access.

### Authentication Patterns

**Required Authentication:**
```python
from api.dependencies import get_current_user

@router.post("/admin/action")
async def admin_action(username: str = Depends(get_current_user)):
    # Returns 401 if no valid JWT token
    # username contains authenticated user
```

**Optional Authentication:**
```python
from api.dependencies import get_optional_user

@router.post("/public/action")
async def public_action(username: Optional[str] = Depends(get_optional_user)):
    # Works with or without token
    # username is None if not authenticated
    if username:
        # Enhanced features for authenticated users
    else:
        # Basic features for public access
```

## Testing Strategy

### Unit Tests
Test individual agent logic in isolation by mocking the message bus:
```python
from unittest.mock import MagicMock
from src.agents.my_agent import MyAgent

agent = MyAgent("test-001", "Test Agent")
agent.message_bus = MagicMock()
agent.setup()
agent.handle_message(test_message)
```

### Integration Tests
Test message flow between agents using the full system:
```python
from src.system import create_system

system = create_system()
system.start()
result = system.enhance_audio(audio_data, sample_rate)
system.stop()
```

### Performance Tests
Located in `tests/performance/`:
- `load_test.py`: Message throughput testing
- `benchmark.py`: Agent performance benchmarks
- `stress_test.py`: Resource usage under load

## Important Architectural Patterns

### 1. Loose Coupling
Agents have ZERO direct dependencies on each other. All communication is via message bus. When adding features, never import one agent into another.

### 2. Message-Based Communication
```python
# CORRECT: Publish message and subscribe to response
self.publish("optimization.request", {"features": features})

# INCORRECT: Direct method call
other_agent.optimize_parameters(features)  # ❌ Never do this
```

### 3. Asynchronous Processing
Agents don't block waiting for responses. Use callbacks or message subscriptions:
```python
def handle_message(self, message: Message):
    if message.topic == "request":
        # Process asynchronously
        result = self.process(message.payload)
        self.publish("response", result)
```

### 4. Error Handling
Always wrap message handling in try-except:
```python
def handle_message(self, message: Message):
    try:
        # Process message
        pass
    except Exception as e:
        self.log("ERROR", f"Failed to process: {e}")
        self.publish("system.error.critical", {
            "agent_id": self.agent_id,
            "error": str(e)
        })
```

## Configuration

### Environment Variables
- Development: `.env`
- Production: `.env.production` (copy from `.env.production.example`)

**CRITICAL:** Never commit `.env` files to git. Add to `.gitignore` immediately.

Key settings:
- `JWT_SECRET`: Secret key for JWT token signing (REQUIRED for authentication)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 60)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)
- `METADATA_DB_PATH`: Path to metadata SQLite database
- `ENVIRONMENT`: `development` or `production`
- `LOG_LEVEL`: `debug`, `info`, `warning`, `error`
- `WORKERS`: Number of API workers

**Generate secure JWT secret for production:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Agent Configuration
`config.json` contains agent-specific settings:
- System monitoring intervals
- Audio processing defaults
- ML model parameters
- Resource limits

**Note:** Database paths in `config.json` support environment variable substitution: `${METADATA_DB_PATH:./metadata.db}`

## Performance Targets

### Latency
- Message dispatch: < 1ms
- Agent-to-agent: < 10ms
- Audio processing pipeline: < 100ms
- Database operations: < 50ms

### Throughput
- Message bus: 10,000+ messages/second
- Audio buffer processing: Real-time (93 buffers/sec @ 48kHz)

### Resource Usage
- Memory: < 500MB per agent
- CPU: < 20% per agent under normal load

If implementing performance-sensitive features, profile before and after.

## Production Deployment

### Docker
```bash
# Build production image
docker build -f Dockerfile.production -t maaps:latest .

# Run with docker-compose
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes
Deploy using manifests in `k8s/`:
```bash
kubectl apply -f k8s/
```

Includes: deployment, service, configmap, PVC, HPA, ingress

### Systemd Service
```bash
# Copy service file
sudo cp maaps.service /etc/systemd/system/

# Enable and start
sudo systemctl enable maaps
sudo systemctl start maaps
```

See `PRODUCTION_DEPLOYMENT.md` for complete deployment guide.

## MAAPS Key Dependencies

- **numpy**: Audio buffer manipulation
- **librosa**: Audio feature extraction and analysis
- **scipy**: Scientific computing for audio processing
- **pretty-midi**: MIDI manipulation
- **music21**: Music theory and analysis
- **psutil**: System resource monitoring
- **FastAPI**: REST API framework
- **uvicorn/gunicorn**: ASGI servers (uvicorn for dev, gunicorn for production)
- **pyjwt**: JWT token generation and verification
- **passlib[bcrypt]**: Password hashing (for future user authentication)

## Critical Security Notes

### 🚨 KNOWN ISSUES - FIX BEFORE PRODUCTION

1. **Authentication is Placeholder** (`api/auth.py` line 94)
   - Current implementation accepts ANY username/password
   - TODO comment explicitly states this is for demo only
   - **MUST implement real user database before production**
   - See `AUTHENTICATION_GUIDE.md` for implementation details

2. **Git Repository Health**
   - Missing `.gitignore` file
   - Create `.gitignore` with: `.env`, `*.db`, `__pycache__/`, `node_modules/`
   - Never commit secrets, databases, or build artifacts

3. **Input Validation**
   - Pydantic models validate types but some lack bounds checking
   - Audio endpoints have `MAX_AUDIO_SAMPLES = 2_000_000` limit
   - Always validate array bounds to prevent memory exhaustion

See `COMPREHENSIVE_EVALUATION_REPORT.md` for complete security audit and remediation plan.

---

# 2. Sonic Mind Forge Platform

Next.js 15 marketing website and platform hub integrating APEX DAW, MAAPS Control Center, and MindWave AI.

## Development Commands

```bash
cd sonic-mind-forge-platform

# Install dependencies
npm install

# Run development server
npm run dev
# Opens at http://localhost:3000

# Build for production
npm run build

# Run production build
npm run start

# Lint
npm run lint
```

## Project Structure

```
sonic-mind-forge-platform/
├── app/                    # Next.js app directory (App Router)
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── platform/          # Platform tool pages
│   ├── services/          # Service detail pages
│   ├── technology/        # Technology stack pages
│   └── globals.css        # Global styles
├── components/
│   ├── layout/            # Header, Footer, MobileMenu
│   ├── home/              # Home page sections
│   ├── platform/          # Platform tool components
│   ├── ui/                # Reusable UI components
│   └── interactive/       # Interactive components (neural network canvas)
├── lib/                   # Utility functions
├── types/                 # TypeScript type definitions
└── public/                # Static assets
```

## Technologies

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom dark theme
- **Features**: Server Components, Client Components, Glass morphism UI

## Design System

Custom dark theme with:
- Background: #0f172a (dark blue)
- Glass panels: rgba(30, 41, 59, 0.7) with backdrop blur
- Accents: Cyan (#38bdf8), Violet (#c084fc), Pink (#f472b6)
- Typography: Inter (body), Space Grotesk (headings)

## Key Features

- Animated neural network particle background
- Glass morphism UI design
- Responsive mobile navigation
- Tool integration pages (APEX DAW, MAAPS, MindWave)
- Service detail pages (Creative Systems, Automation, Education)
- Technology documentation (Hydra Protocol)

## Integration with Other Projects

The platform provides integration pages at:
- `/platform/apex` - APEX DAW integration
- `/platform/maaps` - MAAPS Control Center integration
- `/platform/mindwave` - MindWave AI Dashboard integration

Each integration page offers three modes:
- **Embedded View** - Tool runs in iframe
- **New Window** - Tool opens in separate tab
- **Setup Info** - Integration instructions

See `sonic-mind-forge-platform/INTEGRATION_GUIDE.md` for setup details.

---

# 3. MindWave AI Complete

Monorepo for AI-powered audio mixing applications with Node.js backend, Python AI service, and Next.js frontend.

## Development Commands

```bash
cd mindwave-ai-complete

# Copy environment files (one-time setup)
cp apps/api/.env.example apps/api/.env
cp services/ai-agent/.env.example services/ai-agent/.env
cp apps/web/.env.local.example apps/web/.env.local

# Edit .env files to add GEMINI_API_KEY and other secrets

# Run all services with Docker
docker compose up --build
```

Services available at:
- API: http://localhost:3000
- AI Agent: http://localhost:8000
- Web UI: http://localhost:3001
- MongoDB: localhost:27017

### API Development (apps/api)

```bash
cd apps/api

# Install dependencies
npm ci

# Run development mode (auto-reload)
npm run dev

# Build TypeScript
npm run build

# Run production build
npm start

# Run tests
npm test

# Run single test
NODE_ENV=test npx mocha -r ts-node/register tests/auth.spec.ts
```

### AI Agent Development (services/ai-agent)

```bash
cd services/ai-agent

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Web Development (apps/web)

```bash
cd apps/web

# Install dependencies
npm ci

# Run development server
npm run dev

# Build for production
npm run build

# Run production server
npm start
```

## Architecture

### Authentication Flow
1. User signs up via POST `/api/v1/auth/signup` → creates user in MongoDB `users` collection
2. Returns JWT token signed with `JWT_SECRET`
3. Protected routes require `Authorization: Bearer <token>` header
4. JWT middleware verifies token and attaches `req.user`

### Agent Execution Flow
1. Frontend calls POST `/api/v1/agents/:id/run` with `projectId`
2. API forwards request to AI agent service at `/run` endpoint
3. AI agent calls Google Gemini API with configurable prompts
4. Response logged to MongoDB `agent_logs` collection
5. Result returned to frontend

### MongoDB Collections
- **users**: `{ _id, email, passwordHash, name, createdAt }`
- **agents**: `{ _id, ownerId, name, type, config, createdAt }`
- **agent_logs**: `{ agentId, projectId, input, output, status, durationMs, createdAt }`

### Key Environment Variables

**apps/api/.env:**
- `PORT` - API server port (default: 3000)
- `MONGO_URI` - MongoDB connection string
- `AI_SERVICE_URL` - URL of AI agent service
- `JWT_SECRET` - Secret for signing JWT tokens

**services/ai-agent/.env:**
- `GEMINI_API_KEY` - Google Gemini API key (required)

## Testing

```bash
# Run all tests (requires MongoDB running)
cd apps/api && npm test

# Tests expect MongoDB at localhost:27017 or MONGO_URI env var
```

---

# 4. AI Audio Mix Partner

React + Vite application for AI-powered audio mixing advice using Google Gemini.

## Development Commands

```bash
cd ai-audio-mix-partner

# Install dependencies
npm install

# Run development server
npm run dev
# Opens at http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

## Technologies

- **Framework**: Vite + React 19
- **Language**: TypeScript
- **AI**: Google Gemini API (`@google/genai`)

## Key Features

- Real-time AI mixing advice
- Integration with Google Gemini 2.5 Pro
- Modern React 19 features
- Fast HMR with Vite

---

# 5. APEX DAW

Professional audio interface control GUI built with Python 3.12 and PyQt6.

## Development Commands

```bash
cd Apex

# Install dependencies
pip install PyQt6 numpy --break-system-packages

# Run application
python3 apex_pro_gui.py

# Or make executable and run
chmod +x apex_pro_gui.py
./apex_pro_gui.py
```

## Features

- 8 configurable input channels (XLR, TRS, Digital, USB)
- Real-time signal metering with professional ballistics
- 8 professional channel strips with VU meters
- Record/Solo/Mute controls
- 6 output routing options
- Professional color-coded metering (green → yellow → orange → red)

## Technical Specifications

### Audio Metering Ballistics
- **Attack Time:** 3ms (professional standard)
- **Release Time:** 300ms (smooth decay)
- **Peak Hold:** 2 seconds
- **Update Rate:** 30 Hz

### Performance
- 30 FPS rendering for smooth animations
- Efficient painter operations
- Minimal CPU overhead
- Responsive UI with <16ms frame time

## Architecture

**Core Components:**
- `AudioMeter`: Custom widget with professional ballistics
- `IOChannel`: Input/Output channel representation
- `ChannelStrip`: Complete mixer channel implementation
- `ApexProGUI`: Main application window

---

# 6. MarkerMatic

Python tool for automating cueing and marker placement between consoles and DAWs. Supports 8 console families and 5 DAWs.

## Development Commands

```bash
cd MarkerMatic

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run application
python main.py
```

## Supported Platforms

**Consoles:**
- DiGiCo
- Allen & Heath
- Yamaha
- Midas
- Soundcraft
- Behringer X32
- And more...

**DAWs:**
- Reaper
- Pro Tools
- Studio One
- Nuendo
- Logic Pro

See [MarkerMatic website](https://markermatic.com/) for complete documentation.

---

# 7. MAAPS Frontend (React/Vite)

Web UI for MAAPS Control Center.

## Development Commands

```bash
cd frontend/maaps-ui

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

# 8. Other Projects

### Social Content Engine
Located in `Social Content Engine/` - Social media content generation system.

### Long-Short-Content-Engine
Located in `Long-Short-Content-Engine/` - Video content repurposing for social platforms.

### WordPress
Located in `wordpress/` - WordPress installation with YOOtheme Pro.

---

# Common Workflows

## Working Across Projects

### Starting Full Platform
```bash
# Terminal 1: Start MAAPS backend
cd X:\Sonic Mind
python -m src.system

# Terminal 2: Start MAAPS API
uvicorn api.main:app --reload

# Terminal 3: Start Platform website
cd sonic-mind-forge-platform
npm run dev

# Terminal 4: Start MindWave (if needed)
cd mindwave-ai-complete
docker compose up
```

### Development Best Practices

1. **MAAPS Development**: Follow message bus patterns, never direct agent coupling
2. **Frontend Development**: Use TypeScript, follow Next.js App Router patterns
3. **API Development**: Use FastAPI for Python, Express for Node.js
4. **Testing**: Write tests for all new features before merging
5. **Documentation**: Update relevant docs when adding features

## Documentation References

### MAAPS Documentation
- `README.md`: Project overview and basic usage
- `QUICK_START.md`: Agent implementation guide
- `architecture/README.md`: Complete architecture overview
- `architecture/COMMUNICATION_ARCHITECTURE.md`: Message bus and topics
- `architecture/DATA_FLOW_ARCHITECTURE.md`: Data structures and flows
- `API_GUIDE.md`: REST API reference
- `PRODUCTION_DEPLOYMENT.md`: Production deployment guide
- `LIVE_PERFORMANCE_AGENTS.md`: Live performance system guide
- `MUSICAL_ANALYSIS_TRANSCRIPTION.md`: Transcription system guide

### Platform Documentation
- `sonic-mind-forge-platform/README.md`: Platform overview
- `sonic-mind-forge-platform/INTEGRATION_GUIDE.md`: Integration instructions

### MindWave Documentation
- `mindwave-ai-complete/CLAUDE.md`: MindWave-specific guidance

### Other Documentation
- `Apex/README_APEX.md`: APEX DAW documentation
- `MarkerMatic/README.md`: MarkerMatic usage guide
- Various `*_PLAN.md` files: Product roadmaps and specifications

---

# Environment Setup

## Required Tools

- **Python 3.12+**: For MAAPS, APEX, MarkerMatic
- **Node.js 18+**: For Platform, MindWave, frontends
- **MongoDB**: For MindWave backend
- **Docker**: For containerized deployments
- **Git**: Version control

## Environment Files

Create the following `.env` files from their `.example` templates:
- `.env` (MAAPS development)
- `.env.production` (MAAPS production)
- `mindwave-ai-complete/apps/api/.env`
- `mindwave-ai-complete/services/ai-agent/.env`
- `mindwave-ai-complete/apps/web/.env.local`

---

# Git Workflow

## Current Status
Working directory: `X:\Sonic Mind`
Main branch: `main`

## Common Git Commands

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/your-feature-name

# Stage changes
git add .

# Commit changes
git commit -m "feat: your feature description"

# Push to remote
git push origin feature/your-feature-name

# Pull latest changes
git pull origin main
```

### 🚨 CRITICAL: Git Repository Requires Immediate Attention

**Current State:**
- Only 1 commit in entire repository ("Initial commit: MAAPS Nexus project")
- 100+ untracked files (including 176MB node_modules in Apex/)
- Modified files: `.env` (secrets), `metadata.db` (database)
- **No `.gitignore` file**

**Immediate Actions Required:**

1. **Create `.gitignore`** (CRITICAL - prevents secret commits):
```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.mypy_cache/
dist/
build/

# Environment & Secrets
.env
.env.local
.env.*.local

# Databases
*.db
*.sqlite
*.sqlite3

# Node
node_modules/
dist/
.next/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Project Specific
logs/
data/
metadata.db
.claude/settings.local.json
EOF
```

2. **Never add these to git:**
   - `.env` files (contain secrets)
   - `*.db` files (databases)
   - `node_modules/` (dependencies)
   - Build artifacts

3. **Use atomic commits going forward:**
```bash
# Good commit messages
git commit -m "feat(api): add health check endpoint"
git commit -m "fix(auth): prevent NoneType error in system init"
git commit -m "docs: update API authentication guide"
```

---

# Project Relationships

```
Sonic Mind Forge Platform (Marketing Hub)
    ├── Links to → MAAPS Control Center
    ├── Links to → APEX DAW
    └── Links to → MindWave AI Dashboard

MAAPS (Core Audio Processing)
    ├── REST API → Used by MAAPS UI
    └── Message Bus → Agent communication

MindWave AI (AI Mixing)
    ├── Backend API → Manages users/agents
    └── AI Service → Gemini integration

AI Audio Mix Partner
    └── Standalone Gemini mixing advisor

APEX DAW
    └── Standalone audio interface GUI

MarkerMatic
    └── Standalone console/DAW sync tool
```

Each project can be developed and deployed independently, but they integrate through the Sonic Mind Forge Platform hub.

---

# Recent Improvements & Fixes (December 2025)

## System Initialization Fix
**File:** `api/main.py`
- Added `_ensure_system_ready()` function to validate system state
- Added `get_system_dep()` FastAPI dependency
- All endpoints now use `sys=Depends(get_system_dep)` to guarantee initialized system
- Prevents NoneType errors from uninitialized system access

## Authentication Implementation
**Files:** `api/auth.py`, `api/dependencies.py`, `api/main.py`
- JWT-based authentication with environment-configurable secrets
- Both required and optional authentication patterns
- Protected endpoints (`/system/restart`) require valid JWT token
- Optional auth endpoints (`/audio/*`, `/music/*`) work with or without token
- **WARNING:** Current auth accepts any credentials - placeholder for real user database

## Input Validation
**File:** `api/main.py`
- Added `MAX_AUDIO_SAMPLES = 2_000_000` limit (~45 seconds @ 44.1kHz)
- Pydantic `model_validate` override checks audio_data length
- Prevents memory exhaustion from oversized audio buffers

## API Documentation
**Files Created:**
- `API_IMPLEMENTATION_COMPLETE.md` - Complete API implementation guide
- `AUTHENTICATION_GUIDE.md` - Authentication usage and integration
- `AUTHENTICATION_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `COMPREHENSIVE_EVALUATION_REPORT.md` - Full security audit and roadmap

---

# Troubleshooting

## API Won't Start

**Problem:** `uvicorn api.main:app` fails with import errors

**Solution:**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt
pip install -r requirements-api.txt

# Check Python version
python --version  # Should be 3.11+

# Run from project root
cd "X:\Sonic Mind"
uvicorn api.main:app --reload
```

## System Initialization Errors

**Problem:** API returns 503 "System not initialized yet"

**Cause:** System initialization happens in startup event, may take 2-3 seconds

**Solution:**
- Wait a few seconds after API starts before making requests
- Check logs for initialization errors
- Verify all agent dependencies are installed

## Authentication Fails

**Problem:** Valid JWT token returns 401 Unauthorized

**Causes:**
1. `JWT_SECRET` environment variable not set
2. Token expired (default: 60 minutes)
3. Token generated with different secret

**Solution:**
```bash
# Check .env has JWT_SECRET
cat .env | grep JWT_SECRET

# Generate new token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Verify token
curl http://localhost:8000/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Errors

**Problem:** `metadata.db` file locked or corrupted

**Solution:**
```bash
# Backup existing database
cp metadata.db metadata.db.backup

# Remove and let system recreate
rm metadata.db

# Restart API - will create new database
uvicorn api.main:app --reload
```

## Audio Processing Fails

**Problem:** Audio enhancement returns 500 error

**Causes:**
1. Audio data exceeds `MAX_AUDIO_SAMPLES` limit
2. Invalid sample rate (must be 8000-192000 Hz)
3. Audio samples outside [-1.0, 1.0] range

**Solution:**
- Verify audio_data length < 2,000,000 samples
- Normalize audio to [-1.0, 1.0] range
- Use valid sample rate (44100, 48000, etc.)

## CORS Errors in Browser

**Problem:** Browser shows CORS policy error

**Solution:**
```bash
# Add your frontend URL to .env
echo "ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173" >> .env

# Restart API
uvicorn api.main:app --reload
```

## Docker Health Checks Fail

**Problem:** Containers marked unhealthy

**Cause:** Health check endpoint returns errors

**Solution:**
```bash
# Test health endpoint manually
curl http://localhost:8000/health

# Check system initialization
curl http://localhost:8000/metrics

# View container logs
docker logs <container_id>
```

---

# Quick Reference

## Essential Files

| File | Purpose |
|------|---------|
| `src/system.py` | MAAPS system entry point |
| `api/main.py` | FastAPI application with routes |
| `api/auth.py` | JWT authentication (placeholder) |
| `api/dependencies.py` | Auth middleware |
| `.env` | Development environment config |
| `.env.production.example` | Production config template |
| `config.json` | Agent configuration |
| `COMPREHENSIVE_EVALUATION_REPORT.md` | Security audit & roadmap |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `System not initialized` | Startup event not complete | Wait 2-3 seconds |
| `401 Unauthorized` | Missing/invalid JWT token | Regenerate token |
| `503 Service Unavailable` | System failed to start | Check logs, verify dependencies |
| `422 Unprocessable Entity` | Invalid request data | Check Pydantic validation errors |
| `audio_data too large` | > 2M samples | Reduce audio length |

## Performance Monitoring

```bash
# System health
curl http://localhost:8000/health

# Resource metrics
curl http://localhost:8000/metrics

# Agent status
curl http://localhost:8000/agents

# API documentation
open http://localhost:8000/docs
```
