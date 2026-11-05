"""
CV Director - Semantic Multi-Camera Switching System

A real-time computer vision system that automatically switches between multiple
camera feeds based on active speaker detection using audio + visual fusion.
"""

__version__ = "0.1.0"
__author__ = "Agentic Systems 2026"

# Public API exports
__all__ = [
    "CVDirector",
    "CameraManager",
    "CameraFrame",
    "ActiveSpeakerDetector",
    "DetectionResult",
    "DirectorStateMachine",
    "DirectorState",
    "DirectorDecision",
    "DirectorProfile",
    "DetectorConfig",
    "SwitchRule",
    "OBSClient",
    "get_profile",
    "list_profiles",
]

# Note: Actual imports will be added as modules are implemented
# This prevents import errors during development

try:
    from .director_main import CVDirector
except ImportError:
    pass

try:
    from .camera_manager import CameraManager, CameraFrame
except ImportError:
    pass

try:
    from .detector import ActiveSpeakerDetector, DetectionResult
except ImportError:
    pass

try:
    from .state_machine import (
        DirectorStateMachine,
        DirectorState,
        DirectorDecision,
    )
except ImportError:
    pass

try:
    from .profiles import (
        DirectorProfile,
        DetectorConfig,
        SwitchRule,
        get_profile,
        list_profiles,
    )
except ImportError:
    pass

try:
    from .obs_client import OBSClient
except ImportError:
    pass
