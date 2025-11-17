"""
Tablature Generation Agent.

Generates instrument-specific tablature (guitar, bass, ukulele) from MIDI data
or audio, with intelligent fingering and fret position suggestions.
"""

import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

try:
    import librosa
except ImportError as e:
    logging.warning(f"Missing tablature dependencies: {e}")

from ...core.base_agent import BaseAgent
from ...core.message_types import Message, Priority, Topics


logger = logging.getLogger(__name__)


@dataclass
class TabNote:
    """Represents a tablature note"""
    string: int  # String number (1-6 for guitar)
    fret: int  # Fret number
    start_time: float
    duration: float
    technique: Optional[str] = None  # "h", "p", "s", "b", etc.
    finger: Optional[int] = None  # Suggested finger (1-4)


@dataclass
class ChordDiagram:
    """Guitar chord diagram"""
    name: str
    frets: List[int]  # Fret for each string (-1 = muted, 0 = open)
    fingers: List[int]  # Finger for each string (0 = not played)


@dataclass
class Tablature:
    """Complete tablature"""
    instrument: str  # "guitar", "bass", etc.
    tuning: List[str]  # ["E", "A", "D", "G", "B", "E"]
    notes: List[TabNote]
    tempo_bpm: float
    time_signature: str = "4/4"
    chord_diagrams: List[ChordDiagram] = field(default_factory=list)
    difficulty_rating: float = 5.0  # 1.0 (easy) to 10.0 (expert)


