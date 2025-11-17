# Live Performance Multi-Agent System Extensions

## Overview
Additional agents and capabilities for live performance scenarios, focusing on real-time processing, low latency, reliability, and interactive control.

---

## 1. Real-Time Audio I/O Agent

**Purpose:** Manage live audio input/output streams with ultra-low latency

### Capabilities
- **Audio Stream Management**
  - Multi-channel audio input (microphones, instruments, line inputs)
  - ASIO/Core Audio driver support for low latency
  - Buffer size optimization (32-256 samples)
  - Input gain staging and automatic level control
  - Hot-swappable audio interfaces

- **Monitoring & Routing**
  - Zero-latency monitoring
  - Flexible input/output routing matrix
  - Send/return configuration for external effects
  - Monitor mixes for performers

### Topics
```python
"audio.live.input.stream"        # Live audio input data
"audio.live.output.stream"       # Audio output to interface
"audio.live.monitoring.config"   # Monitor mix configuration
"audio.live.routing.change"      # Update routing matrix
"audio.live.latency.report"      # Latency measurements
"audio.live.interface.status"    # Audio interface health
```

### Key Functions
```python
def configure_audio_interface(
    sample_rate: int = 48000,
    buffer_size: int = 128,
    input_channels: List[int] = [1, 2],
    output_channels: List[int] = [1, 2]
) -> Dict

def create_monitor_mix(
    source_channels: List[int],
    output_channel: int,
    levels: Dict[int, float]
) -> str  # Returns mix_id

def get_latency_metrics() -> Dict:
    # Returns input_latency, output_latency, round_trip_latency
```

---

## 2. Live Effects Chain Agent

**Purpose:** Real-time audio effects processing with preset management

### Capabilities
- **Effect Processing**
  - Zero-latency effect chains
  - Dynamic effect bypass/enable
  - Parallel effect processing
  - Wet/dry mixing
  - Effect parameter automation

- **Preset Management**
  - Scene-based preset recall
  - Smooth parameter transitions
  - A/B comparison
  - Preset morphing

- **Effect Types**
  - Dynamics (compressor, limiter, gate, expander)
  - EQ (parametric, graphic, dynamic)
  - Time-based (reverb, delay, chorus, flanger)
  - Modulation (phaser, tremolo, vibrato)
  - Distortion/Saturation
  - Pitch correction/Auto-tune

### Topics
```python
"effects.chain.update"           # Update effect chain
"effects.preset.recall"          # Load preset
"effects.parameter.change"       # Change effect parameter
"effects.bypass.toggle"          # Bypass/enable effect
"effects.scene.change"           # Scene change
"effects.morph.start"            # Morph between presets
```

### Key Functions
```python
def create_effect_chain(
    chain_name: str,
    effects: List[Dict],  # effect type, parameters, position
    routing: str = "series"  # or "parallel"
) -> str  # Returns chain_id

def recall_preset(
    preset_name: str,
    transition_time: float = 0.0  # seconds
) -> bool

def set_effect_parameter(
    effect_id: str,
    parameter: str,
    value: float,
    ramp_time: float = 0.0
) -> bool

def create_scene(
    scene_name: str,
    effect_states: Dict,  # effect_id -> parameters
    transitions: Dict  # parameter -> ramp_time
) -> str  # Returns scene_id
```

---

## 3. MIDI Control & Integration Agent

**Purpose:** MIDI controller integration and parameter mapping

### Capabilities
- **MIDI Input/Output**
  - Multiple MIDI device support
  - MIDI learn functionality
  - Custom MIDI mapping
  - MIDI message filtering

- **Controller Mapping**
  - CC to parameter mapping
  - Note-based triggering
  - Program change handling
  - MIDI expression mapping

- **MIDI Processing**
  - Note quantization
  - Velocity scaling
  - Arpeggiator
  - MIDI echo/delay

