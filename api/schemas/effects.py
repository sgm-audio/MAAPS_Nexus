"""
Pydantic schemas for Effects Chain API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas.common import EffectType


class EffectParameters(BaseModel):
    """Effect parameter configuration"""

    class Config:
        extra = "allow"  # Allow dynamic parameters


class EffectConfig(BaseModel):
    """Single effect configuration"""

    type: EffectType = Field(..., description="Effect type")
    parameters: Dict[str, float] = Field(
        default_factory=dict, description="Effect parameters"
    )
    bypass: bool = Field(False, description="Bypass state")
    wet_dry: float = Field(1.0, description="Wet/dry mix (0.0-1.0)", ge=0.0, le=1.0)


class CreateChainRequest(BaseModel):
    """Request to create an effect chain"""

    chain_name: str = Field(
        ..., description="Name of the effect chain", min_length=1, max_length=100
    )
    effects: List[EffectConfig] = Field(..., description="List of effects in chain")


class EffectChainResponse(BaseModel):
    """Effect chain response"""

    chain_id: str
    chain_name: str
    num_effects: int
    total_latency_ms: float
    created_at: str


class EffectDetail(BaseModel):
    """Detailed effect information"""

    effect_id: str
    type: str
    bypass: bool
    wet_dry: float
    parameters: Dict[str, float]
    latency_ms: float


class ChainDetailResponse(BaseModel):
    """Detailed chain information"""

    chain_id: str
    chain_name: str
    bypass: bool
    effects: List[EffectDetail]
    total_latency_ms: float


class UpdateParametersRequest(BaseModel):
    """Request to update effect parameters"""

    parameters: Dict[str, float] = Field(..., description="Parameters to update")


class BypassRequest(BaseModel):
    """Request to toggle bypass"""

    bypass: bool = Field(..., description="Bypass state")


class SavePresetRequest(BaseModel):
    """Request to save preset"""

    preset_name: str = Field(
        ..., description="Preset name", min_length=1, max_length=100
    )
    chain_id: str = Field(..., description="Source chain ID")


class PresetResponse(BaseModel):
    """Preset response"""

    preset_id: str
    preset_name: str
    created_at: str


class ChainPreset(BaseModel):
    """Preset for a specific chain"""

    chain_id: str
    preset_id: str


class CreateSceneRequest(BaseModel):
    """Request to create a scene"""

    scene_name: str = Field(..., description="Scene name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Scene description")
    presets: List[ChainPreset] = Field(..., description="Presets to recall")


class SceneResponse(BaseModel):
    """Scene response"""

    scene_id: str
    scene_name: str
    num_presets: int
