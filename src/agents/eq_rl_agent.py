"""
EQ Reinforcement Learning Agent

This agent learns to adjust EQ parameters to maximize audio quality
as judged by the Critic agent. Uses Q-learning / Policy Gradient methods.
"""

import numpy as np
from scipy import signal
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import deque
import torch
import torch.nn as nn
import torch.nn.functional as F
import random

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.types import Message, MessageType
from src.core.audio_ontology import FrequencyRange

logger = logging.getLogger(__name__)


@dataclass
class EQBand:
    """Represents a single EQ band"""
    center_freq: float  # Hz
    gain: float  # dB (-12 to +12)
    q_factor: float  # 0.1 to 10.0
    eq_type: str = "peak"  # peak, lowshelf, highshelf


@dataclass
class EQState:
    """Current state of all EQ bands"""
    bands: List[EQBand]

    def to_vector(self) -> np.ndarray:
        """Convert EQ state to vector for RL"""
        vector = []
        for band in self.bands:
            vector.extend([
                band.center_freq / 20000,  # Normalize
                (band.gain + 12) / 24,      # Normalize to 0-1
                band.q_factor / 10,         # Normalize to 0-1
            ])
        return np.array(vector)

    @classmethod
    def from_vector(cls, vector: np.ndarray, center_freqs: List[float]) -> 'EQState':
        """Create EQ state from vector"""
        bands = []
        for i, center_freq in enumerate(center_freqs):
            idx = i * 3
            gain = vector[idx + 1] * 24 - 12
            q_factor = vector[idx + 2] * 10
            bands.append(EQBand(
                center_freq=center_freq,
                gain=gain,
                q_factor=q_factor,
            ))
        return cls(bands=bands)