### Topics
```python
"midi.device.connected"          # MIDI device connected
"midi.message.received"          # Incoming MIDI message
"midi.mapping.learn"             # Start MIDI learn
"midi.mapping.assign"            # Assign MIDI to parameter
"midi.program.change"            # Program change received
"midi.clock.sync"                # MIDI clock sync
```

### Key Functions
```python
def map_midi_controller(
    midi_cc: int,
    target_agent: str,
    target_parameter: str,
    min_value: float,
    max_value: float,
    curve: str = "linear"  # or "exponential", "logarithmic"
) -> str  # Returns mapping_id

def trigger_on_note(
    note_number: int,
    action: str,  # "scene_change", "effect_toggle", "loop_record"
    parameters: Dict
) -> str  # Returns trigger_id

def send_midi_feedback(
    controller_id: str,
    parameter_values: Dict[int, int]  # CC -> value (0-127)
) -> bool
```

---

## 4. Live Looping Agent

**Purpose:** Real-time loop recording, playback, and manipulation

### Capabilities
- **Loop Management**
  - Multi-track loop recording
  - Synchronized loop start/stop
  - Loop overdubbing
  - Loop undo/redo
  - Loop quantization

- **Loop Processing**
  - Time-stretching
  - Pitch-shifting
  - Reverse playback
  - Half-speed/double-speed
  - Loop slicing

- **Synchronization**
  - Tempo-locked loops
  - Click track generation
  - Count-in functionality
  - Loop length quantization

### Topics
```python
"loop.record.start"              # Start recording loop
"loop.record.stop"               # Stop recording
"loop.playback.toggle"           # Toggle playback
"loop.overdub.enable"            # Enable overdub mode
"loop.clear"                     # Clear loop
"loop.undo"                      # Undo last operation
"loop.sync.quantize"             # Quantize loop timing
```

### Key Functions
```python
def create_loop_track(
    track_name: str,
    length_beats: int,
    sync_to_tempo: bool = True
) -> str  # Returns track_id

def record_loop(
    track_id: str,
    mode: str = "replace",  # or "overdub", "multiply"
    quantize: bool = True
) -> bool

def manipulate_loop(
    track_id: str,
    operation: str,  # "reverse", "half_speed", "pitch_shift"
    parameters: Dict
) -> bool

def sync_loops_to_master(
    master_tempo: float,
    time_signature: str = "4/4"
) -> bool
```

---

## 5. Performance Automation Agent

**Purpose:** Automate parameter changes and scene transitions during performance

### Capabilities
- **Automation Recording**
  - Real-time parameter automation capture
  - Automation editing
  - Automation curves (linear, exponential, bezier)
  - Multiple automation lanes

- **Scene Management**
  - Scene-based automation
  - Automatic scene transitions
  - Timeline-based cues
  - Conditional scene changes

- **Macro Controls**
  - Multi-parameter macros
  - Morph pads (XY control)
  - Performance gestures
  - Touch-sensitive automation

### Topics
```python
"automation.record.start"        # Start recording automation
"automation.playback.enable"     # Enable automation playback
"automation.scene.trigger"       # Trigger scene
"automation.macro.change"        # Change macro value
"automation.cue.fire"            # Fire automation cue
"automation.timeline.sync"       # Sync to timeline
```

### Key Functions
```python
def record_automation(
    parameter_path: str,  # "agent.parameter"
    start_time: float,
    duration: float
) -> str  # Returns automation_id

def create_scene(
    scene_name: str,
    parameter_snapshots: Dict,  # parameter -> value
    transition_curves: Dict  # parameter -> curve_type
) -> str

def define_macro(
    macro_name: str,
    target_parameters: List[Dict],  # param, min, max, curve
    default_value: float = 0.5
) -> str  # Returns macro_id

def create_performance_cue(
    cue_name: str,
    timecode: str,  # "00:02:30.500" or "beat:16.0"
    actions: List[Dict],  # action_type, parameters
    condition: Optional[Dict] = None  # conditional trigger
) -> str  # Returns cue_id
```

---

## 6. Synchronization & Clock Agent

