"""
Content Generation & Gap Filling Agent

This agent handles AI-powered music content generation including:
- Melody generation
- Harmony generation
- Drum pattern generation
- Bass line generation
- Arrangement enhancement
- Style transfer
"""

import numpy as np
import threading
import queue
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import logging
import json

try:
    import librosa
    import pretty_midi
except ImportError:
    librosa = None
    pretty_midi = None

from ..core import BaseAgent, Message, Topics, Priority

logger = logging.getLogger(__name__)


@dataclass
class MusicContext:
    """Musical context for generation"""
    key: str = "C major"
    tempo: float = 120.0
    time_signature: str = "4/4"
    chord_progression: List[str] = field(default_factory=list)
    genre: str = "pop"
    style: str = "modern"
    length_bars: int = 8


@dataclass
class GeneratedContent:
    """Result from content generation"""
    content_type: str
    audio_data: Optional[np.ndarray] = None
    midi_data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class ContentGenerationAgent(BaseAgent):
    """
    Agent responsible for AI-powered music content generation.

    Capabilities:
    - Melody generation based on harmonic context
    - Harmony generation for melodies
    - Drum pattern generation
    - Bass line generation
    - Arrangement enhancement
    - Music style transfer
    """

    def __init__(self):
        super().__init__(
            agent_id="content_generation_agent",
            agent_name="Content Generation & Gap Filling Agent"
        )

        # Processing queue
        self.processing_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None

        # Music theory knowledge
        self.key_signatures = self._initialize_key_signatures()
        self.chord_templates = self._initialize_chord_templates()
        self.scale_patterns = self._initialize_scale_patterns()

        # Generation parameters
        self.generation_params = {
            'melody': {
                'temperature': 0.8,
                'note_range': (60, 84),  # MIDI note range
                'rhythmic_density': 0.7
            },
            'harmony': {
                'num_voices': 4,
                'voice_leading_weight': 0.8
            },
            'drums': {
                'complexity': 'medium',
                'swing_factor': 0.0
            },
            'bass': {
                'pattern_style': 'root_fifth',
                'rhythmic_pattern': 'quarter_notes'
            }
        }

        # Statistics
        self.stats = {
            'melodies_generated': 0,
            'harmonies_generated': 0,
            'drum_patterns_generated': 0,
            'bass_lines_generated': 0,
            'total_generation_time': 0.0
        }
        self.stats_lock = threading.Lock()

    def setup(self):
        """Initialize the content generation agent"""
        # Subscribe to relevant topics
        self.subscribe("music.generation.melody.request")
        self.subscribe("music.generation.harmony.request")
        self.subscribe("music.generation.drums.request")
        self.subscribe("music.generation.bass.request")
        self.subscribe("music.generation.arrangement.request")
        self.subscribe("music.style.transfer.request")

        # Start processing thread
        self._start_processing_thread()

        self.log("INFO", "Content Generation Agent initialized successfully")

    def teardown(self):
        """Cleanup resources"""
        # Stop processing thread
        self._stop_processing_thread()

        self.log("INFO", "Content Generation Agent shutdown complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        try:
            if message.topic == "music.generation.melody.request":
                self._handle_melody_request(message)
            elif message.topic == "music.generation.harmony.request":
                self._handle_harmony_request(message)
            elif message.topic == "music.generation.drums.request":
                self._handle_drums_request(message)
            elif message.topic == "music.generation.bass.request":
                self._handle_bass_request(message)
            elif message.topic == "music.generation.arrangement.request":
                self._handle_arrangement_request(message)
            elif message.topic == "music.style.transfer.request":
                self._handle_style_transfer_request(message)
            else:
                self.log("WARNING", f"Unknown message topic: {message.topic}")

        except Exception as e:
            self.log("ERROR", f"Error handling message: {e}", {"topic": message.topic})

    def _handle_melody_request(self, message: Message):
        """Handle melody generation request"""
        payload = message.payload
        context = self._extract_music_context(payload)

        job = {
            'type': 'melody',
            'message': message,
            'context': context,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _handle_harmony_request(self, message: Message):
        """Handle harmony generation request"""
        payload = message.payload
        context = self._extract_music_context(payload)
        melody_data = payload.get('melody_data')

        job = {
            'type': 'harmony',
            'message': message,
            'context': context,
            'melody_data': melody_data,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _handle_drums_request(self, message: Message):
        """Handle drum pattern generation request"""
        payload = message.payload
        context = self._extract_music_context(payload)

        job = {
            'type': 'drums',
            'message': message,
            'context': context,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _handle_bass_request(self, message: Message):
        """Handle bass line generation request"""
        payload = message.payload
        context = self._extract_music_context(payload)

        job = {
            'type': 'bass',
            'message': message,
            'context': context,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _handle_arrangement_request(self, message: Message):
        """Handle arrangement enhancement request"""
        payload = message.payload
        existing_stems = payload.get('existing_stems', {})

        job = {
            'type': 'arrangement',
            'message': message,
            'existing_stems': existing_stems,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _handle_style_transfer_request(self, message: Message):
        """Handle music style transfer request"""
        payload = message.payload
        source_audio = payload.get('source_audio')
        target_style = payload.get('target_style', 'jazz')

        job = {
            'type': 'style_transfer',
            'message': message,
            'source_audio': source_audio,
            'target_style': target_style,
            'params': payload.get('params', {})
        }
        self.processing_queue.put(job)

    def _start_processing_thread(self):
        """Start the processing worker thread"""
        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            name=f"{self.agent_id}_processor",
            daemon=True
        )
        self.processing_thread.start()

    def _stop_processing_thread(self):
        """Stop the processing worker thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_queue.put(None)  # Sentinel
            self.processing_thread.join(timeout=5.0)

    def _processing_worker(self):
        """Worker thread for processing generation jobs"""
        import time

        while True:
            try:
                job = self.processing_queue.get(timeout=1.0)

                if job is None:  # Sentinel to stop
                    break

                start_time = time.time()

                # Process based on job type
                if job['type'] == 'melody':
                    result = self._generate_melody(job)
                elif job['type'] == 'harmony':
                    result = self._generate_harmony(job)
                elif job['type'] == 'drums':
                    result = self._generate_drums(job)
                elif job['type'] == 'bass':
                    result = self._generate_bass(job)
                elif job['type'] == 'arrangement':
                    result = self._enhance_arrangement(job)
                elif job['type'] == 'style_transfer':
                    result = self._apply_style_transfer(job)
                else:
                    result = {
                        'success': False,
                        'error': f"Unknown job type: {job['type']}"
                    }

                processing_time = time.time() - start_time

                # Update statistics
                with self.stats_lock:
                    if job['type'] == 'melody':
                        self.stats['melodies_generated'] += 1
                    elif job['type'] == 'harmony':
                        self.stats['harmonies_generated'] += 1
                    elif job['type'] == 'drums':
                        self.stats['drum_patterns_generated'] += 1
                    elif job['type'] == 'bass':
                        self.stats['bass_lines_generated'] += 1
                    self.stats['total_generation_time'] += processing_time

                # Add processing time to result
                result['processing_time_seconds'] = processing_time

                # Send response
                self.respond(job['message'], result)

                # Publish completion event
                self.publish(
                    f"music.generation.{job['type']}.complete",
                    {
                        'success': result.get('success', False),
                        'processing_time': processing_time
                    },
                    priority=Priority.LOW
                )

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker: {e}")
                if 'job' in locals() and 'message' in job:
                    self.respond(job['message'], {
                        'success': False,
                        'error': str(e)
                    })

    def _generate_melody(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate melody based on musical context"""
        try:
            context = job['context']
            params = {**self.generation_params['melody'], **job.get('params', {})}

            # Generate melody sequence
            melody_notes = self._create_melody_sequence(context, params)

            # Convert to MIDI
            midi_data = self._notes_to_midi(melody_notes, context.tempo)

            # Synthesize to audio if librosa available
            audio_data = None
            if librosa is not None:
                audio_data = self._synthesize_melody(melody_notes, context.tempo)

            return {
                'success': True,
                'content_type': 'melody',
                'melody_notes': melody_notes,
                'midi_data': midi_data,
                'audio_data': audio_data.tolist() if audio_data is not None else None,
                'context': {
                    'key': context.key,
                    'tempo': context.tempo,
                    'time_signature': context.time_signature,
                    'length_bars': context.length_bars
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Melody generation failed: {str(e)}"
            }

    def _generate_harmony(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate harmony for given melody"""
        try:
            context = job['context']
            melody_data = job.get('melody_data', [])
            params = {**self.generation_params['harmony'], **job.get('params', {})}

            # Analyze melody for harmonic implications
            chord_progression = self._analyze_melody_harmony(melody_data, context)

            # Generate harmony voices
            harmony_voices = self._create_harmony_voices(
                melody_data,
                chord_progression,
                params['num_voices'],
                context
            )

            return {
                'success': True,
                'content_type': 'harmony',
                'chord_progression': chord_progression,
                'harmony_voices': harmony_voices,
                'num_voices': len(harmony_voices),
                'context': {
                    'key': context.key,
                    'tempo': context.tempo
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Harmony generation failed: {str(e)}"
            }

    def _generate_drums(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate drum pattern"""
        try:
            context = job['context']
            params = {**self.generation_params['drums'], **job.get('params', {})}

            # Generate base pattern
            drum_pattern = self._create_drum_pattern(context, params)

            # Add variations
            drum_pattern_with_fills = self._add_drum_variations(drum_pattern, params)

            return {
                'success': True,
                'content_type': 'drums',
                'drum_pattern': drum_pattern_with_fills,
                'tempo': context.tempo,
                'time_signature': context.time_signature,
                'complexity': params.get('complexity', 'medium')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Drum generation failed: {str(e)}"
            }

    def _generate_bass(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bass line"""
        try:
            context = job['context']
            params = {**self.generation_params['bass'], **job.get('params', {})}

            # Generate bass line based on chord progression
            bass_notes = self._create_bass_line(context, params)

            return {
                'success': True,
                'content_type': 'bass',
                'bass_notes': bass_notes,
                'pattern_style': params.get('pattern_style', 'root_fifth'),
                'context': {
                    'key': context.key,
                    'tempo': context.tempo,
                    'chord_progression': context.chord_progression
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Bass generation failed: {str(e)}"
            }

    def _enhance_arrangement(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance arrangement by suggesting missing elements"""
        try:
            existing_stems = job.get('existing_stems', {})
            params = job.get('params', {})

            # Analyze existing arrangement
            analysis = self._analyze_arrangement(existing_stems)

            # Identify missing elements
            missing_elements = self._identify_missing_elements(analysis)

            # Generate suggestions
            suggestions = {
                'missing_elements': missing_elements,
                'arrangement_suggestions': self._create_arrangement_suggestions(analysis),
                'layering_recommendations': self._create_layering_recommendations(analysis)
            }

            return {
                'success': True,
                'arrangement_analysis': analysis,
                'suggestions': suggestions
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Arrangement enhancement failed: {str(e)}"
            }

    def _apply_style_transfer(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Apply style transfer to audio"""
        try:
            source_audio = job.get('source_audio')
            target_style = job.get('target_style', 'jazz')

            # Placeholder for style transfer
            # In production, this would use neural style transfer models

            return {
                'success': True,
                'message': f"Style transfer to {target_style} would be applied here",
                'target_style': target_style,
                'note': 'Style transfer requires ML models - placeholder implementation'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Style transfer failed: {str(e)}"
            }

    # Helper methods for music generation

    def _extract_music_context(self, payload: Dict[str, Any]) -> MusicContext:
        """Extract musical context from payload"""
        return MusicContext(
            key=payload.get('key', 'C major'),
            tempo=payload.get('tempo', 120.0),
            time_signature=payload.get('time_signature', '4/4'),
            chord_progression=payload.get('chord_progression', []),
            genre=payload.get('genre', 'pop'),
            style=payload.get('style', 'modern'),
            length_bars=payload.get('length_bars', 8)
        )

    def _create_melody_sequence(self, context: MusicContext, params: Dict) -> List[Dict]:
        """Create melody note sequence"""
        # Get scale notes for the key
        scale_notes = self._get_scale_notes(context.key)

        # Generate melody notes
        melody = []
        beats_per_bar = 4  # Simplified
        total_beats = context.length_bars * beats_per_bar

        current_beat = 0.0
        while current_beat < total_beats:
            # Choose note from scale
            note_index = np.random.choice(len(scale_notes))
            pitch = scale_notes[note_index]

            # Choose duration (quarter, eighth, half notes)
            duration = np.random.choice([0.25, 0.5, 1.0], p=[0.4, 0.4, 0.2])

            melody.append({
                'pitch': pitch,
                'start': current_beat,
                'duration': duration,
                'velocity': np.random.randint(60, 100)
            })

            current_beat += duration

        return melody

    def _analyze_melody_harmony(self, melody_data: List, context: MusicContext) -> List[str]:
        """Analyze melody to determine chord progression"""
        # Simplified chord progression based on key
        key_root = context.key.split()[0]

        # Common progressions
        progressions = {
            'C': ['C', 'Am', 'F', 'G'],
            'G': ['G', 'Em', 'C', 'D'],
            'D': ['D', 'Bm', 'G', 'A'],
            'A': ['A', 'F#m', 'D', 'E']
        }

        # Return common progression for the key
        base_progression = progressions.get(key_root, ['C', 'Am', 'F', 'G'])

        # Repeat for length
        repeats = max(1, context.length_bars // len(base_progression))
        return base_progression * repeats

    def _create_harmony_voices(self, melody: List, chords: List[str],
                                num_voices: int, context: MusicContext) -> Dict[str, List]:
        """Create harmony voice parts"""
        voices = {}

        for i in range(num_voices):
            voice_name = f"voice_{i+1}"
            voices[voice_name] = []

            # Generate harmonizing notes
            # Simplified: create parallel harmony
            for note in melody:
                harmony_note = note.copy()
                harmony_note['pitch'] = note['pitch'] - (3 + i * 2)  # Simple interval
                voices[voice_name].append(harmony_note)

        return voices

    def _create_drum_pattern(self, context: MusicContext, params: Dict) -> Dict[str, List]:
        """Create drum pattern"""
        beats_per_bar = 4
        total_beats = context.length_bars * beats_per_bar

        pattern = {
            'kick': [],
            'snare': [],
            'hihat': []
        }

        # Basic rock beat
        for beat in range(int(total_beats)):
            # Kick on 1 and 3
            if beat % 4 in [0, 2]:
                pattern['kick'].append({
                    'time': beat,
                    'velocity': np.random.randint(80, 100)
                })

            # Snare on 2 and 4
            if beat % 4 in [1, 3]:
                pattern['snare'].append({
                    'time': beat,
                    'velocity': np.random.randint(70, 90)
                })

            # Hi-hat on every beat
            for subdivision in [0, 0.5]:
                pattern['hihat'].append({
                    'time': beat + subdivision,
                    'velocity': np.random.randint(50, 70)
                })

        return pattern

    def _add_drum_variations(self, pattern: Dict, params: Dict) -> Dict:
        """Add variations and fills to drum pattern"""
        # Simplified: add some variation at end of phrases
        # In production, this would be more sophisticated
        return pattern

    def _create_bass_line(self, context: MusicContext, params: Dict) -> List[Dict]:
        """Create bass line from chord progression"""
        bass_notes = []

        if not context.chord_progression:
            return bass_notes

        beats_per_chord = 4
        current_beat = 0.0

        for chord in context.chord_progression:
            # Get root note of chord
            root_note = self._get_chord_root(chord)

            # Add root note
            bass_notes.append({
                'pitch': root_note,
                'start': current_beat,
                'duration': 1.0,
                'velocity': 80
            })

            current_beat += beats_per_chord

        return bass_notes

    def _analyze_arrangement(self, stems: Dict) -> Dict:
        """Analyze existing arrangement"""
        return {
            'num_stems': len(stems),
            'stem_types': list(stems.keys()),
            'has_drums': 'drums' in stems,
            'has_bass': 'bass' in stems,
            'has_melody': 'melody' in stems,
            'has_harmony': 'harmony' in stems
        }

    def _identify_missing_elements(self, analysis: Dict) -> List[str]:
        """Identify missing arrangement elements"""
        missing = []

        if not analysis.get('has_drums'):
            missing.append('drums')
        if not analysis.get('has_bass'):
            missing.append('bass')
        if not analysis.get('has_melody'):
            missing.append('melody')
        if not analysis.get('has_harmony'):
            missing.append('harmony')

        return missing

    def _create_arrangement_suggestions(self, analysis: Dict) -> List[str]:
        """Create arrangement suggestions"""
        suggestions = []

        if analysis['num_stems'] < 3:
            suggestions.append("Consider adding more layers for fuller sound")

        if not analysis.get('has_drums'):
            suggestions.append("Add rhythmic foundation with drums")

        if not analysis.get('has_bass'):
            suggestions.append("Add bass to support harmonic structure")

        return suggestions

    def _create_layering_recommendations(self, analysis: Dict) -> List[str]:
        """Create layering recommendations"""
        return [
            "Layer pad sounds for ambient texture",
            "Add counter-melodies for interest",
            "Consider adding rhythmic percussion elements"
        ]

    def _get_scale_notes(self, key: str) -> List[int]:
        """Get MIDI notes for a given key's scale"""
        # Simplified: return C major scale transposed
        key_root = key.split()[0]
        is_major = 'major' in key.lower()

        # Semitone mapping
        root_map = {
            'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
            'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
            'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71
        }

        root = root_map.get(key_root, 60)

        # Scale intervals
        if is_major:
            intervals = [0, 2, 4, 5, 7, 9, 11, 12]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10, 12]  # Natural minor scale

        return [root + interval for interval in intervals]

    def _get_chord_root(self, chord: str) -> int:
        """Get MIDI note number for chord root"""
        # Extract root note from chord symbol
        root_map = {
            'C': 36, 'D': 38, 'E': 40, 'F': 41,
            'G': 43, 'A': 45, 'B': 47
        }

        # Get first character as root
        root = chord[0] if chord else 'C'
        return root_map.get(root, 36)

    def _notes_to_midi(self, notes: List[Dict], tempo: float) -> str:
        """Convert notes to MIDI format (simplified)"""
        # In production, this would create actual MIDI file
        return json.dumps({
            'tempo': tempo,
            'notes': notes
        })

    def _synthesize_melody(self, notes: List[Dict], tempo: float) -> Optional[np.ndarray]:
        """Synthesize melody to audio"""
        if librosa is None:
            return None

        # Simple synthesis using sine waves
        sample_rate = 44100
        duration = 0.0

        # Calculate total duration
        for note in notes:
            end_time = note['start'] + note['duration']
            duration = max(duration, end_time)

        # Convert beats to seconds
        beat_duration = 60.0 / tempo
        total_duration = duration * beat_duration

        # Create audio array
        audio = np.zeros(int(total_duration * sample_rate))

        # Synthesize each note
        for note in notes:
            freq = librosa.midi_to_hz(note['pitch'])
            start_sample = int(note['start'] * beat_duration * sample_rate)
            duration_samples = int(note['duration'] * beat_duration * sample_rate)
            end_sample = start_sample + duration_samples

            if end_sample > len(audio):
                end_sample = len(audio)

            # Generate sine wave with envelope
            t = np.arange(duration_samples) / sample_rate
            sine_wave = np.sin(2 * np.pi * freq * t)

            # Apply envelope
            envelope = np.exp(-3 * t / (note['duration'] * beat_duration))
            sine_wave *= envelope

            # Add to audio with velocity scaling
            velocity_scale = note.get('velocity', 80) / 127.0
            audio[start_sample:end_sample] += sine_wave[:end_sample-start_sample] * velocity_scale * 0.3

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8

        return audio

    def _initialize_key_signatures(self) -> Dict:
        """Initialize key signature knowledge"""
        return {
            'C major': {'sharps': 0, 'flats': 0},
            'G major': {'sharps': 1, 'flats': 0},
            'D major': {'sharps': 2, 'flats': 0},
            'A major': {'sharps': 3, 'flats': 0},
            'F major': {'sharps': 0, 'flats': 1},
        }

    def _initialize_chord_templates(self) -> Dict:
        """Initialize chord templates"""
        return {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'dominant7': [0, 4, 7, 10],
            'major7': [0, 4, 7, 11]
        }

    def _initialize_scale_patterns(self) -> Dict:
        """Initialize scale patterns"""
        return {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
            'melodic_minor': [0, 2, 3, 5, 7, 9, 11]
        }
