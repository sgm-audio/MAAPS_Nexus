# Musical Analysis & Transcription Multi-Agent System

## Overview

This multi-agent system provides comprehensive musical analysis and transcription capabilities that integrate seamlessly with both studio production and live performance systems. It goes far beyond simple loudness evaluation to provide deep tonal, harmonic, and rhythmic analysis, plus the ability to generate MIDI data and tablature from any audio source.

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Musical Analysis & Transcription System             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Musical Analysis│  │ Audio-to-MIDI    │  │ Tablature  │ │
│  │ Agent           │  │ Transcription    │  │ Generation │ │
│  │ (Key, Tempo,    │  │ Agent            │  │ Agent      │ │
│  │  Tonality)      │  │                  │  │            │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Harmonic        │  │ Rhythm Analysis  │  │ Multi-Track│ │
│  │ Analysis Agent  │  │ Agent            │  │ Coordinator│ │
│  │ (Chords, Prog.) │  │ (Beat, Groove)   │  │ Agent      │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
           ↕                    ↕                    ↕
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ Studio System    │  │ Live Performance │  │ Stem Separation │
│ (5 Agents)       │  │ System           │  │ (Existing)      │
│ - Enhancement    │  │ (11 Agents)      │  │                 │
│ - Generation     │  │ - Real-time I/O  │  │                 │
│ - Optimization   │  │ - Effects        │  │                 │
│ - Metadata       │  │ - MIDI Control   │  │                 │
│ - Workflow       │  │ - Standards      │  │                 │
└──────────────────┘  └──────────────────┘  └─────────────────┘
```

## Agent Descriptions

### 1. Musical Analysis Agent

**Purpose:** Core agent for detecting musical characteristics including key, tempo, time signature, scale type, modulations, and overall tonal characteristics.

**Capabilities:**
- Key detection (24 major/minor keys)
- Tempo detection (BPM with confidence scoring)
- Time signature identification (4/4, 3/4, 6/8, etc.)
- Scale detection (major, minor, modes, exotic scales)
- Modulation detection (key changes throughout the piece)
- Pitch center analysis
- Tonal brightness/darkness evaluation
- Consonance/dissonance scoring
- Genre classification based on tonal characteristics

**Topics:**
- `musical.analysis.key` - Key detection
- `musical.analysis.tempo` - Tempo detection
- `musical.analysis.time_signature` - Time signature detection
- `musical.analysis.scale` - Scale identification
- `musical.analysis.modulation` - Key change detection
- `musical.analysis.comprehensive` - Full analysis

**Data Structures:**
```python
@dataclass
class MusicalAnalysis:
    key: str  # e.g., "C major", "A minor"
    key_confidence: float  # 0.0-1.0
    tempo_bpm: float
    tempo_confidence: float
    time_signature: str  # e.g., "4/4", "3/4"
    scale_type: str  # e.g., "major", "minor", "dorian"
    modulations: List[Modulation]  # Key changes with timestamps
    pitch_center: float  # Hz
    tonal_brightness: float  # -1.0 (dark) to 1.0 (bright)
    consonance_score: float  # 0.0 (dissonant) to 1.0 (consonant)
    genre_prediction: List[Tuple[str, float]]  # Genre with confidence
```

### 2. Audio-to-MIDI Transcription Agent

**Purpose:** Converts audio signals (monophonic or polyphonic) into MIDI note data with accurate pitch, timing, and velocity information.

**Capabilities:**
- Monophonic transcription (single instrument/voice)
- Polyphonic transcription (chords, multiple notes)
- Pitch detection with microtonal accuracy
- Note onset/offset detection
- Velocity estimation from amplitude
- Pitch bend and vibrato capture
- Glissando and slide detection
- Support for stem-based transcription (more accurate)
- Real-time transcription mode (for live input)

**Topics:**
- `transcription.audio_to_midi` - Convert audio to MIDI
- `transcription.monophonic` - Monophonic-only transcription
- `transcription.polyphonic` - Polyphonic transcription
- `transcription.from_stem` - Transcribe from separated stem
- `transcription.realtime` - Real-time transcription

**Data Structures:**
```python
@dataclass
class MIDINote:
    pitch: int  # MIDI note number (0-127)
    start_time: float  # seconds
    duration: float  # seconds
    velocity: int  # 0-127
    pitch_bend: Optional[List[Tuple[float, int]]]  # time, bend value
    confidence: float  # 0.0-1.0

