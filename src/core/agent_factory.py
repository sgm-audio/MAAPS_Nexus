"""
Agent Factory

Implements the Factory Pattern for creating system agents.
Decouples agent creation logic from the coordinator.
"""

from typing import Dict, Type, Any, Optional

from .base_agent import BaseAgent
from ..agents.audio_enhancement_agent import AudioEnhancementAgent
from ..agents.content_generation_agent import ContentGenerationAgent
from ..agents.performance_optimization_agent import PerformanceOptimizationAgent
from ..agents.metadata_management_agent import MetadataManagementAgent
from ..orchestration.workflow_engine import WorkflowEngine


class AgentFactory:
    """Factory for creating system agents"""

    _agent_registry: Dict[str, Type[BaseAgent]] = {
        "audio_enhancement": AudioEnhancementAgent,
        "content_generation": ContentGenerationAgent,
        "performance_optimization": PerformanceOptimizationAgent,
        "metadata_management": MetadataManagementAgent,
        "workflow_engine": WorkflowEngine
    }

    @classmethod
    def create_agent(cls, agent_type: str, **kwargs: Any) -> BaseAgent:
        """
        Create an agent instance of the specified type.

        Args:
            agent_type: Type of agent to create (key in _agent_registry)
            **kwargs: Arguments to pass to the agent constructor

        Returns:
            New instance of the requested agent

        Raises:
            ValueError: If agent_type is unknown
        """
        agent_class = cls._agent_registry.get(agent_type)
        if not agent_class:
            valid_types = ", ".join(cls._agent_registry.keys())
            raise ValueError(f"Unknown agent type: '{agent_type}'. Valid types: {valid_types}")

        return agent_class(**kwargs)

    @classmethod
    def register_agent_type(cls, type_name: str, agent_class: Type[BaseAgent]):
        """
        Register a new agent type dynamically.
        Useful for plugins or extensions.
        """
        cls._agent_registry[type_name] = agent_class
