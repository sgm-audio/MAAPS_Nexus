"""
Common Pydantic schemas used across the API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    status: str = Field(..., description="Response status: success, error")
    message: Optional[str] = Field(None, description="Optional message")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: str = Field(..., description="Error timestamp")


# Effect Types
class EffectType(str, Enum):
    """Available effect types"""
    GATE = "gate"
    COMPRESSOR = "compressor"
    LIMITER = "limiter"
    EXPANDER = "expander"
    EQ_PARAMETRIC = "eq_parametric"
    EQ_GRAPHIC = "eq_graphic"
    REVERB = "reverb"
    DELAY = "delay"
    CHORUS = "chorus"
    FLANGER = "flanger"
    PHASER = "phaser"
    TREMOLO = "tremolo"
    VIBRATO = "vibrato"
    DISTORTION = "distortion"
    SATURATION = "saturation"


# Automation Curve Types
class CurveType(str, Enum):
    """Automation curve types"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    STEP = "step"
    BEZIER = "bezier"


# Loop Status
class LoopStatus(str, Enum):
    """Loop track status"""
    EMPTY = "empty"
    RECORDING = "recording"
    PLAYING = "playing"
    PAUSED = "paused"


# Recording Mode
class RecordingMode(str, Enum):
    """Loop recording modes"""
    REPLACE = "replace"
    OVERDUB = "overdub"
    MULTIPLY = "multiply"


# Loop Manipulation Operations
class LoopOperation(str, Enum):
    """Loop manipulation operations"""
    REVERSE = "reverse"
    PITCH_SHIFT = "pitch_shift"
    TIME_STRETCH = "time_stretch"
    NORMALIZE = "normalize"
    HALF_SPEED = "half_speed"
    DOUBLE_SPEED = "double_speed"


# Cue Action Types
class CueActionType(str, Enum):
    """Performance cue action types"""
    SCENE_CHANGE = "scene_change"
    PARAMETER_CHANGE = "parameter_change"
    MACRO_CHANGE = "macro_change"


def success_response(data: Any, message: Optional[str] = None) -> Dict:
    """Create success response"""
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def error_response(error: str, detail: str) -> Dict:
    """Create error response"""
    from datetime import datetime
    return {
        "status": "error",
        "error": error,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    }
