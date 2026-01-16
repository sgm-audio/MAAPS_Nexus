"""
HGO (Hierarchical Goal Optimization) Coordinator

Mediates between multiple audio processing agents (EQ, Dynamics, etc.)
to optimize towards global audio quality goals while managing conflicts.

The coordinator:
1. Receives global optimization goals (e.g., "maximize clarity and punch")
2. Decomposes goals into sub-goals for each agent
3. Coordinates agent actions to avoid destructive interference
4. Resolves conflicts when agents work against each other
5. Orchestrates multi-agent training for collaborative learning
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Set
import logging
from dataclasses import dataclass, field
from enum import Enum
import torch
import torch.nn as nn
from collections import defaultdict

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.types import Message, MessageType
from src.core.audio_ontology import get_audio_ontology, AudioOntology

logger = logging.getLogger(__name__)


class GoalPriority(Enum):
    """Priority levels for optimization goals"""
    CRITICAL = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0


@dataclass
class OptimizationGoal:
    """Represents a high-level optimization goal"""
    name: str
    description: str
    target_concepts: List[str]  # Desired audio concepts
    avoid_concepts: List[str]  # Concepts to avoid
    priority: GoalPriority
    weight: float = 1.0  # 0.0 to 1.0

    # Agent-specific sub-goals
    eq_subgoals: List[str] = field(default_factory=list)
    dynamics_subgoals: List[str] = field(default_factory=list)


@dataclass
class AgentAction:
    """Represents an action proposed by an agent"""
    agent_id: str
    agent_type: str
    action_vector: np.ndarray
    predicted_reward: float
    confidence: float
    affected_concepts: List[str]  # Audio concepts this action affects


@dataclass
class ConflictResolution:
    """Resolution strategy for agent conflicts"""
    conflict_type: str
    agents_involved: List[str]
    resolution_strategy: str
    weight_adjustments: Dict[str, float]


class HGOCoordinator(BaseAgent):
    """
    Hierarchical Goal Optimization Coordinator.

    Manages multiple RL agents (EQ, Dynamics, etc.) to achieve
    global audio quality goals while minimizing destructive interference.
    """

    def __init__(self, agent_id: str, message_bus,
                 eq_agent_id: str,
                 dynamics_agent_id: str,
                 critic_agent_id: str,
                 config: Optional[Dict[str, Any]] = None):
        capabilities = [
            AgentCapability.COORDINATION,
            AgentCapability.MACHINE_LEARNING,
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="hgo_coordinator",
            capabilities=capabilities,
            message_bus=message_bus
        )

        self.config = config or {}
        self.eq_agent_id = eq_agent_id
        self.dynamics_agent_id = dynamics_agent_id
        self.critic_agent_id = critic_agent_id

        self.ontology: AudioOntology = get_audio_ontology()

        # Current optimization goals
        self.active_goals: List[OptimizationGoal] = []

        # Agent coordination state
        self.agent_weights: Dict[str, float] = {
            eq_agent_id: 0.5,
            dynamics_agent_id: 0.5,
        }

        # Conflict tracking
        self.conflict_history: List[ConflictResolution] = []
        self.cooperation_score = 1.0  # 0.0 to 1.0

        # Meta-learning for coordination
        self.coordination_network = CoordinationNetwork(
            num_agents=2,
            audio_feature_dim=17,
        )
        self.coordination_optimizer = torch.optim.Adam(
            self.coordination_network.parameters(),
            lr=1e-4
        )

        # Training mode
        self.training_mode = self.config.get('training_mode', 'cooperative')  # or 'competitive'

        # Statistics
        self.coordination_episodes = 0
        self.total_global_reward = 0.0

        logger.info(f"HGO Coordinator {agent_id} initialized")

    def set_goals(self, goals: List[OptimizationGoal]):
        """Set high-level optimization goals"""
        self.active_goals = goals
        logger.info(f"HGO Coordinator set {len(goals)} goals")

        # Decompose goals into agent-specific sub-goals
        for goal in goals:
            self._decompose_goal(goal)

    def _decompose_goal(self, goal: OptimizationGoal):
        """
        Decompose high-level goal into agent-specific sub-goals.

        Examples:
        - "Maximize clarity" -> EQ: boost high-mids, Dynamics: preserve transients
        - "Add warmth" -> EQ: boost low-mids, Dynamics: gentle compression
        - "Control dynamics" -> EQ: minimal, Dynamics: active compression
        """
        # EQ sub-goals based on target concepts
        for concept in goal.target_concepts:
            concept_obj = self.ontology.get_concept(concept)
            if concept_obj and concept_obj.eq_adjustments:
                goal.eq_subgoals.append(f"adjust_eq_for_{concept}")

        # Dynamics sub-goals
        dynamics_concepts = ['punch', 'tightness', 'control', 'dynamic', 'compressed']
        for concept in goal.target_concepts:
            if concept in dynamics_concepts:
                goal.dynamics_subgoals.append(f"adjust_dynamics_for_{concept}")

        # Avoid negative concepts
        for concept in goal.avoid_concepts:
            concept_obj = self.ontology.get_concept(concept)
            if concept_obj:
                # Both agents should work to avoid these
                goal.eq_subgoals.append(f"avoid_{concept}")
                goal.dynamics_subgoals.append(f"avoid_{concept}")

        logger.debug(f"Goal '{goal.name}' decomposed: "
                    f"EQ subgoals={goal.eq_subgoals}, "
                    f"Dynamics subgoals={goal.dynamics_subgoals}")

    def coordinate_agents(self, audio: np.ndarray,
                          training: bool = True,
                          max_steps: int = 5) -> Dict[str, Any]:
        """
        Coordinate multiple agents to optimize audio.

        Args:
            audio: Input audio to process
            training: Whether to train agents
            max_steps: Maximum coordination steps

        Returns:
            Coordination results
        """
        current_audio = audio.copy()
        episode_rewards = []

        # Get initial judgment
        initial_judgment = self._get_critic_judgment(current_audio)
        initial_reward = initial_judgment.get('satisfaction_score', 0.0)

        for step in range(max_steps):
            logger.debug(f"HGO Coordination step {step + 1}/{max_steps}")

            # Get proposed actions from each agent
            eq_action = self._get_agent_proposal(
                self.eq_agent_id,
                current_audio,
                training=training
            )

            dynamics_action = self._get_agent_proposal(
                self.dynamics_agent_id,
                current_audio,
                training=training
            )

            # Detect conflicts
            conflict = self._detect_conflict(eq_action, dynamics_action)

            if conflict:
                logger.info(f"Conflict detected: {conflict['type']}")
                # Resolve conflict
                resolution = self._resolve_conflict(conflict, eq_action, dynamics_action)
                self.conflict_history.append(resolution)

                # Adjust agent weights based on resolution
                for agent_id, weight in resolution.weight_adjustments.items():
                    self.agent_weights[agent_id] = weight

            # Determine action order and coordination
            action_order = self._determine_action_order(eq_action, dynamics_action)

            # Execute actions in coordinated manner
            for agent_id, action in action_order:
                if agent_id == self.eq_agent_id:
                    # Apply EQ
                    response = self.message_bus.request(
                        agent_id,
                        Message(
                            message_type=MessageType.AUDIO_PROCESSING_REQUEST,
                            sender_id=self.agent_id,
                            payload={
                                'audio': current_audio,
                                'mode': 'training' if training else 'inference',
                                'action': action.action_vector,
                            }
                        )
                    )

                    if response and response.get('status') == 'success':
                        current_audio = response.get('audio', current_audio)

                elif agent_id == self.dynamics_agent_id:
                    # Apply dynamics
                    response = self.message_bus.request(
                        agent_id,
                        Message(
                            message_type=MessageType.AUDIO_PROCESSING_REQUEST,
                            sender_id=self.agent_id,
                            payload={
                                'audio': current_audio,
                                'mode': 'training' if training else 'inference',
                                'action': action.action_vector,
                            }
                        )
                    )

                    if response and response.get('status') == 'success':
                        current_audio = response.get('audio', current_audio)

            # Get feedback from Critic
            judgment = self._get_critic_judgment(current_audio)
            step_reward = judgment.get('satisfaction_score', 0.0)
            episode_rewards.append(step_reward)

            # Compute cooperation bonus
            cooperation_bonus = self._compute_cooperation_bonus(judgment)
            total_step_reward = step_reward + cooperation_bonus

            # Update cooperation score
            self._update_cooperation_score(judgment)

            logger.debug(f"Step {step + 1}: reward={step_reward:.3f}, "
                        f"cooperation_bonus={cooperation_bonus:.3f}")

        # Compute final metrics
        final_judgment = self._get_critic_judgment(current_audio)
        final_reward = final_judgment.get('satisfaction_score', 0.0)

        improvement = final_reward - initial_reward
        avg_episode_reward = np.mean(episode_rewards)

        # Update statistics
        self.coordination_episodes += 1
        self.total_global_reward += final_reward

        return {
            'status': 'success',
            'processed_audio': current_audio,
            'initial_reward': initial_reward,
            'final_reward': final_reward,
            'improvement': improvement,
            'episode_rewards': episode_rewards,
            'avg_reward': avg_episode_reward,
            'cooperation_score': self.cooperation_score,
            'conflicts_detected': len([c for c in self.conflict_history
                                      if c.agents_involved]),
            'final_judgment': final_judgment,
        }

    def _get_agent_proposal(self, agent_id: str, audio: np.ndarray,
                           training: bool) -> AgentAction:
        """Get action proposal from an agent"""
        # For now, return placeholder
        # In full implementation, query agent for proposed action

        agent_type = "eq" if agent_id == self.eq_agent_id else "dynamics"

        return AgentAction(
            agent_id=agent_id,
            agent_type=agent_type,
            action_vector=np.zeros(7 if agent_type == "eq" else 10),
            predicted_reward=0.0,
            confidence=0.5,
            affected_concepts=[],
        )

    def _detect_conflict(self, action1: AgentAction, action2: AgentAction) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts between agent actions.

        Conflicts occur when:
        1. Agents work on opposing goals (e.g., EQ boosts, Dynamics compresses)
        2. Actions cancel each other out
        3. Actions reinforce negatively (e.g., both increase loudness -> clipping)
        """
        # Check for opposing concepts
        concepts1 = set(action1.affected_concepts)
        concepts2 = set(action2.affected_concepts)

        # Check if any concept in one is opposite of concept in other
        for concept1 in concepts1:
            opposites = self.ontology.get_opposite_concepts(concept1)
            for opposite in opposites:
                if opposite.name in concepts2:
                    return {
                        'type': 'opposing_goals',
                        'agents': [action1.agent_id, action2.agent_id],
                        'conflicting_concepts': [concept1, opposite.name],
                    }

        # Check for reinforcing negatives (both reducing dynamic range)
        # This is domain-specific logic
        if action1.agent_type == "eq" and action2.agent_type == "dynamics":
            # Example: heavy compression + too much EQ = artifacts
            if action2.predicted_reward < 0 and action1.predicted_reward < 0:
                return {
                    'type': 'reinforcing_negative',
                    'agents': [action1.agent_id, action2.agent_id],
                }

        return None

    def _resolve_conflict(self, conflict: Dict[str, Any],
                         action1: AgentAction,
                         action2: AgentAction) -> ConflictResolution:
        """
        Resolve conflict between agents.

        Strategies:
        1. Priority-based: Use active goals to determine which agent gets priority
        2. Sequential: Order actions to minimize interference
        3. Blending: Weight actions based on predicted rewards
        4. Negotiate: Reduce both actions' magnitudes
        """
        conflict_type = conflict['type']
        agents = conflict['agents']

        if conflict_type == 'opposing_goals':
            # Use goal priorities to decide
            # For now, balance 50/50
            return ConflictResolution(
                conflict_type=conflict_type,
                agents_involved=agents,
                resolution_strategy='balance',
                weight_adjustments={
                    agents[0]: 0.5,
                    agents[1]: 0.5,
                }
            )

        elif conflict_type == 'reinforcing_negative':
            # Reduce both actions
            return ConflictResolution(
                conflict_type=conflict_type,
                agents_involved=agents,
                resolution_strategy='reduce_both',
                weight_adjustments={
                    agents[0]: 0.3,
                    agents[1]: 0.3,
                }
            )

        else:
            # Default: no adjustment
            return ConflictResolution(
                conflict_type='unknown',
                agents_involved=agents,
                resolution_strategy='none',
                weight_adjustments={},
            )

    def _determine_action_order(self, eq_action: AgentAction,
                                dynamics_action: AgentAction) -> List[Tuple[str, AgentAction]]:
        """
        Determine optimal order for applying actions.

        Typical order: EQ first, then Dynamics (industry standard)
        But can be dynamic based on goals.
        """
        # Standard signal chain: EQ -> Dynamics
        return [
            (self.eq_agent_id, eq_action),
            (self.dynamics_agent_id, dynamics_action),
        ]

    def _get_critic_judgment(self, audio: np.ndarray) -> Dict[str, Any]:
        """Get judgment from Critic agent"""
        response = self.message_bus.request(
            self.critic_agent_id,
            Message(
                message_type=MessageType.AUDIO_ANALYSIS_REQUEST,
                sender_id=self.agent_id,
                payload={
                    'audio': audio,
                    'sample_rate': self.config.get('sample_rate', 44100),
                }
            )
        )

        if response and response.get('status') == 'success':
            return response.get('judgment', {})
        else:
            return {'satisfaction_score': 0.0}

    def _compute_cooperation_bonus(self, judgment: Dict[str, Any]) -> float:
        """
        Compute bonus reward for agent cooperation.

        Agents get bonus when they:
        - Improve multiple goals simultaneously
        - Avoid negative concepts
        - Work synergistically
        """
        positive_concepts = judgment.get('positive_concepts', [])
        negative_concepts = judgment.get('negative_concepts', [])

        # Bonus for achieving multiple positive concepts
        diversity_bonus = len(positive_concepts) * 0.05

        # Penalty for negative concepts
        negative_penalty = len(negative_concepts) * -0.1

        # Cooperation bonus based on current cooperation score
        cooperation_bonus = self.cooperation_score * 0.1

        return diversity_bonus + negative_penalty + cooperation_bonus

    def _update_cooperation_score(self, judgment: Dict[str, Any]):
        """Update cooperation score based on judgment"""
        satisfaction = judgment.get('satisfaction_score', 0.0)

        # Update cooperation score (moving average)
        alpha = 0.1
        self.cooperation_score = (1 - alpha) * self.cooperation_score + alpha * max(0, satisfaction)

    def handle_message(self, message: Message) -> Any:
        """Handle incoming messages"""
        try:
            if message.message_type == MessageType.COORDINATION_REQUEST:
                audio = message.payload.get('audio')
                training = message.payload.get('training', True)
                max_steps = message.payload.get('max_steps', 5)

                result = self.coordinate_agents(audio, training, max_steps)
                return result

            elif message.message_type == MessageType.SET_GOALS:
                goals_data = message.payload.get('goals', [])

                # Convert to OptimizationGoal objects
                goals = []
                for g in goals_data:
                    goal = OptimizationGoal(
                        name=g['name'],
                        description=g['description'],
                        target_concepts=g.get('target_concepts', []),
                        avoid_concepts=g.get('avoid_concepts', []),
                        priority=GoalPriority[g.get('priority', 'MEDIUM')],
                        weight=g.get('weight', 1.0),
                    )
                    goals.append(goal)

                self.set_goals(goals)

                return {
                    'status': 'success',
                    'message': f'Set {len(goals)} optimization goals',
                }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {'status': 'error', 'message': str(e)}


class CoordinationNetwork(nn.Module):
    """
    Neural network for learning optimal agent coordination.

    Learns to predict optimal agent weights given audio features and goals.
    """

    def __init__(self, num_agents: int = 2, audio_feature_dim: int = 17,
                 goal_dim: int = 10):
        super(CoordinationNetwork, self).__init__()

        self.num_agents = num_agents
        input_dim = audio_feature_dim + goal_dim

        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, num_agents),
            nn.Softmax(dim=-1),  # Output agent weights summing to 1
        )

    def forward(self, audio_features: torch.Tensor,
                goal_features: torch.Tensor) -> torch.Tensor:
        """
        Compute optimal agent weights.

        Returns:
            Tensor of shape (batch_size, num_agents) with agent weights
        """
        combined = torch.cat([audio_features, goal_features], dim=-1)
        weights = self.network(combined)
        return weights