**Purpose:** Tempo and timing synchronization with external devices

### Capabilities
- **Clock Management**
  - Internal tempo clock
  - MIDI clock sync (send/receive)
  - Ableton Link support
  - LTC/MTC timecode sync
  - Manual tap tempo

- **Tempo Control**
  - BPM detection from audio
  - Tempo mapping
  - Tempo automation
  - Tempo nudge controls

- **Transport Control**
  - Play/stop/pause
  - Loop markers
  - Song position pointer
  - Bar/beat counters

### Topics
```python
"sync.clock.tempo"               # Current tempo
"sync.clock.position"            # Current bar/beat position
"sync.midi.clock.out"            # MIDI clock output
"sync.link.session"              # Ableton Link session
"sync.tap.tempo"                 # Tap tempo input
"sync.transport.control"         # Transport commands
```

### Key Functions
```python
def set_master_tempo(
    bpm: float,
    time_signature: str = "4/4",
    transition_time: float = 0.0
) -> bool

def enable_midi_clock_output(
    midi_port: str,
    send_start_stop: bool = True
) -> bool

def sync_to_ableton_link(
    enable: bool = True,
    set_tempo: bool = False
) -> Dict  # Returns session info

def detect_tempo_from_audio(
    audio_buffer: np.ndarray,
    sample_rate: int
) -> float  # Returns detected BPM

def tap_tempo_input() -> float:
    # Returns calculated BPM from tap input
```

---

## 7. Visual & Lighting Control Agent

**Purpose:** Synchronize visuals and lighting with audio performance

### Capabilities
- **Lighting Control**
  - DMX/ArtNet protocol support
  - Scene-based lighting cues
  - Audio-reactive lighting
  - Fixture management

- **Visual Sync**
  - Video playback synchronization
  - Visual effects triggering
  - Projection mapping control
  - VJ software integration

- **Analysis-Based Control**
  - Beat detection for lights
  - Frequency-based color mapping
  - Amplitude-based intensity
  - Onset detection triggers

### Topics
```python
"visual.lighting.scene"          # Lighting scene change
"visual.dmx.update"              # DMX channel updates
"visual.video.sync"              # Video sync command
"visual.audio.analysis"          # Audio analysis for visuals
"visual.beat.detected"           # Beat detection event
"visual.color.map"               # Frequency to color mapping
```

### Key Functions
```python
def control_dmx_fixture(
    fixture_id: str,
    channels: Dict[int, int],  # channel -> value (0-255)
    fade_time: float = 0.0
) -> bool

def create_lighting_scene(
    scene_name: str,
    fixture_states: Dict,  # fixture_id -> channel_values
    sync_to_beat: bool = False
) -> str  # Returns scene_id

def map_audio_to_lighting(
    frequency_band: Tuple[float, float],  # Hz range
    target_fixture: str,
    target_channel: int,
    response_curve: str = "linear"
) -> str  # Returns mapping_id

def trigger_visual_on_beat(
    visual_layer: str,
    beat_division: int = 4,  # trigger every N beats
    parameters: Dict
) -> str  # Returns trigger_id
```

---

## 8. Live Mixing & Dynamics Agent

**Purpose:** Intelligent mixing and dynamics processing for live performance

### Capabilities
- **Auto-Mixing**
  - Automatic gain riding
  - Dynamic ducking
  - Frequency-aware mixing
  - Priority-based mixing

- **Adaptive Processing**
  - Context-aware compression
  - Intelligent limiting
  - Feedback suppression
  - Noise gating

- **Spatial Processing**
  - Auto-panning
  - Stereo width control
  - Immersive audio (surround/binaural)

### Topics
```python
"mix.automix.enable"             # Enable auto-mixing
"mix.channel.priority"           # Set channel priority
"mix.ducking.configure"          # Configure ducking
"mix.feedback.suppress"          # Feedback suppression
"mix.spatial.position"           # Set spatial position
```