class EQPolicyNetwork(nn.Module):
    """
    Policy network for EQ adjustment.

    Maps audio features to EQ parameter adjustments.
    """

    def __init__(self, audio_feature_dim: int = 17, num_eq_bands: int = 7,
                 hidden_dim: int = 128):
        super(EQPolicyNetwork, self).__init__()

        self.num_eq_bands = num_eq_bands
        self.action_dim = num_eq_bands * 2  # gain and Q for each band

        # Encoder for audio features
        self.feature_encoder = nn.Sequential(
            nn.Linear(audio_feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )

        # Policy head (outputs mean of action distribution)
        self.policy_mean = nn.Linear(hidden_dim // 2, self.action_dim)

        # Log std (learnable parameter)
        self.policy_log_std = nn.Parameter(torch.zeros(self.action_dim))

        # Value head (for advantage estimation)
        self.value_head = nn.Linear(hidden_dim // 2, 1)

    def forward(self, audio_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            (action_mean, action_log_std)
        """
        features = self.feature_encoder(audio_features)
        action_mean = self.policy_mean(features)
        action_log_std = self.policy_log_std.expand_as(action_mean)

        return action_mean, action_log_std

    def get_value(self, audio_features: torch.Tensor) -> torch.Tensor:
        """Get state value estimate"""
        features = self.feature_encoder(audio_features)
        return self.value_head(features)

    def sample_action(self, audio_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Sample action from policy.

        Returns:
            (action, log_prob, value)
        """
        action_mean, action_log_std = self.forward(audio_features)
        action_std = action_log_std.exp()

        # Sample from Gaussian distribution
        normal = torch.distributions.Normal(action_mean, action_std)
        action = normal.sample()

        # Clip actions to valid range
        action = torch.clamp(action, -1.0, 1.0)

        # Compute log probability
        log_prob = normal.log_prob(action).sum(dim=-1)

        # Get value estimate
        value = self.get_value(audio_features)

        return action, log_prob, value


@dataclass
class RLExperience:
    """Single experience for RL training"""
    audio_features: np.ndarray
    action: np.ndarray
    reward: float
    next_audio_features: np.ndarray
    done: bool
    log_prob: float = 0.0
    value: float = 0.0


class EQRLAgent(BaseAgent):
    """
    EQ Agent with Reinforcement Learning.

    Learns to adjust EQ parameters to maximize Critic satisfaction.
    Uses policy gradient (PPO-style) reinforcement learning.
    """

    def __init__(self, agent_id: str, message_bus, critic_agent_id: str,
                 config: Optional[Dict[str, Any]] = None):
        capabilities = [
            AgentCapability.AUDIO_PROCESSING,
            AgentCapability.MACHINE_LEARNING,
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="eq_rl",
            capabilities=capabilities,
            message_bus=message_bus
        )

        self.config = config or {}
        self.critic_agent_id = critic_agent_id

        # EQ configuration - 7 bands matching frequency ranges
        self.center_frequencies = [
            50,    # Sub-bass
            150,   # Bass
            375,   # Low-mids
            1000,  # Mids
            3000,  # High-mids
            5000,  # Presence
            10000, # Brilliance
        ]

        # Initialize EQ state
        self.current_eq = EQState(bands=[
            EQBand(center_freq=freq, gain=0.0, q_factor=1.0)
            for freq in self.center_frequencies
        ])

        # RL components
        self.policy_network = EQPolicyNetwork(
            audio_feature_dim=17,
            num_eq_bands=len(self.center_frequencies),
        )
        self.optimizer = torch.optim.Adam(self.policy_network.parameters(), lr=3e-4)

        # Experience replay buffer
        self.replay_buffer: deque = deque(maxlen=10000)
        self.episode_buffer: List[RLExperience] = []

        # RL hyperparameters
        self.gamma = 0.99  # Discount factor
        self.gae_lambda = 0.95  # GAE parameter
        self.clip_epsilon = 0.2  # PPO clip parameter
        self.value_loss_coef = 0.5
        self.entropy_coef = 0.01
        self.batch_size = 64
        self.update_epochs = 4

        # Exploration
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.1

        # Training statistics
        self.episodes_trained = 0
        self.total_reward = 0.0
        self.best_reward = -float('inf')
        self.best_eq_state = None

        # Audio processing
        self.sample_rate = self.config.get('sample_rate', 44100)

        logger.info(f"EQ RL Agent {agent_id} initialized with {len(self.center_frequencies)} bands")

    def apply_eq(self, audio: np.ndarray, eq_state: EQState) -> np.ndarray:
        """
        Apply EQ filters to audio.

        Args:
            audio: Input audio signal
            eq_state: EQ parameters to apply

        Returns:
            Filtered audio
        """
        output = audio.copy()

        for band in eq_state.bands:
            # Design filter based on band type
            if band.eq_type == "peak":
                # Peaking filter
                b, a = self._design_peak_filter(
                    band.center_freq,
                    band.gain,
                    band.q_factor,
                    self.sample_rate
                )
            elif band.eq_type == "lowshelf":
                b, a = self._design_shelf_filter(
                    band.center_freq,
                    band.gain,
                    self.sample_rate,
                    shelf_type='low'
                )
            elif band.eq_type == "highshelf":
                b, a = self._design_shelf_filter(
                    band.center_freq,
                    band.gain,
                    self.sample_rate,
                    shelf_type='high'
                )
            else:
                continue

            # Apply filter
            output = signal.filtfilt(b, a, output)

        return output

    def _design_peak_filter(self, center_freq: float, gain_db: float,
                           q_factor: float, sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """Design a peaking EQ filter"""
        # Convert gain from dB to linear
        A = 10 ** (gain_db / 40)
        omega = 2 * np.pi * center_freq / sr
        alpha = np.sin(omega) / (2 * q_factor)

        # Biquad coefficients
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(omega)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(omega)
        a2 = 1 - alpha / A

        # Normalize
        b = np.array([b0, b1, b2]) / a0
        a = np.array([1, a1 / a0, a2 / a0])

        return b, a

    def _design_shelf_filter(self, cutoff_freq: float, gain_db: float,
                            sr: int, shelf_type: str = 'low') -> Tuple[np.ndarray, np.ndarray]:
        """Design a shelving filter"""
        A = 10 ** (gain_db / 40)
        omega = 2 * np.pi * cutoff_freq / sr

        if shelf_type == 'low':
            # Low shelf
            alpha = np.sin(omega) / 2 * np.sqrt((A + 1/A) * (1/0.5 - 1) + 2)
            b0 = A * ((A + 1) - (A - 1) * np.cos(omega) + 2 * np.sqrt(A) * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * np.cos(omega))
            b2 = A * ((A + 1) - (A - 1) * np.cos(omega) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) + (A - 1) * np.cos(omega) + 2 * np.sqrt(A) * alpha
            a1 = -2 * ((A - 1) + (A + 1) * np.cos(omega))
            a2 = (A + 1) + (A - 1) * np.cos(omega) - 2 * np.sqrt(A) * alpha
        else:
            # High shelf
            alpha = np.sin(omega) / 2 * np.sqrt((A + 1/A) * (1/0.5 - 1) + 2)
            b0 = A * ((A + 1) + (A - 1) * np.cos(omega) + 2 * np.sqrt(A) * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(omega))
            b2 = A * ((A + 1) + (A - 1) * np.cos(omega) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) - (A - 1) * np.cos(omega) + 2 * np.sqrt(A) * alpha
            a1 = 2 * ((A - 1) - (A + 1) * np.cos(omega))
            a2 = (A + 1) - (A - 1) * np.cos(omega) - 2 * np.sqrt(A) * alpha

        b = np.array([b0, b1, b2]) / a0
        a = np.array([1, a1 / a0, a2 / a0])

        return b, a

    def get_reward_from_critic(self, audio: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """
        Get reward from Critic agent.

        Args:
            audio: Processed audio to judge

        Returns:
            (reward, judgment_details)
        """
        # Request judgment from Critic
        response = self.message_bus.request(
            self.critic_agent_id,
            Message(
                message_type=MessageType.AUDIO_ANALYSIS_REQUEST,
                sender_id=self.agent_id,
                payload={
                    'audio': audio,
                    'sample_rate': self.sample_rate,
                }
            )
        )

        if response and response.get('status') == 'success':
            judgment = response.get('judgment', {})
            reward = judgment.get('satisfaction_score', 0.0)
            return reward, judgment
        else:
            logger.warning("Failed to get reward from Critic")
            return 0.0, {}

    def select_action(self, audio_features: np.ndarray, explore: bool = True) -> Tuple[np.ndarray, float, float]:
        """
        Select EQ adjustment action using policy network.

        Args:
            audio_features: Current audio features
            explore: Whether to add exploration noise

        Returns:
            (action, log_prob, value)
        """
        # Epsilon-greedy exploration
        if explore and random.random() < self.epsilon:
            # Random action
            action = np.random.uniform(-1, 1, size=len(self.center_frequencies) * 2)
            log_prob = 0.0
            value = 0.0
        else:
            # Policy-based action
            feature_tensor = torch.FloatTensor(audio_features).unsqueeze(0)
            with torch.no_grad():
                action_tensor, log_prob_tensor, value_tensor = self.policy_network.sample_action(feature_tensor)
                action = action_tensor.squeeze(0).numpy()
                log_prob = log_prob_tensor.item()
                value = value_tensor.item()

        return action, log_prob, value

    def action_to_eq_adjustments(self, action: np.ndarray) -> EQState:
        """
        Convert RL action to EQ parameter adjustments.

        Args:
            action: Action vector from policy (-1 to 1)

        Returns:
            New EQ state
        """
        bands = []
        for i, center_freq in enumerate(self.center_frequencies):
            gain_action = action[i * 2]  # -1 to 1
            q_action = action[i * 2 + 1]  # -1 to 1

            # Map action to actual parameter changes
            gain_delta = gain_action * 2.0  # Max ±2 dB per step
            q_delta = q_action * 0.5  # Max ±0.5 Q per step

            # Get current values
            current_band = self.current_eq.bands[i]
            new_gain = np.clip(current_band.gain + gain_delta, -12, 12)
            new_q = np.clip(current_band.q_factor + q_delta, 0.1, 10.0)

            bands.append(EQBand(
                center_freq=center_freq,
                gain=new_gain,
                q_factor=new_q,
            ))

        return EQState(bands=bands)

    def train_episode(self, audio: np.ndarray, max_steps: int = 10) -> Dict[str, Any]:
        """
        Run one training episode.

        Args:
            audio: Input audio to process
            max_steps: Maximum steps per episode

        Returns:
            Episode statistics
        """
        self.episode_buffer = []
        episode_reward = 0.0

        # Get initial judgment
        initial_reward, _ = self.get_reward_from_critic(audio)

        current_audio = audio.copy()

        for step in range(max_steps):
            # Get audio features from Critic (reuse its feature extractor)
            # For simplicity, use a placeholder - in production, call Critic
            audio_features = np.random.randn(17)  # TODO: Get from Critic

            # Select action
            action, log_prob, value = self.select_action(audio_features, explore=True)

            # Convert action to EQ adjustments
            new_eq_state = self.action_to_eq_adjustments(action)

            # Apply EQ
            processed_audio = self.apply_eq(current_audio, new_eq_state)

            # Get reward from Critic
            reward, judgment = self.get_reward_from_critic(processed_audio)

            # Store experience
            experience = RLExperience(
                audio_features=audio_features,
                action=action,
                reward=reward,
                next_audio_features=np.random.randn(17),  # TODO: Get from processed audio
                done=(step == max_steps - 1),
                log_prob=log_prob,
                value=value,
            )
            self.episode_buffer.append(experience)

            # Update state
            self.current_eq = new_eq_state
            current_audio = processed_audio
            episode_reward += reward

            logger.debug(f"Step {step}: reward={reward:.3f}, "
                        f"negative_concepts={judgment.get('negative_concepts', [])}")

        # Add episode to replay buffer
        self.replay_buffer.extend(self.episode_buffer)

        # Train on episode
        if len(self.replay_buffer) >= self.batch_size:
            train_stats = self._train_on_buffer()
        else:
            train_stats = {}

        # Decay exploration
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Update statistics
        self.episodes_trained += 1
        self.total_reward += episode_reward

        if episode_reward > self.best_reward:
            self.best_reward = episode_reward
            self.best_eq_state = self.current_eq

        return {
            'episode': self.episodes_trained,
            'episode_reward': episode_reward,
            'best_reward': self.best_reward,
            'epsilon': self.epsilon,
            'initial_reward': initial_reward,
            **train_stats
        }

    def _train_on_buffer(self) -> Dict[str, Any]:
        """Train policy network on replay buffer"""
        if len(self.replay_buffer) < self.batch_size:
            return {}

        # Sample batch
        batch = random.sample(self.replay_buffer, self.batch_size)

        # Prepare tensors
        audio_features = torch.FloatTensor([exp.audio_features for exp in batch])
        actions = torch.FloatTensor([exp.action for exp in batch])
        old_log_probs = torch.FloatTensor([exp.log_prob for exp in batch])
        rewards = torch.FloatTensor([exp.reward for exp in batch])
        old_values = torch.FloatTensor([exp.value for exp in batch])

        # Compute advantages using GAE
        advantages = rewards - old_values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(self.update_epochs):
            # Get current policy outputs
            action_mean, action_log_std = self.policy_network(audio_features)
            action_std = action_log_std.exp()
            dist = torch.distributions.Normal(action_mean, action_std)

            # Compute new log probs
            new_log_probs = dist.log_prob(actions).sum(dim=-1)

            # Compute ratio
            ratio = (new_log_probs - old_log_probs).exp()

            # PPO clipped objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            values = self.policy_network.get_value(audio_features).squeeze()
            value_loss = F.mse_loss(values, rewards)

            # Entropy bonus
            entropy = dist.entropy().mean()

            # Total loss
            loss = policy_loss + self.value_loss_coef * value_loss - self.entropy_coef * entropy

            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_network.parameters(), 0.5)
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy.item()

        return {
            'policy_loss': total_policy_loss / self.update_epochs,
            'value_loss': total_value_loss / self.update_epochs,
            'entropy': total_entropy / self.update_epochs,
        }

    def handle_message(self, message: Message) -> Any:
        """Handle incoming messages"""
        try:
            if message.message_type == MessageType.AUDIO_PROCESSING_REQUEST:
                audio = message.payload.get('audio')
                mode = message.payload.get('mode', 'inference')  # or 'training'

                if mode == 'training':
                    # Run training episode
                    stats = self.train_episode(audio)
                    return {
                        'status': 'success',
                        'mode': 'training',
                        'stats': stats,
                    }
                else:
                    # Inference mode - use best EQ
                    if self.best_eq_state:
                        processed_audio = self.apply_eq(audio, self.best_eq_state)
                    else:
                        processed_audio = audio

                    return {
                        'status': 'success',
                        'mode': 'inference',
                        'audio': processed_audio,
                        'eq_state': [
                            {'freq': band.center_freq, 'gain': band.gain, 'q': band.q_factor}
                            for band in (self.best_eq_state or self.current_eq).bands
                        ]
                    }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {'status': 'error', 'message': str(e)}