@dataclass
class MIDITranscription:
    notes: List[MIDINote]
    tempo_bpm: float
    time_signature: str
    key: str
    track_name: str
    instrument_type: str  # "guitar", "piano", "vocals", etc.
    polyphony_detected: bool
    accuracy_estimate: float  # 0.0-1.0
```

### 3. Tablature Generation Agent

**Purpose:** Generates instrument-specific tablature (guitar, bass, ukulele, mandolin) from MIDI data or audio, with intelligent fingering and fret position suggestions.

**Capabilities:**
- Guitar tablature (standard 6-string, 7-string, 8-string)
- Bass tablature (4-string, 5-string, 6-string)
- Ukulele tablature
- Mandolin tablature
- Intelligent fingering suggestions
- Fret position optimization (minimize hand movement)
- Alternate tunings support (Drop D, Open G, etc.)
- Technique notation (hammer-on, pull-off, slide, bend)
- Chord diagrams
- ASCII and MusicXML output formats

**Topics:**
- `tablature.generate` - Generate tab from MIDI
- `tablature.from_audio` - Generate tab directly from audio
- `tablature.optimize_fingering` - Optimize finger positions
- `tablature.export` - Export in various formats

**Data Structures:**
```python
@dataclass
class TabNote:
    string: int  # String number (1-6 for guitar)
    fret: int  # Fret number
    start_time: float
    duration: float
    technique: Optional[str]  # "h", "p", "s", "b", etc.
    finger: Optional[int]  # Suggested finger (1-4)

@dataclass
class Tablature:
    instrument: str  # "guitar", "bass", etc.
    tuning: List[str]  # ["E", "A", "D", "G", "B", "E"]
    notes: List[TabNote]
    tempo_bpm: float
    time_signature: str
    chord_diagrams: List[ChordDiagram]
    difficulty_rating: float  # 1.0 (easy) to 10.0 (expert)
```

### 4. Harmonic Analysis Agent

**Purpose:** Analyzes chord progressions, identifies chords, evaluates harmonic movement, and provides music theory insights.

**Capabilities:**
- Chord recognition (triads, 7ths, extended chords)
- Roman numeral analysis
- Chord progression identification
- Harmonic function analysis (tonic, dominant, subdominant)
- Circle of fifths movement detection
- Modal interchange identification
- Secondary dominants detection
- Harmonic rhythm analysis
- Voice leading analysis
- Tension/resolution patterns

**Topics:**
- `harmonic.chord.identify` - Identify chords
- `harmonic.progression.analyze` - Analyze chord progressions
- `harmonic.function` - Harmonic function analysis
- `harmonic.voice_leading` - Voice leading analysis

**Data Structures:**
```python
@dataclass
class Chord:
    root: str  # "C", "F#", etc.
    quality: str  # "major", "minor", "diminished", "augmented"
    extensions: List[str]  # ["7", "9", "sus4"]
    bass_note: Optional[str]  # For slash chords
    start_time: float
    duration: float
    roman_numeral: str  # "I", "V7", "ii", etc.
    function: str  # "tonic", "dominant", "subdominant"

@dataclass
class HarmonicAnalysis:
    chords: List[Chord]
    key: str
    chord_progression: List[str]  # ["I", "IV", "V", "I"]
    harmonic_rhythm: float  # Average chord change frequency
    complexity_score: float  # 0.0 (simple) to 1.0 (complex)
    common_progressions: List[str]  # "I-V-vi-IV", "ii-V-I"
