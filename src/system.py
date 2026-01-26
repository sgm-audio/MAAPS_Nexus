"""
Main System Entry Point

Provides easy access to the complete multi-agent system.
"""

import logging
import time
from typing import Optional, Dict, Any, Union, List

from .core import get_message_bus, get_agent_registry
from .core.message_types import Topics, Timeouts
from .orchestration import get_coordinator, WorkflowEngine, create_audio_enhancement_workflow, create_music_production_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def requires_init(func):
    """Decorator to ensure system is initialized before calling methods."""
    def wrapper(self, *args, **kwargs):
        if not getattr(self, 'initialized', False):
            raise RuntimeError(f"System not initialized. Call .start() before {func.__name__}")
        return func(self, *args, **kwargs)
    return wrapper


class MultiAgentSystem:
    """
    Main entry point for the multi-agent audio processing system.

    Provides high-level interface for system management and workflow execution.
    """

    def __init__(self):
        self.coordinator = get_coordinator()
        self.message_bus = get_message_bus()
        self.registry = get_agent_registry()

        self.initialized = False
        self.workflow_engine: Optional[WorkflowEngine] = None

    def start(self):
        """Start the multi-agent system"""
        if self.initialized:
            logger.warning("System already initialized")
            return

        logger.info("Starting multi-agent audio processing system...")

        try:
            # Initialize the system
            self.coordinator.initialize_system()

            # Get workflow engine reference
            self.workflow_engine = self.coordinator.agents.get('workflow_engine')

            self.initialized = True

            logger.info("Multi-agent system started successfully")

        except Exception as e:
            # We log and re-raise to ensure the caller knows start failed
            logger.error(f"Failed to start system: {e}")
            raise

    def stop(self):
        """Stop the multi-agent system"""
        if not self.initialized:
            logger.warning("System not initialized")
            return

        logger.info("Stopping multi-agent system...")

        try:
            self.coordinator.shutdown_system()
            self.initialized = False

            logger.info("Multi-agent system stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping system: {e}")
            raise

    def get_health(self) -> Dict:
        """Get system health status"""
        if not self.initialized:
            return {
                'status': 'not_initialized',
                'health_score': 0
            }

        return self.coordinator.get_system_health()

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get status of a specific agent"""
        return self.coordinator.get_agent_status(agent_id)

    def get_all_agents(self) -> list:
        """Get list of all agents"""
        return self.coordinator.get_all_agent_statuses()

    @requires_init
    def create_workflow(self, workflow_definition: Dict) -> str:
        """
        Create a new workflow.

        Args:
            workflow_definition: Workflow definition dict with 'name', 'description', 'steps'

        Returns:
            workflow_id
        """
        if not self.workflow_engine:
             raise RuntimeError("Workflow engine not available")

        # Send workflow creation request
        response = self.workflow_engine.request(
            Topics.WORKFLOW_CREATE,
            workflow_definition,
            timeout=Timeouts.SHORT
        )

        if response and response.payload.get('success'):
            return response.payload['workflow_id']
        else:
            raise RuntimeError(f"Failed to create workflow: {response.payload.get('error') if response else 'No response'}")

    @requires_init
    def execute_workflow(self, workflow_id: str) -> bool:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of the workflow to execute

        Returns:
            True if workflow was queued successfully
        """
        if not self.workflow_engine:
             raise RuntimeError("Workflow engine not available")

        # Send workflow execution request
        response = self.workflow_engine.request(
            Topics.WORKFLOW_EXECUTE,
            {'workflow_id': workflow_id},
            timeout=Timeouts.SHORT
        )

        if response and response.payload.get('success'):
            return True
        else:
            raise RuntimeError(f"Failed to execute workflow: {response.payload.get('error') if response else 'No response'}")

    @requires_init
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get status of a workflow"""
        if not self.workflow_engine:
             raise RuntimeError("Workflow engine not available")

        response = self.workflow_engine.request(
            Topics.WORKFLOW_STATUS,
            {'workflow_id': workflow_id},
            timeout=Timeouts.SHORT
        )

        if response and response.payload.get('success'):
            return response.payload['status']
        else:
            return None

    @requires_init
    def enhance_audio(self, audio_data: Union[Any, List[float]], sample_rate: int = 44100, params: Optional[Dict] = None) -> Dict:
        """
        Enhance audio using the audio enhancement agent.

        Args:
            audio_data: Audio data (numpy array or list)
            sample_rate: Sample rate in Hz
            params: Enhancement parameters

        Returns:
            Enhancement result dict
        """
        enhancement_agent = self.coordinator.agents.get('audio_enhancement_agent')
        if not enhancement_agent:
            raise RuntimeError("Audio enhancement agent not found")

        # Send enhancement request
        response = enhancement_agent.request(
            Topics.AUDIO_ENHANCEMENT_REQUEST,
            {
                'audio_data': audio_data,
                'sample_rate': sample_rate,
                'params': params or {}
            },
            timeout=Timeouts.VERY_LONG
        )

        if response:
            return response.payload
        else:
            raise RuntimeError("Enhancement request timed out")

    @requires_init
    def generate_music(self, content_type: str, musical_context: Dict, params: Optional[Dict] = None) -> Dict:
        """
        Generate musical content.

        Args:
            content_type: Type of content ('melody', 'harmony', 'drums', 'bass')
            musical_context: Musical context (key, tempo, etc.)
            params: Generation parameters

        Returns:
            Generation result dict
        """
        content_agent = self.coordinator.agents.get('content_generation_agent')
        if not content_agent:
            raise RuntimeError("Content generation agent not found")

        topic_map = {
            'melody': Topics.MUSIC_GEN_MELODY_REQ,
            'harmony': Topics.MUSIC_GEN_HARMONY_REQ,
            'drums': Topics.MUSIC_GEN_DRUMS_REQ,
            'bass': Topics.MUSIC_GEN_BASS_REQ
        }

        topic = topic_map.get(content_type)
        if not topic:
            raise ValueError(f"Invalid content type: {content_type}")

        # Send generation request
        response = content_agent.request(
            topic,
            {
                **musical_context,
                'params': params or {}
            },
            timeout=Timeouts.LONG
        )

        if response:
            return response.payload
        else:
            raise RuntimeError("Generation request timed out")

    @requires_init
    def extract_metadata(self, audio_data: Union[Any, List[float]] = None, audio_path: str = None, sample_rate: int = 44100, deep_analysis: bool = True) -> Dict:
        """
        Extract metadata from audio.

        Args:
            audio_data: Audio data (if available)
            audio_path: Path to audio file
            sample_rate: Sample rate in Hz
            deep_analysis: Whether to perform deep analysis

        Returns:
            Metadata dict
        """
        metadata_agent = self.coordinator.agents.get('metadata_management_agent')
        if not metadata_agent:
            raise RuntimeError("Metadata management agent not found")

        # Send metadata extraction request
        response = metadata_agent.request(
            Topics.METADATA_EXTRACT_REQ,
            {
                'audio_data': audio_data,
                'audio_path': audio_path,
                'sample_rate': sample_rate,
                'deep_analysis': deep_analysis
            },
            timeout=Timeouts.LONG
        )

        if response:
            return response.payload
        else:
            raise RuntimeError("Metadata extraction request timed out")

    @requires_init
    def search_metadata(self, query: str, filters: Optional[Dict] = None) -> Dict:
        """
        Search for audio files by metadata.

        Args:
            query: Search query string
            filters: Optional filters

        Returns:
            Search results dict
        """
        metadata_agent = self.coordinator.agents.get('metadata_management_agent')
        if not metadata_agent:
            raise RuntimeError("Metadata management agent not found")

        response = metadata_agent.request(
            Topics.METADATA_SEARCH_REQ,
            {
                'query': query,
                'filters': filters or {}
            },
            timeout=Timeouts.MEDIUM
        )

        if response:
            return response.payload
        else:
            raise RuntimeError("Search request timed out")

    @requires_init
    def get_resource_metrics(self) -> Dict:
        """Get current system resource metrics"""
        perf_agent = self.coordinator.agents.get('performance_optimization_agent')
        if not perf_agent:
            raise RuntimeError("Performance optimization agent not found")

        response = perf_agent.request(
            Topics.SYSTEM_RESOURCE_REQ,
            {},
            timeout=Timeouts.SHORT
        )

        if response:
            return response.payload
        else:
            raise RuntimeError("Resource metrics request timed out")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Convenience function for quick system access
def create_system() -> MultiAgentSystem:
    """Create a new multi-agent system instance"""
    return MultiAgentSystem()