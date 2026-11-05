"""
Harmonic Analysis Agent.

Analyzes chord progressions, identifies chords, evaluates harmonic movement,
and provides music theory insights.
"""

import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

try:
    import librosa
    import music21
    from scipy.signal import find_peaks
except ImportError as e:
    logging.warning(f"Missing harmonic analysis dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics

logger = logging.getLogger(__name__)


@dataclass
class Chord:
    """Represents a detected chord"""

    root: str  # "C", "F#", etc.
    quality: str  # "major", "minor", "diminished", "augmented"
    extensions: List[str] = field(default_factory=list)  # ["7", "9", "sus4"]
    bass_note: Optional[str] = None  # For slash chords
    start_time: float = 0.0
    duration: float = 0.0
    roman_numeral: str = ""  # "I", "V7", "ii", etc.
    function: str = ""  # "tonic", "dominant", "subdominant"
    confidence: float = 1.0


@dataclass
class HarmonicAnalysis:
    """Complete harmonic analysis results"""

    chords: List[Chord]
    key: str
    chord_progression: List[str]  # ["I", "IV", "V", "I"]
    harmonic_rhythm: float  # Average chord change frequency (chords per measure)
    complexity_score: float  # 0.0 (simple) to 1.0 (complex)
    common_progressions: List[str] = field(
        default_factory=list
    )  # "I-V-vi-IV", "ii-V-I"


class HarmonicAnalysisAgent(BaseAgent):
    """
    Agent for harmonic and chord analysis.

    Capabilities:
    - Chord recognition (triads, 7ths, extended chords)
    - Roman numeral analysis
    - Chord progression identification
    - Harmonic function analysis
    - Voice leading analysis
    - Common progression detection
    """

    # Chord templates (pitch class profiles)
    CHORD_TEMPLATES = {
        "major": [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "minor": [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
        "diminished": [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        "augmented": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "major7": [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        "minor7": [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
        "dominant7": [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        "sus2": [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        "sus4": [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
    }

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Common progressions
    COMMON_PROGRESSIONS = {
        "I-V-vi-IV": ["pop", "contemporary"],
        "I-IV-V-I": ["classical", "traditional"],
        "ii-V-I": ["jazz", "standard"],
        "I-vi-IV-V": ["50s", "doo-wop"],
        "I-IV-I-V": ["blues", "rock"],
        "vi-IV-I-V": ["pop", "modern"],
        "I-V-IV-V": ["rock", "alternative"],
        "ii-V-I-VI": ["jazz", "turnaround"],
    }

    def __init__(self):
        super().__init__(
            agent_id="harmonic_analysis_agent", agent_name="Harmonic Analysis Agent"
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "analyses_performed": 0,
            "chords_identified": 0,
            "progressions_analyzed": 0,
            "errors": 0,
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Harmonic Analysis Agent")

        # Subscribe to harmonic topics
        self.subscribe("harmonic.chord.identify")
        self.subscribe("harmonic.progression.analyze")
        self.subscribe("harmonic.function")
        self.subscribe("harmonic.voice_leading")

        self.log("INFO", "Harmonic Analysis Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Harmonic Analysis Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming analysis requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic == "harmonic.chord.identify":
                result = self._identify_chords(payload)
            elif topic == "harmonic.progression.analyze":
                result = self._analyze_progression(payload)
            elif topic == "harmonic.function":
                result = self._analyze_function(payload)
            elif topic == "harmonic.voice_leading":
                result = self._analyze_voice_leading(payload)
            else:
                result = {"success": False, "error": f"Unknown topic: {topic}"}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats["errors"] += 1
            self.respond(message, {"success": False, "error": str(e)})

    def _identify_chords(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Identify chords from audio"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            key = payload.get("key", "C major")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Extract chords
            chords = self._extract_chords(audio, sr)

            # Add harmonic analysis (roman numerals, function)
            chords = self._add_harmonic_context(chords, key)

            with self._lock:
                self._stats["chords_identified"] += len(chords)

            return {
                "success": True,
                "chords": [self._chord_to_dict(chord) for chord in chords],
                "key": key,
            }

        except Exception as e:
            logger.error(f"Error identifying chords: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_progression(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chord progression"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            key = payload.get("key")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Detect key if not provided
            if not key:
                key = self._detect_key(audio, sr)

            # Extract chords
            chords = self._extract_chords(audio, sr)
            chords = self._add_harmonic_context(chords, key)

            # Build progression
            progression = [
                chord.roman_numeral for chord in chords if chord.roman_numeral
            ]

            # Calculate harmonic rhythm
            if len(chords) > 0 and chords[-1].start_time > 0:
                duration = chords[-1].start_time + chords[-1].duration
                harmonic_rhythm = len(chords) / (
                    duration / 4
                )  # Chords per 4 seconds (approx measure)
            else:
                harmonic_rhythm = 1.0

            # Calculate complexity
            complexity = self._calculate_harmonic_complexity(chords)

            # Identify common progressions
            common = self._identify_common_progressions(progression)

            analysis = HarmonicAnalysis(
                chords=chords,
                key=key,
                chord_progression=progression,
                harmonic_rhythm=float(harmonic_rhythm),
                complexity_score=float(complexity),
                common_progressions=common,
            )

            with self._lock:
                self._stats["analyses_performed"] += 1
                self._stats["progressions_analyzed"] += 1

            return {
                "success": True,
                "analysis": {
                    "chords": [self._chord_to_dict(c) for c in analysis.chords],
                    "key": analysis.key,
                    "chord_progression": analysis.chord_progression,
                    "harmonic_rhythm": float(analysis.harmonic_rhythm),
                    "complexity_score": float(analysis.complexity_score),
                    "common_progressions": analysis.common_progressions,
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing progression: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_function(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze harmonic function of chords"""
        try:
            chords_data = payload.get("chords", [])
            key = payload.get("key", "C major")

            # Convert dict to Chord objects
            chords = [self._dict_to_chord(c) for c in chords_data]

            # Add function analysis
            chords = self._add_harmonic_context(chords, key)

            return {
                "success": True,
                "chords": [self._chord_to_dict(chord) for chord in chords],
            }

        except Exception as e:
            logger.error(f"Error analyzing function: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_voice_leading(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze voice leading between chords"""
        try:
            chords_data = payload.get("chords", [])

            if len(chords_data) < 2:
                return {
                    "success": False,
                    "error": "Need at least 2 chords for voice leading analysis",
                }

            chords = [self._dict_to_chord(c) for c in chords_data]

            voice_leading_analysis = []

            for i in range(len(chords) - 1):
                current = chords[i]
                next_chord = chords[i + 1]

                # Calculate voice movement
                movement = self._calculate_voice_movement(current, next_chord)

                voice_leading_analysis.append(
                    {
                        "from": f"{current.root}{current.quality}",
                        "to": f"{next_chord.root}{next_chord.quality}",
                        "movement": movement,
                        "smooth": movement["total_movement"]
                        < 5,  # Smooth if less than 5 semitones total
                    }
                )

            return {"success": True, "voice_leading": voice_leading_analysis}

        except Exception as e:
            logger.error(f"Error analyzing voice leading: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _extract_chords(self, audio: np.ndarray, sr: int) -> List[Chord]:
        """Extract chords from audio using chromagram"""
        # Extract chromagram
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=2048)

        # Detect chord change points
        change_points = self._detect_chord_changes(chroma)

        chords = []

        # Analyze each segment
        for i in range(len(change_points) - 1):
            start_frame = change_points[i]
            end_frame = change_points[i + 1]

            # Get average chroma for this segment
            segment_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)

            # Identify chord
            chord = self._identify_chord_from_chroma(segment_chroma)

            if chord:
                # Calculate timing
                start_time = librosa.frames_to_time(start_frame, sr=sr, hop_length=2048)
                end_time = librosa.frames_to_time(end_frame, sr=sr, hop_length=2048)

                chord.start_time = float(start_time)
                chord.duration = float(end_time - start_time)

                chords.append(chord)

        return chords

    def _detect_chord_changes(self, chroma: np.ndarray) -> List[int]:
        """Detect chord change points in chromagram"""
        # Calculate chroma change
        chroma_diff = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)

        # Smooth
        from scipy.ndimage import gaussian_filter1d

        chroma_diff_smooth = gaussian_filter1d(chroma_diff, sigma=2)

        # Find peaks
        threshold = np.mean(chroma_diff_smooth) + np.std(chroma_diff_smooth) * 0.5
        peaks, _ = find_peaks(chroma_diff_smooth, height=threshold, distance=8)

        # Add start and end
        change_points = [0] + list(peaks + 1) + [chroma.shape[1]]

        return change_points

    def _identify_chord_from_chroma(self, chroma: np.ndarray) -> Optional[Chord]:
        """Identify chord from chroma vector"""
        # Normalize
        if np.sum(chroma) > 0:
            chroma = chroma / np.sum(chroma)
        else:
            return None

        # Threshold to find active pitch classes
        threshold = 0.15
        active_pitches = chroma > threshold

        if np.sum(active_pitches) < 2:
            return None  # Not enough notes for a chord

        best_match = None
        best_score = -1

        # Try each chord template at each root
        for root in range(12):
            for quality, template in self.CHORD_TEMPLATES.items():
                # Rotate template to root
                rotated = np.roll(template, root)

                # Calculate correlation
                score = np.dot(chroma, rotated)

                if score > best_score:
                    best_score = score
                    best_match = (root, quality)

        if best_match and best_score > 0.5:
            root, quality = best_match

            # Parse quality for extensions
            base_quality = quality
            extensions = []

            if "7" in quality:
                extensions.append("7")
                base_quality = quality.replace("7", "")

            if "sus" in quality:
                extensions.append(quality)
                base_quality = (
                    quality.split("sus")[0] if quality.split("sus")[0] else "major"
                )

            return Chord(
                root=self.NOTE_NAMES[root],
                quality=base_quality if base_quality else "major",
                extensions=extensions,
                confidence=float(best_score),
            )

        return None

    def _add_harmonic_context(self, chords: List[Chord], key: str) -> List[Chord]:
        """Add roman numerals and harmonic function"""
        # Parse key
        key_parts = key.split()
        if len(key_parts) >= 2:
            tonic = key_parts[0]
            mode = key_parts[1].lower()
        else:
            tonic = key
            mode = "major"

        # Get tonic pitch class
        try:
            tonic_pc = self.NOTE_NAMES.index(tonic)
        except ValueError:
            tonic_pc = 0

        # Scale degrees for major and minor
        if mode == "major":
            scale_qualities = [
                "major",
                "minor",
                "minor",
                "major",
                "major",
                "minor",
                "diminished",
            ]
        else:  # minor
            scale_qualities = [
                "minor",
                "diminished",
                "major",
                "minor",
                "minor",
                "major",
                "major",
            ]

        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]

        for chord in chords:
            # Calculate scale degree
            try:
                root_pc = self.NOTE_NAMES.index(chord.root)
            except ValueError:
                continue

            degree = (root_pc - tonic_pc) % 12

            # Map to diatonic scale degree
            diatonic_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}

            if degree in diatonic_map:
                scale_degree = diatonic_map[degree]
                expected_quality = scale_qualities[scale_degree]

                # Roman numeral
                numeral = roman_numerals[scale_degree]

                # Use lowercase for minor/diminished in major keys
                if mode == "major" and expected_quality in ["minor", "diminished"]:
                    numeral = numeral.lower()
                elif mode == "minor" and expected_quality == "major":
                    numeral = numeral.upper()

                # Add extensions
                if chord.extensions:
                    numeral += "".join(chord.extensions)

                chord.roman_numeral = numeral

                # Harmonic function
                if scale_degree in [0]:  # I
                    chord.function = "tonic"
                elif scale_degree in [3]:  # IV
                    chord.function = "subdominant"
                elif scale_degree in [4]:  # V
                    chord.function = "dominant"
                elif scale_degree in [2, 5]:  # iii, vi
                    chord.function = "tonic"
                elif scale_degree in [1]:  # ii
                    chord.function = "subdominant"
                elif scale_degree in [6]:  # vii
                    chord.function = "dominant"
            else:
                # Chromatic chord
                chord.roman_numeral = f"#{chord.root}"
                chord.function = "chromatic"

        return chords

    def _detect_key(self, audio: np.ndarray, sr: int) -> str:
        """Detect key from audio (simplified)"""
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        # Find most prominent pitch class
        tonic = np.argmax(chroma_mean)

        return f"{self.NOTE_NAMES[tonic]} major"

    def _calculate_harmonic_complexity(self, chords: List[Chord]) -> float:
        """Calculate harmonic complexity score"""
        if not chords:
            return 0.0

        complexity_factors = []

        # Factor 1: Chord variety
        unique_chords = len(set(f"{c.root}{c.quality}" for c in chords))
        variety = min(1.0, unique_chords / 8)
        complexity_factors.append(variety)

        # Factor 2: Extension usage
        extended = sum(1 for c in chords if c.extensions)
        extension_ratio = extended / len(chords)
        complexity_factors.append(extension_ratio)

        # Factor 3: Chromatic chords
        chromatic = sum(1 for c in chords if c.function == "chromatic")
        chromatic_ratio = chromatic / len(chords)
        complexity_factors.append(chromatic_ratio)

        # Factor 4: Chord change frequency
        if len(chords) > 1 and chords[-1].start_time > 0:
            duration = chords[-1].start_time + chords[-1].duration
            change_freq = len(chords) / duration
            freq_complexity = min(1.0, change_freq / 2)
            complexity_factors.append(freq_complexity)

        return float(np.mean(complexity_factors))

    def _identify_common_progressions(self, progression: List[str]) -> List[str]:
        """Identify common chord progressions"""
        if len(progression) < 3:
            return []

        found = []

        # Check for common 4-chord progressions
        for i in range(len(progression) - 3):
            segment = "-".join(progression[i : i + 4])

            for pattern, genres in self.COMMON_PROGRESSIONS.items():
                if segment == pattern:
                    found.append(f"{pattern} ({', '.join(genres)})")

        # Check for 3-chord progressions (e.g., ii-V-I)
        for i in range(len(progression) - 2):
            segment = "-".join(progression[i : i + 3])

            for pattern, genres in self.COMMON_PROGRESSIONS.items():
                if segment in pattern:
                    found.append(f"{segment} ({', '.join(genres)})")

        return list(set(found))

    def _calculate_voice_movement(self, chord1: Chord, chord2: Chord) -> Dict[str, Any]:
        """Calculate voice movement between two chords"""
        # Get pitch classes for each chord
        pc1 = self._chord_to_pitch_classes(chord1)
        pc2 = self._chord_to_pitch_classes(chord2)

        # Calculate minimum movement for voice leading
        total_movement = 0
        movements = []

        for p1 in pc1:
            # Find nearest pitch in next chord
            min_dist = 12
            for p2 in pc2:
                dist = min(abs(p2 - p1), 12 - abs(p2 - p1))
                if dist < min_dist:
                    min_dist = dist

            total_movement += min_dist
            movements.append(min_dist)

        return {
            "total_movement": total_movement,
            "individual_movements": movements,
            "average_movement": total_movement / len(pc1) if pc1 else 0,
        }

    def _chord_to_pitch_classes(self, chord: Chord) -> List[int]:
        """Convert chord to pitch classes"""
        try:
            root = self.NOTE_NAMES.index(chord.root)
        except ValueError:
            return []

        pitch_classes = [root]

        # Add third and fifth based on quality
        if chord.quality == "major":
            pitch_classes.extend([(root + 4) % 12, (root + 7) % 12])
        elif chord.quality == "minor":
            pitch_classes.extend([(root + 3) % 12, (root + 7) % 12])
        elif chord.quality == "diminished":
            pitch_classes.extend([(root + 3) % 12, (root + 6) % 12])
        elif chord.quality == "augmented":
            pitch_classes.extend([(root + 4) % 12, (root + 8) % 12])

        # Add extensions
        if "7" in chord.extensions:
            if chord.quality == "major":
                pitch_classes.append((root + 11) % 12)  # Major 7th
            else:
                pitch_classes.append((root + 10) % 12)  # Minor 7th

        return sorted(set(pitch_classes))

    def _chord_to_dict(self, chord: Chord) -> Dict[str, Any]:
        """Convert chord to dictionary"""
        return {
            "root": chord.root,
            "quality": chord.quality,
            "extensions": chord.extensions,
            "bass_note": chord.bass_note,
            "start_time": float(chord.start_time),
            "duration": float(chord.duration),
            "roman_numeral": chord.roman_numeral,
            "function": chord.function,
            "confidence": float(chord.confidence),
        }

    def _dict_to_chord(self, data: Dict[str, Any]) -> Chord:
        """Convert dictionary to Chord object"""
        return Chord(
            root=data.get("root", "C"),
            quality=data.get("quality", "major"),
            extensions=data.get("extensions", []),
            bass_note=data.get("bass_note"),
            start_time=data.get("start_time", 0.0),
            duration=data.get("duration", 0.0),
            roman_numeral=data.get("roman_numeral", ""),
            function=data.get("function", ""),
            confidence=data.get("confidence", 1.0),
        )
