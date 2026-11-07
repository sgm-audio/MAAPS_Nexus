"""
Agent Coordinator for managing agent lifecycle and interactions.

Provides centralized agent management, health monitoring,
and coordination services.
"""

import threading
import time
from typing import Dict, List, Optional
import logging

from ..core import (
    BaseAgent,
    get_agent_registry,
    get_message_bus,
    AgentState,
)
from ..core.agent_factory import AgentFactory
from ..agents.live import (
    RealtimeAudioIOAgent,
    LiveEffectsChainAgent,
    LiveLoopingAgent,
    SynchronizationClockAgent,
    PerformanceAutomationAgent,
)
from ..agents.audio_enhancement_agent import AudioEnhancementAgent
from ..agents.content_generation_agent import ContentGenerationAgent
from ..agents.performance_optimization_agent import PerformanceOptimizationAgent
from ..agents.metadata_management_agent import MetadataManagementAgent
from .workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Central coordinator for managing all agents in the system.

    Responsibilities:
    - Agent lifecycle management
    - Health monitoring
    - Dependency resolution
    - System-wide coordination
    """

    def __init__(self):
        self.registry = get_agent_registry()
        self.message_bus = get_message_bus()

        # Registered agents
        self.agents: Dict[str, BaseAgent] = {}
        self.lock = threading.Lock()

        # Live agent redundancy mapping (primary -> standby)
        self.live_redundancy_pairs: Dict[str, str] = {}
        self.promoted_live_agents: set[str] = set()

        # Health monitoring
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.monitoring_interval = 5.0  # seconds

        # System statistics
        self.stats = {
            "system_start_time": None,
            "total_messages_processed": 0,
            "total_agent_errors": 0,
            "agents_started": 0,
            "agents_stopped": 0,
        }

    def initialize_system(self):
        """Initialize the complete agent system"""
        logger.info("Initializing multi-agent system...")

        try:
            # Create and register all agents
            self._create_core_agents()

            # Start message bus
            if not self.message_bus._running:
                self.message_bus.start()

            # Subscribe to agent status updates (Observer Pattern)
            self.message_bus.subscribe(
                "system.agent.status", "coordinator", self._on_agent_status_changed
            )

            # Start all agents
            self.start_all_agents()

            # Start health monitoring (Watchdog)
            self._start_health_monitoring()

            self.stats["system_start_time"] = time.time()

            logger.info("Multi-agent system initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            raise

    def _on_agent_status_changed(self, message):
        """
        Handle agent status change events (Reactive Health Monitoring).
        """
        payload = message.payload
        agent_id = payload.get("agent_id")
        new_state = payload.get("new_state")
        old_state = payload.get("old_state")

        logger.info(
            f"Coordinator received status change for {agent_id}: {old_state} -> {new_state}"
        )

        if new_state == "error":
            logger.warning(
                f"Agent {agent_id} reported ERROR state. Initiating recovery..."
            )
            self.stats["total_agent_errors"] += 1
            # Reactive recovery
            threading.Thread(
                target=self.restart_agent, args=(agent_id,), daemon=True
            ).start()

        elif new_state == "stopped" and self.monitoring_active:
            # Check if this stop was intentional (initiated by coordinator) or unexpected
            # For now, we assume if the system is running, agents shouldn't stop unless asked.
            # In a real implementation, we'd check a 'desired_state' flag.
            pass

    def shutdown_system(self):
        """Shutdown the complete agent system"""
        logger.info("Shutting down multi-agent system...")

        try:
            # Stop health monitoring
            self._stop_health_monitoring()

            # Stop all agents
            self.stop_all_agents()

            # Unregister agents from registry
            with self.lock:
                for agent_id in list(self.agents.keys()):
                    self.registry.unregister(agent_id)
                self.agents.clear()

            # Stop message bus
            if self.message_bus._running:
                self.message_bus.stop()

            logger.info("Multi-agent system shutdown complete")

        except Exception as e:
            logger.error(f"Error shutting down system: {e}")
            raise

    def _create_core_agents(self):
        """Create and register core system agents"""
        # Create agents
        agents_to_create = [
            AudioEnhancementAgent(),
            ContentGenerationAgent(),
            PerformanceOptimizationAgent(),
            MetadataManagementAgent(),
            PerformanceAutomationAgent(),
            WorkflowEngine(),
        ]

        # Add live performance agents with redundancy
        agents_to_create.extend(self._create_live_agents())

        with self.lock:
            for agent in agents_to_create:
                try:
                    self.agents[agent.agent_id] = agent
                    self.registry.register(agent)
                    logger.info(
                        f"Registered agent: {agent.agent_id} (type: {agent.agent_type})"
                    )
                except ValueError as e:
                    logger.error(f"Failed to register agent {agent.agent_id}: {e}")
                    raise

    def _create_live_agents(self) -> List[BaseAgent]:
        """Create primary/standby instances for live performance agents"""
        # Primary agents keep legacy IDs for compatibility
        live_agents = [
            (
                RealtimeAudioIOAgent(agent_id="realtime_audio_io_agent", active=True),
                RealtimeAudioIOAgent(
                    agent_id="realtime_audio_io_agent_standby", active=False
                ),
            ),
            (
                LiveEffectsChainAgent(agent_id="live_effects_chain_agent", active=True),
                LiveEffectsChainAgent(
                    agent_id="live_effects_chain_agent_standby", active=False
                ),
            ),
            (
                LiveLoopingAgent(agent_id="live_looping_agent", active=True),
                LiveLoopingAgent(agent_id="live_looping_agent_standby", active=False),
            ),
            (
                SynchronizationClockAgent(
                    agent_id="synchronization_clock_agent", active=True
                ),
                SynchronizationClockAgent(
                    agent_id="synchronization_clock_agent_standby", active=False
                ),
            ),
        ]

        # Track primary->standby mapping for failover
        self.live_redundancy_pairs = {
            primary.agent_id: standby.agent_id for primary, standby in live_agents
        }
        self.promoted_live_agents.clear()

        # Flatten list for registration
        flattened = []
        for primary, standby in live_agents:
            flattened.extend([primary, standby])
        return flattened

    def start_all_agents(self):
        """Start all registered agents"""
        with self.lock:
            for agent_id, agent in self.agents.items():
                try:
                    agent.start()
                    self.stats["agents_started"] += 1
                    logger.info(f"Started agent: {agent_id}")
                except Exception as e:
                    logger.error(f"Error starting agent {agent_id}: {e}")

    def stop_all_agents(self):
        """Stop all registered agents"""
        with self.lock:
            for agent_id, agent in self.agents.items():
                try:
                    agent.stop()
                    # Unregister from global registry
                    self.registry.unregister(agent_id)
                    self.stats["agents_stopped"] += 1
                    logger.info(f"Stopped agent: {agent_id}")
                except Exception as e:
                    logger.error(f"Error stopping agent {agent_id}: {e}")

    def start_agent(self, agent_id: str) -> bool:
        """Start a specific agent"""
        with self.lock:
            agent = self.agents.get(agent_id)

            if agent:
                try:
                    agent.start()
                    logger.info(f"Started agent: {agent_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error starting agent {agent_id}: {e}")
                    return False
            else:
                logger.error(f"Agent {agent_id} not found")
                return False

    def stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent"""
        with self.lock:
            agent = self.agents.get(agent_id)

            if agent:
                try:
                    agent.stop()
                    logger.info(f"Stopped agent: {agent_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error stopping agent {agent_id}: {e}")
                    return False
            else:
                logger.error(f"Agent {agent_id} not found")
                return False

    def restart_agent(self, agent_id: str) -> bool:
        """Restart a specific agent"""
        if self.stop_agent(agent_id):
            time.sleep(0.5)  # Brief pause
            return self.start_agent(agent_id)
        return False

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get status of a specific agent"""
        with self.lock:
            agent = self.agents.get(agent_id)

            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "state": agent.get_state().value,
                    "metrics": agent.get_metrics(),
                    "active": getattr(agent, "active", True),
                }
            else:
                return None

    def get_all_agent_statuses(self) -> List[Dict]:
        """Get status of all agents"""
        statuses = []

        with self.lock:
            # Avoid nested locking by building the status objects directly
            for agent in self.agents.values():
                statuses.append(
                    {
                        "agent_id": agent.agent_id,
                        "agent_name": agent.agent_name,
                        "state": agent.get_state().value,
                        "metrics": agent.get_metrics(),
                        "active": getattr(agent, "active", True),
                    }
                )

        return statuses

    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        statuses = self.get_all_agent_statuses()

        healthy_agents = sum(1 for s in statuses if s["state"] == "running")
        total_agents = len(statuses)

        # Calculate overall health score
        health_score = (healthy_agents / total_agents * 100) if total_agents > 0 else 0

        # Get message bus metrics
        bus_metrics = self.message_bus.get_metrics()

        return {
            "health_score": health_score,
            "agents_total": total_agents,
            "agents_healthy": healthy_agents,
            "agents_error": sum(1 for s in statuses if s["state"] == "error"),
            "system_uptime_seconds": (
                time.time() - self.stats["system_start_time"]
                if self.stats["system_start_time"]
                else 0
            ),
            "message_bus_metrics": bus_metrics,
            "system_stats": self.stats,
        }

    def _start_health_monitoring(self):
        """Start health monitoring thread"""
        self.monitoring_active = True
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitoring_loop, name="health_monitor", daemon=True
        )
        self.health_monitor_thread.start()
        logger.info("Health monitoring started")

    def _stop_health_monitoring(self):
        """Stop health monitoring thread"""
        self.monitoring_active = False
        if self.health_monitor_thread and self.health_monitor_thread.is_alive():
            self.health_monitor_thread.join(timeout=2.0)
        logger.info("Health monitoring stopped")

    def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_active:
            try:
                # Check health of all agents
                statuses = self.get_all_agent_statuses()

                for status in statuses:
                    agent_id = status["agent_id"]
                    state = status["state"]

                    # Check for error state
                    if state == "error":
                        logger.warning(f"Agent {agent_id} is in error state")
                        self.stats["total_agent_errors"] += 1

                        # Attempt restart
                        logger.info(f"Attempting to restart agent {agent_id}")
                        self.restart_agent(agent_id)

                    # Check for stopped state (unexpected)
                    elif state == "stopped":
                        logger.warning(f"Agent {agent_id} unexpectedly stopped")

                        # Attempt restart
                        logger.info(f"Attempting to restart agent {agent_id}")
                        self.restart_agent(agent_id)

                # Promote standby live agents if primaries are unhealthy
                self._check_live_redundancy(statuses)

                # Update message processing stats
                bus_metrics = self.message_bus.get_metrics()
                self.stats["total_messages_processed"] = bus_metrics.get(
                    "messages_delivered", 0
                )

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _check_live_redundancy(self, statuses: List[Dict]):
        """Promote standby live agents when primaries fail"""
        if not self.live_redundancy_pairs:
            return

        status_map = {s["agent_id"]: s for s in statuses}

        for primary_id, standby_id in self.live_redundancy_pairs.items():
            primary_status = status_map.get(primary_id)

            # Healthy primary -> no action
            if primary_status and primary_status["state"] == "running":
                continue

            standby_status = status_map.get(standby_id)
            standby_agent = self.agents.get(standby_id)

            if (
                standby_agent
                and standby_status
                and standby_status["state"] == "running"
            ):
                if getattr(standby_agent, "active", True):
                    # Already promoted
                    continue

                standby_agent.set_active(True)
                self.promoted_live_agents.add(standby_id)
                logger.warning(
                    f"Promoted standby live agent {standby_id} to active role "
                    f"after primary {primary_id} became unavailable"
                )
            elif (
                standby_agent
                and standby_status
                and standby_status["state"] != "running"
            ):
                # Attempt to bring standby online if it's not running
                logger.warning(
                    f"Standby live agent {standby_id} not running; attempting restart"
                )
                self.restart_agent(standby_id)


# Global coordinator instance
_coordinator: Optional[AgentCoordinator] = None
_coordinator_lock = threading.Lock()


def get_coordinator() -> AgentCoordinator:
    """Get the global agent coordinator instance (singleton)"""
    global _coordinator

    if _coordinator is None:
        with _coordinator_lock:
            if _coordinator is None:
                _coordinator = AgentCoordinator()

    return _coordinator
