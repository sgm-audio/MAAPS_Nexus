# Test Plan for MAAPS Nexus

## 1. Test Strategy

### 1.1 Testing Levels
- **Unit Tests**: Validate individual components (agents, ontology, message bus, etc.) in isolation
- **Integration Tests**: Verify interactions between components (RL pipeline, message bus, API)
- **End-to-End (E2E) Tests**: Validate complete user workflows (standalone test, DAW integration, API usage)
- **Performance Tests**: Verify non-functional requirements (latency, throughput, resource usage)
- **Security Tests**: Validate protection against common vulnerabilities

### 1.2 Tooling
- **Unit/Integration**: PyTest with mocking (unittest.mock)
- **E2E**: PyTest for API, custom audio processing scripts for DAW integration
- **Performance**: Custom benchmarks using time.perf_counter, memory_profiler
- **Security**: Bandit for static analysis, safety for dependency scanning
- **Coverage**: pytest-cov for coverage reporting
- **Continuous Integration**: GitHub Actions

### 1.3 Test Execution
- Run unit tests on every commit: `pytest tests/unit/ -xvs`
- Run full test suite nightly: `pytest tests/ --cov=src --cov-report=html`
- Performance tests run weekly or on release branches
- Security scans on every pull request

## 2. Traceability Matrix

| Requirement ID | Description | Test Type | Test Case ID |
|----------------|-------------|-----------|--------------|
| REQ-RL-01 | Initialize Ray cluster with configurable resources | Unit | TC_RL_CLUSTER_001 |
| REQ-RL-02 | Initialize audio ontology | Unit | TC_RL_ONTOLOGY_001 |
| REQ-RL-03 | Initialize Critic, EQ, Dynamics, HGO Coordinator agents | Unit | TC_RL_AGENTS_INIT_001 |
| REQ-RL-04 | Support plugin modes: vst3, clap, ara, none | Integration | TC_RL_PLUGIN_MODES_001 |
| REQ-RL-05 | Standalone test mode processes audio for specified duration | Integration | TC_RL_STANDALONE_001 |
| REQ-RL-06 | Process audio frames through multi-agent pipeline | Integration | TC_RL_PIPELINE_001 |
| REQ-RL-07 | Maintain state using AudioOntology | Unit | TC_RL_ONTOLOGY_STATE_001 |
| REQ-RL-08 | Log processing statistics periodically | Unit | TC_RL_LOGGING_001 |
| REQ-RL-09 | Shut down gracefully releasing resources | Unit | TC_RL_SHUTDOWN_001 |
| REQ-RL-10 | Achieve <10ms latency per audio frame | Performance | TC_RL_LATENCY_001 |
| REQ-LS-01 | Provide basic usage examples | Unit | TC_LS_EXAMPLES_001 |
| REQ-LS-02 | Provide REST API server for legacy functions | Integration | TC_LS_API_001 |
| REQ-LS-03 | Support audio enhancement, content generation via agents | Unit | TC_LS_AGENTS_001 |

## 3. Test Cases

### 3.1 Unit Tests

#### TC_RL_CLUSTER_001: Ray Cluster Initialization
- **Verify**: Cluster initializes with correct CPU/GPU allocation
- **Test**: 
  1. Initialize RayClusterManager with num_cpus=2, num_gpus=0
  2. Verify cluster.resources() shows correct allocation
  3. Test with num_gpus=1 (if GPU available) or skip if not
  4. Verify shutdown releases resources

#### TC_RL_ONTOLOGY_001: Audio Ontology Manager
- **Verify**: Ontology correctly defines attributes and relationships
- **Test**:
  1. Create AudioOntologyManager instance
  2. Verify all AudioAttribute enums are present
  3. Test get_attribute_correlation for known pairs (e.g., CLARITY-MUD: -0.8)
  4. Test get_conflicting_attributes and get_synergistic_attributes
  5. Test estimate_satisfaction_score with known goals and state

#### TC_RL_AGENTS_INIT_001: Agent Initialization
- **Verify**: All agents initialize correctly with proper parameters
- **Test**:
  1. Initialize MAAPSNexusSystem in test mode
  2. Verify critic_agent, eq_agent, dynamics_agent, coordinator are not None
  3. Verify agents are registered with coordinator
  4. Verify model loading when use_pretrained=True and model exists

#### TC_RL_ONTOLOGY_STATE_001: AudioState Management
- **Verify**: AudioState correctly stores and retrieves attributes
- **Test**:
  1. Create AudioState instance
  2. Set attribute CLARITY to 0.8 with confidence 0.9
  3. Verify get_attribute returns 0.8
  4. Verify get_confidence returns 0.9
  5. Test to_vector conversion
  6. Test default value return for unset attributes

#### TC_RL_LOGGING_001: System Logging
- **Verify**: System logs key events at appropriate levels
- **Test**:
  1. Initialize system with logging level INFO
  2. Capture log output during initialization
  3. Verify "Initializing Ray cluster", "Initializing audio ontology", etc. appear
  4. Verify error logging when components fail to initialize

