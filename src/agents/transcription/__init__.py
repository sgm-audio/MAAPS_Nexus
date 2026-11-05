"""
Musical Analysis & Transcription Multi-Agent System.

This package provides comprehensive musical analysis and transcription capabilities
including key/tempo detection, audio-to-MIDI conversion, tablature generation,
harmonic analysis, rhythm analysis, and multi-track coordination.
"""

from .musical_analysis_agent import MusicalAnalysisAgent, MusicalAnalysis, Modulation
from .audio_to_midi_agent import AudioToMIDIAgent, MIDINote, MIDITranscription
from .tablature_generation_agent import (
    TablatureGenerationAgent,
    TabNote,
    Tablature,
    ChordDiagram,
)
from .harmonic_analysis_agent import HarmonicAnalysisAgent, Chord, HarmonicAnalysis
from .rhythm_analysis_agent import RhythmAnalysisAgent, BeatGrid, RhythmicAnalysis
from .multitrack_coordinator_agent import (
    MultiTrackCoordinatorAgent,
    TrackTranscription,
    MultiTrackTranscription,
)

__all__ = [
    # Agents
    "MusicalAnalysisAgent",
    "AudioToMIDIAgent",
    "TablatureGenerationAgent",
    "HarmonicAnalysisAgent",
    "RhythmAnalysisAgent",
    "MultiTrackCoordinatorAgent",
    # Data structures - Musical Analysis
    "MusicalAnalysis",
    "Modulation",
    # Data structures - MIDI Transcription
    "MIDINote",
    "MIDITranscription",
    # Data structures - Tablature
    "TabNote",
    "Tablature",
    "ChordDiagram",
    # Data structures - Harmonic Analysis
    "Chord",
    "HarmonicAnalysis",
    # Data structures - Rhythm Analysis
    "BeatGrid",
    "RhythmicAnalysis",
    # Data structures - Multi-track
    "TrackTranscription",
    "MultiTrackTranscription",
]


# Version info
__version__ = "1.0.0"
__author__ = "Musical Analysis & Transcription Team"
__description__ = "Multi-agent system for musical analysis and transcription"
