"""
Dynamics/Compression Reinforcement Learning Agent

This agent learns to adjust dynamics processing (compression, limiting)
to maximize audio quality as judged by the Critic agent. Works alongside
(and sometimes conflicts with) the EQ agent.
"""

import numpy as np
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

logger = logging.getLogger(__name__)


@dataclass
class DynamicsParameters:
    """Parameters for dynamics processing"""
    # Compressor parameters
    threshold: float = -20.0  # dB (-60 to 0)
    ratio: float = 4.0  # 1.0 to 20.0
    attack_ms: float = 10.0  # 0.1 to 100 ms
    release_ms: float = 100.0  # 10 to 1000 ms
    knee_width: float = 6.0  # 0 to 12 dB
    makeup_gain: float = 0.0  # 0 to 24 dB

    # Limiter parameters
    limiter_threshold: float = -0.3  # dB (-6 to 0)
    limiter_release: float = 50.0  # ms

    # Gate parameters (optional)
    gate_threshold: float = -60.0  # dB (-80 to 0)
    gate_enabled: bool = False

    def to_vector(self) -> np.ndarray:
        """Convert parameters to vector for RL"""
        return np.array([
            (self.threshold + 60) / 60,  # Normalize to 0-1
            (self.ratio - 1) / 19,  # Normalize to 0-1
            np.log10(self.attack_ms / 0.1) / 3,  # Log scale, normalized
            np.log10(self.release_ms / 10) / 2,  # Log scale, normalized
            self.knee_width / 12,
            self.makeup_gain / 24,
            (self.limiter_threshold + 6) / 6,
            np.log10(self.limiter_release / 10) / 2,
            float(self.gate_enabled),
            (self.gate_threshold + 80) / 80,
        ])

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> 'DynamicsParameters':
        """Create parameters from vector"""
        return cls(
            threshold=vector[0] * 60 - 60,
            ratio=vector[1] * 19 + 1,
            attack_ms=0.1 * (10 ** (vector[2] * 3)),
            release_ms=10 * (10 ** (vector[3] * 2)),
            knee_width=vector[4] * 12,
            makeup_gain=vector[5] * 24,
            limiter_threshold=vector[6] * 6 - 6,
            limiter_release=10 * (10 ** (vector[7] * 2)),
            gate_enabled=vector[8] > 0.5,
            gate_threshold=vector[9] * 80 - 80,
        )


