"""
Director configuration profiles

Defines Pydantic models for type-safe configuration of the CV Director system,
including detection settings, switching rules, and predefined director profiles.
"""

from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import json


class DetectorConfig(BaseModel):
    """Configuration for active speaker detection"""

    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    vad_aggressiveness: int = Field(
        default=3,
        ge=0,
        le=3,
        description="webrtcvad aggressiveness level (0=least aggressive, 3=most aggressive)",
    )
    audio_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for audio score in fusion (0.0-1.0)",
    )
    visual_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for visual score in fusion (0.0-1.0)",
    )
    face_detection_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for MediaPipe face detection",
    )
    lip_movement_threshold: float = Field(
        default=0.02,
        ge=0.0,
        description="Threshold for detecting significant lip movement",
    )
    temporal_window_size: int = Field(
        default=5,
        ge=1,
        description="Number of frames to consider for temporal lip movement analysis",
    )


class SwitchRule(BaseModel):
    """Switching rules for director state machine"""

    min_dwell_time: float = Field(
        default=2.0, ge=0.5, description="Minimum time to stay on a camera (seconds)"
    )
    max_dwell_time: float = Field(
        default=30.0,
        ge=1.0,
        description="Maximum time before forcing variety switch (seconds)",
    )
    switch_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger a switch (0.0-1.0)",
    )
    hysteresis: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Hysteresis buffer to prevent rapid switching back to current camera",
    )
    variety_bonus: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Score bonus for cameras not recently used",
    )
    idle_timeout: float = Field(
        default=5.0,
        ge=0.0,
        description="Time before returning to default camera when idle (seconds)",
    )
    transition_cooldown: float = Field(
        default=0.3,
        ge=0.0,
        description="Cooldown time during camera transition (seconds)",
    )


class DirectorProfile(BaseModel):
    """Complete director profile with all configuration"""

    name: str = Field(description="Profile name identifier")
    description: str = Field(description="Human-readable profile description")

    # Detection configuration
    detector: DetectorConfig = Field(
        default_factory=DetectorConfig, description="Active speaker detection settings"
    )

    # Switching rules
    rules: SwitchRule = Field(
        default_factory=SwitchRule, description="Camera switching rules"
    )

    # Camera configuration
    default_camera: str = Field(
        default="camera_0", description="Default camera ID to use when idle"
    )
    camera_scene_map: Dict[str, str] = Field(
        default_factory=dict, description="Maps camera_id to OBS scene name"
    )

    @classmethod
    def from_json(cls, path: Path) -> "DirectorProfile":
        """
        Load profile from JSON file

        Args:
            path: Path to JSON file

        Returns:
            DirectorProfile instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_json(self, path: Path) -> None:
        """
        Save profile to JSON file

        Args:
            path: Path to save JSON file
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)

    def model_dump_json(self, **kwargs) -> str:
        """
        Serialize profile to JSON string

        Returns:
            JSON string
        """
        return super().model_dump_json(indent=2, **kwargs)


# =============================================================================
# PREDEFINED PROFILES
# =============================================================================

DYNAMIC_PODCAST_PROFILE = DirectorProfile(
    name="Dynamic_Podcast",
    description="Fast-paced switching for dynamic conversations and multi-host podcasts",
    detector=DetectorConfig(
        audio_weight=0.7,
        visual_weight=0.3,
        vad_aggressiveness=2,  # Moderate sensitivity
        face_detection_confidence=0.5,
        lip_movement_threshold=0.02,
        temporal_window_size=5,
    ),
    rules=SwitchRule(
        min_dwell_time=1.5,  # Quick switches allowed
        max_dwell_time=15.0,  # Force variety after 15s
        switch_threshold=0.6,  # Moderate confidence needed
        hysteresis=0.15,  # Moderate stability
        variety_bonus=0.1,  # Encourage shot diversity
        idle_timeout=5.0,
        transition_cooldown=0.3,
    ),
    default_camera="camera_0",
    camera_scene_map={
        "camera_0": "Camera 1",
        "camera_1": "Camera 2",
        "camera_2": "Camera 3",
    },
)

STATIC_INTERVIEW_PROFILE = DirectorProfile(
    name="Static_Interview",
    description="Conservative switching for formal interviews and presentations",
    detector=DetectorConfig(
        audio_weight=0.8,
        visual_weight=0.2,
        vad_aggressiveness=3,  # Very aggressive (less false positives)
        face_detection_confidence=0.6,
        lip_movement_threshold=0.03,
        temporal_window_size=7,
    ),
    rules=SwitchRule(
        min_dwell_time=4.0,  # Long minimum dwell
        max_dwell_time=60.0,  # Allow long shots
        switch_threshold=0.75,  # High confidence required
        hysteresis=0.2,  # Strong stability
        variety_bonus=0.05,  # Less emphasis on variety
        idle_timeout=10.0,
        transition_cooldown=0.5,
    ),
    default_camera="camera_0",
    camera_scene_map={
        "camera_0": "Host",
        "camera_1": "Guest",
        "camera_2": "Wide Shot",
    },
)

ENERGETIC_PANEL_PROFILE = DirectorProfile(
    name="Energetic_Panel",
    description="Very fast switching for high-energy panel discussions",
    detector=DetectorConfig(
        audio_weight=0.65,
        visual_weight=0.35,
        vad_aggressiveness=1,  # Less aggressive (catch more activity)
        face_detection_confidence=0.45,
        lip_movement_threshold=0.015,
        temporal_window_size=4,
    ),
    rules=SwitchRule(
        min_dwell_time=1.0,  # Very quick switches
        max_dwell_time=10.0,  # Force variety quickly
        switch_threshold=0.55,  # Lower threshold
        hysteresis=0.1,  # Less stability (more responsive)
        variety_bonus=0.15,  # Strong variety emphasis
        idle_timeout=3.0,
        transition_cooldown=0.2,
    ),
    default_camera="camera_0",
    camera_scene_map={
        "camera_0": "Panel View",
        "camera_1": "Speaker 1",
        "camera_2": "Speaker 2",
        "camera_3": "Speaker 3",
    },
)

# Profile registry
PROFILE_REGISTRY: Dict[str, DirectorProfile] = {
    "Dynamic_Podcast": DYNAMIC_PODCAST_PROFILE,
    "Static_Interview": STATIC_INTERVIEW_PROFILE,
    "Energetic_Panel": ENERGETIC_PANEL_PROFILE,
}


# =============================================================================
# PUBLIC API
# =============================================================================


def get_profile(name: str) -> DirectorProfile:
    """
    Get a director profile by name

    Args:
        name: Profile name

    Returns:
        DirectorProfile instance

    Raises:
        ValueError: If profile not found
    """
    if name not in PROFILE_REGISTRY:
        available = ", ".join(PROFILE_REGISTRY.keys())
        raise ValueError(f"Profile '{name}' not found. Available profiles: {available}")
    return PROFILE_REGISTRY[name]


def list_profiles() -> List[str]:
    """
    List all available profile names

    Returns:
        List of profile names
    """
    return list(PROFILE_REGISTRY.keys())


def register_profile(profile: DirectorProfile) -> None:
    """
    Register a custom profile

    Args:
        profile: DirectorProfile to register
    """
    PROFILE_REGISTRY[profile.name] = profile


def load_custom_profile(path: Path) -> DirectorProfile:
    """
    Load a custom profile from JSON file and register it

    Args:
        path: Path to JSON profile file

    Returns:
        DirectorProfile instance
    """
    profile = DirectorProfile.from_json(path)
    register_profile(profile)
    return profile
