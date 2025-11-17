# Windows GUI Plan - Multi-Agent Audio Processing System

## Executive Summary

This document outlines the plan for a professional Windows GUI application to control and visualize the Multi-Agent Audio Processing System (Phases 1-3). The GUI will provide intuitive access to live effects processing, looping, synchronization, and performance automation capabilities.

**Target Platform**: Windows 10/11
**Estimated Development Time**: 4-6 weeks
**Technology Stack**: Python + Qt (PySide6) or Electron + React

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Architecture](#architecture)
3. [Main Views & Screens](#main-views--screens)
4. [UI Components Library](#ui-components-library)
5. [Integration Strategy](#integration-strategy)
6. [User Experience Design](#user-experience-design)
7. [Implementation Phases](#implementation-phases)
8. [Technical Specifications](#technical-specifications)

---

## Technology Stack

### Option 1: PySide6 (Qt for Python) ⭐ RECOMMENDED

**Pros:**
- Native Python integration with agent system
- Professional, native-looking Windows UI
- Excellent performance for real-time audio UIs
- Rich widget library (sliders, knobs, meters)
- Built-in threading support
- Cross-platform (bonus: works on macOS/Linux)

**Cons:**
- Steeper learning curve
- More verbose code for complex layouts

**Tech Stack:**
- **Framework**: PySide6 (Qt 6.5+)
- **Graphics**: QPainter for custom widgets
- **Audio Visualization**: pyqtgraph or matplotlib
- **Styling**: QSS (Qt Style Sheets) - CSS-like
- **State Management**: Qt Signals/Slots + Python

### Option 2: Electron + React

**Pros:**
- Modern web technologies (HTML/CSS/JS)
- Rich ecosystem of UI libraries
- Faster prototyping
- Beautiful, customizable UIs

**Cons:**
- Higher memory footprint
- Need IPC bridge to Python backend
- Potentially higher latency
- Not ideal for real-time audio control

**Tech Stack:**
- **Framework**: Electron + React
- **UI Library**: Material-UI or Ant Design
- **State Management**: Redux or Zustand
- **Backend Bridge**: Python subprocess + WebSocket/REST API
- **Audio Viz**: Web Audio API or Tone.js

### Decision Matrix

| Criteria | PySide6 | Electron | Winner |
|----------|---------|----------|--------|
| Performance | ✅ Excellent | ⚠️ Good | PySide6 |
| Python Integration | ✅ Native | ⚠️ IPC needed | PySide6 |
| Development Speed | ⚠️ Moderate | ✅ Fast | Electron |
| Real-time Capability | ✅ Excellent | ⚠️ Good | PySide6 |
| Memory Footprint | ✅ Low | ❌ High | PySide6 |
| UI Flexibility | ⚠️ Good | ✅ Excellent | Electron |
| Learning Curve | ⚠️ Steep | ✅ Easy | Electron |

**Recommendation**: **PySide6** for professional audio application with real-time requirements.

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Windows GUI Application                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │  Main Window  │  │  Dashboard    │  │  Effects View │   │
│  │  (QMainWindow)│  │  (Overview)   │  │  (Chain Ctrl) │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
│          │                   │                   │            │
│  ┌───────┴───────────────────┴───────────────────┴───────┐  │
│  │            Central Widget Manager (QStackedWidget)    │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                               │                               │
│  ┌────────────────────────────┴────────────────────────────┐ │
│  │         GUI Controller Layer (Qt Signals/Slots)         │ │
│  └────────────────────────────┬────────────────────────────┘ │
│                               │                               │
├───────────────────────────────┼───────────────────────────────┤
│         Python Backend Integration Layer                      │
├───────────────────────────────┼───────────────────────────────┤
│  ┌────────────────────────────┴────────────────────────────┐ │
│  │         Message Bus Adapter (Thread-Safe Queue)         │ │
│  │  - Subscribes to agent topics                           │ │
│  │  - Publishes GUI events                                 │ │
│  │  - Emits Qt signals for UI updates                      │ │
│  └────────────────────────────┬────────────────────────────┘ │
│                               │                               │
└───────────────────────────────┼───────────────────────────────┘
                                │
┌───────────────────────────────┼───────────────────────────────┐
│              Multi-Agent System (Existing Backend)            │
├───────────────────────────────┴───────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Effects      │  │ Looping      │  │ Sync Clock   │       │
│  │ Chain Agent  │  │ Agent        │  │ Agent        │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │                │
│  ┌──────┴──────────────────┴──────────────────┴────────────┐ │
│  │              Message Bus (Existing)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Separation of Concerns**
   - GUI Layer: Pure UI logic, no business logic
   - Controller Layer: Event handling, state management
   - Backend Integration: Message bus adapter, threading

2. **Thread Safety**
   - Backend agents run in separate threads
   - GUI updates only on main Qt thread
   - Use Qt signals/slots for thread-safe communication

3. **Message Bus Integration**
   - GUI acts as another "agent" on the message bus
   - Subscribes to relevant topics for UI updates
   - Publishes user actions as messages

4. **Reactive Updates**
   - Real-time parameter changes
   - Live meter updates (VU, spectrum)
   - Status indicators

---

## Main Views & Screens

### 1. Main Window Layout

```
┌────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Session  Tools  Help            [_][□][X]   │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│ │Dashboard │  │ Effects  │  │ Looping  │  │ Sync &   │  ...  │
│ │          │  │ Chain    │  │          │  │ Automation│       │
│ └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    [Active View Content]                       │
│                                                                 │
│                                                                 │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│ Transport: [◀◀][▶][■][▶▶]  BPM: 120.0  Bar: 1.2  CPU: 45%    │
└────────────────────────────────────────────────────────────────┘
```

### 2. Dashboard View (Overview)

**Purpose**: System overview, quick access, monitoring

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Active Agents Status                                         │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │ Effects     │  │ Looping     │  │ Sync Clock  │          │
│ │ ● Running   │  │ ● Running   │  │ ● Running   │          │
│ │ 6 chains    │  │ 3 tracks    │  │ 120.0 BPM   │          │
│ └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│ System Performance                                           │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ CPU Usage:    [████████████░░░░░░░░░░░░░░] 45%       │   │
│ │ Memory:       [██████░░░░░░░░░░░░░░░░░░░░] 28%       │   │
│ │ Audio Buffer: [███░░░░░░░░░░░░░░░░░░░░░░░] 12%       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Recent Messages (Live Log)                                   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ 12:34:56 [INFO] Scene triggered: "Drop Section"       │   │
│ │ 12:34:55 [INFO] Tempo changed: 120.0 -> 128.0 BPM    │   │
│ │ 12:34:52 [INFO] Loop recorded: Track 1 (4 bars)      │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Quick Actions                                                │
│ [Load Session] [Save Session] [Import Audio] [Export Mix]   │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Agent status indicators (running/stopped/error)
- ✅ Real-time performance metrics
- ✅ Live message log with filtering
- ✅ Quick access buttons
- ✅ System health indicators

### 3. Effects Chain View

**Purpose**: Configure and control live effects processing

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Chain: [Vocal Chain ▼]               [+ Add Chain]          │
├─────────────────────────────────────────────────────────────┤
│ Effects Chain Pipeline                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │ │
│ │  │  Gate    │ → │Compressor│ → │    EQ    │ → [+]      │ │
│ │  │  -40 dB  │   │  4:1     │   │  Bright  │            │ │
│ │  │  [BP]    │   │  [BP]    │   │  [BP]    │            │ │
│ │  └──────────┘   └──────────┘   └──────────┘            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ Selected Effect: Compressor                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Threshold: -18.0 dB  [━━━━━●━━━━━━━━━━━━━━━━━━━━━━]  │   │
│ │ Ratio:      4.0:1    [━━━━━━━━━●━━━━━━━━━━━━━━━━━━]  │   │
│ │ Attack:     5.0 ms   [━●━━━━━━━━━━━━━━━━━━━━━━━━━━]  │   │
│ │ Release:    50 ms    [━━━━●━━━━━━━━━━━━━━━━━━━━━━━]  │   │
│ │ Makeup:     Auto     [☑]  Wet/Dry: 100% [━━━━━━━━●]  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Presets: [Studio Vocal ▼]  [Save Preset] [A/B Compare]      │
│                                                               │
│ Meters:                                                      │
│ Input:  [████████████████░░] -6 dB                           │
│ Output: [█████████████░░░░░] -9 dB (GR: -3 dB)              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Visual effect chain pipeline
- ✅ Drag & drop to reorder effects
- ✅ Real-time parameter controls (knobs/sliders)
- ✅ VU meters (input/output/gain reduction)
- ✅ Bypass toggles per effect
- ✅ Preset management
- ✅ A/B comparison
- ✅ Effect library browser
- ✅ Wet/dry mix control

**Effect Library Panel (Collapsible):**
```
┌─────────────────────────┐
│ Available Effects       │
├─────────────────────────┤
│ Dynamics                │
│  - Compressor           │
│  - Limiter              │
│  - Gate                 │
│  - Expander             │
│ EQ                      │
│  - Parametric EQ        │
│  - Graphic EQ           │
│ Time-Based              │
│  - Reverb               │
│  - Delay                │
│  - Chorus               │
│  - Flanger              │
│ Modulation              │
│  - Phaser               │
│  - Tremolo              │
│  - Vibrato              │
│ Distortion              │
│  - Distortion           │
│  - Saturation           │
└─────────────────────────┘
```

### 4. Live Looping View

**Purpose**: Record, playback, and manipulate loops

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Loop Tracks                                                  │
├─────────────────────────────────────────────────────────────┤
│ Track 1: Drums        [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│ │ 4 bars │ 120 BPM │ Quantized                          │   │
│ └───────────────────────────────────────────────────────┘   │
│ [Overdub] [Replace] [Multiply] [Reverse] [Pitch +/-]        │
│                                                               │
│ Track 2: Bass         [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│ │ 2 bars │ 120 BPM │ Synced                             │   │
│ └───────────────────────────────────────────────────────┘   │
│ [Overdub] [Replace] [Multiply] [Reverse] [Pitch +/-]        │
│                                                               │
│ Track 3: Melody       [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Empty - Click [●] to start recording                  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Global Controls                                              │
│ Sync to Clock: [☑]  Quantize: [☑]  Undo: [⟲]  Redo: [⟳]   │
│ Master Volume: [━━━━━●━━━━━━]                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Up to 8 loop tracks
- ✅ Waveform visualization
- ✅ Record/Play/Stop per track
- ✅ Overdub/Replace/Multiply modes
- ✅ Loop manipulation (reverse, pitch, speed)
- ✅ Tempo sync visualization
- ✅ Undo/redo system (10 levels)
- ✅ Volume/pan per track
- ✅ Beat grid overlay

### 5. Sync & Clock View

**Purpose**: Tempo, transport, and synchronization control

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Transport Control                                            │
│ ┌───────────────────────────────────────────────────────┐   │
│ │       [◀◀]      [▶]      [■]      [▶▶]               │   │
│ │     Rewind     Play     Stop    Forward               │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Tempo Control                                                │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  BPM:  [  120.0  ]  [-] [+]  [Tap Tempo]             │   │
│ │  Time Signature: [4] / [4]                            │   │
│ │  Position: Bar 16 | Beat 3.24 | Time 00:01:32.500    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Synchronization                                              │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  MIDI Clock:     [☐] Enable  Port: [MIDI OUT 1 ▼]    │   │
│ │  Ableton Link:   [☐] Enable  Peers: 0                │   │
│ │  Tempo Detect:   [Analyze Audio] Detected: -- BPM    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Timeline Visualization                                       │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  |----|----|----|----|----|----|----|----|----|----|  │   │
│ │  1    2    3    4    5    6    7    8    9    10     │   │
│ │         ▲ Playhead                                    │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Large transport buttons
- ✅ Tempo control (type, tap, +/-)
- ✅ Time signature selector
- ✅ Position display (bars/beats/time)
- ✅ MIDI clock enable/port select
- ✅ Ableton Link enable/peer count
- ✅ Tempo detection
- ✅ Timeline with playhead

### 6. Performance Automation View

**Purpose**: Scene management, macros, cues, automation recording/playback

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ ┌─ Scenes ─────┐  ┌─ Macros ────┐  ┌─ Cues ──────┐        │
│ │ [1] Intro    │  │ Energy      │  │ Drop 2:30   │        │
│ │ [2] Verse    │  │ [━━━━━●━━━] │  │ ● 00:02:30  │        │
│ │►[3] Drop     │  │             │  │ [Fire Now]  │        │
│ │ [4] Breakdown│  │ Brightness  │  │             │        │
│ │ [5] Outro    │  │ [━━━●━━━━━] │  │ Build 1:45  │        │
│ │ [+ New]      │  │             │  │ ○ 00:01:45  │        │
│ └──────────────┘  └─────────────┘  │ [Fire Now]  │        │
│                                    └─────────────┘        │
│                                                             │
│ Scene Editor: "Drop"                                        │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Parameter Snapshots:                                  │  │
│ │  effects.filter.cutoff    20000 Hz  [Linear    ]     │  │
│ │  effects.reverb.wet_dry      0.6    [Exponential]    │  │
│ │  effects.delay.feedback      0.4    [Linear    ]     │  │
│ │  [+ Add Parameter]                                    │  │
│ │                                                        │  │
│ │ Transition Time: [2.0] seconds                        │  │
│ │ [Save Changes] [Discard]                              │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ Automation Recording                                        │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Recording: ● effects.reverb.wet_dry                   │  │
│ │ [■ Stop Recording]  [▶ Enable Playback]               │  │
│ │                                                        │  │
│ │ Timeline:                                              │  │
│ │ ┌───────────────────────────────────────────────────┐ │  │
│ │ │     ●───────●────────●──────────●                 │ │  │
│ │ │   0.0     1.0      2.0        3.0                 │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ │ Curve: [Linear ▼]  [Delete Points]                   │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Scene list with trigger buttons
- ✅ Macro controls (multi-parameter sliders)
- ✅ Cue list with timecode
- ✅ Scene editor (parameter snapshots, curves)
- ✅ Automation recording/playback
- ✅ Timeline visualization
- ✅ Curve type selection
- ✅ Manual cue firing

### 7. Settings View

**Purpose**: System configuration, preferences, I/O setup

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ ┌─ Audio I/O ──────────────────────────────────────────┐   │
│ │ Input Device:  [ASIO Device ▼]                        │   │
│ │ Output Device: [ASIO Device ▼]                        │   │
│ │ Sample Rate:   [44100 Hz ▼]                           │   │
│ │ Buffer Size:   [512 samples ▼] (11.6 ms latency)     │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ ┌─ Agent Configuration ─────────────────────────────────┐   │
│ │ Effects Chain:         [☑] Enabled  Max Chains: [16] │   │
│ │ Live Looping:          [☑] Enabled  Max Tracks: [8]  │   │
│ │ Sync Clock:            [☑] Enabled                    │   │
│ │ Performance Automation:[☑] Enabled                    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ ┌─ UI Preferences ──────────────────────────────────────┐   │
│ │ Theme:        [Dark ▼]                                │   │
│ │ Font Size:    [Medium ▼]                              │   │
│ │ Meter Style:  [VU ▼]                                  │   │
│ │ Show Tooltips:[☑]                                     │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ ┌─ Performance ─────────────────────────────────────────┐   │
│ │ CPU Threshold: [85]%  [Enable CPU limiter: ☐]        │   │
│ │ Memory Threshold: [90]%                               │   │
│ │ Auto-save interval: [5] minutes [☑]                  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ [Apply] [Reset to Defaults] [Cancel]                        │
└─────────────────────────────────────────────────────────────┘
```

---

## UI Components Library

### Custom Widgets (To Be Implemented)

#### 1. **RotaryKnob Widget**
```python
class RotaryKnob(QWidget):
    """
    Circular knob control for parameters
    - Value range: 0.0 to 1.0 (scaled internally)
    - Visual: Arc-based indicator
    - Interaction: Click + drag or mouse wheel
    - Display: Center value label
    """
```

**Features:**
- Smooth rotation animation
- Value tooltip on hover
- Double-click to reset to default
- MIDI learn capability
- Parameter automation recording

#### 2. **VUMeter Widget**
```python
class VUMeter(QWidget):
    """
    Professional VU meter with peak hold
    - Ranges: -60 dB to +6 dB
    - Styles: VU, PPM, Loudness (LUFS)
    - Peak indicators
    - Clip warning
    """
```

**Features:**
- Real-time level display
- Peak hold with decay
- Configurable ballistics (fast/slow)
- Color gradient (green/yellow/red)
- Clip indicator

#### 3. **WaveformView Widget**
```python
class WaveformView(QWidget):
    """
    Waveform visualization for loops
    - Zoomable timeline
    - Beat grid overlay
    - Playhead cursor
    - Selection regions
    """
```

**Features:**
- Pan and zoom
- Beat markers
- Loop points
- Transient detection markers

#### 4. **SpectrumAnalyzer Widget**
```python
class SpectrumAnalyzer(QWidget):
    """
    Real-time frequency spectrum display
    - FFT-based visualization
    - Configurable resolution
    - Peak hold
    - Smooth animation
    """
```

**Features:**
- 20 Hz - 20 kHz range
- dB scale
- Octave bands
- Peak markers

#### 5. **AutomationLaneWidget**
```python
class AutomationLaneWidget(QWidget):
    """
    Timeline-based automation editor
    - Add/remove/move points
    - Curve type selection
    - Grid snapping
    - Value editing
    """
```

**Features:**
- Bezier handles for curve editing
- Multi-selection of points
- Copy/paste automation
- Curve type icons

#### 6. **EffectChainWidget**
```python
class EffectChainWidget(QWidget):
    """
    Visual effect chain pipeline
    - Drag & drop reordering
    - Effect slots
    - Bypass toggles
    - Connection lines
    """
```

**Features:**
- Animated signal flow
- Drop zones between effects
- Effect type icons
- CPU usage per effect

---

## Integration Strategy

### Backend-to-GUI Communication

#### Message Bus Adapter

```python
# gui/backend_adapter.py

from PySide6.QtCore import QObject, Signal, QThread
from src.core import get_message_bus, Message
import queue

class MessageBusAdapter(QObject):
    """
    Thread-safe adapter between message bus and Qt GUI
    Runs in separate thread, emits Qt signals for GUI updates
    """

    # Qt Signals (thread-safe)
    tempo_changed = Signal(float)  # BPM
    scene_triggered = Signal(str, str)  # scene_id, scene_name
    loop_recorded = Signal(str, float)  # track_id, duration
    effect_parameter_changed = Signal(str, str, float)  # chain, param, value
    agent_status_changed = Signal(str, str)  # agent_id, status
    meter_update = Signal(str, float, float)  # meter_id, level_l, level_r

    def __init__(self):
        super().__init__()
        self.message_bus = get_message_bus()
        self.running = False
        self.message_queue = queue.Queue()

    def start(self):
        """Subscribe to relevant topics"""
        self.running = True

        # Subscribe to all relevant topics
        self.message_bus.subscribe("sync.clock.tempo", "gui", self._on_tempo_changed)
        self.message_bus.subscribe("automation.scene.triggered", "gui", self._on_scene_triggered)
        self.message_bus.subscribe("loop.record.stopped", "gui", self._on_loop_recorded)
        self.message_bus.subscribe("effects.parameter.change", "gui", self._on_parameter_changed)
        self.message_bus.subscribe("system.agent.*", "gui", self._on_agent_status)

    def _on_tempo_changed(self, message: Message):
        """Handle tempo change"""
        bpm = message.payload.get('bpm', 120.0)
        self.tempo_changed.emit(bpm)

    def _on_scene_triggered(self, message: Message):
        """Handle scene trigger"""
        scene_id = message.payload.get('scene_id', '')
        scene_name = message.payload.get('scene_name', '')
        self.scene_triggered.emit(scene_id, scene_name)

    # ... more handlers

    def publish_gui_event(self, topic: str, payload: dict):
        """Thread-safe message publishing from GUI"""
        message = Message(
            topic=topic,
            sender="gui",
            payload=payload
        )
        self.message_bus.publish(message)
```

#### GUI Controller

```python
# gui/main_controller.py

from PySide6.QtCore import QObject, Slot
from .backend_adapter import MessageBusAdapter

class MainController(QObject):
    """
    Central controller for GUI state and backend communication
    """

    def __init__(self):
        super().__init__()
        self.adapter = MessageBusAdapter()

        # Connect adapter signals to handlers
        self.adapter.tempo_changed.connect(self._update_tempo_display)
        self.adapter.scene_triggered.connect(self._highlight_scene)
        # ... more connections

        # Start adapter
        self.adapter.start()

    @Slot(float)
    def _update_tempo_display(self, bpm: float):
        """Update tempo display in UI"""
        # Update all widgets showing BPM
        pass

    @Slot(str, str)
    def _highlight_scene(self, scene_id: str, scene_name: str):
        """Highlight triggered scene in UI"""
        # Update scene list widget
        pass

    def set_tempo(self, bpm: float):
        """User action: Set tempo"""
        self.adapter.publish_gui_event("sync.tempo.set", {
            'bpm': bpm,
            'time_signature': '4/4'
        })
```

### Threading Model

```
Main Thread (Qt GUI Thread)
├── Window rendering
├── Event handling (mouse, keyboard)
├── Widget updates
└── Signal/slot connections

Worker Thread (Message Bus Adapter)
├── Message bus subscription
├── Backend message handling
├── Emit Qt signals
└── Message publishing queue

Backend Threads (Agent System)
├── Agent worker threads
├── Clock thread (1ms)
├── Playback thread (10ms)
└── Processing threads
```

**Key Rules:**
1. ✅ Only update GUI from main thread
2. ✅ Use Qt signals for cross-thread communication
3. ✅ Backend adapter runs in separate thread
4. ✅ Queue messages for publishing

---

## User Experience Design

### Workflow Optimization

#### 1. **Keyboard Shortcuts**
```
Global:
Ctrl+N        New Session
Ctrl+O        Open Session
Ctrl+S        Save Session
Ctrl+Q        Quit
Space         Play/Pause
Enter         Stop
Ctrl+Z        Undo
Ctrl+Y        Redo

Transport:
Home          Go to Start
End           Go to End
Left Arrow    Previous Bar
Right Arrow   Next Bar

Views:
F1            Dashboard
F2            Effects Chain
F3            Live Looping
F4            Sync & Clock
F5            Automation

Effects:
B             Toggle Bypass (selected effect)
Delete        Remove Effect
Ctrl+D        Duplicate Effect

Looping:
R             Record (selected track)
O             Overdub
M             Multiply
Ctrl+R        Reverse

Scenes:
1-9           Trigger Scene 1-9
Ctrl+1-9      Create/Edit Scene
```

#### 2. **Context Menus**
- Right-click effect → Bypass, Remove, Save Preset, A/B
- Right-click loop → Clear, Reverse, Export, Properties
- Right-click parameter → Automate, MIDI Learn, Reset

#### 3. **Drag & Drop**
- Drag effects to reorder
- Drag audio files to loop tracks
- Drag presets to effect slots
- Drag parameters to automation lanes

#### 4. **Visual Feedback**
- Animated transitions (200ms)
- Color-coded states (active/bypassed/error)
- Tooltips with parameter values
- Status indicators (●○◐)
- Progress bars for operations

### Accessibility

- **High Contrast Mode**: For visually impaired users
- **Large Font Option**: Scalable UI text
- **Keyboard Navigation**: Full keyboard control
- **Screen Reader Support**: ARIA labels (if Electron)
- **Tooltips**: Explain every control

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Basic window, navigation, backend connection

**Tasks:**
- [ ] Set up PySide6 project structure
- [ ] Create main window with tab navigation
- [ ] Implement MessageBusAdapter
- [ ] Create MainController
- [ ] Build Dashboard view (basic)
- [ ] Test backend communication

**Deliverable**: App launches, connects to backend, shows agent status

### Phase 2: Effects Chain UI (Week 2)
**Goal**: Full effects chain control

**Tasks:**
- [ ] Implement EffectChainWidget
- [ ] Create effect parameter controls
- [ ] Build effect library browser
- [ ] Add drag & drop support
- [ ] Implement preset system
- [ ] Create VUMeter widget

**Deliverable**: Can create chains, add effects, adjust parameters

### Phase 3: Looping UI (Week 2-3)
**Goal**: Loop recording and playback control

**Tasks:**
- [ ] Implement WaveformView widget
- [ ] Create loop track controls
- [ ] Build recording interface
- [ ] Add loop manipulation buttons
- [ ] Implement undo/redo
- [ ] Add transport sync visualization

**Deliverable**: Can record, playback, and manipulate loops

### Phase 4: Sync & Automation UI (Week 3-4)
**Goal**: Tempo, scenes, macros, cues

**Tasks:**
- [ ] Build transport controls
- [ ] Create tempo/time signature controls
- [ ] Implement scene management UI
- [ ] Build macro control widgets
- [ ] Create cue list and editor
- [ ] Implement AutomationLaneWidget

**Deliverable**: Full automation and sync control

### Phase 5: Polish & Optimization (Week 4-5)
**Goal**: Performance, UX, visual design

**Tasks:**
- [ ] Optimize real-time updates
- [ ] Implement themes (light/dark)
- [ ] Add animations and transitions
- [ ] Create keyboard shortcuts
- [ ] Add context menus
- [ ] Performance profiling
- [ ] Memory optimization

**Deliverable**: Polished, performant application

### Phase 6: Advanced Features (Week 5-6)
**Goal**: Session management, export, settings

**Tasks:**
- [ ] Implement session save/load
- [ ] Create settings dialog
- [ ] Add audio export
- [ ] Build preset manager
- [ ] Create help/documentation
- [ ] Add error handling and logging

**Deliverable**: Production-ready application

---

## Technical Specifications

### Performance Requirements

| Metric | Target | Critical |
|--------|--------|----------|
| UI Update Rate | 60 FPS | 30 FPS |
| Meter Update | 30 Hz | 20 Hz |
| Parameter Latency | <10ms | <50ms |
| Memory Usage | <200 MB | <500 MB |
| CPU (UI Thread) | <5% | <15% |
| Startup Time | <2s | <5s |

### Code Quality Standards

**Style Guide:**
- PEP 8 for Python code
- Type hints for all functions
- Docstrings (Google style)
- Maximum function length: 50 lines
- Maximum file length: 500 lines

**Testing:**
- Unit tests for all widgets
- Integration tests for controller
- Manual UI testing checklist
- Performance benchmarks

**Documentation:**
- User manual
- Developer guide
- API reference
- Architecture diagrams

### File Structure

```
F:/agents/
├── gui/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── main_window.py             # Main window class
│   ├── backend_adapter.py         # Message bus integration
│   ├── main_controller.py         # Central controller
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   ├── dashboard_view.py
│   │   ├── effects_chain_view.py
│   │   ├── looping_view.py
│   │   ├── sync_clock_view.py
│   │   ├── automation_view.py
│   │   └── settings_view.py
│   │
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── rotary_knob.py
│   │   ├── vu_meter.py
│   │   ├── waveform_view.py
│   │   ├── spectrum_analyzer.py
│   │   ├── automation_lane.py
│   │   └── effect_chain.py
│   │
│   ├── resources/
│   │   ├── icons/
│   │   ├── themes/
│   │   │   ├── dark.qss
│   │   │   └── light.qss
│   │   └── fonts/
│   │
│   └── utils/
│       ├── __init__.py
│       ├── settings_manager.py
│       └── session_manager.py
│
├── tests/
│   └── gui/
│       ├── test_widgets.py
│       ├── test_views.py
│       └── test_integration.py
│
└── docs/
    └── gui/
        ├── user_manual.md
        ├── developer_guide.md
        └── screenshots/
```

---

## Dependencies

### Python Packages (requirements-gui.txt)

```txt
# Core GUI Framework
PySide6>=6.5.0

# Audio Visualization
pyqtgraph>=0.13.0
matplotlib>=3.7.0

# Additional Utils
numpy>=1.24.0
pillow>=10.0.0  # Image loading

# Development
pytest-qt>=4.2.0  # GUI testing
black>=23.0.0  # Code formatting
mypy>=1.0.0  # Type checking
```

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-gui.txt

# Run GUI
python gui/main.py
```

---

## Risks & Mitigation

### Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Real-time performance issues | High | Medium | Profile early, optimize critical paths |
| Threading bugs (race conditions) | High | Medium | Strict signal/slot usage, thorough testing |
| Complex state synchronization | Medium | High | Single source of truth (backend), reactive UI |
| PySide6 learning curve | Medium | High | Prototype early, use Qt examples |
| Memory leaks | Medium | Low | Careful object lifecycle management |
| Platform compatibility issues | Low | Low | Test on multiple Windows versions |

---

## Success Criteria

### Minimum Viable Product (MVP)

- [ ] Application launches without errors
- [ ] All 5 main views functional
- [ ] Can control all agent features from GUI
- [ ] Real-time parameter updates work
- [ ] Session save/load functional
- [ ] No major performance issues
- [ ] Basic error handling

### Production Ready

- [ ] All MVP criteria met
- [ ] Comprehensive testing (100+ tests)
- [ ] User documentation complete
- [ ] Performance targets met
- [ ] Memory usage under control
- [ ] Professional visual design
- [ ] Keyboard shortcuts implemented
- [ ] Context menus functional
- [ ] Error recovery robust

---

## Future Enhancements

### Post-V1.0 Features

1. **Plugin System**
   - Load custom effects (VST3)
   - User-created widgets
   - Scripting API

2. **Cloud Features**
   - Preset sharing
   - Collaboration (multiple users)
   - Cloud backup

3. **Advanced Visualization**
   - 3D spectrum analyzer
   - Waveform morphing animations
   - Custom skins/themes

4. **MIDI Control**
   - Hardware controller mapping
   - MIDI learn
   - Control surfaces (Ableton Push, etc.)

5. **Mobile Companion App**
   - Remote control via tablet/phone
   - Wireless MIDI control
   - Quick preset triggering

---

## Conclusion

This plan provides a comprehensive roadmap for building a professional Windows GUI for the Multi-Agent Audio Processing System. The PySide6-based approach ensures:

✅ **Performance**: Native Qt rendering, low latency
✅ **Integration**: Direct Python backend connection
✅ **Scalability**: Modular architecture, easy to extend
✅ **Professional**: Industry-standard audio UI patterns
✅ **Maintainable**: Clean code structure, well-tested

**Next Steps:**
1. Review and approve plan
2. Set up development environment
3. Start Phase 1 implementation
4. Iterate based on user feedback

**Estimated Timeline**: 4-6 weeks to MVP, 6-8 weeks to production-ready.