#### TC_RL_SHUTDOWN_001: Graceful Shutdown
- **Verify**: System releases all resources during shutdown
- **Test**:
  1. Initialize system in test mode
  2. Call shutdown() method
  3. Verify Ray cluster is shut down
  4. Verify plugin communicators are closed/stopped
  5. Verify no resource leaks (check with lsof or similar in CI)

### 3.2 Integration Tests

#### TC_RL_PLUGIN_MODES_001: Plugin Mode Initialization
- **Verify**: System initializes correctly for each plugin mode
- **Test**:
  1. For each mode in ["vst3", "clap", "ara", "none"]:
     - Initialize MAAPSNexusSystem with plugin_mode=mode
     - Verify appropriate communicator is initialized (or None for "none")
     - For "vst3"/"clap": verify StreamingPluginCommunicator is started
     - For "ara": verify AraPluginCommunicator is started
     - Shut down system and verify clean cleanup

#### TC_RL_STANDALONE_001: Standalone Test Mode
- **Verify**: System processes audio for specified duration in test mode
- **Test**:
  1. Initialize system with plugin_mode="none", test_duration=2.0
  2. Call run_standalone_test()
  3. Verify total_frames_processed > 0
  4. Verify logs show progression through frames
  5. Verify statistics are printed at end

#### TC_RL_PIPELINE_001: Audio Processing Pipeline
- **Verify**: Audio flows correctly through EQ -> Dynamics -> Coordinator -> Critic
- **Test**:
  1. Initialize system in test mode
  2. Create test audio buffer (white noise, buffer_size=512, channels=2)
  3. Create initial AudioState with mid-range values
  4. Call process_audio_frame() and verify:
     - Returns processed audio of same shape
     - Returns updated AudioState
     - total_frames_processed increments
     - Agents' process_audio methods were called (verify via mocks in test)
  5. Verify coordinator.coordinate was called with two proposals
  6. Verify critic_agent.evaluate was called with processed audio and new state

### 3.3 End-to-End Tests

#### TC_RL_E2E_001: Full Real-time Processing Loop (VST3/CLAP Simulation)
- **Verify**: System can sustain processing loop without dropping frames
- **Test**:
  1. Initialize system with plugin_mode="vst3" (or "clap")
  2. Mock StreamingPluginCommunicator to provide test audio and accept processed audio
  3. Run processing loop for 100 frames (or time-boxed)
  4. Verify no exceptions occur
  5. Verify latency measurements are recorded
  6. Verify statistics logging occurs periodically
  7. Shut down cleanly

#### TC_LS_API_001: Legacy API Basic Functionality
- **Verify**: Legacy API server starts and responds to basic requests
- **Test**:
  1. Start uvicorn server for api.main:app in test process
  2. Send GET request to /docs or /health endpoint
  3. Verify 200 response
  4. Send POST request to an example endpoint (e.g., /audio/enhance) with test audio
  5. Verify appropriate response (or 404 if endpoint not implemented, but verify server is running)
  6. Stop server

### 3.4 Performance Tests

#### TC_RL_LATENCY_001: Audio Frame Processing Latency
- **Verify**: Average latency per frame < 10ms under test conditions
- **Test**:
  1. Initialize system in test mode
  2. Process 1000 audio frames using process_audio_frame()
  3. Measure time per frame using time.perf_counter()
  4. Calculate average and 95th percentile latency
  5. Assert average < 10ms (adjust threshold for CI environment if needed)
  6. Log results for tracking

### 3.5 Security Tests

#### TC_SEC_001: No Secret Logging
- **Verify**: System does not log API keys or sensitive data
- **Test**:
  1. Initialize system with fake API keys in environment
  2. Capture all logs during operation
  3. Verify no log lines contain the API key values
  4. Verify error messages don't expose secrets

## 4. Load/Performance Test Plan

### 4.1 Audio Processing Load Test
- **Goal**: Determine maximum sustainable audio processing rate
- **Method**:
  1. Run system in test mode with increasing complexity (more agents, larger buffer sizes)
  2. Measure latency and throughput at each level
  3. Identify saturation point where latency exceeds 10ms
- **Tools**: Custom Python script, time.perf_counter, memory_profiler
- **Frequency**: Weekly performance benchmark

### 4.2 Message Bus Load Test (Legacy System)
- **Goal**: Verify message bus handles expected message volume
- **Method**:
  1. Publish messages at increasing rates (100msg/s, 1000msg/s, 10000msg/s)
  2. Measure end-to-end latency and message loss
  3. Verify backpressure mechanisms work correctly
- **Tools**: Custom publisher/subscriber scripts
- **Frequency**: Monthly

### 4.3 Resource Usage Test
- **Goal**: Ensure system stays within defined resource limits
- **Method**:
  1. Run system under typical load for extended period (1 hour)
  2. Monitor CPU, memory, file descriptors, network usage
  3. Verify no leaks or excessive growth
- **Tools**: psutil, /proc monitoring
- **Frequency**: Before each release

