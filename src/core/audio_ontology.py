"""
Audio Ontology for Multi-Agent Audio Processing System (MAAPS)

Defines the shared vocabulary and semantic understanding that agents use to
communicate about audio characteristics, goals, and transformations.

This ontology provides a common language for agents to reason about audio
quality attributes like "Clarity," "Warmth," "Mud," "Punch," etc.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum, auto
import numpy as np


class FrequencyRange(Enum):
    """Represents a frequency range with low and high bounds in Hz."""

    SUB_BASS = (20.0, 60.0)
    BASS = (60.0, 250.0)
    LOW_MIDS = (250.0, 500.0)
    MIDS = (500.0, 2000.0)
    HIGH_MIDS = (2000.0, 4000.0)
    PRESENCE = (4000.0, 6000.0)
    BRILLIANCE = (6000.0, 20000.0)

    def __init__(self, low: float, high: float):
        self._low = float(low)
        self._high = float(high)

    @property
    def low(self) -> float:
        return self._low

    @property
    def high(self) -> float:
        return self._high


@dataclass
class AudioConcept:
    """Represents a qualitative audio concept with physical associations."""

    name: str
    description: str
    frequency_ranges: List[FrequencyRange] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    opposite_concepts: List[str] = field(default_factory=list)

    # Measurable properties (0.0 to 1.0)
    clarity_impact: float = 0.5
    warmth_impact: float = 0.5
    brightness_impact: float = 0.5

    # Processing suggestions
    eq_adjustments: Dict[FrequencyRange, float] = field(default_factory=dict)
    compression_ratio: Optional[float] = None

    # User satisfaction correlation (-1.0 to 1.0)
    satisfaction_correlation: float = 0.0


class AudioAttribute(Enum):
    """Core audio quality attributes in the ontology."""

    # Frequency Domain
    CLARITY = auto()  # High-frequency definition, articulation
    WARMTH = auto()  # Low-mid frequency richness
    BRIGHTNESS = auto()  # High-frequency presence
    MUD = auto()  # Low-mid frequency buildup (negative)
    HARSHNESS = auto()  # Upper-mid harshness (negative)
    THINNESS = auto()  # Lack of low-frequency content (negative)

    # Dynamics
    PUNCH = auto()  # Transient impact and attack
    COMPRESSION = auto()  # Dynamic range reduction
    EXPANSION = auto()  # Dynamic range increase
    SUSTAIN = auto()  # Note/sound length
    DENSITY = auto()  # Harmonic/sonic fullness

    # Spatial
    WIDTH = auto()  # Stereo width
    DEPTH = auto()  # Front-to-back dimension
    HEIGHT = auto()  # Vertical spatial dimension

    # Tonal Balance
    BALANCE = auto()  # Overall frequency balance
    PRESENCE = auto()  # Mid-range presence (vocal/lead focus)
    AIR = auto()  # Ultra-high frequency extension

    # Artifacts
    DISTORTION = auto()  # Harmonic/inharmonic distortion (negative)
    NOISE = auto()  # Background noise level (negative)
    CLIPPING = auto()  # Digital clipping (negative)


class FrequencyBand(Enum):
    """Standard frequency bands for audio processing."""

    SUB_BASS = (20, 60)  # Sub-bass
    BASS = (60, 250)  # Bass
    LOW_MID = (250, 500)  # Low-mids
    MID = (500, 2000)  # Mids
    HIGH_MID = (2000, 6000)  # High-mids
    PRESENCE = (6000, 12000)  # Presence
    BRILLIANCE = (12000, 20000)  # Brilliance/Air

    def __init__(self, low: float, high: float):
        self.low_freq = low
        self.high_freq = high


@dataclass
class AudioGoal:
    """
    Represents a target audio quality state.
    Used by agents to understand desired outcomes.
    """

    attribute: AudioAttribute
    target_value: float  # 0.0 to 1.0 (0 = none, 1 = maximum)
    priority: float = 0.5  # 0.0 to 1.0 (importance weight)
    tolerance: float = 0.1  # Acceptable deviation from target

    def is_satisfied(self, current_value: float) -> bool:
        """Check if current value satisfies the goal."""
        return abs(current_value - self.target_value) <= self.tolerance

    def distance_from_target(self, current_value: float) -> float:
        """Calculate normalized distance from target."""
        return abs(current_value - self.target_value)


@dataclass
class AudioState:
    """
    Represents the current state of audio in terms of ontology attributes.
    This is what the Critic agent evaluates.
    """

    attributes: Dict[AudioAttribute, float] = field(default_factory=dict)
    confidence: Dict[AudioAttribute, float] = field(default_factory=dict)
    timestamp: Optional[float] = None

    def get_attribute(self, attr: AudioAttribute, default: float = 0.5) -> float:
        """Get attribute value with default."""
        return self.attributes.get(attr, default)

    def set_attribute(
        self, attr: AudioAttribute, value: float, confidence: float = 1.0
    ):
        """Set attribute value with confidence."""
        self.attributes[attr] = np.clip(value, 0.0, 1.0)
        self.confidence[attr] = np.clip(confidence, 0.0, 1.0)

    def get_confidence(self, attr: AudioAttribute) -> float:
        """Get confidence in attribute measurement."""
        return self.confidence.get(attr, 0.0)

    def to_vector(
        self, attributes: Optional[List[AudioAttribute]] = None
    ) -> np.ndarray:
        """Convert state to feature vector for ML models."""
        if attributes is None:
            attributes = list(AudioAttribute)
        return np.array([self.get_attribute(attr) for attr in attributes])


@dataclass
class AgentAction:
    """
    Represents an action an agent can take (e.g., EQ adjustment, compression).
    """

    agent_id: str
    action_type: str  # "eq_adjustment", "compression", etc.
    parameters: Dict[str, float]
    expected_impact: Dict[AudioAttribute, float] = field(default_factory=dict)
    confidence: float = 1.0

    def estimate_impact_on_attribute(self, attr: AudioAttribute) -> float:
        """Estimate impact on specific attribute (-1.0 to 1.0)."""
        return self.expected_impact.get(attr, 0.0)


class AudioOntologyManager:
    """
    Manages the audio ontology and provides reasoning capabilities.
    Helps agents understand relationships between attributes and actions.
    """

    def __init__(self):
        # Define attribute relationships (correlations)
        # Positive correlation: increasing one tends to increase the other
        # Negative correlation: increasing one tends to decrease the other
        self.attribute_correlations = {
            (AudioAttribute.CLARITY, AudioAttribute.MUD): -0.8,
            (AudioAttribute.WARMTH, AudioAttribute.THINNESS): -0.7,
            (AudioAttribute.BRIGHTNESS, AudioAttribute.HARSHNESS): 0.6,
            (AudioAttribute.PUNCH, AudioAttribute.COMPRESSION): 0.5,
            (AudioAttribute.WIDTH, AudioAttribute.CLARITY): -0.3,
            (AudioAttribute.WARMTH, AudioAttribute.MUD): 0.4,
            (AudioAttribute.CLARITY, AudioAttribute.BRIGHTNESS): 0.7,
        }

        # Define frequency band -> attribute mappings
        self.frequency_attribute_map = {
            FrequencyBand.SUB_BASS: [AudioAttribute.WARMTH],
            FrequencyBand.BASS: [AudioAttribute.WARMTH, AudioAttribute.PUNCH],
            FrequencyBand.LOW_MID: [AudioAttribute.WARMTH, AudioAttribute.MUD],
            FrequencyBand.MID: [AudioAttribute.PRESENCE, AudioAttribute.CLARITY],
            FrequencyBand.HIGH_MID: [AudioAttribute.CLARITY, AudioAttribute.HARSHNESS],
            FrequencyBand.PRESENCE: [AudioAttribute.BRIGHTNESS, AudioAttribute.CLARITY],
            FrequencyBand.BRILLIANCE: [AudioAttribute.AIR, AudioAttribute.BRIGHTNESS],
        }

        self.concepts: Dict[str, AudioConcept] = {}
        self._initialize_concepts()

    def get_attribute_correlation(
        self, attr1: AudioAttribute, attr2: AudioAttribute
    ) -> float:
        """Get correlation between two attributes."""
        key = (
            (attr1, attr2)
            if (attr1, attr2) in self.attribute_correlations
            else (attr2, attr1)
        )
        return self.attribute_correlations.get(key, 0.0)

    def get_conflicting_attributes(
        self, attr: AudioAttribute, threshold: float = 0.6
    ) -> List[AudioAttribute]:
        """Get attributes that conflict with the given attribute."""
        conflicts = []
        for (a1, a2), correlation in self.attribute_correlations.items():
            if correlation < -threshold:
                if a1 == attr:
                    conflicts.append(a2)
                elif a2 == attr:
                    conflicts.append(a1)
        return conflicts

    def get_synergistic_attributes(
        self, attr: AudioAttribute, threshold: float = 0.6
    ) -> List[AudioAttribute]:
        """Get attributes that work well together with the given attribute."""
        synergies = []
        for (a1, a2), correlation in self.attribute_correlations.items():
            if correlation > threshold:
                if a1 == attr:
                    synergies.append(a2)
                elif a2 == attr:
                    synergies.append(a1)
        return synergies

    def get_attributes_for_frequency_band(
        self, band: FrequencyBand
    ) -> List[AudioAttribute]:
        """Get audio attributes affected by a frequency band."""
        return self.frequency_attribute_map.get(band, [])

    def get_frequency_bands_for_attribute(
        self, attr: AudioAttribute
    ) -> List[FrequencyBand]:
        """Get frequency bands that affect an attribute."""
        bands = []
        for band, attributes in self.frequency_attribute_map.items():
            if attr in attributes:
                bands.append(band)
        return bands

    def estimate_satisfaction_score(
        self, current_state: AudioState, goals: List[AudioGoal]
    ) -> float:
        """
        Calculate overall satisfaction score (0.0 to 1.0).
        Used by Critic agent to evaluate audio quality.
        """
        if not goals:
            return 0.5

        total_weighted_satisfaction = 0.0
        total_weight = 0.0

        for goal in goals:
            current_value = current_state.get_attribute(goal.attribute)
            distance = goal.distance_from_target(current_value)

            # Convert distance to satisfaction (closer = better)
            satisfaction = 1.0 - min(distance / (goal.tolerance + 1e-6), 1.0)

            # Weight by priority
            weighted_satisfaction = satisfaction * goal.priority
            total_weighted_satisfaction += weighted_satisfaction
            total_weight += goal.priority

        # Normalize
        if total_weight > 0:
            return total_weighted_satisfaction / total_weight
        return 0.5

    def predict_action_impact(
        self, action: AgentAction, current_state: AudioState
    ) -> AudioState:
        """
        Predict the resulting audio state after applying an action.
        Simple physics-based model for action consequences.
        """
        new_state = AudioState()
        new_state.attributes = current_state.attributes.copy()
        new_state.confidence = current_state.confidence.copy()

        # Apply direct impact
        for attr, impact in action.expected_impact.items():
            current_val = current_state.get_attribute(attr)
            new_val = np.clip(current_val + impact, 0.0, 1.0)
            new_state.set_attribute(attr, new_val, action.confidence)

        # Apply correlated effects
        for attr, impact in action.expected_impact.items():
            for other_attr in AudioAttribute:
                if other_attr != attr:
                    correlation = self.get_attribute_correlation(attr, other_attr)
                    if abs(correlation) > 0.3:
                        current_val = new_state.get_attribute(other_attr)
                        correlated_impact = (
                            impact * correlation * 0.3
                        )  # Damped correlation
                        new_val = np.clip(current_val + correlated_impact, 0.0, 1.0)
                        confidence = new_state.get_confidence(other_attr) * 0.9
                        new_state.set_attribute(other_attr, new_val, confidence)

        return new_state

    def _initialize_concepts(self):
        """Initialize standard audio concepts."""
        self.concepts = {
            "clarity": AudioConcept(
                name="clarity",
                description="Clear definition and separation of individual elements",
                frequency_ranges=[FrequencyRange.HIGH_MIDS, FrequencyRange.PRESENCE],
                related_concepts=["brightness", "presence", "airiness"],
                opposite_concepts=["mud", "clutter", "dullness"],
                clarity_impact=1.0,
                warmth_impact=0.3,
                brightness_impact=0.7,
                eq_adjustments={
                    FrequencyRange.LOW_MIDS: -2.0,
                    FrequencyRange.HIGH_MIDS: 2.0,
                    FrequencyRange.PRESENCE: 1.5,
                },
                satisfaction_correlation=0.8,
            ),
            "warmth": AudioConcept(
                name="warmth",
                description="Pleasant fullness in low-mid frequencies",
                frequency_ranges=[FrequencyRange.BASS, FrequencyRange.LOW_MIDS],
                related_concepts=["richness", "fullness", "depth"],
                opposite_concepts=["thinness", "harshness", "shrillness"],
                clarity_impact=0.4,
                warmth_impact=1.0,
                brightness_impact=0.2,
                eq_adjustments={
                    FrequencyRange.BASS: 1.5,
                    FrequencyRange.LOW_MIDS: 2.0,
                    FrequencyRange.HIGH_MIDS: -1.0,
                },
                satisfaction_correlation=0.7,
            ),
            "mud": AudioConcept(
                name="mud",
                description="Unclear, undefined mix from excessive low-mid energy",
                frequency_ranges=[FrequencyRange.LOW_MIDS],
                related_concepts=["boominess", "clutter", "boxiness"],
                opposite_concepts=["clarity", "tightness", "presence"],
                clarity_impact=-0.8,
                warmth_impact=0.6,
                brightness_impact=-0.4,
                eq_adjustments={
                    FrequencyRange.LOW_MIDS: -4.0,
                    FrequencyRange.MIDS: 1.0,
                    FrequencyRange.HIGH_MIDS: 2.0,
                },
                satisfaction_correlation=-0.9,
            ),
            "brightness": AudioConcept(
                name="brightness",
                description="High-frequency energy that adds sparkle and air",
                frequency_ranges=[FrequencyRange.PRESENCE, FrequencyRange.BRILLIANCE],
                related_concepts=["sparkle", "airiness", "clarity"],
                opposite_concepts=["dullness", "darkness", "muffle"],
                clarity_impact=0.7,
                warmth_impact=-0.2,
                brightness_impact=1.0,
                eq_adjustments={
                    FrequencyRange.PRESENCE: 2.0,
                    FrequencyRange.BRILLIANCE: 2.5,
                },
                satisfaction_correlation=0.6,
            ),
            "harshness": AudioConcept(
                name="harshness",
                description="Aggressive, fatiguing high-frequency content",
                frequency_ranges=[FrequencyRange.HIGH_MIDS, FrequencyRange.PRESENCE],
                related_concepts=["shrillness", "aggression"],
                opposite_concepts=["smoothness", "warmth", "gentle"],
                clarity_impact=0.3,
                warmth_impact=-0.5,
                brightness_impact=0.8,
                eq_adjustments={
                    FrequencyRange.HIGH_MIDS: -3.0,
                    FrequencyRange.PRESENCE: -2.5,
                },
                compression_ratio=3.0,
                satisfaction_correlation=-0.85,
            ),
            "punch": AudioConcept(
                name="punch",
                description="Strong transient impact and definition",
                frequency_ranges=[FrequencyRange.BASS, FrequencyRange.LOW_MIDS],
                related_concepts=["tightness", "presence", "impact"],
                opposite_concepts=["softness", "weakness"],
                clarity_impact=0.6,
                warmth_impact=0.5,
                brightness_impact=0.4,
                eq_adjustments={
                    FrequencyRange.BASS: 2.0,
                    FrequencyRange.LOW_MIDS: 1.5,
                },
                compression_ratio=4.0,
                satisfaction_correlation=0.75,
            ),
            "depth": AudioConcept(
                name="depth",
                description="Three-dimensional spaciousness and depth",
                frequency_ranges=[FrequencyRange.SUB_BASS, FrequencyRange.BASS],
                related_concepts=["width", "space", "dimension"],
                opposite_concepts=["flatness", "mono"],
                clarity_impact=0.5,
                warmth_impact=0.7,
                brightness_impact=0.3,
                eq_adjustments={
                    FrequencyRange.SUB_BASS: 1.5,
                    FrequencyRange.BASS: 1.0,
                },
                satisfaction_correlation=0.7,
            ),
            "airiness": AudioConcept(
                name="airiness",
                description="Open, spacious quality in high frequencies",
                frequency_ranges=[FrequencyRange.BRILLIANCE],
                related_concepts=["sparkle", "openness", "space"],
                opposite_concepts=["dullness", "closed", "muffled"],
                clarity_impact=0.8,
                warmth_impact=0.1,
                brightness_impact=0.9,
                eq_adjustments={
                    FrequencyRange.BRILLIANCE: 3.0,
                },
                satisfaction_correlation=0.65,
            ),
            "boominess": AudioConcept(
                name="boominess",
                description="Excessive, resonant low-frequency energy",
                frequency_ranges=[FrequencyRange.BASS],
                related_concepts=["resonance", "rumble"],
                opposite_concepts=["tightness", "control"],
                clarity_impact=-0.6,
                warmth_impact=0.4,
                brightness_impact=-0.3,
                eq_adjustments={
                    FrequencyRange.BASS: -4.0,
                    FrequencyRange.LOW_MIDS: -2.0,
                },
                compression_ratio=6.0,
                satisfaction_correlation=-0.8,
            ),
            "presence": AudioConcept(
                name="presence",
                description="Forward, immediate sonic quality",
                frequency_ranges=[FrequencyRange.HIGH_MIDS, FrequencyRange.PRESENCE],
                related_concepts=["clarity", "definition", "forward"],
                opposite_concepts=["distance", "background"],
                clarity_impact=0.9,
                warmth_impact=0.3,
                brightness_impact=0.7,
                eq_adjustments={
                    FrequencyRange.HIGH_MIDS: 3.0,
                    FrequencyRange.PRESENCE: 2.5,
                },
                satisfaction_correlation=0.75,
            ),
            "boxiness": AudioConcept(
                name="boxiness",
                description="Narrow, confined quality in midrange",
                frequency_ranges=[FrequencyRange.LOW_MIDS, FrequencyRange.MIDS],
                related_concepts=["nasal", "honky"],
                opposite_concepts=["openness", "width", "space"],
                clarity_impact=-0.5,
                warmth_impact=0.2,
                brightness_impact=-0.4,
                eq_adjustments={
                    FrequencyRange.LOW_MIDS: -3.0,
                    FrequencyRange.MIDS: -2.5,
                },
                satisfaction_correlation=-0.7,
            ),
            "tightness": AudioConcept(
                name="tightness",
                description="Controlled, focused low-frequency response",
                frequency_ranges=[FrequencyRange.BASS],
                related_concepts=["control", "focus", "punch"],
                opposite_concepts=["looseness", "boominess", "flabby"],
                clarity_impact=0.7,
                warmth_impact=0.5,
                brightness_impact=0.3,
                eq_adjustments={
                    FrequencyRange.SUB_BASS: -1.0,
                    FrequencyRange.BASS: 1.0,
                },
                compression_ratio=4.0,
                satisfaction_correlation=0.8,
            ),
        }

    def get_concept(self, name: str) -> Optional[AudioConcept]:
        """Get an audio concept by name."""
        return self.concepts.get(name.lower())

    def get_related_concepts(self, concept_name: str) -> List[AudioConcept]:
        """Get concepts related to given concept."""
        concept = self.get_concept(concept_name)
        if not concept:
            return []
        return [
            self.concepts[name]
            for name in concept.related_concepts
            if name in self.concepts
        ]

    def get_opposite_concepts(self, concept_name: str) -> List[AudioConcept]:
        """Get concepts opposite to given concept."""
        concept = self.get_concept(concept_name)
        if not concept:
            return []
        return [
            self.concepts[name]
            for name in concept.opposite_concepts
            if name in self.concepts
        ]

    def suggest_corrections(
        self, negative_concepts: List[str]
    ) -> Dict[str, List[Tuple[FrequencyRange, float]]]:
        """Suggest corrections for negative audio qualities."""
        corrections: Dict[str, List[Tuple[FrequencyRange, float]]] = {}
        for concept_name in negative_concepts:
            concept = self.get_concept(concept_name)
            if concept and concept.eq_adjustments:
                corrections[concept_name] = [
                    (freq_range, db_change)
                    for freq_range, db_change in concept.eq_adjustments.items()
                ]
        return corrections

    def predict_satisfaction(self, detected_concepts: List[str]) -> float:
        """Predict user satisfaction score based on detected concepts."""
        if not detected_concepts:
            return 0.0
        scores = [
            self.concepts[name].satisfaction_correlation
            for name in detected_concepts
            if name in self.concepts
        ]
        return float(np.mean(scores)) if scores else 0.0

    def get_all_positive_concepts(self) -> List[str]:
        """Get all concepts with positive satisfaction correlation."""
        return [
            name
            for name, concept in self.concepts.items()
            if concept.satisfaction_correlation > 0.5
        ]

    def get_all_negative_concepts(self) -> List[str]:
        """Get all concepts with negative satisfaction correlation."""
        return [
            name
            for name, concept in self.concepts.items()
            if concept.satisfaction_correlation < -0.5
        ]

    def get_concept_names(self) -> List[str]:
        """Get all registered concept names."""
        return list(self.concepts.keys())


# Convenience functions for creating common goals
def create_clarity_goal(target: float = 0.8, priority: float = 1.0) -> AudioGoal:
    """Create a goal to increase clarity."""
    return AudioGoal(AudioAttribute.CLARITY, target, priority)


def create_warmth_goal(target: float = 0.7, priority: float = 0.8) -> AudioGoal:
    """Create a goal to add warmth."""
    return AudioGoal(AudioAttribute.WARMTH, target, priority)


def create_reduce_mud_goal(target: float = 0.2, priority: float = 0.9) -> AudioGoal:
    """Create a goal to reduce mud."""
    return AudioGoal(AudioAttribute.MUD, target, priority)


def create_punch_goal(target: float = 0.8, priority: float = 0.9) -> AudioGoal:
    """Create a goal to increase punch."""
    return AudioGoal(AudioAttribute.PUNCH, target, priority)


def create_balanced_mix_goals() -> List[AudioGoal]:
    """Create a set of goals for a balanced mix."""
    return [
        create_clarity_goal(0.75, 1.0),
        create_warmth_goal(0.65, 0.8),
        create_reduce_mud_goal(0.25, 0.9),
        create_punch_goal(0.70, 0.85),
        AudioGoal(AudioAttribute.BALANCE, 0.80, 0.95),
        AudioGoal(AudioAttribute.WIDTH, 0.70, 0.7),
    ]


if __name__ == "__main__":
    # Example usage
    ontology = AudioOntologyManager()

    # Create current audio state
    state = AudioState()
    state.set_attribute(AudioAttribute.CLARITY, 0.4, confidence=0.9)
    state.set_attribute(AudioAttribute.WARMTH, 0.7, confidence=0.8)
    state.set_attribute(AudioAttribute.MUD, 0.6, confidence=0.85)

    # Create goals
    goals = [
        create_clarity_goal(0.8, 1.0),
        create_reduce_mud_goal(0.3, 0.9),
    ]

    # Evaluate satisfaction
    satisfaction = ontology.estimate_satisfaction_score(state, goals)
    print(f"Current satisfaction: {satisfaction:.2f}")

    # Check attribute relationships
    conflicts = ontology.get_conflicting_attributes(AudioAttribute.CLARITY)
    print(f"Attributes conflicting with CLARITY: {conflicts}")

    synergies = ontology.get_synergistic_attributes(AudioAttribute.CLARITY)
    print(f"Attributes synergistic with CLARITY: {synergies}")


# Alias for backward compatibility
AudioOntology = AudioOntologyManager


def get_audio_ontology() -> AudioOntologyManager:
    """Get the singleton audio ontology instance."""
    return AudioOntologyManager()