class DynamicsPolicyNetwork(nn.Module):
    """
    Policy network for dynamics processing.

    Maps audio features to dynamics parameter adjustments.
    """

    def __init__(self, audio_feature_dim: int = 17, hidden_dim: int = 128):
        super(DynamicsPolicyNetwork, self).__init__()

        self.action_dim = 10  # All dynamics parameters

        # Encoder for audio features
        self.feature_encoder = nn.Sequential(
            nn.Linear(audio_feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )

        # Policy head
        self.policy_mean = nn.Linear(hidden_dim // 2, self.action_dim)
        self.policy_log_std = nn.Parameter(torch.zeros(self.action_dim))

        # Value head
        self.value_head = nn.Linear(hidden_dim // 2, 1)

    def forward(self, audio_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass - returns (action_mean, action_log_std)"""
        features = self.feature_encoder(audio_features)
        action_mean = torch.tanh(self.policy_mean(features))  # Bound to [-1, 1]
        action_log_std = self.policy_log_std.expand_as(action_mean)
        return action_mean, action_log_std

    def get_value(self, audio_features: torch.Tensor) -> torch.Tensor:
        """Get state value estimate"""
        features = self.feature_encoder(audio_features)
        return self.value_head(features)

    def sample_action(self, audio_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample action from policy"""
        action_mean, action_log_std = self.forward(audio_features)
        action_std = action_log_std.exp()

        normal = torch.distributions.Normal(action_mean, action_std)
        action = normal.sample()
        action = torch.clamp(action, -1.0, 1.0)

        log_prob = normal.log_prob(action).sum(dim=-1)
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


class DynamicsRLAgent(BaseAgent):
    """
    Dynamics/Compression Agent with Reinforcement Learning.

    Learns to adjust dynamics parameters to maximize Critic satisfaction.
    Works alongside EQ agent, sometimes cooperating, sometimes conflicting.
    """

    def __init__(self, agent_id: str, message_bus, critic_agent_id: str,
                 config: Optional[Dict[str, Any]] = None):
        capabilities = [
            AgentCapability.AUDIO_PROCESSING,
            AgentCapability.MACHINE_LEARNING,
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="dynamics_rl",
            capabilities=capabilities,
            message_bus=message_bus
        )

        self.config = config or {}
        self.critic_agent_id = critic_agent_id

        # Initialize dynamics parameters
        self.current_params = DynamicsParameters()

        # RL components
        self.policy_network = DynamicsPolicyNetwork()
        self.optimizer = torch.optim.Adam(self.policy_network.parameters(), lr=3e-4)

        # Experience replay
        self.replay_buffer: deque = deque(maxlen=10000)
        self.episode_buffer: List[RLExperience] = []

        # RL hyperparameters
        self.gamma = 0.99
        self.gae_lambda = 0.95
        self.clip_epsilon = 0.2
        self.value_loss_coef = 0.5
        self.entropy_coef = 0.01
        self.batch_size = 64
        self.update_epochs = 4

        # Exploration
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.1

        # Training statistics
        self.episodes_trained = 0
        self.total_reward = 0.0
        self.best_reward = -float('inf')
        self.best_params = None

        # Audio processing
        self.sample_rate = self.config.get('sample_rate', 44100)

        logger.info(f"Dynamics RL Agent {agent_id} initialized")

    def apply_dynamics(self, audio: np.ndarray, params: DynamicsParameters) -> np.ndarray:
        """
        Apply dynamics processing to audio.

        Args:
            audio: Input audio signal
            params: Dynamics parameters to apply

        Returns:
            Processed audio
        """
        output = audio.copy()

        # Apply gate if enabled
        if params.gate_enabled:
            output = self._apply_gate(output, params.gate_threshold)

        # Apply compressor
        output = self._apply_compressor(
            output,
            threshold=params.threshold,
            ratio=params.ratio,
            attack_ms=params.attack_ms,
            release_ms=params.release_ms,
            knee_width=params.knee_width,
        )

        # Apply makeup gain
        if params.makeup_gain > 0:
            gain_linear = 10 ** (params.makeup_gain / 20)
            output = output * gain_linear

        # Apply limiter
        output = self._apply_limiter(
            output,
            threshold=params.limiter_threshold,
            release_ms=params.limiter_release,
        )

        return output

    def _apply_gate(self, audio: np.ndarray, threshold_db: float) -> np.ndarray:
        """Apply noise gate"""
        threshold_linear = 10 ** (threshold_db / 20)

        # Simple gate: zero out samples below threshold
        gated = audio.copy()
        envelope = np.abs(audio)

        # Smooth envelope
        window_size = int(self.sample_rate * 0.01)  # 10ms window
        if window_size > 0:
            envelope = np.convolve(envelope, np.ones(window_size) / window_size, mode='same')

        # Apply gate
        mask = envelope > threshold_linear
        gated = gated * mask

        return gated

    def _apply_compressor(self, audio: np.ndarray, threshold: float, ratio: float,
                          attack_ms: float, release_ms: float, knee_width: float) -> np.ndarray:
        """
        Apply dynamic range compression.

        Uses a feed-forward design with smooth gain reduction.
        """
        # Convert to dB
        epsilon = 1e-10
        audio_db = 20 * np.log10(np.abs(audio) + epsilon)

        # Calculate gain reduction
        gain_reduction_db = np.zeros_like(audio_db)

        for i, sample_db in enumerate(audio_db):
            if knee_width > 0:
                # Soft knee
                if sample_db < (threshold - knee_width / 2):
                    # Below knee - no compression
                    gr = 0
                elif sample_db > (threshold + knee_width / 2):
                    # Above knee - full compression
                    gr = (threshold - sample_db) + (sample_db - threshold) / ratio
                else:
                    # In knee - smooth transition
                    knee_factor = (sample_db - threshold + knee_width / 2) / knee_width
                    gr = knee_factor * (sample_db - threshold) * (1 - 1 / ratio)
            else:
                # Hard knee
                if sample_db > threshold:
                    gr = (threshold - sample_db) + (sample_db - threshold) / ratio
                else:
                    gr = 0

            gain_reduction_db[i] = gr

        # Apply attack and release smoothing
        attack_samples = int(attack_ms * self.sample_rate / 1000)
        release_samples = int(release_ms * self.sample_rate / 1000)

        smoothed_gr = gain_reduction_db.copy()
        for i in range(1, len(smoothed_gr)):
            if gain_reduction_db[i] < smoothed_gr[i - 1]:
                # Attack (gain reduction increasing)
                alpha = 1.0 / attack_samples if attack_samples > 0 else 1.0
            else:
                # Release (gain reduction decreasing)
                alpha = 1.0 / release_samples if release_samples > 0 else 1.0

            smoothed_gr[i] = alpha * gain_reduction_db[i] + (1 - alpha) * smoothed_gr[i - 1]

        # Apply gain reduction
        gain_linear = 10 ** (smoothed_gr / 20)
        compressed = audio * gain_linear

        return compressed

    def _apply_limiter(self, audio: np.ndarray, threshold: float,
                      release_ms: float) -> np.ndarray:
        """
        Apply peak limiter.

        Fast attack, controlled release.
        """
        threshold_linear = 10 ** (threshold / 20)

        # Fast peak detection
        envelope = np.abs(audio)

        # Calculate gain reduction
        gain_reduction = np.ones_like(audio)
        for i, peak in enumerate(envelope):
            if peak > threshold_linear:
                gain_reduction[i] = threshold_linear / (peak + 1e-10)

        # Apply release smoothing
        release_samples = int(release_ms * self.sample_rate / 1000)
        smoothed_gain = gain_reduction.copy()

        for i in range(1, len(smoothed_gain)):
            # Fast attack (instant), slow release
            if gain_reduction[i] < smoothed_gain[i - 1]:
                # Attack - instant
                smoothed_gain[i] = gain_reduction[i]
            else:
                # Release - smooth
                alpha = 1.0 / release_samples if release_samples > 0 else 1.0
                smoothed_gain[i] = alpha * gain_reduction[i] + (1 - alpha) * smoothed_gain[i - 1]

        # Apply limiting
        limited = audio * smoothed_gain

        return limited

    def get_reward_from_critic(self, audio: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Get reward from Critic agent"""
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
        """Select dynamics adjustment action using policy network"""
        if explore and random.random() < self.epsilon:
            # Random exploration
            action = np.random.uniform(-1, 1, size=10)
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

    def action_to_param_adjustments(self, action: np.ndarray) -> DynamicsParameters:
        """
        Convert RL action to dynamics parameter adjustments.

        Args:
            action: Action vector from policy (-1 to 1)

        Returns:
            New dynamics parameters
        """
        # Get current parameters as vector
        current_vector = self.current_params.to_vector()

        # Apply action as delta (scaled)
        adjustment_scale = 0.1  # Max 10% change per step
        new_vector = current_vector + (action * adjustment_scale)

        # Clip to valid range [0, 1]
        new_vector = np.clip(new_vector, 0, 1)

        # Convert back to parameters
        return DynamicsParameters.from_vector(new_vector)

    def train_episode(self, audio: np.ndarray, max_steps: int = 10) -> Dict[str, Any]:
        """Run one training episode"""
        self.episode_buffer = []
        episode_reward = 0.0

        # Get initial judgment
        initial_reward, _ = self.get_reward_from_critic(audio)

        current_audio = audio.copy()

        for step in range(max_steps):
            # Get audio features (placeholder)
            audio_features = np.random.randn(17)  # TODO: Get from Critic

            # Select action
            action, log_prob, value = self.select_action(audio_features, explore=True)

            # Convert action to parameter adjustments
            new_params = self.action_to_param_adjustments(action)

            # Apply dynamics processing
            processed_audio = self.apply_dynamics(current_audio, new_params)

            # Get reward from Critic
            reward, judgment = self.get_reward_from_critic(processed_audio)

            # Store experience
            experience = RLExperience(
                audio_features=audio_features,
                action=action,
                reward=reward,
                next_audio_features=np.random.randn(17),
                done=(step == max_steps - 1),
                log_prob=log_prob,
                value=value,
            )
            self.episode_buffer.append(experience)

            # Update state
            self.current_params = new_params
            current_audio = processed_audio
            episode_reward += reward

            logger.debug(f"Dynamics step {step}: reward={reward:.3f}")

        # Add to replay buffer
        self.replay_buffer.extend(self.episode_buffer)

        # Train on buffer
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
            self.best_params = self.current_params

        return {
            'episode': self.episodes_trained,
            'episode_reward': episode_reward,
            'best_reward': self.best_reward,
            'epsilon': self.epsilon,
            'initial_reward': initial_reward,
            **train_stats
        }

    def _train_on_buffer(self) -> Dict[str, Any]:
        """Train policy network on replay buffer (PPO)"""
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

        # Compute advantages
        advantages = rewards - old_values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(self.update_epochs):
            action_mean, action_log_std = self.policy_network(audio_features)
            action_std = action_log_std.exp()
            dist = torch.distributions.Normal(action_mean, action_std)

            new_log_probs = dist.log_prob(actions).sum(dim=-1)
            ratio = (new_log_probs - old_log_probs).exp()

            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            values = self.policy_network.get_value(audio_features).squeeze()
            value_loss = F.mse_loss(values, rewards)

            entropy = dist.entropy().mean()

            loss = policy_loss + self.value_loss_coef * value_loss - self.entropy_coef * entropy

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
                mode = message.payload.get('mode', 'inference')

                if mode == 'training':
                    stats = self.train_episode(audio)
                    return {
                        'status': 'success',
                        'mode': 'training',
                        'stats': stats,
                    }
                else:
                    # Inference mode
                    if self.best_params:
                        processed_audio = self.apply_dynamics(audio, self.best_params)
                        params_dict = {
                            'threshold': self.best_params.threshold,
                            'ratio': self.best_params.ratio,
                            'attack_ms': self.best_params.attack_ms,
                            'release_ms': self.best_params.release_ms,
                            'makeup_gain': self.best_params.makeup_gain,
                        }
                    else:
                        processed_audio = audio
                        params_dict = {}

                    return {
                        'status': 'success',
                        'mode': 'inference',
                        'audio': processed_audio,
                        'params': params_dict,
                    }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {'status': 'error', 'message': str(e)}
