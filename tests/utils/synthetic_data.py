"""
Synthetic Data Generator for MAAPS Nexus Testing

This module provides utilities to generate synthetic audio data, agent states,
messages, and ontology structures for robust testing.
"""

import numpy as np
import uuid
import time
import random
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

from src.core.message_types import (
    Message, AudioBuffer, Priority, MessageType, Topics,
    AudioFeatures, SpectralFeatures, TemporalFeatures,
    HarmonicFeatures, DynamicFeatures
)
from src.core.audio_ontology import (
    AudioState, AudioAttribute, AudioGoal, AgentAction, FrequencyBand
)

@dataclass
class GenerationParams:
    """Parameters for synthetic data generation"""
    seed: Optional[int] = None
    sample_rate: int = 44100
    min_duration_sec: float = 0.1
    max_duration_sec: float = 2.0
    channels: int = 1
    noise_level: float = 0.01
    
    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)

class SyntheticDataGenerator:
    """Generates valid synthetic data for MAAPS components."""
    
    def __init__(self, params: GenerationParams = GenerationParams()):
        self.params = params

    def generate_audio_samples(self, duration: Optional[float] = None, signal_type: str = "sine") -> np.ndarray:
        """
        Generate synthetic audio samples.
        
        Args:
            duration: Duration in seconds (random if None)
            signal_type: 'sine', 'noise', 'silence', 'chirp', 'complex'
        """
        if duration is None:
            duration = random.uniform(self.params.min_duration_sec, self.params.max_duration_sec)
            
        num_samples = int(duration * self.params.sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        if signal_type == "sine":
            freq = random.uniform(100, 1000)
            audio = np.sin(2 * np.pi * freq * t)
        elif signal_type == "noise":
            audio = np.random.normal(0, 1, num_samples)
        elif signal_type == "silence":
            audio = np.zeros(num_samples)
        elif signal_type == "chirp":
            f0, f1 = random.uniform(50, 200), random.uniform(1000, 5000)
            audio = np.sin(2 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t**2 / duration))
        elif signal_type == "complex":
            # Mix of sines and noise
            audio = np.zeros(num_samples)
            for _ in range(random.randint(2, 5)):
                freq = random.uniform(50, 5000)
                amp = random.uniform(0.1, 0.5)
                audio += amp * np.sin(2 * np.pi * freq * t)
            audio += np.random.normal(0, self.params.noise_level, num_samples)
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")
            
        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
            
        # Handle channels
        if self.params.channels > 1:
            audio = np.stack([audio] * self.params.channels, axis=1)
            
        return audio

    def generate_audio_buffer(self) -> AudioBuffer:
        """Generate a complete AudioBuffer object."""
        samples = self.generate_audio_samples()
        duration = len(samples) / self.params.sample_rate
        
        return AudioBuffer(
            buffer_id=str(uuid.uuid4()),
            sample_rate=self.params.sample_rate,
            channels=self.params.channels,
            bit_depth=32,
            samples=samples,
            timestamp=time.time(),
            duration_ms=duration * 1000,
            metadata={"source": "synthetic", "type": "test_data"}
        )

    def generate_audio_state(self, completeness: float = 1.0) -> AudioState:
        """
        Generate a synthetic AudioState.
        
        Args:
            completeness: Percentage of attributes to include (0.0 to 1.0)
        """
        state = AudioState()
        attributes = list(AudioAttribute)
        
        # Select subset of attributes if not complete
        if completeness < 1.0:
            k = int(len(attributes) * completeness)
            selected_attrs = random.sample(attributes, k)
        else:
            selected_attrs = attributes
            
        for attr in selected_attrs:
            val = random.random() # 0.0 to 1.0
            conf = random.uniform(0.5, 1.0) # High confidence for synthetic data
            state.set_attribute(attr, val, conf)
            
        return state

    def generate_audio_goal(self, attribute: Optional[AudioAttribute] = None) -> AudioGoal:
        """Generate a random AudioGoal."""
        if attribute is None:
            attribute = random.choice(list(AudioAttribute))
            
        return AudioGoal(
            attribute=attribute,
            target_value=random.random(),
            priority=random.random(),
            tolerance=random.uniform(0.05, 0.2)
        )

    def generate_message(self, topic: Optional[str] = None) -> Message:
        """Generate a valid Message object."""
        if topic is None:
            topic = "test.topic.synthetic"
            
        payload = {
            "data_id": str(uuid.uuid4()),
            "value": random.random(),
            "timestamp": time.time(),
            "tags": ["synthetic", "test"]
        }
        
        return Message(
            topic=topic,
            sender="synthetic_generator",
            payload=payload,
            priority=random.choice(list(Priority)),
            message_type=MessageType.EVENT
        )

    def validate_audio_buffer(self, buffer: AudioBuffer) -> bool:
        """Validate an AudioBuffer schema."""
        if not isinstance(buffer.samples, np.ndarray):
            return False
        if buffer.sample_rate <= 0:
            return False
        if buffer.channels < 1:
            return False
        if len(buffer.samples) == 0:
            return False
        return True

    def validate_audio_state(self, state: AudioState) -> bool:
        """Validate AudioState constraints."""
        for val in state.attributes.values():
            if not (0.0 <= val <= 1.0):
                return False
        for conf in state.confidence.values():
            if not (0.0 <= conf <= 1.0):
                return False
        return True
