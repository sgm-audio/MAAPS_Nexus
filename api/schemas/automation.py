"""
Pydantic schemas for Performance Automation API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas.common import CurveType, CueActionType


class StartRecordingRequest(BaseModel):
    """Request to start automation recording"""

    parameter_path: str = Field(..., description="Parameter path to record")


class RecordingResponse(BaseModel):
    """Automation recording response"""

    recording: bool
    parameter_path: Optional[str] = None
    lane_id: Optional[str] = None
    points_recorded: Optional[int] = None


class EnablePlaybackRequest(BaseModel):
    """Request to enable automation playback"""

    enable: bool = Field(..., description="Enable playback")


class PlaybackResponse(BaseModel):
    """Automation playback response"""

    playback_enabled: bool
    active_lanes: int


class CreateSceneRequest(BaseModel):
    """Request to create automation scene"""

    scene_name: str = Field(..., description="Scene name", min_length=1, max_length=100)
    parameter_snapshots: Dict[str, float] = Field(
        ..., description="Parameter snapshots"
    )
    transition_time: float = Field(
        2.0, description="Transition time in seconds", ge=0.0, le=60.0
    )
    transition_curves: Optional[Dict[str, CurveType]] = Field(
        None, description="Transition curves per parameter"
    )


class SceneResponse(BaseModel):
    """Scene response"""

    scene_id: str
    scene_name: str
    num_parameters: int
    transition_time: float


class TriggerSceneResponse(BaseModel):
    """Scene trigger response"""

    scene_id: str
    scene_name: str
    triggered_at: str


class MacroTarget(BaseModel):
    """Macro target parameter"""

    param: str = Field(..., description="Parameter path")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    curve: CurveType = Field(CurveType.LINEAR, description="Scaling curve")


class CreateMacroRequest(BaseModel):
    """Request to create macro control"""

    macro_name: str = Field(..., description="Macro name", min_length=1, max_length=100)
    target_parameters: List[MacroTarget] = Field(..., description="Target parameters")


class MacroResponse(BaseModel):
    """Macro response"""

    macro_id: str
    macro_name: str
    num_targets: int
    value: float


class AffectedParameter(BaseModel):
    """Affected parameter from macro change"""

    param: str
    value: float


class ChangeMacroRequest(BaseModel):
    """Request to change macro value"""

    value: float = Field(..., description="Macro value (0.0-1.0)", ge=0.0, le=1.0)


class MacroValueResponse(BaseModel):
    """Macro value change response"""

    macro_id: str
    value: float
    affected_parameters: List[AffectedParameter]


class CueAction(BaseModel):
    """Performance cue action"""

    action_type: CueActionType = Field(..., description="Action type")
    parameters: Dict[str, any] = Field(..., description="Action parameters")


class CreateCueRequest(BaseModel):
    """Request to create performance cue"""

    cue_name: str = Field(..., description="Cue name", min_length=1, max_length=100)
    timecode: str = Field(..., description="Timecode (HH:MM:SS.mmm)")
    actions: List[CueAction] = Field(..., description="Actions to execute")


class CueResponse(BaseModel):
    """Cue response"""

    cue_id: str
    cue_name: str
    timecode: str
    num_actions: int


class FireCueResponse(BaseModel):
    """Fire cue response"""

    cue_id: str
    cue_name: str
    fired_at: str
    actions_executed: int