### Key Functions
```python
def enable_auto_mixing(
    input_channels: List[int],
    target_channels: List[int],
    sensitivity: float = 0.7
) -> bool

def configure_ducking(
    sidechain_channel: int,
    target_channels: List[int],
    threshold_db: float = -20.0,
    ratio: float = 4.0,
    release_ms: float = 300.0
) -> str  # Returns ducking_id

def suppress_feedback(
    input_channel: int,
    num_filters: int = 12,
    auto_adapt: bool = True
) -> bool

def set_channel_priority(
    channel_id: int,
    priority_level: int  # 1-10, higher = more important
) -> bool
```

---

## 9. Performance Monitoring & Analytics Agent

**Purpose:** Real-time monitoring and performance analytics

### Capabilities
- **Performance Metrics**
  - CPU/latency monitoring
  - Audio quality metrics
  - Processing load distribution
  - Buffer underrun detection

- **Audio Analysis**
  - Real-time spectrum analysis
  - Loudness metering (LUFS)
  - Phase correlation
  - Dynamic range monitoring

- **System Health**
  - Temperature monitoring
  - Disk space tracking
  - Network status
  - Backup system status

### Topics
```python
"monitor.performance.cpu"        # CPU usage metrics
"monitor.audio.quality"          # Audio quality metrics
"monitor.system.health"          # System health status
"monitor.loudness.lufs"          # LUFS measurements
"monitor.alert.critical"         # Critical alerts
```

### Key Functions
```python
def get_realtime_metrics() -> Dict:
    # Returns CPU, latency, buffer status

def analyze_audio_quality(
    channel: int,
    metrics: List[str]  # ["lufs", "true_peak", "dynamic_range"]
) -> Dict

def set_performance_alert(
    metric: str,  # "cpu_usage", "latency", "temperature"
    threshold: float,
    alert_callback: Callable
) -> str  # Returns alert_id

def generate_performance_report(
    duration_seconds: float,
    include_graphs: bool = True
) -> Dict
```

---

## 10. Backup & Redundancy Agent

**Purpose:** Ensure reliability with hot backup and failover systems

### Capabilities
- **System Redundancy**
  - Hot backup audio processing
  - Automatic failover
  - Dual audio interface support
  - State synchronization

- **Data Backup**
  - Real-time preset backup
  - Performance recording
  - Configuration snapshots
  - Cloud sync

- **Recovery**
  - Crash recovery
  - State restoration
  - Automatic restart
  - Error logging

### Topics
```python
"backup.system.status"           # Backup system status
"backup.failover.trigger"        # Initiate failover
"backup.state.sync"              # Sync state to backup
"backup.recording.save"          # Save performance recording
"backup.restore.state"           # Restore from backup
```

### Key Functions
```python
def enable_hot_backup(
    primary_interface: str,
    backup_interface: str,
    sync_interval_ms: int = 100
) -> bool

def configure_failover(
    trigger_conditions: Dict,  # condition -> threshold
    failover_time_ms: int = 50,
    auto_recover: bool = True
) -> str  # Returns config_id

def save_performance_state(
    state_name: str,
    include_audio: bool = False
) -> str  # Returns state_id

def record_performance(
    output_path: str,
    format: str = "wav",  # or "flac", "mp3"
    bit_depth: int = 24,
    include_video: bool = False
) -> str  # Returns recording_id
```

---

## Integration Architecture

### Message Flow Example
```python
# Live performance scenario
1. MIDI Controller → MIDI Agent → "midi.message.received"
2. MIDI Agent → Automation Agent → "automation.parameter.change"
3. Automation Agent → Effects Agent → "effects.parameter.change"
4. Effects Agent → Audio I/O Agent → "audio.live.output.stream"
5. Audio I/O Agent → Monitoring Agent → "monitor.audio.quality"
6. Audio Analysis → Visual Agent → "visual.beat.detected"
7. Visual Agent → Lighting Control → "visual.lighting.scene"
8. All Agents → Backup Agent → "backup.state.sync"
```

