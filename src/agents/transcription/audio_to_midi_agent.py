"""
Audio-to-MIDI Transcription Agent.

Converts audio signals (monophonic or polyphonic) into MIDI note data with
accurate pitch, timing, and velocity information.
"""

import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

try:
    import librosa
    import pretty_midi
    import scipy.signal
except ImportError as e:
    logging.warning(f"Missing MIDI transcription dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics

logger = logging.getLogger(__name__)


@dataclass
class MIDINote:
    """Represents a detected MIDI note"""

    pitch: int  # MIDI note number (0-127)
    start_time: float  # seconds
    duration: float  # seconds
    velocity: int  # 0-127
    pitch_bend: Optional[List[Tuple[float, int]]] = None  # time, bend value
    confidence: float = 1.0  # 0.0-1.0


@dataclass
class MIDITranscription:
    """Complete MIDI transcription result"""

    notes: List[MIDINote]
    tempo_bpm: float
    time_signature: str
    key: str
    track_name: str
    instrument_type: str  # "guitar", "piano", "vocals", etc.
    polyphony_detected: bool
    accuracy_estimate: float  # 0.0-1.0


class AudioToMIDIAgent(BaseAgent):
    """
    Agent for converting audio to MIDI.

    Capabilities:
    - Monophonic pitch detection (YIN/PYIN algorithm)
    - Polyphonic transcription (chromagram-based)
    - Note onset/offset detection
    - Velocity estimation
    - Pitch bend capture
    - Support for stem-based transcription
    - Real-time mode support
    """

    def __init__(self):
        super().__init__(
            agent_id="audio_to_midi_agent",
            agent_name="Audio-to-MIDI Transcription Agent",
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "transcriptions_performed": 0,
            "monophonic_transcriptions": 0,
            "polyphonic_transcriptions": 0,
            "total_notes_detected": 0,
            "errors": 0,
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Audio-to-MIDI Agent")

        # Subscribe to transcription topics
        self.subscribe("transcription.audio_to_midi")
        self.subscribe("transcription.monophonic")
        self.subscribe("transcription.polyphonic")
        self.subscribe("transcription.from_stem")
        self.subscribe("transcription.realtime")

        self.log("INFO", "Audio-to-MIDI Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Audio-to-MIDI Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming transcription requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic in ["transcription.audio_to_midi", "transcription.from_stem"]:
                result = self._transcribe_audio(payload)
            elif topic == "transcription.monophonic":
                result = self._transcribe_monophonic(payload)
            elif topic == "transcription.polyphonic":
                result = self._transcribe_polyphonic(payload)
            elif topic == "transcription.realtime":
                result = self._transcribe_realtime(payload)
            else:
                result = {"success": False, "error": f"Unknown topic: {topic}"}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats["errors"] += 1
            self.respond(message, {"success": False, "error": str(e)})

    def _transcribe_audio(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically detect and transcribe audio (mono or poly)"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            instrument_type = payload.get("instrument_type", "unknown")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Detect if polyphonic
            is_polyphonic = self._detect_polyphony(audio, sr)

            if is_polyphonic:
                transcription = self._transcribe_polyphonic_internal(
                    audio, sr, instrument_type
                )
                with self._lock:
                    self._stats["polyphonic_transcriptions"] += 1
            else:
                transcription = self._transcribe_monophonic_internal(
                    audio, sr, instrument_type
                )
                with self._lock:
                    self._stats["monophonic_transcriptions"] += 1

            with self._lock:
                self._stats["transcriptions_performed"] += 1
                self._stats["total_notes_detected"] += len(transcription.notes)

            return {
                "success": True,
                "transcription": self._transcription_to_dict(transcription),
            }

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _transcribe_monophonic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe monophonic audio"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            instrument_type = payload.get("instrument_type", "unknown")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            transcription = self._transcribe_monophonic_internal(
                audio, sr, instrument_type
            )

            with self._lock:
                self._stats["transcriptions_performed"] += 1
                self._stats["monophonic_transcriptions"] += 1
                self._stats["total_notes_detected"] += len(transcription.notes)

            return {
                "success": True,
                "transcription": self._transcription_to_dict(transcription),
            }

        except Exception as e:
            logger.error(f"Error in monophonic transcription: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _transcribe_polyphonic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe polyphonic audio"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            instrument_type = payload.get("instrument_type", "unknown")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            transcription = self._transcribe_polyphonic_internal(
                audio, sr, instrument_type
            )

            with self._lock:
                self._stats["transcriptions_performed"] += 1
                self._stats["polyphonic_transcriptions"] += 1
                self._stats["total_notes_detected"] += len(transcription.notes)

            return {
                "success": True,
                "transcription": self._transcription_to_dict(transcription),
            }

        except Exception as e:
            logger.error(f"Error in polyphonic transcription: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _transcribe_realtime(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio in real-time mode (optimized for low latency)"""
        try:
            audio = payload.get("audio")
            sr = payload.get("sample_rate", 22050)
            instrument_type = payload.get("instrument_type", "unknown")

            if audio is None:
                return {"success": False, "error": "No audio data provided"}

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Use faster monophonic detection for real-time
            transcription = self._transcribe_monophonic_internal(
                audio, sr, instrument_type, realtime=True
            )

            return {
                "success": True,
                "transcription": self._transcription_to_dict(transcription),
                "latency_optimized": True,
            }

        except Exception as e:
            logger.error(f"Error in real-time transcription: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _detect_polyphony(self, audio: np.ndarray, sr: int) -> bool:
        """Detect if audio contains polyphonic content"""
        # Use chromagram to detect multiple simultaneous pitches
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)

        # Count active pitch classes per frame
        threshold = 0.3
        active_pitches_per_frame = np.sum(chroma > threshold, axis=0)

        # If average active pitches > 1.5, likely polyphonic
        avg_active = np.mean(active_pitches_per_frame)

        return avg_active > 1.5

    def _transcribe_monophonic_internal(
        self, audio: np.ndarray, sr: int, instrument_type: str, realtime: bool = False
    ) -> MIDITranscription:
        """Internal monophonic transcription using PYIN algorithm"""

        # Extract pitch using PYIN (probabilistic YIN)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            frame_length=2048 if realtime else 4096,
        )

        # Detect onsets
        onset_frames = librosa.onset.onset_detect(
            y=audio, sr=sr, backtrack=True, units="frames"
        )

        # Convert to times
        times = librosa.frames_to_time(np.arange(len(f0)), sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # Extract notes from f0 contour
        notes = self._extract_notes_from_f0(
            f0, voiced_flag, voiced_probs, times, onset_times, audio, sr
        )

        # Estimate tempo and key
        tempo = self._estimate_tempo(audio, sr)
        key = self._estimate_key(audio, sr)

        return MIDITranscription(
            notes=notes,
            tempo_bpm=tempo,
            time_signature="4/4",
            key=key,
            track_name=f"{instrument_type}_track",
            instrument_type=instrument_type,
            polyphony_detected=False,
            accuracy_estimate=self._estimate_accuracy(notes, voiced_probs),
        )

    def _transcribe_polyphonic_internal(
        self, audio: np.ndarray, sr: int, instrument_type: str
    ) -> MIDITranscription:
        """Internal polyphonic transcription using chromagram"""

        # Use CQT-based chromagram for better frequency resolution
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=512)

        # Get onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, backtrack=True
        )

        # Convert frames to time
        times = librosa.frames_to_time(
            np.arange(chroma.shape[1]), sr=sr, hop_length=512
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # Extract notes from chromagram
        notes = self._extract_notes_from_chroma(chroma, times, onset_times, audio, sr)

        # Estimate tempo and key
        tempo = self._estimate_tempo(audio, sr)
        key = self._estimate_key(audio, sr)

        return MIDITranscription(
            notes=notes,
            tempo_bpm=tempo,
            time_signature="4/4",
            key=key,
            track_name=f"{instrument_type}_track",
            instrument_type=instrument_type,
            polyphony_detected=True,
            accuracy_estimate=self._estimate_accuracy_polyphonic(notes, chroma),
        )

    def _extract_notes_from_f0(
        self,
        f0: np.ndarray,
        voiced_flag: np.ndarray,
        voiced_probs: np.ndarray,
        times: np.ndarray,
        onset_times: np.ndarray,
        audio: np.ndarray,
        sr: int,
    ) -> List[MIDINote]:
        """Extract MIDI notes from F0 contour"""
        notes = []

        if len(f0) == 0:
            return notes

        # Group consecutive voiced frames into notes
        note_start = None
        note_pitches = []

        for i in range(len(f0)):
            if voiced_flag[i] and not np.isnan(f0[i]) and voiced_probs[i] > 0.5:
                if note_start is None:
                    note_start = times[i]
                note_pitches.append(f0[i])
            else:
                # End of note
                if note_start is not None and len(note_pitches) > 0:
                    # Calculate median pitch for stability
                    median_hz = np.median(note_pitches)
                    midi_note = librosa.hz_to_midi(median_hz)
                    midi_note = int(np.round(midi_note))

                    # Calculate velocity from amplitude
                    start_frame = int(note_start * sr)
                    end_frame = int(times[i] * sr)
                    note_audio = audio[start_frame:end_frame]

                    if len(note_audio) > 0:
                        velocity = int(
                            np.clip(np.sqrt(np.mean(note_audio**2)) * 127 * 10, 1, 127)
                        )
                    else:
                        velocity = 64

                    duration = times[i] - note_start

                    # Only add notes with reasonable duration
                    if duration > 0.05 and 0 <= midi_note <= 127:
                        notes.append(
                            MIDINote(
                                pitch=midi_note,
                                start_time=note_start,
                                duration=duration,
                                velocity=velocity,
                                confidence=float(
                                    np.mean(
                                        voiced_probs[max(0, i - len(note_pitches)) : i]
                                    )
                                ),
                            )
                        )

                    note_start = None
                    note_pitches = []

        # Handle final note
        if note_start is not None and len(note_pitches) > 0:
            median_hz = np.median(note_pitches)
            midi_note = int(np.round(librosa.hz_to_midi(median_hz)))

            if 0 <= midi_note <= 127:
                notes.append(
                    MIDINote(
                        pitch=midi_note,
                        start_time=note_start,
                        duration=times[-1] - note_start,
                        velocity=64,
                        confidence=0.8,
                    )
                )

        return notes

    def _extract_notes_from_chroma(
        self,
        chroma: np.ndarray,
        times: np.ndarray,
        onset_times: np.ndarray,
        audio: np.ndarray,
        sr: int,
    ) -> List[MIDINote]:
        """Extract MIDI notes from chromagram (polyphonic)"""
        notes = []

        # Threshold for note detection
        threshold = 0.4

        # Track active notes (pitch class -> (start_time, octave_estimate))
        active_notes: Dict[int, List[Tuple[float, int]]] = {}

        for frame_idx in range(chroma.shape[1]):
            current_time = times[frame_idx]
            active_pitches = np.where(chroma[:, frame_idx] > threshold)[0]

            # Estimate octave based on spectral content
            frame_start = int(current_time * sr)
            frame_end = int((current_time + 0.023) * sr)  # ~23ms frame
            frame_audio = audio[frame_start:frame_end]

            if len(frame_audio) > 0:
                # Rough octave estimation from spectral centroid
                centroid = librosa.feature.spectral_centroid(y=frame_audio, sr=sr)[0, 0]
                octave_estimate = max(2, min(6, int(np.log2(centroid / 32.7) - 2)))
            else:
                octave_estimate = 4

            # Update active notes
            current_active = set()

            for pitch_class in active_pitches:
                current_active.add(pitch_class)

                if pitch_class not in active_notes:
                    # New note started
                    active_notes[pitch_class] = [(current_time, octave_estimate)]

            # Check for ended notes
            for pitch_class in list(active_notes.keys()):
                if pitch_class not in current_active:
                    # Note ended
                    for start_time, octave in active_notes[pitch_class]:
                        duration = current_time - start_time

                        if duration > 0.05:  # Minimum duration
                            midi_note = pitch_class + (octave * 12)

                            # Calculate velocity
                            start_frame = int(start_time * sr)
                            end_frame = int(current_time * sr)
                            note_audio = audio[start_frame:end_frame]

                            if len(note_audio) > 0:
                                velocity = int(
                                    np.clip(
                                        np.sqrt(np.mean(note_audio**2)) * 127 * 10,
                                        1,
                                        127,
                                    )
                                )
                            else:
                                velocity = 64

                            if 0 <= midi_note <= 127:
                                notes.append(
                                    MIDINote(
                                        pitch=midi_note,
                                        start_time=start_time,
                                        duration=duration,
                                        velocity=velocity,
                                        confidence=0.7,
                                    )
                                )

                    del active_notes[pitch_class]

        # Handle remaining active notes
        if len(times) > 0:
            final_time = times[-1]
            for pitch_class, note_list in active_notes.items():
                for start_time, octave in note_list:
                    duration = final_time - start_time
                    if duration > 0.05:
                        midi_note = pitch_class + (octave * 12)
                        if 0 <= midi_note <= 127:
                            notes.append(
                                MIDINote(
                                    pitch=midi_note,
                                    start_time=start_time,
                                    duration=duration,
                                    velocity=64,
                                    confidence=0.6,
                                )
                            )

        return notes

    def _estimate_tempo(self, audio: np.ndarray, sr: int) -> float:
        """Estimate tempo from audio"""
        try:
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            return float(tempo)
        except:
            return 120.0

    def _estimate_key(self, audio: np.ndarray, sr: int) -> str:
        """Estimate key from audio"""
        try:
            chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            key_idx = np.argmax(chroma_mean)
            keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            return f"{keys[key_idx]} major"
        except:
            return "C major"

    def _estimate_accuracy(
        self, notes: List[MIDINote], voiced_probs: np.ndarray
    ) -> float:
        """Estimate transcription accuracy"""
        if len(notes) == 0:
            return 0.0

        # Average confidence of all notes
        avg_confidence = np.mean([note.confidence for note in notes])

        # Factor in voicing probability
        avg_voicing = np.mean(voiced_probs[~np.isnan(voiced_probs)])

        return float((avg_confidence + avg_voicing) / 2)

    def _estimate_accuracy_polyphonic(
        self, notes: List[MIDINote], chroma: np.ndarray
    ) -> float:
        """Estimate polyphonic transcription accuracy"""
        if len(notes) == 0:
            return 0.0

        # Use chroma energy as confidence
        avg_energy = np.mean(np.max(chroma, axis=0))

        # Average note confidence
        avg_confidence = np.mean([note.confidence for note in notes])

        return float(min(1.0, (avg_confidence + avg_energy) / 2))

    def _transcription_to_dict(
        self, transcription: MIDITranscription
    ) -> Dict[str, Any]:
        """Convert transcription to dictionary"""
        return {
            "notes": [
                {
                    "pitch": note.pitch,
                    "start_time": float(note.start_time),
                    "duration": float(note.duration),
                    "velocity": note.velocity,
                    "confidence": float(note.confidence),
                }
                for note in transcription.notes
            ],
            "tempo_bpm": float(transcription.tempo_bpm),
            "time_signature": transcription.time_signature,
            "key": transcription.key,
            "track_name": transcription.track_name,
            "instrument_type": transcription.instrument_type,
            "polyphony_detected": transcription.polyphony_detected,
            "accuracy_estimate": float(transcription.accuracy_estimate),
        }

    def create_midi_file(
        self, transcription: MIDITranscription, output_path: str
    ) -> bool:
        """Create a MIDI file from transcription"""
        try:
            midi = pretty_midi.PrettyMIDI(initial_tempo=transcription.tempo_bpm)

            # Create instrument
            program = self._get_midi_program(transcription.instrument_type)
            instrument = pretty_midi.Instrument(program=program)

            # Add notes
            for note in transcription.notes:
                midi_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=note.start_time,
                    end=note.start_time + note.duration,
                )
                instrument.notes.append(midi_note)

            midi.instruments.append(instrument)

            # Write MIDI file
            midi.write(output_path)

            return True

        except Exception as e:
            logger.error(f"Error creating MIDI file: {e}", exc_info=True)
            return False

    def _get_midi_program(self, instrument_type: str) -> int:
        """Get MIDI program number for instrument type"""
        program_map = {
            "piano": 0,
            "guitar": 24,
            "bass": 32,
            "violin": 40,
            "trumpet": 56,
            "saxophone": 64,
            "flute": 73,
            "synth": 80,
            "vocals": 53,
            "drums": 0,  # Channel 10
        }
        return program_map.get(instrument_type.lower(), 0)
