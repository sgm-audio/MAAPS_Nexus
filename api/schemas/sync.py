"""
Pydantic schemas for Sync & Clock API
"""

from pydantic import BaseModel, Field
from typing import Optional


class SetTempoRequest(BaseModel):
    """Request to set tempo"""

    bpm: float = Field(..., description="Beats per minute", ge=20.0, le=999.0)
    time_signature: str = Field("4/4", description="Time signature")


class TempoResponse(BaseModel):
    """Tempo response"""

    bpm: float
    time_signature: str


class TapTempoResponse(BaseModel):
    """Tap tempo response"""

    bpm: float
    taps_recorded: int
    confidence: float


class TransportResponse(BaseModel):
    """Transport control response"""

    playing: bool
    position_seconds: float
    position_beats: Optional[float] = None
    position_bars: Optional[int] = None


class ClockPosition(BaseModel):
    """Clock position information"""

    seconds: float
    beats: float
    bars: int
    beat_in_bar: int


class MIDIClockInfo(BaseModel):
    """MIDI clock information"""

    enabled: bool
    port: Optional[str] = None


class AbletonLinkInfo(BaseModel):
    """Ableton Link information"""

    enabled: bool
    peers: int


class ClockStatusResponse(BaseModel):
    """Clock status response"""

    bpm: float
    time_signature: str
    playing: bool
    position: ClockPosition
    midi_clock: MIDIClockInfo
    ableton_link: AbletonLinkInfo


class EnableMIDIClockRequest(BaseModel):
    """Request to enable MIDI clock"""

    enable: bool = Field(..., description="Enable MIDI clock")
    midi_port: Optional[str] = Field(None, description="MIDI port name")


class MIDIClockResponse(BaseModel):
    """MIDI clock response"""

    midi_clock_enabled: bool
    midi_port: Optional[str] = None


class EnableLinkRequest(BaseModel):
    """Request to enable Ableton Link"""

    enable: bool = Field(..., description="Enable Ableton Link")


class AbletonLinkResponse(BaseModel):
    """Ableton Link response"""

    link_enabled: bool
    peers: int
    session_tempo: float
