"""
Critic Agent - Audio Quality Judge

This agent predicts user satisfaction with audio quality by analyzing
audio features and mapping them to the audio ontology. It serves as
the reward function for reinforcement learning agents.
"""

import numpy as np
import librosa
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.audio_ontology import get_audio_ontology, AudioOntology, FrequencyRange
from src.core.types import Message, MessageType

logger = logging.getLogger(__name__)


@dataclass
class AudioFeatures:
    """Extracted audio features for critic analysis"""
    # Spectral features
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_flatness: float = 0.0

    # Energy features by frequency band
    sub_bass_energy: float = 0.0
    bass_energy: float = 0.0
    low_mid_energy: float = 0.0
    mid_energy: float = 0.0
    high_mid_energy: float = 0.0
    presence_energy: float = 0.0
    brilliance_energy: float = 0.0

    # Dynamic features
    rms_energy: float = 0.0
    dynamic_range: float = 0.0
    crest_factor: float = 0.0

    # Temporal features
    zero_crossing_rate: float = 0.0
    tempo: float = 0.0

    # Harmonic features
    harmonic_ratio: float = 0.0

    def to_vector(self) -> np.ndarray:
        """Convert features to numpy vector"""
        return np.array([
            self.spectral_centroid,
            self.spectral_rolloff,
            self.spectral_bandwidth,
            self.spectral_flatness,
            self.sub_bass_energy,
            self.bass_energy,
            self.low_mid_energy,
            self.mid_energy,
            self.high_mid_energy,
            self.presence_energy,
            self.brilliance_energy,
            self.rms_energy,
            self.dynamic_range,
            self.crest_factor,
            self.zero_crossing_rate,
            self.tempo,
            self.harmonic_ratio,
        ])


@dataclass
class CriticJudgment:
    """Critic's judgment of audio quality"""
    satisfaction_score: float  # -1.0 to 1.0
    detected_concepts: List[str]
    positive_concepts: List[str]
    negative_concepts: List[str]
    frequency_balance: Dict[str, float]
    suggested_corrections: Dict[str, List[Tuple[FrequencyRange, float]]]
    confidence: float  # 0.0 to 1.0


