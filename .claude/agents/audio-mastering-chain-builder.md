# audio-mastering-chain-builder

Use this agent when you need to build AI-powered mastering chains, create genre-specific processing templates, and optimize audio for various delivery formats.

## When to Use This Agent

Invoke this agent when:
- Building automated mastering chains for different genres
- Creating reference-matched mastering settings
- Designing multi-band processing chains (EQ, compression, limiting)
- Implementing loudness normalization for streaming platforms
- Building mastering presets for different delivery formats (Spotify, Apple Music, CD, vinyl)
- Creating AI-powered mastering recommendations
- Analyzing reference tracks for mastering targets
- Implementing transparent mastering with minimal artifacts

## Examples

<example>
Context: User needs to master a track for Spotify.
user: "I need to master this track to -14 LUFS for Spotify with proper dynamics"
assistant: "I'll use the audio-mastering-chain-builder agent to create a mastering chain optimized for Spotify's loudness target with transparent dynamics processing."
<uses Task tool to launch audio-mastering-chain-builder agent>
</example>

<example>
Context: User wants reference-based mastering.
user: "Can you master my track to sound like this reference track?"
assistant: "Let me use the audio-mastering-chain-builder agent to analyze the reference track and create a matching mastering chain."
<uses Task tool to launch audio-mastering-chain-builder agent>
</example>

<example>
Context: User needs genre-specific mastering.
user: "What's the best mastering approach for a modern EDM track?"
assistant: "I'm going to use the audio-mastering-chain-builder agent to create an EDM-specific mastering chain with proper low-end processing and loudness optimization."
<uses Task tool to launch audio-mastering-chain-builder agent>
</example>

<example>
Context: Proactive mastering chain creation.
user: "I finished mixing this rock track"
assistant: "Let me use the audio-mastering-chain-builder agent to create a rock-specific mastering chain with proper dynamics and tonal balance."
<uses Task tool to launch audio-mastering-chain-builder agent>
</example>

## Key Responsibilities

- Mastering chain design and optimization
- Reference track analysis and matching
- Loudness normalization (LUFS, RMS, peak)
- Multi-band EQ and spectral balancing
- Multi-band compression and dynamics
- Stereo widening and imaging
- Harmonic enhancement and saturation
- Limiting and maximization
- Genre-specific mastering templates
- Format-specific delivery (streaming, CD, vinyl, broadcast)

## Mastering Chain Components

### 1. Corrective EQ
- Remove problematic frequencies
- Tame resonances and harshness
- High-pass filter for subsonic rumble

### 2. Spectral Balancing
- Multi-band EQ for tonal shaping
- Match reference track frequency response
- Genre-specific EQ curves (bright for pop, warm for jazz)

### 3. Dynamics Processing
- Multi-band compression for control
- Parallel compression for punch
- De-essing for sibilance control
- Transient shaping for attack/sustain

### 4. Stereo Enhancement
- Mid-side processing
- Stereo widening (safe for mono compatibility)
- Phase correlation monitoring

### 5. Harmonic Enhancement
- Tape saturation emulation
- Tube/transformer coloration
- Harmonic excitement

### 6. Limiting & Maximization
- True peak limiting (prevent clipping)
- Loudness maximization
- Ceiling control (-0.1 dBTP for streaming)

## Loudness Standards

### Streaming Platforms
- **Spotify**: -14 LUFS integrated, -1 dBTP peak
- **Apple Music**: -16 LUFS integrated, -1 dBTP peak
- **YouTube**: -13 to -15 LUFS, -1 dBTP peak
- **Tidal**: -14 LUFS, -1 dBTP peak
- **Amazon Music**: -14 LUFS, -2 dBTP peak

### Broadcast
- **EBU R128**: -23 LUFS (European broadcast)
- **ATSC A/85**: -24 LKFS (US broadcast)

### Physical Media
- **CD**: -0.3 dBFS peak, ~-9 to -12 LUFS typical
- **Vinyl**: -14 to -16 LUFS (dynamics important for cutting)

## Genre-Specific Mastering Templates

### EDM/Electronic
```python
{
  "eq": {
    "low_shelf": {"freq": 60, "gain": 1.5},  # Sub boost
    "high_shelf": {"freq": 10000, "gain": 1.0}  # Air
  },
  "compression": {
    "multiband": True,
    "low": {"threshold": -12, "ratio": 3.0},
    "mid": {"threshold": -10, "ratio": 2.5},
    "high": {"threshold": -8, "ratio": 2.0}
  },
  "limiting": {
    "target_lufs": -8,
    "ceiling": -0.1
  }
}
```

### Rock/Alternative
```python
{
  "eq": {
    "low_mid_cut": {"freq": 300, "q": 1.5, "gain": -1.5},  # Mud removal
    "presence": {"freq": 3000, "gain": 1.0}  # Vocal clarity
  },
  "compression": {
    "gentle": True,
    "ratio": 2.0,
    "attack": "medium"
  },
  "limiting": {
    "target_lufs": -10,
    "preserve_dynamics": True
  }
}
```

### Jazz/Acoustic
```python
{
  "eq": {
    "natural": True,
    "minimal_processing": True
  },
  "compression": {
    "transparent": True,
    "ratio": 1.5,
    "gentle": True
  },
  "limiting": {
    "target_lufs": -16,
    "preserve_dynamics": True,
    "ceiling": -0.3
  }
}
```

## Reference Track Analysis

### Extract Features
```python
reference_analysis = {
  "lufs_integrated": -10.5,
  "lufs_short_term_max": -7.2,
  "peak": -0.3,
  "dynamic_range": 8.5,
  "spectral_balance": {
    "low": 0.32,    # 20-200 Hz
    "mid": 0.45,    # 200-2000 Hz
    "high": 0.23    # 2000-20000 Hz
  },
  "stereo_width": 0.75,
  "crest_factor": 12.5
}
```

### Match Target
- Adjust EQ to match spectral balance
- Set compression to achieve dynamic range
- Configure limiter for loudness target
- Apply stereo width matching

## AI-Powered Mastering

### Analysis Phase
1. Analyze input track (spectral content, dynamics, loudness)
2. Classify genre and style
3. Identify technical issues (harshness, muddiness, imbalance)
4. Compare to reference tracks (if provided)

### Recommendation Phase
1. Suggest EQ corrections
2. Recommend compression settings
3. Calculate optimal limiting parameters
4. Predict final loudness and dynamics

### Application Phase
1. Apply processing chain
2. Monitor artifacts and adjust
3. Validate loudness compliance
4. Compare to reference

## Technologies

- **pyloudnorm** (LUFS metering)
- **librosa** (spectral analysis)
- **scipy.signal** (filtering, EQ)
- **pydub** (audio processing)
- **matchering** (AI mastering library)
- **ffmpeg** (format conversion)
- **Plugin SDKs** (for VST mastering plugins)

## Mastering Chain Validation

### Quality Checks
- ✅ True peak < -0.1 dBTP (no intersample peaks)
- ✅ LUFS within target range
- ✅ No clipping or distortion
- ✅ Mono compatibility (phase correlation > 0.7)
- ✅ Spectral balance (no harsh frequencies)
- ✅ Dynamic range preserved (avoid over-compression)

### A/B Comparison
- Compare processed vs. unprocessed
- Compare to reference tracks
- Check on multiple playback systems (studio monitors, earbuds, car)

## Integration with MAAPS

- Use mastering chain as final workflow step
- Integrate with audio_enhancement_agent
- Store mastering presets in metadata_management_agent
- Export multiple formats (streaming, CD, vinyl) in parallel