class TablatureGenerationAgent(BaseAgent):
    """
    Agent for generating tablature from MIDI or audio.

    Capabilities:
    - Guitar tablature (6, 7, 8 string)
    - Bass tablature (4, 5, 6 string)
    - Ukulele tablature
    - Intelligent fingering suggestions
    - Fret position optimization
    - Alternate tunings support
    - Technique notation
    - ASCII and JSON export
    """

    # Standard tunings (low to high)
    TUNINGS = {
        'guitar_standard': ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'guitar_drop_d': ['D2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'guitar_7string': ['B1', 'E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'guitar_8string': ['F#1', 'B1', 'E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'bass_4string': ['E1', 'A1', 'D2', 'G2'],
        'bass_5string': ['B0', 'E1', 'A1', 'D2', 'G2'],
        'bass_6string': ['B0', 'E1', 'A1', 'D2', 'G2', 'C3'],
        'ukulele_standard': ['G4', 'C4', 'E4', 'A4'],
        'ukulele_baritone': ['D3', 'G3', 'B3', 'E4'],
    }

    def __init__(self):
        super().__init__(
            agent_id="tablature_generation_agent",
            agent_name="Tablature Generation Agent"
        )

        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            'tablatures_generated': 0,
            'guitar_tabs': 0,
            'bass_tabs': 0,
            'ukulele_tabs': 0,
            'total_notes': 0,
            'errors': 0
        }

    def setup(self):
        """Initialize the agent and subscribe to topics"""
        self.log("INFO", "Setting up Tablature Generation Agent")

        # Subscribe to tablature topics
        self.subscribe("tablature.generate")
        self.subscribe("tablature.from_audio")
        self.subscribe("tablature.optimize_fingering")
        self.subscribe("tablature.export")

        self.log("INFO", "Tablature Generation Agent ready")

    def teardown(self):
        """Cleanup resources"""
        self.log("INFO", "Tablature Generation Agent shutting down")
        self.log("INFO", f"Final statistics: {self._stats}")

    def handle_message(self, message: Message):
        """Handle incoming tablature requests"""
        try:
            topic = message.topic
            payload = message.payload

            if topic == "tablature.generate":
                result = self._generate_tablature(payload)
            elif topic == "tablature.from_audio":
                result = self._generate_from_audio(payload)
            elif topic == "tablature.optimize_fingering":
                result = self._optimize_fingering(payload)
            elif topic == "tablature.export":
                result = self._export_tablature(payload)
            else:
                result = {'success': False, 'error': f'Unknown topic: {topic}'}

            # Send response
            self.respond(message, result)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            with self._lock:
                self._stats['errors'] += 1
            self.respond(message, {'success': False, 'error': str(e)})

    def _generate_tablature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tablature from MIDI notes"""
        try:
            notes = payload.get('notes', [])
            instrument = payload.get('instrument', 'guitar').lower()
            tuning_name = payload.get('tuning', f'{instrument}_standard')
            tempo_bpm = payload.get('tempo_bpm', 120.0)

            if not notes:
                return {'success': False, 'error': 'No notes provided'}

            # Get tuning
            tuning = self._get_tuning(instrument, tuning_name)

            # Convert MIDI notes to tab notes
            tab_notes = self._midi_to_tab(notes, tuning, instrument)

            # Optimize fingering
            tab_notes = self._apply_fingering(tab_notes, tuning)

            # Calculate difficulty
            difficulty = self._calculate_difficulty(tab_notes)

            # Create tablature
            tablature = Tablature(
                instrument=instrument,
                tuning=[self._note_name(note) for note in tuning],
                notes=tab_notes,
                tempo_bpm=tempo_bpm,
                difficulty_rating=difficulty
            )

            # Update statistics
            with self._lock:
                self._stats['tablatures_generated'] += 1
                self._stats['total_notes'] += len(tab_notes)
                if 'guitar' in instrument:
                    self._stats['guitar_tabs'] += 1
                elif 'bass' in instrument:
                    self._stats['bass_tabs'] += 1
                elif 'ukulele' in instrument:
                    self._stats['ukulele_tabs'] += 1

            return {
                'success': True,
                'tablature': self._tablature_to_dict(tablature)
            }

        except Exception as e:
            logger.error(f"Error generating tablature: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _generate_from_audio(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tablature directly from audio"""
        try:
            audio = payload.get('audio')
            sr = payload.get('sample_rate', 22050)
            instrument = payload.get('instrument', 'guitar').lower()

            if audio is None:
                return {'success': False, 'error': 'No audio data provided'}

            # First transcribe to MIDI
            # This would normally call the AudioToMIDIAgent
            # For now, we'll do a simple monophonic transcription

            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Extract pitch
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr
            )

            # Convert to MIDI notes (simplified)
            notes = self._f0_to_midi_notes(f0, voiced_flag, sr)

            # Get tuning
            tuning_name = f'{instrument}_standard'
            tuning = self._get_tuning(instrument, tuning_name)

            # Convert to tablature
            tab_notes = self._midi_to_tab(notes, tuning, instrument)
            tab_notes = self._apply_fingering(tab_notes, tuning)

            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)

            tablature = Tablature(
                instrument=instrument,
                tuning=[self._note_name(note) for note in tuning],
                notes=tab_notes,
                tempo_bpm=float(tempo),
                difficulty_rating=self._calculate_difficulty(tab_notes)
            )

            with self._lock:
                self._stats['tablatures_generated'] += 1

            return {
                'success': True,
                'tablature': self._tablature_to_dict(tablature)
            }

        except Exception as e:
            logger.error(f"Error generating from audio: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _optimize_fingering(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize fingering for tablature"""
        try:
            tablature_dict = payload.get('tablature')

            if not tablature_dict:
                return {'success': False, 'error': 'No tablature provided'}

            # Reconstruct tablature
            tab_notes = [
                TabNote(
                    string=n['string'],
                    fret=n['fret'],
                    start_time=n['start_time'],
                    duration=n['duration'],
                    technique=n.get('technique'),
                    finger=n.get('finger')
                )
                for n in tablature_dict.get('notes', [])
            ]

            tuning = self._parse_tuning(tablature_dict.get('tuning', []))

            # Re-optimize fingering
            optimized_notes = self._apply_fingering(tab_notes, tuning)

            return {
                'success': True,
                'optimized_notes': [
                    {
                        'string': n.string,
                        'fret': n.fret,
                        'start_time': n.start_time,
                        'duration': n.duration,
                        'technique': n.technique,
                        'finger': n.finger
                    }
                    for n in optimized_notes
                ]
            }

        except Exception as e:
            logger.error(f"Error optimizing fingering: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _export_tablature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Export tablature in various formats"""
        try:
            tablature_dict = payload.get('tablature')
            export_format = payload.get('format', 'ascii').lower()

            if not tablature_dict:
                return {'success': False, 'error': 'No tablature provided'}

            if export_format == 'ascii':
                output = self._to_ascii(tablature_dict)
            elif export_format == 'json':
                output = tablature_dict  # Already in JSON format
            else:
                return {'success': False, 'error': f'Unknown format: {export_format}'}

            return {
                'success': True,
                'format': export_format,
                'output': output
            }

        except Exception as e:
            logger.error(f"Error exporting tablature: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _get_tuning(self, instrument: str, tuning_name: str) -> List[int]:
        """Get tuning as MIDI note numbers"""
        if tuning_name not in self.TUNINGS:
            # Default to standard tuning for instrument
            tuning_name = f'{instrument}_standard'

        if tuning_name not in self.TUNINGS:
            # Ultimate fallback
            tuning_name = 'guitar_standard'

        note_names = self.TUNINGS[tuning_name]
        return [librosa.note_to_midi(note) for note in note_names]

    def _parse_tuning(self, tuning_names: List[str]) -> List[int]:
        """Parse tuning from note names"""
        tuning = []
        for note_name in tuning_names:
            # Add octave if not present
            if len(note_name) == 1 or (len(note_name) == 2 and '#' in note_name):
                note_name += '3'  # Default octave
            tuning.append(librosa.note_to_midi(note_name))
        return tuning

    def _midi_to_tab(
        self,
        notes: List[Dict[str, Any]],
        tuning: List[int],
        instrument: str
    ) -> List[TabNote]:
        """Convert MIDI notes to tablature notes"""
        tab_notes = []

        for note in notes:
            pitch = note.get('pitch')
            start_time = note.get('start_time', 0.0)
            duration = note.get('duration', 0.5)

            if pitch is None:
                continue

            # Find best string/fret combination
            string, fret = self._find_position(pitch, tuning)

            if string is not None and fret is not None:
                tab_notes.append(TabNote(
                    string=string,
                    fret=fret,
                    start_time=start_time,
                    duration=duration
                ))

        return tab_notes

    def _find_position(self, pitch: int, tuning: List[int]) -> Tuple[Optional[int], Optional[int]]:
        """Find best string and fret for a pitch"""
        max_fret = 24  # Maximum fret number

        best_string = None
        best_fret = None
        best_score = -1

        # Try each string
        for string_idx, open_pitch in enumerate(tuning):
            fret = pitch - open_pitch

            if 0 <= fret <= max_fret:
                # Calculate score (prefer lower frets and middle strings)
                fret_score = 1.0 - (fret / max_fret)
                string_score = 1.0 - abs(string_idx - len(tuning) / 2) / len(tuning)
                score = fret_score * 0.7 + string_score * 0.3

                if score > best_score:
                    best_score = score
                    best_string = string_idx + 1  # 1-indexed
                    best_fret = fret

        return best_string, best_fret

    def _apply_fingering(self, tab_notes: List[TabNote], tuning: List[int]) -> List[TabNote]:
        """Apply intelligent fingering suggestions"""
        if not tab_notes:
            return tab_notes

        # Sort notes by time
        sorted_notes = sorted(tab_notes, key=lambda n: n.start_time)

        # Apply fingering based on fret position
        for i, note in enumerate(sorted_notes):
            if note.fret == 0:
                note.finger = 0  # Open string
            elif note.fret <= 4:
                # First position - map fret to finger
                note.finger = min(note.fret, 4)
            else:
                # Higher positions - use hand position
                # Estimate hand position from previous notes
                if i > 0:
                    prev_note = sorted_notes[i - 1]
                    hand_position = max(1, prev_note.fret - 3)
                else:
                    hand_position = max(1, note.fret - 3)

                # Finger is fret - hand_position + 1
                finger = note.fret - hand_position + 1
                note.finger = max(1, min(4, finger))

            # Detect techniques based on note transitions
            if i > 0:
                prev_note = sorted_notes[i - 1]
                time_diff = note.start_time - prev_note.start_time

                # Same string, close time -> could be hammer-on/pull-off
                if note.string == prev_note.string and time_diff < 0.3:
                    if note.fret > prev_note.fret:
                        note.technique = 'h'  # Hammer-on
                    elif note.fret < prev_note.fret:
                        note.technique = 'p'  # Pull-off

                # Quick fret change -> could be slide
                if (note.string == prev_note.string and
                    abs(note.fret - prev_note.fret) > 2 and
                    time_diff < 0.2):
                    note.technique = 's'  # Slide

        return sorted_notes

    def _calculate_difficulty(self, tab_notes: List[TabNote]) -> float:
        """Calculate tablature difficulty rating"""
        if not tab_notes:
            return 1.0

        difficulty_factors = []

        # Factor 1: Average fret position (higher = harder)
        avg_fret = np.mean([note.fret for note in tab_notes if note.fret > 0])
        fret_difficulty = min(10, avg_fret / 2)
        difficulty_factors.append(fret_difficulty)

        # Factor 2: Fret range (larger range = harder)
        frets = [note.fret for note in tab_notes]
        fret_range = max(frets) - min(frets)
        range_difficulty = min(10, fret_range / 3)
        difficulty_factors.append(range_difficulty)

        # Factor 3: String jumps
        string_jumps = 0
        for i in range(1, len(tab_notes)):
            if abs(tab_notes[i].string - tab_notes[i-1].string) > 2:
                string_jumps += 1
        jump_difficulty = min(10, string_jumps / len(tab_notes) * 50)
        difficulty_factors.append(jump_difficulty)

        # Factor 4: Techniques
        technique_count = sum(1 for note in tab_notes if note.technique)
        technique_difficulty = min(10, technique_count / len(tab_notes) * 30)
        difficulty_factors.append(technique_difficulty)

        # Factor 5: Note density
        if len(tab_notes) > 1:
            duration = tab_notes[-1].start_time - tab_notes[0].start_time
            if duration > 0:
                density = len(tab_notes) / duration
                density_difficulty = min(10, density / 2)
                difficulty_factors.append(density_difficulty)

        # Average all factors
        difficulty = np.mean(difficulty_factors)

        return float(np.clip(difficulty, 1.0, 10.0))

    def _f0_to_midi_notes(
        self,
        f0: np.ndarray,
        voiced_flag: np.ndarray,
        sr: int
    ) -> List[Dict[str, Any]]:
        """Convert F0 contour to MIDI notes (simplified)"""
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
                        notes.append({
                            'pitch': midi_note,
                            'start_time': note_start,
                            'duration': times[i] - note_start,
                            'velocity': 64
                        })

                    note_start = None
                    note_pitches = []

        return notes

    def _note_name(self, midi_note: int) -> str:
        """Convert MIDI note number to name"""
        return librosa.midi_to_note(midi_note)

    def _tablature_to_dict(self, tablature: Tablature) -> Dict[str, Any]:
        """Convert tablature to dictionary"""
        return {
            'instrument': tablature.instrument,
            'tuning': tablature.tuning,
            'notes': [
                {
                    'string': n.string,
                    'fret': n.fret,
                    'start_time': float(n.start_time),
                    'duration': float(n.duration),
                    'technique': n.technique,
                    'finger': n.finger
                }
                for n in tablature.notes
            ],
            'tempo_bpm': float(tablature.tempo_bpm),
            'time_signature': tablature.time_signature,
            'difficulty_rating': float(tablature.difficulty_rating)
        }

    def _to_ascii(self, tablature_dict: Dict[str, Any]) -> str:
        """Convert tablature to ASCII format"""
        tuning = tablature_dict.get('tuning', [])
        notes = tablature_dict.get('notes', [])

        if not tuning or not notes:
            return "Empty tablature"

        # Create ASCII tab lines
        num_strings = len(tuning)
        lines = [f"{tuning[i]}|" for i in range(num_strings)]

        # Sort notes by time
        sorted_notes = sorted(notes, key=lambda n: n['start_time'])

        # Group notes by time (chords)
        time_groups = {}
        for note in sorted_notes:
            time_key = round(note['start_time'] * 4) / 4  # Quantize to 16th notes
            if time_key not in time_groups:
                time_groups[time_key] = []
            time_groups[time_key].append(note)

        # Build tablature
        for time_key in sorted(time_groups.keys()):
            group = time_groups[time_key]

            # Add dashes for spacing
            for i in range(num_strings):
                lines[i] += "-"

            # Add notes
            for note in group:
                string_idx = note['string'] - 1
                fret = note['fret']
                technique = note.get('technique', '')

                # Add fret number
                fret_str = str(fret)
                if technique:
                    fret_str += technique

                # Pad lines
                max_len = max(len(line) for line in lines)
                for i in range(num_strings):
                    while len(lines[i]) < max_len:
                        lines[i] += "-"

                # Add note
                lines[string_idx] += fret_str

        # Close lines
        for i in range(num_strings):
            lines[i] += "|"

        return "\n".join(lines)