### Latency Targets
- **Audio I/O**: < 5ms round-trip
- **MIDI processing**: < 1ms
- **Effect processing**: < 2ms per effect
- **Visual sync**: < 10ms
- **State sync**: < 50ms

### Reliability Features
- Watchdog timers for all agents
- Automatic restart on crash
- Hot-swappable components
- Graceful degradation
- Comprehensive error logging

---

## Example Use Cases

### Use Case 1: Electronic Live Set
```python
# Setup
system.enable_ableton_link()
system.create_loop_track("drums", length_beats=16)
system.create_loop_track("bass", length_beats=16)
system.map_midi_controller(cc=1, target="effects.filter_cutoff")
system.map_midi_controller(cc=2, target="effects.reverb_wet")

# Performance
system.record_loop("drums", mode="replace")
system.record_loop("bass", mode="overdub")
system.trigger_scene("breakdown")
system.manipulate_loop("drums", operation="half_speed")
```

### Use Case 2: Vocal Performance with Effects
```python
# Setup
system.configure_audio_interface(buffer_size=128)
system.create_effect_chain("vocal", [
    {"type": "noise_gate", "threshold": -40},
    {"type": "compressor", "ratio": 4.0},
    {"type": "reverb", "room_size": 0.7},
    {"type": "delay", "time": 0.375}  # dotted eighth
])
system.map_midi_controller(cc=1, target="effects.reverb.wet")

# Performance
system.recall_preset("verse")
# ... perform ...
system.recall_preset("chorus", transition_time=0.5)
```

### Use Case 3: DJ Set with Visuals
```python
# Setup
system.sync_to_ableton_link()
system.create_lighting_scene("intro", {...})
system.map_audio_to_lighting(
    frequency_band=(60, 250),  # Bass
    target_fixture="stage_wash",
    target_channel=3  # Blue channel
)

# Performance
system.detect_tempo_from_audio(deck_a_audio, 44100)
system.trigger_visual_on_beat("strobe", beat_division=2)
system.create_lighting_scene("drop", {...})
```

---

## Configuration File: live_performance_config.json

```json
{
  "audio_interface": {
    "driver": "ASIO",
    "sample_rate": 48000,
    "buffer_size": 128,
    "input_channels": [1, 2, 3, 4],
    "output_channels": [1, 2]
  },
  "midi_controllers": [
    {
      "name": "Controller1",
      "type": "APC40",
      "port": "MIDI_IN_1",
      "mappings": "presets/controller1_map.json"
    }
  ],
  "effects_chains": {
    "default_latency_ms": 2.0,
    "max_effects_per_chain": 8,
    "parallel_processing": true
  },
  "looping": {
    "max_loop_tracks": 8,
    "quantize_default": true,
    "undo_history": 10
  },
  "synchronization": {
    "master_clock": "internal",
    "ableton_link": true,
    "midi_clock_out": true,
    "tap_tempo_enabled": true
  },
  "backup": {
    "hot_backup_enabled": true,
    "backup_interface": "AUDIO_DEVICE_2",
    "state_sync_interval_ms": 100,
    "auto_record": false
  },
  "monitoring": {
    "cpu_alert_threshold": 80,
    "latency_alert_threshold_ms": 10,
    "enable_performance_logging": true
  }
}
```

---

## Next Steps

1. **Implement Priority Order:**
   - Phase 1: Audio I/O Agent + MIDI Agent
   - Phase 2: Effects Chain Agent + Looping Agent
   - Phase 3: Automation Agent + Sync Agent
   - Phase 4: Visual Control + Monitoring
   - Phase 5: Backup & Redundancy

2. **Testing Requirements:**
   - Latency measurements
   - Stress testing
   - Failover testing
   - Real-world performance testing

3. **Documentation:**
   - API documentation
   - Performance best practices
   - Troubleshooting guide
   - Example performances

4. **Integration:**
   - Compatibility testing with existing agents
   - Message bus performance optimization
   - Priority queue implementation
   - Resource allocation strategy