```

### 5. Rhythm Analysis Agent

**Purpose:** Analyzes rhythmic patterns, beat structures, groove characteristics, and provides quantization suggestions.

**Capabilities:**
- Beat tracking and downbeat detection
- Tempo variation detection (rubato, accelerando, ritardando)
- Groove analysis (swing, shuffle, straight)
- Rhythmic complexity scoring
- Syncopation detection
- Polyrhythm identification
- Quantization suggestions (snap to grid)
- Microtiming analysis (humanization)
- Rhythmic motif detection
- Ghost note detection

**Topics:**
- `rhythm.beat.track` - Track beats and downbeats
- `rhythm.groove.analyze` - Analyze groove characteristics
- `rhythm.quantize` - Suggest quantization
- `rhythm.complexity` - Evaluate rhythmic complexity

**Data Structures:**
```python
@dataclass
class BeatGrid:
    beats: List[float]  # Beat timestamps in seconds
    downbeats: List[float]  # Downbeat timestamps
    tempo_curve: List[Tuple[float, float]]  # time, BPM
    grid_resolution: str  # "1/4", "1/8", "1/16", "1/32"

@dataclass
class RhythmicAnalysis:
    beat_grid: BeatGrid
    groove_type: str  # "straight", "swing", "shuffle"
    swing_percentage: float  # 0-100%
    syncopation_score: float  # 0.0-1.0
    complexity_score: float  # 0.0-1.0
    polyrhythms: List[str]  # "3:2", "4:3"
    microtiming_deviation: float  # milliseconds
```

### 6. Multi-Track Transcription Coordinator Agent

**Purpose:** Coordinates transcription of multi-track audio, optionally using stem separation for improved accuracy. Manages workflow between analysis, separation, and transcription agents.

**Capabilities:**
- Multi-track audio analysis coordination
- Automatic stem separation triggering
- Per-instrument transcription coordination
- Track identification (drums, bass, guitar, vocals, etc.)
- Transcription result merging
- Quality assessment and re-transcription
- Export coordination (MIDI, MusicXML, tablature)
- Integration with studio/live systems
- Real-time multi-source transcription

**Topics:**
- `coordinator.transcribe.multitrack` - Coordinate multi-track transcription
- `coordinator.separate_and_transcribe` - Trigger stem separation then transcribe
- `coordinator.merge_results` - Merge transcription results
- `coordinator.export` - Export all results

**Data Structures:**
```python
@dataclass
class TrackTranscription:
    track_id: str
    instrument_type: str
    midi_data: MIDITranscription
    tablature: Optional[Tablature]
    harmonic_analysis: HarmonicAnalysis
    rhythm_analysis: RhythmicAnalysis
    quality_score: float  # 0.0-1.0

@dataclass
class MultiTrackTranscription:
    project_name: str
    tracks: List[TrackTranscription]
    overall_analysis: MusicalAnalysis
    tempo_map: List[Tuple[float, float]]  # time, BPM
    key_changes: List[Tuple[float, str]]  # time, key
    time_signature_changes: List[Tuple[float, str]]
    export_formats: List[str]  # ["midi", "musicxml", "tab"]
