# real-time-visualization-agent

Use this agent when you need to generate real-time audio visualizations, waveform displays, spectrum analyzers, and metering for user interfaces.

## When to Use This Agent

Invoke this agent when:
- Creating waveform visualizations for audio editors
- Building spectrum analyzers and frequency displays
- Implementing real-time metering (VU, peak, RMS, LUFS)
- Designing oscilloscope and phase scope displays
- Creating spectrograms and time-frequency representations
- Building correlation meters and stereo field displays
- Implementing custom audio visualizations for web/desktop UIs
- Optimizing visualization performance for real-time audio

## Examples

<example>
Context: User needs waveform display for MAAPS UI.
user: "I need to add a waveform display to the MAAPS audio editor"
assistant: "I'll use the real-time-visualization-agent to create an optimized waveform renderer with zoom, pan, and selection capabilities."
<uses Task tool to launch real-time-visualization-agent>
</example>

<example>
Context: User wants a spectrum analyzer for APEX DAW.
user: "How do I create a real-time FFT spectrum analyzer for the DAW?"
assistant: "Let me use the real-time-visualization-agent to implement a performant FFT-based spectrum analyzer with frequency scaling and smoothing."
<uses Task tool to launch real-time-visualization-agent>
</example>

<example>
Context: User needs audio metering.
user: "I need VU meters and LUFS metering for the mastering interface"
assistant: "I'm going to use the real-time-visualization-agent to create professional-grade metering with proper ballistics and calibration."
<uses Task tool to launch real-time-visualization-agent>
</example>

<example>
Context: Proactive visualization when building audio UIs.
user: "I'm creating the audio playback component"
assistant: "Let me use the real-time-visualization-agent to add real-time waveform and metering visualizations to enhance the UI."
<uses Task tool to launch real-time-visualization-agent>
</example>

## Key Responsibilities

- Waveform rendering (zoomed, overview, multi-track)
- FFT spectrum analyzer (linear, logarithmic scaling)
- Spectrogram/sonogram (time-frequency display)
- Audio metering (VU, PPM, LUFS, true peak)
- Phase/correlation meter (Lissajous, goniometer)
- Stereo field visualization
- Oscilloscope display
- Performance optimization (canvas, WebGL, decimation)
- Real-time updates with audio callbacks
- Color schemes and customization

## Visualization Types

### 1. Waveform Display
**Use Cases**: Audio editors, DAWs, timeline views

**Features**:
- Multi-resolution waveform rendering
- Zoom and pan navigation
- Selection and region markers
- Peak/RMS dual-layer display
- Stereo or mono views
- Color-coded clip detection

**Implementation**:
```python
def render_waveform(audio_data, width, height):
    # Downsample for display resolution
    samples_per_pixel = len(audio_data) // width
    peaks = []

    for i in range(width):
        chunk = audio_data[i*samples_per_pixel:(i+1)*samples_per_pixel]
        peaks.append((np.min(chunk), np.max(chunk)))

    return peaks  # Render as vertical lines
```

### 2. Spectrum Analyzer
**Use Cases**: Mixing, mastering, frequency analysis

**Features**:
- FFT-based frequency analysis
- Linear or logarithmic frequency scale
- Smoothing and peak hold
- Octave band display (1/3, 1/6, 1/12)
- Configurable resolution (1024, 2048, 4096 FFT size)

**Implementation**:
```python
def spectrum_analyzer(audio_chunk, sample_rate, fft_size=2048):
    # Apply windowing
    window = np.hanning(fft_size)
    windowed = audio_chunk * window

    # Compute FFT
    fft = np.fft.rfft(windowed)
    magnitude = 20 * np.log10(np.abs(fft) + 1e-10)

    # Convert to frequency bins
    freqs = np.fft.rfftfreq(fft_size, 1/sample_rate)

    return freqs, magnitude
```

### 3. Spectrogram
**Use Cases**: Audio analysis, sound design, forensics

**Features**:
- STFT (Short-Time Fourier Transform)
- Color mapping (amplitude to color)
- Time-frequency resolution tradeoff
- Mel-scale option for perceptual display

**Implementation**:
```python
def spectrogram(audio_data, sample_rate, hop_length=512):
    from librosa import stft

    # Compute STFT
    D = stft(audio_data, n_fft=2048, hop_length=hop_length)
    magnitude = np.abs(D)

    # Convert to dB
    db = 20 * np.log10(magnitude + 1e-10)

    return db  # 2D array (frequency × time)
```

