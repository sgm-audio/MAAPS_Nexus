"""
Musical Analysis Agent - Comprehensive musical characteristic analysis.

This agent provides deep musical analysis including key detection, tempo analysis,
time signature identification, scale detection, modulation detection, and tonal
characteristic evaluation.
"""

import threading
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np

try:
    import librosa
    import scipy.signal
    from scipy.stats import mode as scipy_mode
except ImportError as e:
    logging.warning(f"Missing musical analysis dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics

logger = logging.getLogger(__name__)


# Data structures for musical analysis
@dataclass
class Modulation:
    """Represents a key modulation"""

    time: float  # seconds
    new_key: str
    confidence: float


@dataclass
class MusicalAnalysis:
    """Complete musical analysis results"""

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
    genre_predictions: List[Tuple[str, float]]  # Genre with confidence


class MusicalAnalysisAgent(BaseAgent):
    """
    Agent for comprehensive musical analysis.

    Capabilities:
    - Key detection using Krumhansl-Schmuckler algorithm
    - Tempo detection with autocorrelation and onset detection
    - Time signature detection
    - Scale identification (major, minor, modes)
    - Modulation detection
    - Tonal brightness/darkness calculation
    - Consonance scoring
    - Genre prediction based on features
    """

    # Krumhansl-Schmuckler key profiles
    MAJOR_PROFILE = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    MINOR_PROFILE = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )

    # Scale patterns (semitones from root)
    SCALE_PATTERNS = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "aeolian": [0, 2, 3, 5, 7, 8, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
        "pentatonic_major": [0, 2, 4, 7, 9],
        "pentatonic_minor": [0, 3, 5, 7, 10],
        "blues": [0, 3, 5, 6, 7, 10],
    }

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self):
        super().__init__(
            agent_id="musical_analysis_agent", agent_name="Musical Analysis Agent"
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "analyses_performed": 0,
            "key_detections": 0,
            "tempo_detections": 0,
            "modulations_detected": 0,
            "errors": 0,
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Musical Analysis Agent")

        # Subscribe to analysis topics
        self.subscribe("musical.analysis.key")
        self.subscribe("musical.analysis.tempo")
        self.subscribe("musical.analysis.time_signature")
        self.subscribe("musical.analysis.scale")
        self.subscribe("musical.analysis.modulation")
        self.subscribe("musical.analysis.comprehensive")

        self.log("INFO", "Musical Analysis Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Musical Analysis Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming analysis requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic == "musical.analysis.comprehensive":
                result = self._analyze_comprehensive(payload)
            elif topic == "musical.analysis.key":
                result = self._detect_key(payload)
            elif topic == "musical.analysis.tempo":
                result = self._detect_tempo(payload)
            elif topic == "musical.analysis.time_signature":
                result = self._detect_time_signature(payload)
            elif topic == "musical.analysis.scale":
                result = self._detect_scale(payload)
            elif topic == "musical.analysis.modulation":
                result = self._detect_modulations(payload)
            else:
                result = {"success": False, "error": f"Unknown topic: {topic}"}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats["errors"] += 1
            self.respond(message, {"success": False, "error": str(e)})

    def _analyze_comprehensive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive musical analysis"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Detect key
            key, key_conf = self._analyze_key(audio, sr)

            # Detect tempo
            tempo, tempo_conf = self._analyze_tempo(audio, sr)

            # Detect time signature
            time_sig = self._analyze_time_signature(audio, sr, tempo)

            # Detect scale type
            scale_type = self._analyze_scale_type(audio, sr)

            # Detect modulations
            modulations = self._analyze_modulations(audio, sr)

            # Calculate pitch center
            pitch_center = self._calculate_pitch_center(audio, sr)

            # Calculate tonal brightness
            brightness = self._calculate_tonal_brightness(audio, sr)

            # Calculate consonance
            consonance = self._calculate_consonance(audio, sr)

            # Predict genre
            genres = self._predict_genre(audio, sr, tempo, key)

            analysis = MusicalAnalysis(
                key=key,
                key_confidence=key_conf,
                tempo_bpm=tempo,
                tempo_confidence=tempo_conf,
                time_signature=time_sig,
                scale_type=scale_type,
                modulations=modulations,
                pitch_center=pitch_center,
                tonal_brightness=brightness,
                consonance_score=consonance,
                genre_predictions=genres,
            )

            with self._lock:
                self._stats["analyses_performed"] += 1

            return {
                "success": True,
                "analysis": {
                    "key": analysis.key,
                    "key_confidence": float(analysis.key_confidence),
                    "tempo_bpm": float(analysis.tempo_bpm),
                    "tempo_confidence": float(analysis.tempo_confidence),
                    "time_signature": analysis.time_signature,
                    "scale_type": analysis.scale_type,
                    "modulations": [
                        {
                            "time": m.time,
                            "new_key": m.new_key,
                            "confidence": m.confidence,
                        }
                        for m in analysis.modulations
                    ],
                    "pitch_center": float(analysis.pitch_center),
                    "tonal_brightness": float(analysis.tonal_brightness),
                    "consonance_score": float(analysis.consonance_score),
                    "genre_predictions": analysis.genre_predictions,
                },
            }

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_key(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect musical key only"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            key, confidence = self._analyze_key(audio, sr)

            with self._lock:
                self._stats["key_detections"] += 1

            return {"success": True, "key": key, "confidence": float(confidence)}

        except Exception as e:
            logger.error(f"Error detecting key: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_tempo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect tempo only"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            tempo, confidence = self._analyze_tempo(audio, sr)

            with self._lock:
                self._stats["tempo_detections"] += 1

            return {
                "success": True,
                "tempo_bpm": float(tempo),
                "confidence": float(confidence),
            }

        except Exception as e:
            logger.error(f"Error detecting tempo: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_time_signature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect time signature"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            tempo = payload.get("tempo_bpm")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            if tempo is None:
                tempo, _ = self._analyze_tempo(audio, sr)

            time_sig = self._analyze_time_signature(audio, sr, tempo)

            return {"success": True, "time_signature": time_sig}

        except Exception as e:
            logger.error(f"Error detecting time signature: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_scale(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect scale type"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            scale_type = self._analyze_scale_type(audio, sr)

            return {"success": True, "scale_type": scale_type}

        except Exception as e:
            logger.error(f"Error detecting scale: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_modulations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect key modulations"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            modulations = self._analyze_modulations(audio, sr)

            with self._lock:
                self._stats["modulations_detected"] += len(modulations)

            return {
                "success": True,
                "modulations": [
                    {"time": m.time, "new_key": m.new_key, "confidence": m.confidence}
                    for m in modulations
                ],
            }

        except Exception as e:
            logger.error(f"Error detecting modulations: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_key(self, audio: np.ndarray, sr: int) -> Tuple[str, float]:
        """Detect key using Krumhansl-Schmuckler algorithm"""
        # Extract chromagram
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        # Normalize
        chroma_mean = chroma_mean / np.sum(chroma_mean)

        best_correlation = -1
        best_key = "C major"

        # Test all 24 major/minor keys
        for shift in range(12):
            # Test major
            major_profile = np.roll(self.MAJOR_PROFILE, shift)
            major_profile = major_profile / np.sum(major_profile)
            correlation = np.corrcoef(chroma_mean, major_profile)[0, 1]

            if correlation > best_correlation:
                best_correlation = correlation
                best_key = f"{self.NOTE_NAMES[shift]} major"

            # Test minor
            minor_profile = np.roll(self.MINOR_PROFILE, shift)
            minor_profile = minor_profile / np.sum(minor_profile)
            correlation = np.corrcoef(chroma_mean, minor_profile)[0, 1]

            if correlation > best_correlation:
                best_correlation = correlation
                best_key = f"{self.NOTE_NAMES[shift]} minor"

        # Convert correlation to confidence (0-1)
        confidence = (best_correlation + 1) / 2

        return best_key, confidence

    def _analyze_tempo(self, audio: np.ndarray, sr: int) -> Tuple[float, float]:
        """Detect tempo using onset detection and autocorrelation"""
        # Use librosa's tempo detection
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]

        # Also get dynamic programming tempo for confidence
        tempo_dp, beats = librosa.beat.beat_track(y=audio, sr=sr)

        # Calculate confidence based on beat consistency
        if len(beats) > 1:
            beat_intervals = np.diff(beats)
            if len(beat_intervals) > 0:
                interval_std = np.std(beat_intervals)
                interval_mean = np.mean(beat_intervals)
                # Lower variance = higher confidence
                confidence = max(0.0, 1.0 - (interval_std / (interval_mean + 1e-6)))
            else:
                confidence = 0.5
        else:
            confidence = 0.5

        # Average the two tempo estimates
        final_tempo = (tempo + tempo_dp) / 2

        return float(final_tempo), float(confidence)

    def _analyze_time_signature(self, audio: np.ndarray, sr: int, tempo: float) -> str:
        """Detect time signature"""
        # Get beat times
        _, beats = librosa.beat.beat_track(y=audio, sr=sr, bpm=tempo)

        if len(beats) < 4:
            return "4/4"  # Default

        # Convert beat frames to times
        beat_times = librosa.frames_to_time(beats, sr=sr)

        # Detect downbeats using onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)

        # Analyze beat strength patterns
        beat_strengths = []
        for beat_frame in beats:
            if beat_frame < len(onset_env):
                beat_strengths.append(onset_env[beat_frame])

        if len(beat_strengths) < 4:
            return "4/4"

        # Look for patterns in beat strengths
        # Strong-weak-medium-weak suggests 4/4
        # Strong-weak-weak suggests 3/4
        # Strong-weak-weak-medium-weak-weak suggests 6/8

        beat_strengths = np.array(beat_strengths)

        # Try to find periodicity in strong beats
        for period in [3, 4, 6]:
            if len(beat_strengths) >= period * 2:
                # Check if every Nth beat is stronger
                strong_positions = beat_strengths[::period]
                other_positions = np.delete(
                    beat_strengths, np.arange(0, len(beat_strengths), period)
                )

                if (
                    len(other_positions) > 0
                    and np.mean(strong_positions) > np.mean(other_positions) * 1.2
                ):
                    if period == 3:
                        return "3/4"
                    elif period == 4:
                        return "4/4"
                    elif period == 6:
                        return "6/8"

        return "4/4"  # Default

    def _analyze_scale_type(self, audio: np.ndarray, sr: int) -> str:
        """Detect scale type"""
        # Extract chromagram
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        # Normalize
        chroma_mean = chroma_mean / (np.sum(chroma_mean) + 1e-6)

        best_correlation = -1
        best_scale = "major"

        # Test each scale pattern
        for scale_name, pattern in self.SCALE_PATTERNS.items():
            # Create a profile for this scale
            profile = np.zeros(12)
            for note in pattern:
                profile[note] = 1.0

            # Normalize
            profile = profile / np.sum(profile)

            # Find best rotation
            for shift in range(12):
                shifted_profile = np.roll(profile, shift)
                correlation = np.corrcoef(chroma_mean, shifted_profile)[0, 1]

                if correlation > best_correlation:
                    best_correlation = correlation
                    best_scale = scale_name

        return best_scale

    def _analyze_modulations(self, audio: np.ndarray, sr: int) -> List[Modulation]:
        """Detect key modulations over time"""
        modulations = []

        # Divide audio into segments
        segment_duration = 10.0  # seconds
        hop_duration = 5.0  # seconds

        segment_length = int(segment_duration * sr)
        hop_length = int(hop_duration * sr)

        if len(audio) < segment_length:
            return modulations

        current_key = None

        for start in range(0, len(audio) - segment_length, hop_length):
            end = start + segment_length
            segment = audio[start:end]

            # Detect key for this segment
            key, confidence = self._analyze_key(segment, sr)

            # Check if key changed
            if current_key is None:
                current_key = key
            elif key != current_key and confidence > 0.7:
                time = start / sr
                modulations.append(
                    Modulation(time=time, new_key=key, confidence=confidence)
                )
                current_key = key

        return modulations

    def _calculate_pitch_center(self, audio: np.ndarray, sr: int) -> float:
        """Calculate the pitch center in Hz"""
        # Use spectral centroid as approximation
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
        mean_centroid = np.mean(centroid)
        return float(mean_centroid)

    def _calculate_tonal_brightness(self, audio: np.ndarray, sr: int) -> float:
        """Calculate tonal brightness (-1 dark to 1 bright)"""
        # Use spectral rolloff and centroid
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)

        mean_rolloff = np.mean(rolloff)
        mean_centroid = np.mean(centroid)

        # Normalize to -1 to 1 range
        # Higher rolloff/centroid = brighter
        brightness = (mean_centroid / sr) * 4 - 1
        brightness = np.clip(brightness, -1, 1)

        return float(brightness)

    def _calculate_consonance(self, audio: np.ndarray, sr: int) -> float:
        """Calculate consonance score (0 dissonant to 1 consonant)"""
        # Use spectral flatness as a measure
        # Flatter spectrum = more noise-like = more dissonant
        flatness = librosa.feature.spectral_flatness(y=audio)
        mean_flatness = np.mean(flatness)

        # Invert so high flatness = low consonance
        consonance = 1.0 - mean_flatness

        # Also consider harmonic content
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        chroma_var = np.var(chroma, axis=1)

        # More concentrated chroma = more consonant
        chroma_concentration = 1.0 - (np.mean(chroma_var) * 12)
        chroma_concentration = np.clip(chroma_concentration, 0, 1)

        # Combine measures
        consonance = (consonance + chroma_concentration) / 2

        return float(consonance)

    def _predict_genre(
        self, audio: np.ndarray, sr: int, tempo: float, key: str
    ) -> List[Tuple[str, float]]:
        """Predict genre based on musical features"""
        predictions = []

        # Calculate various features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))
        zero_crossing = np.mean(librosa.feature.zero_crossing_rate(audio))

        # Simple heuristic-based genre classification
        # Rock/Metal: high energy, high spectral features
        if spectral_centroid > 3000 and zero_crossing > 0.1:
            predictions.append(("rock", 0.7))

        # Classical: lower tempo, high consonance, complex harmony
        if 60 < tempo < 120 and spectral_centroid < 2000:
            predictions.append(("classical", 0.6))

        # Electronic/Dance: precise tempo, usually 120-140 BPM
        if 120 < tempo < 140:
            predictions.append(("electronic", 0.65))

        # Jazz: complex harmony, syncopation
        if 100 < tempo < 180 and "7" in key or "#" in key:
            predictions.append(("jazz", 0.5))

        # Hip-hop: usually 80-110 BPM
        if 80 < tempo < 110:
            predictions.append(("hip-hop", 0.55))

        # Pop: 100-130 BPM, simple harmony
        if 100 < tempo < 130:
            predictions.append(("pop", 0.6))

        # Sort by confidence
        predictions.sort(key=lambda x: x[1], reverse=True)

        # Return top 3
        return predictions[:3] if predictions else [("unknown", 0.5)]
