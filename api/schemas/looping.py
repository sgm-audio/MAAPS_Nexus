"""
Pydantic schemas for Live Looping API
"""

from pydantic import BaseModel, Field
from typing import Optional
from api.schemas.common import LoopStatus, RecordingMode, LoopOperation


class CreateTrackRequest(BaseModel):
    """Request to create a loop track"""

    track_name: str = Field(..., description="Track name", min_length=1, max_length=100)
    length_beats: int = Field(4, description="Length in beats", ge=1, le=64)
    sync_to_tempo: bool = Field(True, description="Sync to tempo clock")
    volume: float = Field(0.8, description="Track volume", ge=0.0, le=1.0)
    pan: float = Field(0.0, description="Pan position (-1.0 to 1.0)", ge=-1.0, le=1.0)


class TrackResponse(BaseModel):
    """Loop track response"""

    track_id: str
    track_name: str
    length_beats: int
    length_samples: int
    status: LoopStatus
    sync_to_tempo: bool


class StartRecordingRequest(BaseModel):
    """Request to start recording"""

    mode: RecordingMode = Field(RecordingMode.REPLACE, description="Recording mode")


class RecordingStartedResponse(BaseModel):
    """Recording started response"""

    track_id: str
    recording: bool
    mode: RecordingMode
    started_at: str


class RecordingStoppedResponse(BaseModel):
    """Recording stopped response"""

    track_id: str
    recording: bool
    recorded_length_samples: int
    recorded_length_beats: int
    status: LoopStatus


class PlaybackResponse(BaseModel):
    """Playback toggle response"""

    track_id: str
    playing: bool


class ManipulateRequest(BaseModel):
    """Request to manipulate loop"""

    operation: LoopOperation = Field(..., description="Manipulation operation")
    parameters: Optional[dict] = Field(None, description="Operation parameters")


class ManipulationResponse(BaseModel):
    """Loop manipulation response"""

    track_id: str
    operation: LoopOperation
    applied: bool
    processing_time_ms: float


class UndoResponse(BaseModel):
    """Undo/redo response"""

    track_id: str
    undo_available: int
    redo_available: int


class TrackStatusResponse(BaseModel):
    """Track status response"""

    track_id: str
    status: LoopStatus


class TrackListItem(BaseModel):
    """Loop track list item"""

    track_id: str
    track_name: str
    status: LoopStatus
    length_beats: int
    volume: float
    pan: float
    undo_available: int
    redo_available: int


class TrackListResponse(BaseModel):
    """List of loop tracks"""

    tracks: list[TrackListItem]
    total_tracks: int
