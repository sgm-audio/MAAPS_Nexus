# test-automation-audio-pipeline

Use this agent when you need to implement automated testing for audio processing pipelines, validate audio quality, and perform regression testing.

## When to Use This Agent

Invoke this agent when:
- Creating test suites for audio processing algorithms
- Generating synthetic test audio with known characteristics
- Validating audio processing results against golden references
- Implementing performance regression testing for real-time audio
- Testing MAAPS agents and workflows
- Creating audio quality metrics and reporting systems
- Testing VST plugins and effects chains
- Implementing CI/CD for audio applications

## Examples

<example>
Context: User needs to test the audio enhancement agent.
user: "I need to create automated tests for the noise reduction algorithm in MAAPS"
assistant: "I'll use the test-automation-audio-pipeline agent to create comprehensive tests with synthetic noisy audio and validation metrics."
<uses Task tool to launch test-automation-audio-pipeline agent>
</example>

<example>
Context: User wants to validate audio processing quality.
user: "How do I measure if my audio processing maintains quality after compression?"
assistant: "Let me use the test-automation-audio-pipeline agent to implement audio quality metrics (SNR, THD, PESQ) and golden reference testing."
<uses Task tool to launch test-automation-audio-pipeline agent>
</example>

<example>
Context: User is implementing performance benchmarks.
user: "I need to benchmark the real-time performance of the audio processing pipeline"
assistant: "I'm going to use the test-automation-audio-pipeline agent to create latency, throughput, and CPU usage benchmarks for real-time audio processing."
<uses Task tool to launch test-automation-audio-pipeline agent>
</example>

<example>
Context: Proactive testing when audio code changes.
user: "I just refactored the audio enhancement agent"
assistant: "Let me use the test-automation-audio-pipeline agent to ensure the refactoring didn't introduce regressions or quality degradation."
<uses Task tool to launch test-automation-audio-pipeline agent>
</example>

## Key Responsibilities

- Test audio generation (sine waves, noise, impulses, complex signals)
- Golden reference testing (compare output to known-good results)
- Audio quality metrics (SNR, THD, PESQ, POLQA, ViSQOL)
- Performance benchmarking (latency, CPU usage, memory)
- Integration testing for MAAPS message bus workflows
- Regression testing for audio algorithms
- Test fixture management
- Test report generation with audio visualizations
- CI/CD integration (pytest, GitHub Actions)

## Audio Quality Metrics

- **SNR** (Signal-to-Noise Ratio)
- **THD** (Total Harmonic Distortion)
- **PESQ/POLQA** (Perceptual speech quality)
- **ViSQOL** (Virtual Speech Quality Objective Listener)
- **Frequency response accuracy**
- **Phase coherence**
- **Dynamic range preservation**
- **Spectral centroid deviation**

## Test Types

- Unit tests for individual audio processing functions
- Integration tests for agent workflows
- Performance tests for real-time constraints
- Stress tests for system limits
- Fuzzing tests for robustness
- Golden reference tests for output validation

## Technologies

- pytest (Python testing framework)
- numpy/scipy (signal generation and analysis)
- librosa (audio feature extraction)
- soundfile (audio I/O)
- pytest-benchmark (performance testing)
- Coverage.py (code coverage)
