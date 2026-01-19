"""
Tests for HGO Coordinator
"""

import unittest
import ray
import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.hgo_coordinator import HGOCoordinator, AgentProposal, ConflictType
from src.core.audio_ontology import (
    AudioState,
    AudioAttribute,
    AgentAction,
    create_clarity_goal,
    create_warmth_goal
)

class TestHGOCoordinator(unittest.TestCase):
    """Test suite for HGO Coordinator"""

    def setUp(self):
        """Set up coordinator for each test"""
        self.goals = [
            create_clarity_goal(target=0.8, priority=1.0),
            create_warmth_goal(target=0.7, priority=0.8),
        ]
        self.coordinator = HGOCoordinator.remote(goal_hierarchy=self.goals)

    def test_initialization(self):
        """Test coordinator initialization"""
        stats = ray.get(self.coordinator.get_statistics.remote())
        self.assertEqual(stats['registered_agents'], 0)
        self.assertEqual(stats['total_coordinations'], 0)

    def test_agent_registration(self):
        """Test agent registration"""
        ray.get(self.coordinator.register_agent.remote("test_agent", None, priority=0.8))
        stats = ray.get(self.coordinator.get_statistics.remote())
        self.assertEqual(stats['registered_agents'], 1)
        
        agent_info = ray.get(self.coordinator.get_agent_performance.remote("test_agent"))
        self.assertEqual(agent_info['agent_id'], "test_agent")
        self.assertEqual(agent_info['priority'], 0.8)

    def test_conflict_detection_no_conflict(self):
        """Test detection when there are no conflicts"""
        current_state = AudioState()
        
        prop1 = AgentProposal(
            agent_id="agent1",
            action=AgentAction(agent_id="agent1", action_type="eq", parameters={}),
            predicted_impact={AudioAttribute.CLARITY: 0.1},
            predicted_satisfaction=0.6,
            confidence=0.9
        )
        
        prop2 = AgentProposal(
            agent_id="agent2",
            action=AgentAction(agent_id="agent2", action_type="comp", parameters={}),
            predicted_impact={AudioAttribute.PUNCH: 0.1},
            predicted_satisfaction=0.6,
            confidence=0.9
        )
        
        decision = ray.get(self.coordinator.coordinate.remote([prop1, prop2], current_state))
        
        self.assertEqual(len(decision.approved_proposals), 2)
        self.assertEqual(len(decision.rejected_proposals), 0)
        self.assertEqual(len(decision.compromise_adjustments), 0)

    def test_conflict_detection_with_conflict(self):
        """Test detection of direct conflicts"""
        current_state = AudioState()
        
        # Agent 1 wants more Clarity (High Freq Boost)
        prop1 = AgentProposal(
            agent_id="agent1",
            action=AgentAction(agent_id="agent1", action_type="eq", parameters={}),
            predicted_impact={AudioAttribute.CLARITY: 0.3},
            predicted_satisfaction=0.7,
            confidence=0.9
        )
        
        # Agent 2 reduces Clarity (e.g., Low Pass Filter or Mud increase)
        # Or specifically opposing attribute
        prop2 = AgentProposal(
            agent_id="agent2",
            action=AgentAction(agent_id="agent2", action_type="comp", parameters={}),
            predicted_impact={AudioAttribute.CLARITY: -0.3},
            predicted_satisfaction=0.6,
            confidence=0.9
        )
        
        decision = ray.get(self.coordinator.coordinate.remote([prop1, prop2], current_state))
        
        # Should detect conflict and likely approve agent1 because Clarity has higher priority (1.0)
        # Agent 2 might be rejected or compromised
        
        self.assertTrue(len(decision.approved_proposals) > 0)
        
        # Check that we caught a conflict
        stats = ray.get(self.coordinator.get_statistics.remote())
        self.assertGreater(stats['total_conflicts'], 0)

    def test_execution_ordering(self):
        """Test execution order logic (EQ before Dynamics)"""
        current_state = AudioState()
        
        prop_eq = AgentProposal(
            agent_id="eq_agent",
            action=AgentAction(agent_id="eq_agent", action_type="eq", parameters={}),
            predicted_impact={AudioAttribute.CLARITY: 0.1},
            predicted_satisfaction=0.7,
            confidence=0.9
        )
        
        prop_dyn = AgentProposal(
            agent_id="dynamics_agent",
            action=AgentAction(agent_id="dynamics_agent", action_type="comp", parameters={}),
            predicted_impact={AudioAttribute.PUNCH: 0.1},
            predicted_satisfaction=0.7,
            confidence=0.9
        )
        
        decision = ray.get(self.coordinator.coordinate.remote([prop_dyn, prop_eq], current_state))
        
        # Should reorder EQ first
        self.assertEqual(decision.execution_order[0], "eq_agent")
        self.assertEqual(decision.execution_order[1], "dynamics_agent")

if __name__ == '__main__':
    unittest.main()