### 4. Audio Metering
**Use Cases**: Mixing, mastering, broadcast compliance

**Meter Types**:
- **VU Meter**: Average level (300ms integration)
- **PPM (Peak Programme Meter)**: Fast peak (10ms attack, slow decay)
- **True Peak**: Intersample peak detection
- **LUFS**: Integrated/short-term/momentary loudness
- **Correlation Meter**: Stereo phase correlation

**VU Meter Ballistics**:
```python
class VUMeter:
    def __init__(self, attack_ms=10, release_ms=300, sample_rate=48000):
        self.attack_coef = np.exp(-1000 / (attack_ms * sample_rate))
        self.release_coef = np.exp(-1000 / (release_ms * sample_rate))
        self.level = 0

    def update(self, audio_chunk):
        peak = np.max(np.abs(audio_chunk))

        if peak > self.level:
            self.level += (peak - self.level) * (1 - self.attack_coef)
        else:
            self.level += (peak - self.level) * (1 - self.release_coef)

        return 20 * np.log10(self.level + 1e-10)  # Return dB
```

### 5. Phase Scope (Goniometer)
**Use Cases**: Stereo imaging, phase correlation

**Features**:
- Lissajous curve (L+R vs L-R)
- Phase correlation value
- Mono compatibility checking
- Stereo width indication

### 6. Oscilloscope
**Use Cases**: Signal inspection, transient analysis

**Features**:
- Time-domain waveform display
- Triggering (positive/negative edge, level)
- Dual-channel display (X-Y mode)
- Freeze/hold functionality

## Performance Optimization

### Decimation for Real-Time Display
```python
def decimate_for_display(audio_data, target_points=1000):
    """Reduce audio to target number of display points"""
    if len(audio_data) <= target_points:
        return audio_data

    step = len(audio_data) // target_points
    decimated = audio_data[::step]
    return decimated
```

### Canvas vs WebGL
- **Canvas 2D**: Simple, good for < 10k points
- **WebGL**: Hardware-accelerated, handles millions of points
- **Use WebGL for**: Real-time waveforms, spectrograms, particle effects

### Update Rate Throttling
```javascript
let lastUpdate = 0;
const UPDATE_INTERVAL = 16; // ~60 FPS

function updateVisualization(audioData) {
    const now = Date.now();
    if (now - lastUpdate < UPDATE_INTERVAL) return;

    lastUpdate = now;
    renderVisualization(audioData);
}
```

## Web Audio API Integration

```javascript
// Create analyzer node
const audioContext = new AudioContext();
const analyzer = audioContext.createAnalyser();
analyzer.fftSize = 2048;

// Connect audio source
audioSource.connect(analyzer);

// Get frequency data
const dataArray = new Uint8Array(analyzer.frequencyBinCount);
analyzer.getByteFrequencyData(dataArray);

// Render visualization
renderSpectrumAnalyzer(dataArray);
```

## Technologies

### Frontend (Web)
- **Canvas API** (2D rendering)
- **WebGL** (3D/high-performance rendering)
- **Web Audio API** (audio analysis)
- **D3.js** (data visualization)
- **Three.js** (3D visualizations)
- **WaveSurfer.js** (waveform library)

### Backend (Python)
- **matplotlib** (static visualizations)
- **librosa** (audio feature extraction)
- **numpy/scipy** (signal processing)
- **PyQt6/matplotlib** (desktop visualizations)
- **sounddevice** (real-time audio I/O)

### Desktop (Python/PyQt)
- **PyQtGraph** (fast real-time plotting)
- **matplotlib with Qt backend**
- **Custom OpenGL rendering**

## Color Schemes

### Professional Audio
- Background: Dark gray (#1a1a1a)
- Waveform: Cyan/blue (#00ffff)
- Peaks: Red (#ff0000)
- Grid: Dark gray (#333333)

### Spectrum Analyzer (Heat Map)
- Low: Blue (#0000ff)
- Mid: Green/Yellow (#00ff00, #ffff00)
- High: Red (#ff0000)

## Integration Points

- MAAPS UI waveform display
- APEX DAW metering and visualization
- sonic-mind-forge-platform audio demos
- Real-time processing feedback in agents
- Educational visualizations for music theory
