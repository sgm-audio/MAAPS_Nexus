"""
Multi-Track Transcription Coordinator Agent.

Coordinates transcription of multi-track audio, optionally using stem separation
for improved accuracy. Manages workflow between analysis, separation, and
transcription agents.
"""

import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

try:
    import librosa
    import pretty_midi
except ImportError as e:
    logging.warning(f"Missing coordinator dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics

logger = logging.getLogger(__name__)


@dataclass
class TrackTranscription:
    """Transcription result for a single track"""

    track_id: str
    instrument_type: str
    midi_data: Dict[str, Any]  # MIDITranscription as dict
    tablature: Optional[Dict[str, Any]] = None  # Tablature as dict
    harmonic_analysis: Optional[Dict[str, Any]] = None  # HarmonicAnalysis as dict
    rhythm_analysis: Optional[Dict[str, Any]] = None  # RhythmicAnalysis as dict
    quality_score: float = 0.0  # 0.0-1.0


@dataclass
class MultiTrackTranscription:
    """Complete multi-track transcription"""

    project_name: str
    tracks: List[TrackTranscription]
    overall_analysis: Dict[str, Any]  # MusicalAnalysis as dict
    tempo_map: List[Tuple[float, float]]  # time, BPM
    key_changes: List[Tuple[float, str]] = field(default_factory=list)  # time, key
    time_signature_changes: List[Tuple[float, str]] = field(default_factory=list)
    export_formats: List[str] = field(
        default_factory=list
    )  # ["midi", "musicxml", "tab"]


class MultiTrackCoordinatorAgent(BaseAgent):
    """
    Coordinator agent for multi-track transcription.

    Capabilities:
    - Multi-track audio analysis coordination
    - Automatic stem separation triggering
    - Per-instrument transcription coordination
    - Track identification
    - Transcription result merging
    - Quality assessment and re-transcription
    - Export coordination
    - Integration with studio/live systems
    """

    # Instrument detection based on frequency ranges
    INSTRUMENT_PROFILES = {
        "drums": {"freq_min": 20, "freq_max": 8000, "percussive": True},
        "bass": {"freq_min": 30, "freq_max": 250, "percussive": False},
        "guitar": {"freq_min": 80, "freq_max": 1200, "percussive": False},
        "piano": {"freq_min": 27.5, "freq_max": 4186, "percussive": False},
        "vocals": {"freq_min": 80, "freq_max": 1100, "percussive": False},
        "synth": {"freq_min": 40, "freq_max": 8000, "percussive": False},
    }

    def __init__(self):
        super().__init__(
            agent_id="multitrack_coordinator_agent",
            agent_name="Multi-Track Coordinator Agent",
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "projects_processed": 0,
            "tracks_transcribed": 0,
            "stems_separated": 0,
            "exports_performed": 0,
            "errors": 0,
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Multi-Track Coordinator Agent")

        # Subscribe to coordinator topics
        self.subscribe("coordinator.transcribe.multitrack")
        self.subscribe("coordinator.separate_and_transcribe")
        self.subscribe("coordinator.merge_results")
        self.subscribe("coordinator.export")

        self.log("INFO", "Multi-Track Coordinator Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Multi-Track Coordinator Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming coordination requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic == "coordinator.transcribe.multitrack":
                result = self._transcribe_multitrack(payload)
            elif topic == "coordinator.separate_and_transcribe":
                result = self._separate_and_transcribe(payload)
            elif topic == "coordinator.merge_results":
                result = self._merge_results(payload)
            elif topic == "coordinator.export":
                result = self._export_multitrack(payload)
            else:
                result = {"success": False, "error": f"Unknown topic: {topic}"}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats["errors"] += 1
            self.respond(message, {"success": False, "error": str(e)})

    def _transcribe_multitrack(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multi-track transcription"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            project_name = payload.get("project_name", "untitled_project")
            separate_stems = payload.get("separate_stems", True)

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono if stereo for analysis
            if len(audio.shape) > 1:
                audio_mono = librosa.to_mono(audio)
            else:
                audio_mono = audio

            # Step 1: Overall musical analysis
            overall_analysis = self._perform_overall_analysis(audio_mono, sr)

            # Step 2: Determine if stem separation is needed
            if separate_stems:
                # Trigger stem separation
                stems = self._request_stem_separation(audio, sr)

                if stems:
                    # Transcribe each stem
                    tracks = self._transcribe_stems(stems, sr, overall_analysis)
                    with self._lock:
                        self._stats["stems_separated"] += 1
                else:
                    # Fallback to single track
                    tracks = self._transcribe_single_track(
                        audio_mono, sr, overall_analysis
                    )
            else:
                # Direct transcription without separation
                tracks = self._transcribe_single_track(audio_mono, sr, overall_analysis)

            # Step 3: Build tempo and key change maps
            tempo_map = overall_analysis.get(
                "tempo_map", [(0.0, overall_analysis.get("tempo_bpm", 120.0))]
            )
            key_changes = overall_analysis.get("key_changes", [])

            # Step 4: Create multi-track transcription
            multitrack = MultiTrackTranscription(
                project_name=project_name,
                tracks=tracks,
                overall_analysis=overall_analysis,
                tempo_map=tempo_map,
                key_changes=key_changes,
                export_formats=["midi", "json"],
            )

            with self._lock:
                self._stats["projects_processed"] += 1
                self._stats["tracks_transcribed"] += len(tracks)

            return {"success": True, "multitrack": self._multitrack_to_dict(multitrack)}

        except Exception as e:
            logger.error(f"Error in multi-track transcription: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _separate_and_transcribe(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Separate stems and transcribe each"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            project_name = payload.get("project_name", "separated_project")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono for analysis
            if len(audio.shape) > 1:
                audio_mono = librosa.to_mono(audio)
            else:
                audio_mono = audio

            # Overall analysis
            overall_analysis = self._perform_overall_analysis(audio_mono, sr)

            # Request stem separation
            stems = self._request_stem_separation(audio, sr)

            if not stems:
                return {"success": False, "error": "Stem separation failed"}

            # Transcribe stems
            tracks = self._transcribe_stems(stems, sr, overall_analysis)

            multitrack = MultiTrackTranscription(
                project_name=project_name,
                tracks=tracks,
                overall_analysis=overall_analysis,
                tempo_map=[(0.0, overall_analysis.get("tempo_bpm", 120.0))],
                export_formats=["midi"],
            )

            with self._lock:
                self._stats["stems_separated"] += 1
                self._stats["tracks_transcribed"] += len(tracks)

            return {"success": True, "multitrack": self._multitrack_to_dict(multitrack)}

        except Exception as e:
            logger.error(f"Error in separate and transcribe: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _merge_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Merge transcription results from multiple sources"""
        try:
            transcriptions = payload.get("transcriptions", [])

            if not transcriptions:
                return {"success": False, "error": "No transcriptions to merge"}

            # Merge tracks
            merged_tracks = []

            for trans in transcriptions:
                if "tracks" in trans:
                    merged_tracks.extend(trans["tracks"])

            # Use first transcription's overall analysis
            overall_analysis = transcriptions[0].get("overall_analysis", {})

            merged = {
                "project_name": "merged_project",
                "tracks": merged_tracks,
                "overall_analysis": overall_analysis,
                "tempo_map": transcriptions[0].get("tempo_map", []),
                "key_changes": transcriptions[0].get("key_changes", []),
            }

            return {"success": True, "merged": merged}

        except Exception as e:
            logger.error(f"Error merging results: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _export_multitrack(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Export multi-track transcription in various formats"""
        try:
            multitrack_data = payload.get("multitrack")
            export_format = payload.get("format", "midi").lower()
            output_path = payload.get("output_path")

            if not multitrack_data:
                return {"success": False, "error": "No multitrack data provided"}

            if export_format == "midi":
                result = self._export_as_midi(multitrack_data, output_path)
            elif export_format == "json":
                result = {"success": True, "data": multitrack_data}
            elif export_format == "musicxml":
                result = self._export_as_musicxml(multitrack_data, output_path)
            else:
                return {"success": False, "error": f"Unknown format: {export_format}"}

            with self._lock:
                self._stats["exports_performed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error exporting: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _perform_overall_analysis(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Perform overall musical analysis"""
        # This would normally send a request to MusicalAnalysisAgent
        # For now, we'll do basic analysis

        try:
            # Detect tempo
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)

            # Detect key (simplified)
            chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            key_idx = np.argmax(chroma_mean)
            keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            key = f"{keys[key_idx]} major"

            # Basic time signature (assume 4/4)
            time_sig = "4/4"

            return {
                "tempo_bpm": float(tempo),
                "key": key,
                "time_signature": time_sig,
                "tempo_map": [(0.0, float(tempo))],
                "key_changes": [],
                "scale_type": "major",
            }

        except Exception as e:
            logger.error(f"Error in overall analysis: {e}", exc_info=True)
            return {"tempo_bpm": 120.0, "key": "C major", "time_signature": "4/4"}

    def _request_stem_separation(
        self, audio: np.ndarray, sr: int
    ) -> Optional[Dict[str, np.ndarray]]:
        """Request stem separation from stem separation agent"""
        # This would normally send a request to stem separation agent
        # For now, we'll return a simple simulation

        # In production, this would be:
        # response = self.request("stem.separate", {"audio": audio, "sample_rate": sr})

        # Simulate basic stem separation (placeholder)
        # In reality, would use Demucs or similar
        try:
            # Very basic separation simulation - NOT production quality
            # Just create frequency-based splits for demonstration

            # Low-pass for bass
            bass = librosa.effects.preemphasis(audio, coef=0.0)

            # High-pass for other instruments
            other = audio - bass * 0.3

            stems = {"bass": bass, "other": other}

            return stems

        except Exception as e:
            logger.error(f"Stem separation failed: {e}", exc_info=True)
            return None

    def _transcribe_stems(
        self, stems: Dict[str, np.ndarray], sr: int, overall_analysis: Dict[str, Any]
    ) -> List[TrackTranscription]:
        """Transcribe each stem"""
        tracks = []

        for stem_name, stem_audio in stems.items():
            # Identify instrument type
            instrument_type = self._identify_instrument(stem_audio, sr, stem_name)

            # Transcribe to MIDI
            midi_data = self._transcribe_to_midi(
                stem_audio, sr, instrument_type, overall_analysis
            )

            # Generate tablature if string instrument
            tablature = None
            if instrument_type in ["guitar", "bass"]:
                tablature = self._generate_tablature(midi_data, instrument_type)

            # Harmonic analysis
            harmonic = self._analyze_harmony(
                stem_audio, sr, overall_analysis.get("key", "C major")
            )

            # Rhythmic analysis
            rhythm = self._analyze_rhythm(stem_audio, sr)

            # Quality assessment
            quality = self._assess_quality(midi_data, stem_audio, sr)

            track = TrackTranscription(
                track_id=f"track_{stem_name}",
                instrument_type=instrument_type,
                midi_data=midi_data,
                tablature=tablature,
                harmonic_analysis=harmonic,
                rhythm_analysis=rhythm,
                quality_score=quality,
            )

            tracks.append(track)

        return tracks

    def _transcribe_single_track(
        self, audio: np.ndarray, sr: int, overall_analysis: Dict[str, Any]
    ) -> List[TrackTranscription]:
        """Transcribe single track (no separation)"""
        # Identify instrument
        instrument_type = self._identify_instrument(audio, sr, "mixed")

        # Transcribe
        midi_data = self._transcribe_to_midi(
            audio, sr, instrument_type, overall_analysis
        )

        # Additional analysis
        harmonic = self._analyze_harmony(
            audio, sr, overall_analysis.get("key", "C major")
        )
        rhythm = self._analyze_rhythm(audio, sr)
        quality = self._assess_quality(midi_data, audio, sr)

        track = TrackTranscription(
            track_id="track_main",
            instrument_type=instrument_type,
            midi_data=midi_data,
            harmonic_analysis=harmonic,
            rhythm_analysis=rhythm,
            quality_score=quality,
        )

        return [track]

    def _identify_instrument(self, audio: np.ndarray, sr: int, hint: str = "") -> str:
        """Identify instrument type from audio"""
        # Use hint if available
        if hint in ["bass", "guitar", "drums", "vocals", "piano"]:
            return hint

        # Analyze frequency content
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))

        # Simple heuristic-based identification
        if spectral_centroid < 300:
            return "bass"
        elif spectral_centroid < 1000:
            return "guitar"
        elif spectral_centroid < 3000:
            return "piano"
        else:
            return "vocals"

    def _transcribe_to_midi(
        self,
        audio: np.ndarray,
        sr: int,
        instrument_type: str,
        overall_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Transcribe audio to MIDI"""
        # This would normally call AudioToMIDIAgent
        # Simple transcription for now

        try:
            # Extract pitch
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=sr,
            )

            # Convert to notes
            notes = []
            note_start = None
            note_pitches = []
            times = librosa.frames_to_time(np.arange(len(f0)), sr=sr)

            for i in range(len(f0)):
                if voiced_flag[i] and not np.isnan(f0[i]):
                    if note_start is None:
                        note_start = times[i]
                    note_pitches.append(f0[i])
                else:
                    if note_start is not None and len(note_pitches) > 0:
                        median_hz = np.median(note_pitches)
                        midi_note = int(np.round(librosa.hz_to_midi(median_hz)))

                        if 0 <= midi_note <= 127:
                            notes.append(
                                {
                                    "pitch": midi_note,
                                    "start_time": float(note_start),
                                    "duration": float(times[i] - note_start),
                                    "velocity": 64,
                                }
                            )

                        note_start = None
                        note_pitches = []

            return {
                "notes": notes,
                "tempo_bpm": overall_analysis.get("tempo_bpm", 120.0),
                "time_signature": overall_analysis.get("time_signature", "4/4"),
                "key": overall_analysis.get("key", "C major"),
                "instrument_type": instrument_type,
                "track_name": f"{instrument_type}_track",
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                "notes": [],
                "tempo_bpm": 120.0,
                "time_signature": "4/4",
                "key": "C major",
                "instrument_type": instrument_type,
            }

    def _generate_tablature(
        self, midi_data: Dict[str, Any], instrument_type: str
    ) -> Optional[Dict[str, Any]]:
        """Generate tablature from MIDI data"""
        # This would call TablatureGenerationAgent
        # Simplified version

        try:
            return {
                "instrument": instrument_type,
                "tuning": (
                    ["E", "A", "D", "G", "B", "E"]
                    if instrument_type == "guitar"
                    else ["E", "A", "D", "G"]
                ),
                "notes": [],
                "difficulty_rating": 5.0,
            }
        except:
            return None

    def _analyze_harmony(self, audio: np.ndarray, sr: int, key: str) -> Dict[str, Any]:
        """Analyze harmony"""
        # This would call HarmonicAnalysisAgent
        return {"chords": [], "key": key, "chord_progression": []}

    def _analyze_rhythm(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze rhythm"""
        # This would call RhythmAnalysisAgent
        try:
            tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            return {
                "beat_grid": {
                    "beats": beat_times.tolist(),
                    "downbeats": [],
                    "tempo_curve": [(0.0, float(tempo))],
                },
                "groove_type": "straight",
                "tempo_bpm": float(tempo),
            }
        except:
            return {
                "beat_grid": {"beats": [], "downbeats": []},
                "groove_type": "unknown",
            }

    def _assess_quality(
        self, midi_data: Dict[str, Any], audio: np.ndarray, sr: int
    ) -> float:
        """Assess transcription quality"""
        # Simple quality metric based on note count and coverage
        notes = midi_data.get("notes", [])

        if not notes:
            return 0.0

        # Factor 1: Note count (more notes = potentially better transcription)
        note_count_score = min(1.0, len(notes) / 100)

        # Factor 2: Time coverage
        if len(notes) > 0:
            duration = audio.shape[0] / sr
            last_note_time = notes[-1]["start_time"] + notes[-1]["duration"]
            coverage = min(1.0, last_note_time / duration)
        else:
            coverage = 0.0

        quality = (note_count_score + coverage) / 2

        return float(quality)

    def _export_as_midi(
        self, multitrack_data: Dict[str, Any], output_path: Optional[str]
    ) -> Dict[str, Any]:
        """Export as MIDI file"""
        try:
            midi = pretty_midi.PrettyMIDI(
                initial_tempo=multitrack_data["overall_analysis"].get(
                    "tempo_bpm", 120.0
                )
            )

            # Add each track
            for track_data in multitrack_data.get("tracks", []):
                midi_data = track_data["midi_data"]
                instrument_type = track_data["instrument_type"]

                # Create instrument
                program = self._get_midi_program(instrument_type)
                instrument = pretty_midi.Instrument(program=program)

                # Add notes
                for note in midi_data.get("notes", []):
                    midi_note = pretty_midi.Note(
                        velocity=note.get("velocity", 64),
                        pitch=note["pitch"],
                        start=note["start_time"],
                        end=note["start_time"] + note["duration"],
                    )
                    instrument.notes.append(midi_note)

                midi.instruments.append(instrument)

            if output_path:
                midi.write(output_path)
                return {"success": True, "output_path": output_path}
            else:
                return {"success": True, "midi_data": "MIDI object created"}

        except Exception as e:
            logger.error(f"MIDI export error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _export_as_musicxml(
        self, multitrack_data: Dict[str, Any], output_path: Optional[str]
    ) -> Dict[str, Any]:
        """Export as MusicXML (placeholder)"""
        # Would use music21 for full implementation
        return {
            "success": True,
            "message": "MusicXML export not fully implemented",
            "format": "musicxml",
        }

    def _get_midi_program(self, instrument_type: str) -> int:
        """Get MIDI program number for instrument"""
        program_map = {
            "piano": 0,
            "guitar": 24,
            "bass": 32,
            "violin": 40,
            "trumpet": 56,
            "saxophone": 64,
            "vocals": 53,
            "synth": 80,
            "drums": 0,
        }
        return program_map.get(instrument_type.lower(), 0)

    def _multitrack_to_dict(
        self, multitrack: MultiTrackTranscription
    ) -> Dict[str, Any]:
        """Convert MultiTrackTranscription to dictionary"""
        return {
            "project_name": multitrack.project_name,
            "tracks": [
                {
                    "track_id": t.track_id,
                    "instrument_type": t.instrument_type,
                    "midi_data": t.midi_data,
                    "tablature": t.tablature,
                    "harmonic_analysis": t.harmonic_analysis,
                    "rhythm_analysis": t.rhythm_analysis,
                    "quality_score": float(t.quality_score),
                }
                for t in multitrack.tracks
            ],
            "overall_analysis": multitrack.overall_analysis,
            "tempo_map": multitrack.tempo_map,
            "key_changes": multitrack.key_changes,
            "time_signature_changes": multitrack.time_signature_changes,
            "export_formats": multitrack.export_formats,
        }