class CriticNetwork(nn.Module):
    """
    Neural network for predicting audio satisfaction.

    This is a simple feed-forward network that can be trained
    to predict user satisfaction from audio features.
    """

    def __init__(self, input_dim: int = 17, hidden_dims: List[int] = [64, 32, 16]):
        super(CriticNetwork, self).__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        # Output layer: satisfaction score (-1 to 1)
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Tanh())  # Output between -1 and 1

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through network"""
        return self.network(x)


class CriticAgent(BaseAgent):
    """
    Critic Agent that judges audio quality and predicts user satisfaction.

    The Critic:
    1. Extracts audio features from input audio
    2. Maps features to ontology concepts
    3. Predicts user satisfaction score
    4. Suggests corrections for negative qualities
    5. Can be trained to improve predictions
    """

    def __init__(self, agent_id: str, message_bus, config: Optional[Dict[str, Any]] = None):
        capabilities = [
            AgentCapability.AUDIO_ANALYSIS,
            AgentCapability.MACHINE_LEARNING,
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="critic",
            capabilities=capabilities,
            message_bus=message_bus
        )

        self.config = config or {}
        self.ontology: AudioOntology = get_audio_ontology()

        # Neural network for satisfaction prediction
        self.network = CriticNetwork()
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=0.001)

        # Feature extraction parameters
        self.sample_rate = self.config.get('sample_rate', 44100)
        if self.sample_rate <= 0:
            raise ValueError(
                f"sample_rate must be positive (got {self.sample_rate})"
            )
        self.n_fft = self.config.get('n_fft', 2048)
        self.hop_length = self.config.get('hop_length', 512)

        # Training data — bounded ring buffer to prevent unbounded growth
        # over long sessions. Override via config['max_training_samples'].
        self.max_training_samples = self.config.get('max_training_samples', 10000)
        from collections import deque as _deque
        self.training_data: "_deque[Tuple[AudioFeatures, float]]" = _deque(
            maxlen=self.max_training_samples
        )

        # Concept detection thresholds — caller may override the defaults
        # by passing config['concept_thresholds'] = {...} (deep-merged).
        self.concept_thresholds = self._initialize_thresholds()
        override = self.config.get('concept_thresholds')
        if override:
            for concept, fields in override.items():
                if concept in self.concept_thresholds:
                    self.concept_thresholds[concept].update(fields)
                else:
                    self.concept_thresholds[concept] = dict(fields)

        logger.info(f"Critic agent {agent_id} initialized")

    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize concept detection thresholds"""
        return {
            "mud": {
                "low_mid_energy": 0.7,  # High low-mid energy indicates mud
                "clarity_threshold": 0.3,  # Low clarity indicates mud
            },
            "harshness": {
                "high_mid_energy": 0.8,  # High high-mid energy
                "presence_energy": 0.8,  # High presence energy
            },
            "boominess": {
                "bass_energy": 0.8,  # Excessive bass
                "dynamic_range": 0.2,  # Low dynamic range
            },
            "clarity": {
                "spectral_centroid": 3000,  # Higher centroid = more clarity
                "high_mid_energy": 0.5,  # Adequate high-mid energy
            },
            "warmth": {
                "bass_energy": 0.5,  # Good bass presence
                "low_mid_energy": 0.5,  # Good low-mid presence
            },
        }

    def extract_features(self, audio: np.ndarray, sr: int = None) -> AudioFeatures:
        """
        Extract comprehensive audio features for critic analysis.

        Args:
            audio: Audio signal as numpy array
            sr: Sample rate (uses default if None)

        Returns:
            AudioFeatures object
        """
        if sr is None:
            sr = self.sample_rate

        features = AudioFeatures()

        try:
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length
            )[0]
            features.spectral_centroid = np.mean(spectral_centroids) / sr  # Normalize

            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length
            )[0]
            features.spectral_rolloff = np.mean(spectral_rolloff) / sr

            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=audio, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length
            )[0]
            features.spectral_bandwidth = np.mean(spectral_bandwidth) / sr

            spectral_flatness = librosa.feature.spectral_flatness(
                y=audio, n_fft=self.n_fft, hop_length=self.hop_length
            )[0]
            features.spectral_flatness = np.mean(spectral_flatness)

            # Energy per frequency band
            stft = np.abs(librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length))
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)

            def get_band_energy(low_freq, high_freq):
                band_mask = (frequencies >= low_freq) & (frequencies < high_freq)
                band_energy = np.mean(stft[band_mask, :])
                return float(band_energy)

            features.sub_bass_energy = get_band_energy(20, 60)
            features.bass_energy = get_band_energy(60, 250)
            features.low_mid_energy = get_band_energy(250, 500)
            features.mid_energy = get_band_energy(500, 2000)
            features.high_mid_energy = get_band_energy(2000, 4000)
            features.presence_energy = get_band_energy(4000, 6000)
            features.brilliance_energy = get_band_energy(6000, 20000)

            # Normalize band energies
            total_energy = (
                features.sub_bass_energy + features.bass_energy
                + features.low_mid_energy + features.mid_energy
                + features.high_mid_energy + features.presence_energy
                + features.brilliance_energy
            )

            if total_energy > 0:
                features.sub_bass_energy /= total_energy
                features.bass_energy /= total_energy
                features.low_mid_energy /= total_energy
                features.mid_energy /= total_energy
                features.high_mid_energy /= total_energy
                features.presence_energy /= total_energy
                features.brilliance_energy /= total_energy

            # Dynamic features
            features.rms_energy = float(np.sqrt(np.mean(audio**2)))

            # Dynamic range (difference between 95th and 5th percentile)
            audio_db = librosa.amplitude_to_db(np.abs(audio), ref=np.max)
            features.dynamic_range = float(np.percentile(audio_db, 95) - np.percentile(audio_db, 5))

            # Crest factor (peak to RMS ratio)
            peak = np.max(np.abs(audio))
            if features.rms_energy > 0:
                features.crest_factor = peak / features.rms_energy
            else:
                features.crest_factor = 0.0

            # Temporal features
            zcr = librosa.feature.zero_crossing_rate(audio, hop_length=self.hop_length)[0]
            features.zero_crossing_rate = np.mean(zcr)

            # Tempo
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            features.tempo = float(tempo) / 200.0  # Normalize to 0-1 range (assuming max 200 BPM)

            # Harmonic-percussive separation
            y_harmonic, y_percussive = librosa.effects.hpss(audio)
            harmonic_energy = np.sum(y_harmonic**2)
            percussive_energy = np.sum(y_percussive**2)
            total = harmonic_energy + percussive_energy
            if total > 0:
                features.harmonic_ratio = harmonic_energy / total
            else:
                features.harmonic_ratio = 0.5

        except Exception as e:
            logger.error(f"Error extracting features: {e}")

        return features

    def detect_concepts(self, features: AudioFeatures) -> Tuple[List[str], List[str]]:
        """
        Detect audio concepts from features.

        Returns:
            Tuple of (positive_concepts, negative_concepts)
        """
        positive_concepts = []
        negative_concepts = []

        # Detect MUD
        if (features.low_mid_energy > self.concept_thresholds["mud"]["low_mid_energy"]):
            negative_concepts.append("mud")

        # Detect HARSHNESS
        if (
            features.high_mid_energy > self.concept_thresholds["harshness"]["high_mid_energy"]
            or features.presence_energy > self.concept_thresholds["harshness"]["presence_energy"]
        ):
            negative_concepts.append("harshness")

        # Detect BOOMINESS
        if (
            features.bass_energy > self.concept_thresholds["boominess"]["bass_energy"]
            and features.dynamic_range < self.concept_thresholds["boominess"]["dynamic_range"]
        ):
            negative_concepts.append("boominess")

        # Detect CLARITY
        clarity_centroid = self.concept_thresholds["clarity"]["spectral_centroid"] / self.sample_rate
        if (
            features.spectral_centroid > clarity_centroid
            and features.high_mid_energy > self.concept_thresholds["clarity"]["high_mid_energy"]
        ):
            positive_concepts.append("clarity")

        # Detect WARMTH
        if (
            features.bass_energy > self.concept_thresholds["warmth"]["bass_energy"]
            and features.low_mid_energy > self.concept_thresholds["warmth"]["low_mid_energy"]
            and "mud" not in negative_concepts
        ):
            positive_concepts.append("warmth")

        # Detect BRIGHTNESS
        if features.presence_energy > 0.3 or features.brilliance_energy > 0.2:
            if "harshness" not in negative_concepts:
                positive_concepts.append("brightness")

        # Detect TIGHTNESS
        if features.dynamic_range > 50 and features.bass_energy < 0.7:
            positive_concepts.append("tightness")

        # Detect DEPTH
        if features.sub_bass_energy > 0.1:
            positive_concepts.append("depth")

        return positive_concepts, negative_concepts

    def judge_audio(self, audio: np.ndarray, sr: int = None) -> CriticJudgment:
        """
        Judge audio quality and provide satisfaction score.

        Args:
            audio: Audio signal as numpy array
            sr: Sample rate

        Returns:
            CriticJudgment with satisfaction score and analysis
        """
        # Extract features
        features = self.extract_features(audio, sr)

        # Detect concepts
        positive_concepts, negative_concepts = self.detect_concepts(features)
        all_concepts = positive_concepts + negative_concepts

        # Predict satisfaction using neural network
        feature_vector = torch.FloatTensor(features.to_vector()).unsqueeze(0)
        with torch.no_grad():
            nn_satisfaction = self.network(feature_vector).item()

        # Also use ontology-based prediction
        ontology_satisfaction = self.ontology.predict_satisfaction(all_concepts)

        # Combine both predictions (weighted average)
        satisfaction_score = 0.6 * nn_satisfaction + 0.4 * ontology_satisfaction

        # Calculate confidence based on agreement
        confidence = 1.0 - abs(nn_satisfaction - ontology_satisfaction) / 2.0

        # Get frequency balance
        frequency_balance = {
            "sub_bass": features.sub_bass_energy,
            "bass": features.bass_energy,
            "low_mids": features.low_mid_energy,
            "mids": features.mid_energy,
            "high_mids": features.high_mid_energy,
            "presence": features.presence_energy,
            "brilliance": features.brilliance_energy,
        }

        # Get suggested corrections
        suggested_corrections = self.ontology.suggest_corrections(negative_concepts)

        judgment = CriticJudgment(
            satisfaction_score=satisfaction_score,
            detected_concepts=all_concepts,
            positive_concepts=positive_concepts,
            negative_concepts=negative_concepts,
            frequency_balance=frequency_balance,
            suggested_corrections=suggested_corrections,
            confidence=confidence,
        )

        logger.info(
            f"Critic judgment: satisfaction={satisfaction_score:.3f}, "
            f"confidence={confidence:.3f}, concepts={all_concepts}"
        )

        return judgment

    def train_on_feedback(self, audio: np.ndarray, user_satisfaction: float, sr: int = None):
        """
        Train the critic network on user feedback.

        Args:
            audio: Audio signal
            user_satisfaction: User-provided satisfaction score (-1.0 to 1.0)
            sr: Sample rate
        """
        features = self.extract_features(audio, sr)
        self.training_data.append((features, user_satisfaction))

        # Train on batch if we have enough data
        if len(self.training_data) >= 32:
            self._train_batch()

    def _train_batch(self):
        """Train network on accumulated training data"""
        if len(self.training_data) < 8:
            return

        # Prepare batch
        batch_size = min(32, len(self.training_data))
        batch_indices = np.random.choice(len(self.training_data), batch_size, replace=False)

        features_batch = []
        labels_batch = []

        for idx in batch_indices:
            features, satisfaction = self.training_data[idx]
            features_batch.append(features.to_vector())
            labels_batch.append(satisfaction)

        features_tensor = torch.FloatTensor(np.array(features_batch))
        labels_tensor = torch.FloatTensor(labels_batch).unsqueeze(1)

        # Training step
        self.network.train()
        self.optimizer.zero_grad()

        predictions = self.network(features_tensor)
        loss = F.mse_loss(predictions, labels_tensor)

        loss.backward()
        self.optimizer.step()

        logger.info(f"Critic trained on batch: loss={loss.item():.4f}")

    def handle_message(self, message: Message) -> Any:
        """Handle incoming messages"""
        try:
            if message.message_type == MessageType.AUDIO_ANALYSIS_REQUEST:
                audio = message.payload.get('audio')
                sr = message.payload.get('sample_rate', self.sample_rate)

                judgment = self.judge_audio(audio, sr)

                return {
                    'status': 'success',
                    'judgment': {
                        'satisfaction_score': judgment.satisfaction_score,
                        'confidence': judgment.confidence,
                        'positive_concepts': judgment.positive_concepts,
                        'negative_concepts': judgment.negative_concepts,
                        'frequency_balance': judgment.frequency_balance,
                        'suggested_corrections': [
                            {
                                'concept': concept,
                                'adjustments': [(fr.name, db) for fr, db in adjustments]
                            }
                            for concept, adjustments in judgment.suggested_corrections.items()
                        ]
                    }
                }

            elif message.message_type == MessageType.TRAINING_DATA:
                audio = message.payload.get('audio')
                satisfaction = message.payload.get('satisfaction')
                sr = message.payload.get('sample_rate', self.sample_rate)

                self.train_on_feedback(audio, satisfaction, sr)

                return {'status': 'success', 'message': 'Training data received'}

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {'status': 'error', 'message': str(e)}