```

## Integration Points

### Studio System Integration
- **Enhancement Agent** → Musical Analysis for pre/post enhancement comparison
- **Content Generation Agent** → Use analyzed characteristics as generation seeds
- **Metadata Management** → Store analysis results as metadata
- **Workflow Engine** → Automated transcription workflows

### Live Performance System Integration
- **Real-Time Audio I/O** → Live transcription of performances
- **MIDI Control Agent** → Generated MIDI controls effects/instruments
- **Live Looping Agent** → Analyze loops for key/tempo matching
- **Performance Monitoring** → Track musical accuracy/consistency
- **Industry Standards Agent** → Musical compliance with broadcast standards

### Stem Separation Integration
- **Automatic Stem Separation** → Triggered for polyphonic sources
- **Per-Stem Analysis** → Individual instrument characteristic analysis
- **Improved Accuracy** → Cleaner audio = better transcription
- **Instrument Isolation** → Separate drums, bass, melody, harmony

## Use Cases

### Use Case 1: Import Song and Transcribe
1. User imports MP3/WAV file
2. Multi-Track Coordinator analyzes audio
3. Determines polyphonic complexity
4. Triggers stem separation (if needed)
5. Each stem sent to Audio-to-MIDI Agent
6. Harmonic Analysis identifies chords
7. Rhythm Analysis maps groove
8. Tablature generated for guitar parts
9. Complete score exported as MIDI + tabs

### Use Case 2: Live Performance Transcription
1. Real-time audio from Live Audio I/O Agent
2. Musical Analysis detects key/tempo
3. Audio-to-MIDI transcribes on-the-fly
4. Rhythm Analysis tracks groove
5. Generated MIDI triggers backing tracks
6. Performance logged for review

### Use Case 3: Studio Production Enhancement
1. Record guitar performance
2. Musical Analysis evaluates tuning accuracy
3. Harmonic Analysis identifies out-of-key notes
4. Audio-to-MIDI generates reference MIDI
5. Enhancement Agent applies pitch correction
6. Metadata Agent stores analysis results

### Use Case 4: Educational Tool
1. Student plays exercise
2. System transcribes performance
3. Compares to reference tablature
4. Identifies mistakes (wrong notes, timing)
5. Provides feedback and scoring
6. Generates practice suggestions

## Performance Targets

- **Key Detection Accuracy:** >95% for clear audio
- **Tempo Detection Accuracy:** >98% for steady tempo
- **Monophonic Transcription:** >90% note accuracy
- **Polyphonic Transcription:** >80% note accuracy
- **Stem-Based Transcription:** >95% note accuracy
- **Chord Recognition:** >85% accuracy
- **Real-Time Latency:** <100ms for live transcription
- **Processing Speed:** >10x real-time for offline processing

## Technology Stack

### Core Libraries
- **librosa** - Audio analysis, feature extraction
- **pretty_midi** - MIDI file creation/manipulation
- **music21** - Music theory analysis, chord recognition
- **numpy/scipy** - Signal processing, FFT
- **crepe** (optional) - Deep learning pitch detection
- **madmom** (optional) - Beat tracking, chord recognition

### Algorithm Approaches
- **Pitch Detection:** YIN, PYIN, autocorrelation, harmonic product spectrum
- **Beat Tracking:** Dynamic programming, onset detection
- **Chord Recognition:** Chromagram analysis, HMM, template matching
- **Transcription:** Constant-Q transform, non-negative matrix factorization
- **Key Detection:** Krumhansl-Schmuckler algorithm, template matching

## Output Formats

### MIDI
- Type 0 (single track) or Type 1 (multi-track)
- Standard MIDI File format (.mid)
- Tempo and time signature meta events
- Program change messages for instrument selection

### Tablature
- ASCII text format (for display/printing)
- Guitar Pro format (.gp5, .gpx)
- MusicXML (for notation software)
- JSON format (for web applications)

### Analysis Reports
- JSON (machine-readable)
- Markdown (human-readable)
- PDF (formatted report)
- HTML (interactive visualization)

## Future Enhancements

1. **Machine Learning Models:**
   - Trained transcription models (Onsets and Frames, MT3)
   - Genre-specific chord recognition
   - Instrument-specific transcription optimization

2. **Advanced Features:**
   - Automatic drum notation
   - Vocal melody with lyrics alignment
   - Multi-instrument score generation
   - Automatic arrangement suggestions

3. **Collaboration:**
   - Cloud-based transcription processing
   - Collaborative editing of transcriptions
   - Community accuracy improvements
