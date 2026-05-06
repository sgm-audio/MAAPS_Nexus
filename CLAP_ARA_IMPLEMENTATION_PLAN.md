# CLAP & ARA Implementation Plan

**Date:** Feb 14, 2026
**Target:** MAAPS Nexus Audio Engine
**Objective:** Migration to CLAP format and implementation of ARA 2.0 capabilities while maintaining VST3 support.

## 1. Architectural Overview

The MAAPS Nexus system currently uses a shared-memory IPC bridge to communicate with a VST3 wrapper. To support CLAP and ARA, we will bifurcate the architecture:

1.  **Real-Time Streaming Path (CLAP / VST3)**: Uses the existing ring-buffer shared memory pattern. Both CLAP and VST3 plugins will act as thin clients writing to the same IPC protocol.
2.  **Random Access Path (ARA 2.0)**: A new IPC protocol based on file references and random-access memory mapping, enabling global analysis and non-linear processing.

## 2. CLAP Integration Strategy

CLAP (Clever Audio Plugin) offers superior threading models and event handling compared to VST3.

### C++ Plugin Side (New `clap-wrapper`)
-   **Factory**: Implement `clap_plugin_factory`.
-   **Entry Point**: A single binary can expose both CLAP and VST3 entry points.
-   **Event Loop**: Map CLAP parameter events to the existing IPC control pipe.
-   **Audio Processing**: Inside `clap_plugin::process()`, copy buffer pointers to the `SharedMemoryAudioBuffer` (just like VST3).
-   **Polyphony**: CLAP supports better note expression; we can map these to the `AudioOntology` (e.g., specific notes getting more "Warmth").

### Python Side (Refactoring)
-   **Renaming**: `VST3Communicator` -> `StreamingPluginCommunicator`.
-   **Agnosticism**: The Python code does not need to know if the bytes came from VST3 or CLAP, as long as the shared memory layout remains `[Header | Audio Float32]`.
-   **Metadata**: Add a handshake field in the shared memory header to identify the host DAW and plugin format (e.g., "Bitwig/CLAP", "Reaper/VST3") for logging/telemetry.

## 3. ARA 2.0 Implementation Strategy

ARA allows the plugin to read the full audio file from the DAW, enabling "Time Travel" for our agents (seeing the future audio context).

### C++ ARA Extension
-   **Interface**: Implement `ARA::PlugIn::DocumentController`.
-   **Audio Access**: Use `ARA::AudioSource::getAudioReader()` to read raw samples.
-   **IPC Strategy**:
    -   Instead of streaming buffers, the C++ plugin will send a **File Path** or **Memory Handle** to Python.
    -   Command: `ARA_ANALYZE_REGION(audio_source_id, start_time, duration)`
    -   Command: `ARA_UPDATE_REGION(audio_modification_id, start_time, duration)`

### Python ARA Wrapper (`AraPluginCommunicator`)
-   **Communication**: Use a specialized Request/Response socket (ZeroMQ or Named Pipe) separate from the real-time audio stream.
-   **Workflow**:
    1.  **Analysis Phase**: ARA triggers Python to run `extract_metadata` and `CriticAgent` analysis on the *entire* track immediately upon load.
    2.  **Visualization**: Python sends back high-res spectral data for the DAW timeline overlay.
    3.  **Processing**: When the user applies an edit, Python processes the region offline (faster than real-time) and writes the result back to a shared buffer or temp file which the ARA plugin reads.

## 4. Implementation Steps

### Phase 1: Python Refactoring (Immediate)
1.  Rename `vst3_wrapper.py` to `streaming_plugin_wrapper.py`.
2.  Generalize `MAAPSNexusSystem` to accept a generic `plugin_interface`.
3.  Create `ara_plugin_wrapper.py` stub with new protocol definitions.

### Phase 2: C++ Development (External Team)
1.  Set up `clap-juce-extensions` or raw `clap-libs`.
2.  Port the Shared Memory writer from VST3 to the CLAP `process()` callback.
3.  Implement `ARAFactory` and basic `DocumentController`.

### Phase 3: Integration
1.  Update `nexus_system.py` to initialize both `Streaming` and `ARA` communicators.
2.  Train agents (EQ/Dynamics) to utilize "Lookahead" context provided by ARA.

## 5. Technical Constraints & Risks

-   **ARA Latency**: While ARA is "offline", the user expects immediate visual feedback. Python analysis must happen in <200ms for UX.
-   **Memory Safety**: Sharing file handles or raw memory pointers between C++ DAW and Python process requires strict locking to prevent DAW crashes.
-   **Concurrency**: The `Streaming` and `ARA` paths must not block each other. They should run on separate Ray actors / threads.
