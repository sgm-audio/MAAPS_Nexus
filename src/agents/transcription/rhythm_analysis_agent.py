"""
Rhythm Analysis Agent.

Analyzes rhythmic patterns, beat structures, groove characteristics, and
provides quantization suggestions.
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
    logging.warning(f"Missing rhythm analysis dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics

logger = logging.getLogger(__name__)


@dataclass
class BeatGrid:
    """Represents a beat grid"""

    beats: List[float]  # Beat timestamps in seconds
    downbeats: List[float]  # Downbeat timestamps
    tempo_curve: List[Tuple[float, float]]  # time, BPM
    grid_resolution: str = "1/16"  # "1/4", "1/8", "1/16", "1/32"


@dataclass
class RhythmicAnalysis:
    """Complete rhythmic analysis results"""

    beat_grid: BeatGrid
    groove_type: str  # "straight", "swing", "shuffle"
    swing_percentage: float  # 0-100%
    syncopation_score: float  # 0.0-1.0
    complexity_score: float  # 0.0-1.0
    polyrhythms: List[str] = field(default_factory=list)  # "3:2", "4:3"
    microtiming_deviation: float = 0.0  # milliseconds


class RhythmAnalysisAgent(BaseAgent):
    """
    Agent for rhythmic analysis.

    Capabilities:
    - Beat tracking using librosa.beat.beat_track
    - Downbeat detection
    - Tempo variation detection
    - Groove analysis (swing, shuffle)
    - Syncopation scoring
    - Quantization suggestions
    - Microtiming deviation analysis
    """

    def __init__(self):
        super().__init__(
            agent_id="rhythm_analysis_agent", agent_name="Rhythm Analysis Agent"
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "analyses_performed": 0,
            "beats_tracked": 0,
            "groove_analyses": 0,
            "errors": 0,
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Rhythm Analysis Agent")

        # Subscribe to rhythm topics
        self.subscribe("rhythm.beat.track")
        self.subscribe("rhythm.groove.analyze")
        self.subscribe("rhythm.quantize")
        self.subscribe("rhythm.complexity")

        self.log("INFO", "Rhythm Analysis Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Rhythm Analysis Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming rhythm analysis requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic == "rhythm.beat.track":
                result = self._track_beats(payload)
            elif topic == "rhythm.groove.analyze":
                result = self._analyze_groove(payload)
            elif topic == "rhythm.quantize":
                result = self._suggest_quantization(payload)
            elif topic == "rhythm.complexity":
                result = self._analyze_complexity(payload)
            else:
                result = {"success": False, "error": f"Unknown topic: {topic}"}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats["errors"] += 1
            self.respond(message, {"success": False, "error": str(e)})

    def _track_beats(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Track beats and downbeats"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Track beats
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # Detect downbeats
            downbeat_times = self._detect_downbeats(audio, sr, beat_times)

            # Calculate tempo curve
            tempo_curve = self._calculate_tempo_curve(beat_times)

            # Create beat grid
            beat_grid = BeatGrid(
                beats=beat_times.tolist(),
                downbeats=downbeat_times,
                tempo_curve=tempo_curve,
                grid_resolution="1/16",
            )

            with self._lock:
                self._stats["beats_tracked"] += len(beat_times)

            return {
                "success": True,
                "beat_grid": {
                    "beats": beat_grid.beats,
                    "downbeats": beat_grid.downbeats,
                    "tempo_curve": beat_grid.tempo_curve,
                    "grid_resolution": beat_grid.grid_resolution,
                },
                "tempo_bpm": float(tempo),
            }

        except Exception as e:
            logger.error(f"Error tracking beats: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_groove(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze groove characteristics"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Track beats
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # Detect downbeats
            downbeat_times = self._detect_downbeats(audio, sr, beat_times)

            # Calculate tempo curve
            tempo_curve = self._calculate_tempo_curve(beat_times)

            # Analyze groove type and swing
            groove_type, swing_pct = self._detect_groove_type(audio, sr, beat_times)

            # Calculate syncopation
            syncopation = self._calculate_syncopation(audio, sr, beat_times)

            # Calculate complexity
            complexity = self._calculate_rhythmic_complexity(beat_times, tempo_curve)

            # Detect polyrhythms
            polyrhythms = self._detect_polyrhythms(audio, sr, tempo)

            # Calculate microtiming
            microtiming = self._calculate_microtiming(beat_times)

            # Create analysis
            beat_grid = BeatGrid(
                beats=beat_times.tolist(),
                downbeats=downbeat_times,
                tempo_curve=tempo_curve,
            )

            analysis = RhythmicAnalysis(
                beat_grid=beat_grid,
                groove_type=groove_type,
                swing_percentage=swing_pct,
                syncopation_score=syncopation,
                complexity_score=complexity,
                polyrhythms=polyrhythms,
                microtiming_deviation=microtiming,
            )

            with self._lock:
                self._stats["analyses_performed"] += 1
                self._stats["groove_analyses"] += 1

            return {
                "success": True,
                "analysis": {
                    "beat_grid": {
                        "beats": analysis.beat_grid.beats,
                        "downbeats": analysis.beat_grid.downbeats,
                        "tempo_curve": analysis.beat_grid.tempo_curve,
                        "grid_resolution": analysis.beat_grid.grid_resolution,
                    },
                    "groove_type": analysis.groove_type,
                    "swing_percentage": float(analysis.swing_percentage),
                    "syncopation_score": float(analysis.syncopation_score),
                    "complexity_score": float(analysis.complexity_score),
                    "polyrhythms": analysis.polyrhythms,
                    "microtiming_deviation": float(analysis.microtiming_deviation),
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing groove: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _suggest_quantization(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest quantization settings"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            note_times = payload.get("note_times")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Track beats
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # Determine optimal grid resolution
            grid_resolution = self._determine_grid_resolution(audio, sr, beat_times)

            # If note times provided, calculate quantization suggestions
            if note_times:
                quantized_times = self._quantize_times(
                    note_times, beat_times, grid_resolution, tempo
                )

                return {
                    "success": True,
                    "grid_resolution": grid_resolution,
                    "tempo_bpm": float(tempo),
                    "quantized_times": quantized_times,
                    "original_times": note_times,
                }
            else:
                return {
                    "success": True,
                    "grid_resolution": grid_resolution,
                    "tempo_bpm": float(tempo),
                }

        except Exception as e:
            logger.error(f"Error suggesting quantization: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _analyze_complexity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze rhythmic complexity"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Track beats
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # Calculate tempo curve
            tempo_curve = self._calculate_tempo_curve(beat_times)

            # Calculate complexity
            complexity = self._calculate_rhythmic_complexity(beat_times, tempo_curve)

            # Calculate syncopation
            syncopation = self._calculate_syncopation(audio, sr, beat_times)

            return {
                "success": True,
                "complexity_score": float(complexity),
                "syncopation_score": float(syncopation),
                "tempo_variation": float(np.std([t for _, t in tempo_curve])),
            }

        except Exception as e:
            logger.error(f"Error analyzing complexity: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_downbeats(
        self, audio: np.ndarray, sr: int, beat_times: np.ndarray
    ) -> List[float]:
        """Detect downbeats (first beat of measure)"""
        # Calculate onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)

        # Get beat frames
        beat_frames = librosa.time_to_frames(beat_times, sr=sr)

        # Analyze beat strengths
        beat_strengths = []
        for frame in beat_frames:
            if frame < len(onset_env):
                beat_strengths.append(onset_env[frame])
            else:
                beat_strengths.append(0)

        if len(beat_strengths) < 4:
            return []

        # Detect time signature by finding periodicity in strong beats
        # Assume 4/4 for simplicity (every 4th beat is downbeat)
        time_sig = 4

        # Find first strong beat
        first_downbeat_idx = 0
        if len(beat_strengths) > 0:
            # Look for strongest beat in first measure
            first_measure_end = min(time_sig, len(beat_strengths))
            first_downbeat_idx = np.argmax(beat_strengths[:first_measure_end])

        # Mark every Nth beat as downbeat
        downbeat_indices = list(range(first_downbeat_idx, len(beat_times), time_sig))
        downbeat_times = [
            beat_times[i] for i in downbeat_indices if i < len(beat_times)
        ]

        return downbeat_times

    def _calculate_tempo_curve(
        self, beat_times: np.ndarray
    ) -> List[Tuple[float, float]]:
        """Calculate tempo variation over time"""
        if len(beat_times) < 2:
            return [(0.0, 120.0)]

        tempo_curve = []

        # Calculate local tempo from beat intervals
        for i in range(len(beat_times) - 1):
            interval = beat_times[i + 1] - beat_times[i]
            if interval > 0:
                tempo = 60.0 / interval
                tempo_curve.append((float(beat_times[i]), float(tempo)))

        # Add final point
        if tempo_curve:
            tempo_curve.append((float(beat_times[-1]), tempo_curve[-1][1]))

        return tempo_curve

    def _detect_groove_type(
        self, audio: np.ndarray, sr: int, beat_times: np.ndarray
    ) -> Tuple[str, float]:
        """Detect groove type (straight, swing, shuffle)"""
        if len(beat_times) < 4:
            return "straight", 0.0

        # Detect onsets at subdivision level
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr, aggregate=np.median)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # Analyze subdivision timing
        subdivisions = []

        for i in range(len(beat_times) - 1):
            beat_start = beat_times[i]
            beat_end = beat_times[i + 1]
            beat_duration = beat_end - beat_start

            # Find onsets within this beat
            beat_onsets = onset_times[
                (onset_times >= beat_start) & (onset_times < beat_end)
            ]

            # Calculate positions within beat (0.0 to 1.0)
            if len(beat_onsets) > 0:
                positions = (beat_onsets - beat_start) / beat_duration
                subdivisions.extend(positions)

        if len(subdivisions) < 10:
            return "straight", 0.0

        subdivisions = np.array(subdivisions)

        # Analyze 8th note subdivisions
        # In straight time: should be near 0.5
        # In swing: should be near 0.67 (2:1 ratio)
        # In shuffle: should be near 0.75 (3:1 ratio)

        mid_subdivisions = subdivisions[(subdivisions > 0.3) & (subdivisions < 0.8)]

        if len(mid_subdivisions) > 0:
            median_pos = np.median(mid_subdivisions)

            if median_pos < 0.55:
                return "straight", 0.0
            elif median_pos < 0.62:
                swing_pct = (median_pos - 0.5) / 0.17 * 50  # Scale to 0-50%
                return "swing", float(swing_pct)
            else:
                swing_pct = min(100.0, (median_pos - 0.5) / 0.25 * 100)
                return "shuffle", float(swing_pct)

        return "straight", 0.0

    def _calculate_syncopation(
        self, audio: np.ndarray, sr: int, beat_times: np.ndarray
    ) -> float:
        """Calculate syncopation score"""
        if len(beat_times) < 2:
            return 0.0

        # Get onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # Count onsets between beats (off-beat)
        off_beat_onsets = 0
        on_beat_onsets = 0

        beat_tolerance = 0.05  # 50ms tolerance

        for onset_time in onset_times:
            # Check if onset is on or off beat
            on_beat = False
            for beat_time in beat_times:
                if abs(onset_time - beat_time) < beat_tolerance:
                    on_beat = True
                    break

            if on_beat:
                on_beat_onsets += 1
            else:
                off_beat_onsets += 1

        total_onsets = on_beat_onsets + off_beat_onsets

        if total_onsets == 0:
            return 0.0

        # Syncopation ratio
        syncopation = off_beat_onsets / total_onsets

        return float(np.clip(syncopation, 0.0, 1.0))

    def _calculate_rhythmic_complexity(
        self, beat_times: np.ndarray, tempo_curve: List[Tuple[float, float]]
    ) -> float:
        """Calculate rhythmic complexity score"""
        complexity_factors = []

        # Factor 1: Tempo variation
        if len(tempo_curve) > 1:
            tempos = [t for _, t in tempo_curve]
            tempo_std = np.std(tempos)
            tempo_var = min(1.0, tempo_std / 20)  # Normalize
            complexity_factors.append(tempo_var)

        # Factor 2: Beat irregularity
        if len(beat_times) > 2:
            intervals = np.diff(beat_times)
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)
            irregularity = min(1.0, interval_std / (interval_mean + 1e-6))
            complexity_factors.append(irregularity)

        if not complexity_factors:
            return 0.5

        return float(np.mean(complexity_factors))

    def _detect_polyrhythms(
        self, audio: np.ndarray, sr: int, base_tempo: float
    ) -> List[str]:
        """Detect polyrhythmic patterns"""
        polyrhythms = []

        # This is a simplified implementation
        # Real polyrhythm detection would require more sophisticated analysis

        # Get onset strength with different hop lengths to detect different pulse rates
        onset_env_fast = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=256)
        onset_env_slow = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=1024)

        # Autocorrelation to find periodicities
        acf_fast = librosa.autocorrelate(onset_env_fast)
        acf_slow = librosa.autocorrelate(onset_env_slow)

        # Find peaks in autocorrelation
        from scipy.signal import find_peaks

        peaks_fast, _ = find_peaks(acf_fast, height=np.max(acf_fast) * 0.3)
        peaks_slow, _ = find_peaks(acf_slow, height=np.max(acf_slow) * 0.3)

        # Look for common polyrhythmic ratios
        if len(peaks_fast) > 1 and len(peaks_slow) > 1:
            # Check for 3:2 (hemiola)
            ratio = peaks_fast[0] / (peaks_slow[0] + 1e-6)
            if 1.4 < ratio < 1.6:
                polyrhythms.append("3:2")
            elif 1.3 < ratio < 1.35:
                polyrhythms.append("4:3")

        return polyrhythms

    def _calculate_microtiming(self, beat_times: np.ndarray) -> float:
        """Calculate average microtiming deviation"""
        if len(beat_times) < 3:
            return 0.0

        # Calculate expected beat times (perfect grid)
        intervals = np.diff(beat_times)
        avg_interval = np.mean(intervals)

        expected_times = [beat_times[0]]
        for i in range(1, len(beat_times)):
            expected_times.append(expected_times[-1] + avg_interval)

        expected_times = np.array(expected_times)

        # Calculate deviations
        deviations = np.abs(beat_times - expected_times)

        # Convert to milliseconds
        avg_deviation_ms = np.mean(deviations) * 1000

        return float(avg_deviation_ms)

    def _determine_grid_resolution(
        self, audio: np.ndarray, sr: int, beat_times: np.ndarray
    ) -> str:
        """Determine optimal grid resolution for quantization"""
        if len(beat_times) < 2:
            return "1/16"

        # Detect onsets
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # Calculate average onsets per beat
        avg_interval = np.mean(np.diff(beat_times))

        onsets_per_beat = 0
        for i in range(len(beat_times) - 1):
            beat_onsets = onset_times[
                (onset_times >= beat_times[i]) & (onset_times < beat_times[i + 1])
            ]
            onsets_per_beat += len(beat_onsets)

        onsets_per_beat /= len(beat_times) - 1

        # Determine resolution based on density
        if onsets_per_beat < 2:
            return "1/4"
        elif onsets_per_beat < 4:
            return "1/8"
        elif onsets_per_beat < 8:
            return "1/16"
        else:
            return "1/32"

    def _quantize_times(
        self,
        note_times: List[float],
        beat_times: np.ndarray,
        grid_resolution: str,
        tempo: float,
    ) -> List[float]:
        """Quantize note times to grid"""
        resolution_map = {"1/4": 1.0, "1/8": 0.5, "1/16": 0.25, "1/32": 0.125}

        beat_fraction = resolution_map.get(grid_resolution, 0.25)

        if len(beat_times) < 2:
            return note_times

        avg_beat_duration = np.mean(np.diff(beat_times))
        grid_duration = avg_beat_duration * beat_fraction

        quantized = []

        for note_time in note_times:
            # Find nearest grid point
            grid_point = round(note_time / grid_duration) * grid_duration
            quantized.append(float(grid_point))

        return quantized
