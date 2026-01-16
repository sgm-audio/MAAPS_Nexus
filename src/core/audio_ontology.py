"""
Audio Ontology for Multi-Agent Audio System

Defines the vocabulary and semantic relationships between audio concepts
that agents use to communicate about audio quality and characteristics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FrequencyRange(Enum):
    """Frequency ranges for audio processing"""
    SUB_BASS = (20, 60)          # 20-60 Hz
    BASS = (60, 250)             # 60-250 Hz
    LOW_MIDS = (250, 500)        # 250-500 Hz
    MIDS = (500, 2000)           # 500-2000 Hz
    HIGH_MIDS = (2000, 4000)     # 2-4 kHz
    PRESENCE = (4000, 6000)      # 4-6 kHz
    BRILLIANCE = (6000, 20000)   # 6-20 kHz


class AudioQuality(Enum):
    """Audio quality descriptors"""
    # Positive qualities
    CLARITY = "clarity"
    WARMTH = "warmth"
    BRIGHTNESS = "brightness"
    PUNCH = "punch"
    DEPTH = "depth"
    AIRINESS = "airiness"
    PRESENCE = "presence"
    SPARKLE = "sparkle"
    RICHNESS = "richness"
    SMOOTHNESS = "smoothness"
    FULLNESS = "fullness"
    TIGHTNESS = "tightness"

    # Negative qualities
    MUD = "mud"
    HARSHNESS = "harshness"
    THINNESS = "thinness"
    BOXINESS = "boxiness"
    HONKINESS = "honkiness"
    BOOMINESS = "boominess"
    SHRILLNESS = "shrillness"
    DULLNESS = "dullness"
    CLUTTER = "clutter"
    RESONANCE = "resonance"


class DynamicsQuality(Enum):
    """Dynamics-related quality descriptors"""
    PUNCHY = "punchy"
    COMPRESSED = "compressed"
    DYNAMIC = "dynamic"
    FLAT = "flat"
    SQUASHED = "squashed"
    BREATHING = "breathing"
    NATURAL = "natural"
    CONTROLLED = "controlled"
    AGGRESSIVE = "aggressive"
    GENTLE = "gentle"


@dataclass
class AudioConcept:
    """
    Represents an audio concept with semantic relationships.
    """
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


class AudioOntology:
    """
    Complete audio ontology defining concepts and relationships.

    This provides a shared vocabulary for agents to reason about audio quality.
    """

    def __init__(self):
        self.concepts: Dict[str, AudioConcept] = {}
        self._initialize_ontology()

    def _initialize_ontology(self):
        """Initialize the complete audio ontology"""

        # CLARITY - Clear, defined, separation
        self.concepts["clarity"] = AudioConcept(
            name="clarity",
            description="Clear definition and separation of individual elements",
            frequency_ranges=[FrequencyRange.HIGH_MIDS, FrequencyRange.PRESENCE],
            related_concepts=["brightness", "presence", "airiness"],
            opposite_concepts=["mud", "clutter", "dullness"],
            clarity_impact=1.0,
            warmth_impact=0.3,
            brightness_impact=0.7,
            eq_adjustments={
                FrequencyRange.LOW_MIDS: -2.0,  # Cut muddiness
                FrequencyRange.HIGH_MIDS: 2.0,  # Boost clarity
                FrequencyRange.PRESENCE: 1.5,   # Add presence
            },
            satisfaction_correlation=0.8
        )

        # WARMTH - Warm, full, rich low-mids
        self.concepts["warmth"] = AudioConcept(
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
            satisfaction_correlation=0.7
        )

        # MUD - Unclear, boomy, undefined low-mids
        self.concepts["mud"] = AudioConcept(
            name="mud",
            description="Unclear, undefined mix from excessive low-mid energy",
            frequency_ranges=[FrequencyRange.LOW_MIDS],
            related_concepts=["boominess", "clutter", "boxiness"],
            opposite_concepts=["clarity", "tightness", "presence"],
            clarity_impact=-0.8,
            warmth_impact=0.6,
            brightness_impact=-0.4,
            eq_adjustments={
                FrequencyRange.LOW_MIDS: -4.0,  # Cut mud
                FrequencyRange.MIDS: 1.0,       # Boost definition
                FrequencyRange.HIGH_MIDS: 2.0,  # Add clarity
            },
            satisfaction_correlation=-0.9
        )

        # BRIGHTNESS - High-frequency energy and sparkle
        self.concepts["brightness"] = AudioConcept(
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
            satisfaction_correlation=0.6
        )

        # HARSHNESS - Aggressive, unpleasant high frequencies
        self.concepts["harshness"] = AudioConcept(
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
            satisfaction_correlation=-0.85
        )

        # PUNCH - Transient impact and definition
        self.concepts["punch"] = AudioConcept(
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
            compression_ratio=4.0,  # Fast attack for punch
            satisfaction_correlation=0.75
        )

        # DEPTH - Perceived depth and spaciousness
        self.concepts["depth"] = AudioConcept(
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
            satisfaction_correlation=0.7
        )

        # AIRINESS - Open, spacious high-frequency character
        self.concepts["airiness"] = AudioConcept(
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
            satisfaction_correlation=0.65
        )

        # BOOMINESS - Excessive low-frequency resonance
        self.concepts["boominess"] = AudioConcept(
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
            satisfaction_correlation=-0.8
        )

        # PRESENCE - Forward, in-your-face quality
        self.concepts["presence"] = AudioConcept(
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
            satisfaction_correlation=0.75
        )

        # BOXINESS - Narrow, confined mid-range sound
        self.concepts["boxiness"] = AudioConcept(
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
            satisfaction_correlation=-0.7
        )

        # TIGHTNESS - Controlled, focused low-end
        self.concepts["tightness"] = AudioConcept(
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
            satisfaction_correlation=0.8
        )

    def get_concept(self, name: str) -> Optional[AudioConcept]:
        """Get audio concept by name"""
        return self.concepts.get(name.lower())

    def get_related_concepts(self, concept_name: str) -> List[AudioConcept]:
        """Get concepts related to given concept"""
        concept = self.get_concept(concept_name)
        if not concept:
            return []
        return [self.concepts[name] for name in concept.related_concepts
                if name in self.concepts]

    def get_opposite_concepts(self, concept_name: str) -> List[AudioConcept]:
        """Get concepts opposite to given concept"""
        concept = self.get_concept(concept_name)
        if not concept:
            return []
        return [self.concepts[name] for name in concept.opposite_concepts
                if name in self.concepts]

    def analyze_frequency_range(self, freq_hz: float) -> FrequencyRange:
        """Determine frequency range for a given frequency"""
        for freq_range in FrequencyRange:
            low, high = freq_range.value
            if low <= freq_hz < high:
                return freq_range
        return FrequencyRange.BRILLIANCE  # Default for frequencies above 20kHz

    def get_concepts_for_frequency(self, freq_hz: float) -> List[AudioConcept]:
        """Get all concepts that affect a given frequency"""
        freq_range = self.analyze_frequency_range(freq_hz)
        return [concept for concept in self.concepts.values()
                if freq_range in concept.frequency_ranges]

    def compute_quality_vector(self, concept_names: List[str]) -> np.ndarray:
        """
        Compute a quality vector from concept names.

        Returns: [clarity, warmth, brightness] vector
        """
        vector = np.zeros(3)
        count = 0

        for name in concept_names:
            concept = self.get_concept(name)
            if concept:
                vector[0] += concept.clarity_impact
                vector[1] += concept.warmth_impact
                vector[2] += concept.brightness_impact
                count += 1

        if count > 0:
            vector /= count

        return vector

    def suggest_corrections(self, negative_concepts: List[str]) -> Dict[str, List[Tuple[FrequencyRange, float]]]:
        """
        Suggest EQ corrections to address negative concepts.

        Args:
            negative_concepts: List of negative audio qualities detected

        Returns:
            Dictionary mapping concept names to EQ adjustments
        """
        corrections = {}

        for concept_name in negative_concepts:
            concept = self.get_concept(concept_name)
            if concept and concept.eq_adjustments:
                corrections[concept_name] = [
                    (freq_range, db_change)
                    for freq_range, db_change in concept.eq_adjustments.items()
                ]

        return corrections

    def predict_satisfaction(self, detected_concepts: List[str]) -> float:
        """
        Predict user satisfaction based on detected audio concepts.

        Args:
            detected_concepts: List of detected audio qualities

        Returns:
            Predicted satisfaction score (-1.0 to 1.0)
        """
        if not detected_concepts:
            return 0.0

        satisfaction_scores = [
            self.concepts[name].satisfaction_correlation
            for name in detected_concepts
            if name in self.concepts
        ]

        if not satisfaction_scores:
            return 0.0

        return np.mean(satisfaction_scores)

    def get_all_positive_concepts(self) -> List[str]:
        """Get all concepts with positive satisfaction correlation"""
        return [
            name for name, concept in self.concepts.items()
            if concept.satisfaction_correlation > 0.5
        ]

    def get_all_negative_concepts(self) -> List[str]:
        """Get all concepts with negative satisfaction correlation"""
        return [
            name for name, concept in self.concepts.items()
            if concept.satisfaction_correlation < -0.5
        ]

    def get_concept_names(self) -> List[str]:
        """Get all concept names in ontology"""
        return list(self.concepts.keys())

    def describe_concept(self, concept_name: str) -> str:
        """Get detailed description of a concept"""
        concept = self.get_concept(concept_name)
        if not concept:
            return f"Unknown concept: {concept_name}"

        freq_ranges = ", ".join([fr.name for fr in concept.frequency_ranges])
        related = ", ".join(concept.related_concepts)
        opposite = ", ".join(concept.opposite_concepts)

        return f"""
Concept: {concept.name.upper()}
Description: {concept.description}
Frequency Ranges: {freq_ranges}
Related Concepts: {related}
Opposite Concepts: {opposite}
Satisfaction Correlation: {concept.satisfaction_correlation:.2f}
Impact: Clarity={concept.clarity_impact:.1f}, Warmth={concept.warmth_impact:.1f}, Brightness={concept.brightness_impact:.1f}
"""


# Global ontology instance
_ontology: Optional[AudioOntology] = None


def get_audio_ontology() -> AudioOntology:
    """Get or create global audio ontology instance"""
    global _ontology
    if _ontology is None:
        _ontology = AudioOntology()
        logger.info(f"Audio ontology initialized with {len(_ontology.concepts)} concepts")
    return _ontology
