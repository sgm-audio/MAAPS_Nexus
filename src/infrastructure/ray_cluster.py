"""
Ray Cluster Infrastructure for Multi-Agent Audio System

This module provides Ray cluster management for distributed agent execution,
including single-machine and multi-node cluster support.
"""

import os
import ray
from ray import serve
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
import psutil

logger = logging.getLogger(__name__)


@dataclass
class RayClusterConfig:
    """Configuration for Ray cluster setup"""
    num_cpus: Optional[int] = None  # Auto-detect if None
    num_gpus: Optional[int] = 0
    memory: Optional[int] = None  # MB, auto-detect if None
    object_store_memory: Optional[int] = None  # MB
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8265
    include_dashboard: bool = True
    log_to_driver: bool = True
    namespace: str = "maaps_nexus"
    _temp_dir: Optional[str] = None


class RayClusterManager:
    """
    Manages Ray cluster lifecycle for MAAPS Nexus multi-agent system.

    Supports:
    - Single-machine clusters for development
    - Multi-node clusters for production
    - Resource management and monitoring
    - Actor and task deployment
    """

    def __init__(self, config: Optional[RayClusterConfig] = None):
        self.config = config or RayClusterConfig()
        self._initialized = False
        self._cluster_resources: Dict[str, Any] = {}

    def initialize_cluster(self, head_node: bool = True) -> bool:
        """
        Initialize Ray cluster (single-machine or head node).

        Args:
            head_node: If True, start as head node (default for single-machine)

        Returns:
            True if initialization successful
        """
        try:
            if ray.is_initialized():
                logger.warning("Ray already initialized, shutting down first")
                ray.shutdown()

            # Auto-detect resources if not specified
            if self.config.num_cpus is None:
                self.config.num_cpus = psutil.cpu_count(logical=True)

            if self.config.memory is None:
                # Use 80% of available memory
                total_memory_mb = psutil.virtual_memory().total // (1024 * 1024)
                self.config.memory = int(total_memory_mb * 0.8)

            if self.config.object_store_memory is None:
                # Use 30% of total memory for object store
                self.config.object_store_memory = int(self.config.memory * 0.3)

            init_kwargs = {
                "num_cpus": self.config.num_cpus,
                "num_gpus": self.config.num_gpus,
                "memory": self.config.memory * 1024 * 1024,  # Convert to bytes
                "object_store_memory": self.config.object_store_memory * 1024 * 1024,
                "include_dashboard": self.config.include_dashboard,
                "dashboard_host": self.config.dashboard_host,
                "dashboard_port": self.config.dashboard_port,
                "log_to_driver": self.config.log_to_driver,
                "namespace": self.config.namespace,
                "ignore_reinit_error": True,
            }

            if self.config._temp_dir:
                init_kwargs["_temp_dir"] = self.config._temp_dir

            # Initialize Ray
            ray.init(**init_kwargs)

            self._initialized = True
            self._cluster_resources = ray.cluster_resources()

            logger.info(f"Ray cluster initialized successfully")
            logger.info(f"Available resources: {self._cluster_resources}")
            logger.info(f"Dashboard: http://{self.config.dashboard_host}:{self.config.dashboard_port}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Ray cluster: {e}")
            return False

    def connect_to_cluster(self, address: str) -> bool:
        """
        Connect to existing Ray cluster as worker node.

        Args:
            address: Address of the head node (e.g., "ray://192.168.1.100:10001")

        Returns:
            True if connection successful
        """
        try:
            if ray.is_initialized():
                logger.warning("Ray already initialized, shutting down first")
                ray.shutdown()

            ray.init(
                address=address,
                namespace=self.config.namespace,
                log_to_driver=self.config.log_to_driver,
            )

            self._initialized = True
            self._cluster_resources = ray.cluster_resources()

            logger.info(f"Connected to Ray cluster at {address}")
            logger.info(f"Available resources: {self._cluster_resources}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Ray cluster: {e}")
            return False

    def shutdown_cluster(self):
        """Shutdown Ray cluster gracefully"""
        if self._initialized:
            try:
                ray.shutdown()
                self._initialized = False
                logger.info("Ray cluster shutdown successfully")
            except Exception as e:
                logger.error(f"Error during cluster shutdown: {e}")

    def get_cluster_resources(self) -> Dict[str, Any]:
        """Get current cluster resources"""
        if not self._initialized:
            return {}
        return ray.cluster_resources()

    def get_available_resources(self) -> Dict[str, Any]:
        """Get currently available (not allocated) resources"""
        if not self._initialized:
            return {}
        return ray.available_resources()

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status"""
        if not self._initialized:
            return {"status": "not_initialized"}

        return {
            "status": "running",
            "total_resources": ray.cluster_resources(),
            "available_resources": ray.available_resources(),
            "nodes": ray.nodes(),
            "namespace": self.config.namespace,
            "dashboard_url": f"http://{self.config.dashboard_host}:{self.config.dashboard_port}",
        }

    def is_initialized(self) -> bool:
        """Check if cluster is initialized"""
        return self._initialized and ray.is_initialized()


@ray.remote
class RayAgent:
    """
    Base Ray Actor for distributed agent execution.

    This wraps MAAPS agents for distributed execution in Ray cluster.
    """

    def __init__(self, agent_class, *args, **kwargs):
        """
        Initialize Ray agent actor.

        Args:
            agent_class: The agent class to instantiate
            *args, **kwargs: Arguments for agent initialization
        """
        self.agent = agent_class(*args, **kwargs)
        self.agent_id = kwargs.get('agent_id', 'unknown')

    def start(self):
        """Start the agent"""
        return self.agent.start()

    def stop(self):
        """Stop the agent"""
        return self.agent.stop()

    def process_message(self, message: Dict[str, Any]) -> Any:
        """Process a message through the agent"""
        return self.agent.handle_message(message)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "status": getattr(self.agent, 'status', 'unknown'),
            "metrics": getattr(self.agent, 'get_metrics', lambda: {})(),
        }


class DistributedAgentPool:
    """
    Pool of distributed agents running as Ray actors.

    Provides load balancing and fault tolerance for agent execution.
    """

    def __init__(self, cluster_manager: RayClusterManager):
        self.cluster_manager = cluster_manager
        self.agents: Dict[str, List] = {}  # agent_type -> [actor_refs]

    def create_agent_pool(
        self,
        agent_class,
        agent_type: str,
        num_replicas: int = 2,
        num_cpus: float = 1.0,
        num_gpus: float = 0.0,
        **agent_kwargs
    ) -> bool:
        """
        Create a pool of agent actors for load balancing.

        Args:
            agent_class: The agent class to replicate
            agent_type: Type identifier for the agent
            num_replicas: Number of replicas to create
            num_cpus: CPUs per replica
            num_gpus: GPUs per replica
            **agent_kwargs: Arguments for agent initialization

        Returns:
            True if pool created successfully
        """
        try:
            if not self.cluster_manager.is_initialized():
                logger.error("Cluster not initialized")
                return False

            actors = []
            for i in range(num_replicas):
                agent_id = f"{agent_type}_replica_{i}"
                actor = RayAgent.options(
                    num_cpus=num_cpus,
                    num_gpus=num_gpus,
                    name=agent_id,
                ).remote(agent_class, agent_id=agent_id, **agent_kwargs)
                actors.append(actor)

                # Start the agent
                ray.get(actor.start.remote())

            self.agents[agent_type] = actors
            logger.info(f"Created agent pool '{agent_type}' with {num_replicas} replicas")

            return True

        except Exception as e:
            logger.error(f"Failed to create agent pool: {e}")
            return False

    def submit_task(self, agent_type: str, message: Dict[str, Any]) -> Any:
        """
        Submit task to agent pool (round-robin load balancing).

        Args:
            agent_type: Type of agent to submit to
            message: Message/task to process

        Returns:
            Result from agent processing
        """
        if agent_type not in self.agents or not self.agents[agent_type]:
            raise ValueError(f"No agents available for type: {agent_type}")

        # Simple round-robin (Ray handles load balancing internally for actors)
        actor = self.agents[agent_type][0]  # Ray will distribute automatically

        return ray.get(actor.process_message.remote(message))

    def get_pool_status(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get status of all agents in pool"""
        if agent_type not in self.agents:
            return []

        status_futures = [actor.get_status.remote() for actor in self.agents[agent_type]]
        return ray.get(status_futures)

    def shutdown_pool(self, agent_type: str):
        """Shutdown specific agent pool"""
        if agent_type in self.agents:
            for actor in self.agents[agent_type]:
                ray.get(actor.stop.remote())
                ray.kill(actor)
            del self.agents[agent_type]
            logger.info(f"Shutdown agent pool: {agent_type}")

    def shutdown_all_pools(self):
        """Shutdown all agent pools"""
        for agent_type in list(self.agents.keys()):
            self.shutdown_pool(agent_type)


# Global cluster manager instance
_cluster_manager: Optional[RayClusterManager] = None


def get_cluster_manager(config: Optional[RayClusterConfig] = None) -> RayClusterManager:
    """Get or create global cluster manager instance"""
    global _cluster_manager
    if _cluster_manager is None:
        _cluster_manager = RayClusterManager(config)
    return _cluster_manager


def initialize_ray_cluster(config: Optional[RayClusterConfig] = None) -> RayClusterManager:
    """
    Initialize Ray cluster for MAAPS Nexus.

    This is the main entry point for setting up distributed execution.

    Args:
        config: Optional cluster configuration

    Returns:
        Initialized cluster manager

    Example:
        >>> config = RayClusterConfig(num_cpus=8, num_gpus=1)
        >>> cluster = initialize_ray_cluster(config)
        >>> cluster.get_cluster_status()
    """
    cluster_manager = get_cluster_manager(config)
    cluster_manager.initialize_cluster()
    return cluster_manager