## 5. Test Data and Environment Needs

### 5.1 Test Data
- **Audio Signals**:
  - Synthetic: white noise, pink noise, sine waves, impulse responses
  - Edge cases: silent buffers, clipping signals, DC offset, NaN/inf values
  - Format variations: mono/stereo, different sample rates (44.1k, 48k, 96k), bit depths (16-bit, 24-bit, float32)
- **Message Bus Test Data**:
  - Valid and invalid message schemas per agent type
  - Oversized payloads (1x, 2x, 10x max size)
  - Malformed JSON where applicable
- **API Test Data**:
  - Valid request bodies per OpenAPI spec (if available)
  - Invalid inputs: type mismatches, missing required fields, boundary values
  - Common attack payloads (SQL injection, XSS attempts where applicable)

### 5.2 Environment Requirements
- **Hardware**:
  - Minimum: x86_64 CPU, 4GB RAM (for unit tests)
  - Recommended: x86_64 CPU with 4+ cores, 8GB RAM, GPU optional
  - For DAW integration tests: Linux system with shared memory capabilities
- **Software**:
  - Python 3.9-3.11
  - Required packages: see requirements.txt
  - For audio testing: libsndfile1, portaudio19-dev (optional, for real audio I/O)
  - For shared memory: posix-ipc (Linux)
  - For testing: pytest, pytest-cov, mock, bandit, safety
- **Isolation**:
  - Tests run in dedicated virtualenv
  - Audio testing uses synthetic signals (no hardware dependency)
  - Message bus tests use in-memory mode where possible
  - External services (Vertex AI, LLM APIs) mocked in unit tests

## 6. Test Implementation Approach

### 6.1 Test Organization
```
tests/
├── unit/
│   ├── test_ray_cluster.py
│   ├── test_audio_ontology.py
│   ├── test_agents.py
│   ├── test_nexus_system.py
│   └── test_message_bus.py
├── integration/
│   ├── test_plugin_modes.py
│   ├── test_standalone_mode.py
│   ├── test_audio_pipeline.py
│   └── test_api.py
├── performance/
│   ├── test_latency.py
│   └── test_throughput.py
└── security/
    └── test_secrets.py
```

### 6.2 Mocking Strategy
- **Ray Agents**: Use unittest.mock to create mock remote methods
- **External APIs**: Mock Vertex AI, LLM integrations
- **File System**: Use temporary directories for model saving/loading
- **Audio Hardware**: Use numpy-generated audio instead of real audio I/O
- **Shared Memory**: Mock or use in-memory alternatives for testing

### 6.3 Test Data Generation
- **Audio Generators**: Utility functions in tests/conftest.py or tests/utils/
- **State Generators**: Functions to create valid AudioState instances
- **Message Factories**: Functions to create valid/invalid messages for legacy system
- **Fixture Management**: Use pytest fixtures for reusable test objects

## 7. Pass/Fail Criteria

### 7.1 Unit Tests
- Must pass 100% of unit tests for code to be mergeable
- Coverage threshold: 85% for new code, maintain overall >80%

### 7.2 Integration Tests
- Must pass 100% of integration tests for release candidates
- Performance tests must show no regression >10% from baseline

### 7.3 Performance Tests
- Latency must consistently measure <10ms for 95% of frames under test conditions
- Memory growth must be bounded (<10% increase over 1 hour test)

### 7.4 Security Tests
- No high or medium severity vulnerabilities reported by Bandit
- No secrets detected in code or logs by custom checks
- Dependency scan must show no high-severity vulnerabilities

## 8. Assumptions and Dependencies

### 8.1 Assumptions
- Audio processing latency is dominated by the Python->Ray->Python roundtrip
- Real-time performance requires <10ms processing time (excluding host DAW buffer)
- Test environment CPU performance is representative of production
- Shared memory performance on Linux is sufficient for VST3/CLAP integration

### 8.2 Dependencies
- Ray 2.0+ for distributed agent execution
- Librosa/Torchaudio for audio feature extraction (placeholder currently)
- SoundFile for audio I/O in examples/tests
- FastAPI for legacy system REST API
- POSIX shared memory for plugin integration (Linux)

## 9. Open Issues and Risks

### 9.1 Test Coverage Gaps
- VST3 plugin C++ code is not covered by Python tests
- GUI components lack automated tests
- End-to-end DAW integration requires manual validation

### 9.2 Environment Dependencies
- Performance tests may vary significantly based on host CPU
- GPU-dependent tests require CUDA-capable hardware
- Shared memory behavior may differ between Linux distributions

### 9.3 Mitigations
- Use hardware abstraction layers in performance tests
- Skip GPU tests if no CUDA available, run separately in GPU CI
- Document Linux distribution requirements for shared memory
- Provide VST3 build verification as separate gate

--- 
*This test plan ensures all PRD-derived requirements have corresponding verification methods. It balances automated test depth with practical execution constraints, focusing on correctness of the RL system while validating legacy system interfaces.*