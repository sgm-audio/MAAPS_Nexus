"""
Workflow Engine for orchestrating complex multi-agent workflows.

Provides high-level workflow coordination, dependency management,
and automated process execution across multiple agents.
"""

import threading
import time
import queue
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

from ..core import BaseAgent, Message, Topics, Priority

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Workflow step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    name: str
    agent_id: str
    topic: str
    payload: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class Workflow:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine(BaseAgent):
    """
    Workflow engine for orchestrating complex multi-agent processes.

    Capabilities:
    - Workflow definition and execution
    - Dependency management
    - Error handling and retry logic
    - Progress tracking
    - Result aggregation
    """

    def __init__(self):
        super().__init__(
            agent_id="workflow_engine",
            agent_name="Workflow Orchestration Engine"
        )

        # Active workflows
        self.workflows: Dict[str, Workflow] = {}
        self.workflows_lock = threading.Lock()

        # Execution queue
        self.execution_queue = queue.Queue()
        self.executor_thread: Optional[threading.Thread] = None

        # Step result handlers
        self.result_handlers: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            'workflows_executed': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'total_steps_executed': 0,
            'avg_workflow_duration': 0.0
        }
        self.stats_lock = threading.Lock()

    def setup(self):
        """Initialize the workflow engine"""
        # Subscribe to workflow topics
        self.subscribe("workflow.create")
        self.subscribe("workflow.execute")
        self.subscribe("workflow.cancel")
        self.subscribe("workflow.status")
        self.subscribe("workflow.step.result")

        # Start executor thread
        self._start_executor()

        self.log("INFO", "Workflow Engine initialized successfully")

    def teardown(self):
        """Cleanup resources"""
        # Stop executor
        self._stop_executor()

        # Cancel all running workflows
        with self.workflows_lock:
            for workflow in self.workflows.values():
                if workflow.status == WorkflowStatus.RUNNING:
                    workflow.status = WorkflowStatus.CANCELLED

        self.log("INFO", "Workflow Engine shutdown complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        try:
            if message.topic == "workflow.create":
                self._handle_workflow_create(message)
            elif message.topic == "workflow.execute":
                self._handle_workflow_execute(message)
            elif message.topic == "workflow.cancel":
                self._handle_workflow_cancel(message)
            elif message.topic == "workflow.status":
                self._handle_workflow_status(message)
            elif message.topic == "workflow.step.result":
                self._handle_step_result(message)
            else:
                self.log("WARNING", f"Unknown message topic: {message.topic}")

        except Exception as e:
            self.log("ERROR", f"Error handling message: {e}", {"topic": message.topic})

    def _handle_workflow_create(self, message: Message):
        """Handle workflow creation request"""
        payload = message.payload
        workflow_name = payload.get('name', 'Untitled Workflow')
        description = payload.get('description', '')
        steps_data = payload.get('steps', [])

        # Create workflow
        workflow = self._create_workflow(workflow_name, description, steps_data)

        # Store workflow
        with self.workflows_lock:
            self.workflows[workflow.workflow_id] = workflow

        self.respond(message, {
            'success': True,
            'workflow_id': workflow.workflow_id,
            'workflow_name': workflow.name,
            'num_steps': len(workflow.steps)
        })

    def _handle_workflow_execute(self, message: Message):
        """Handle workflow execution request"""
        payload = message.payload
        workflow_id = payload.get('workflow_id')

        if not workflow_id:
            self.respond(message, {
                'success': False,
                'error': 'No workflow_id provided'
            })
            return

        with self.workflows_lock:
            workflow = self.workflows.get(workflow_id)

        if not workflow:
            self.respond(message, {
                'success': False,
                'error': f'Workflow {workflow_id} not found'
            })
            return

        # Queue for execution
        self.execution_queue.put(workflow_id)

        self.respond(message, {
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Workflow queued for execution'
        })

    def _handle_workflow_cancel(self, message: Message):
        """Handle workflow cancellation request"""
        payload = message.payload
        workflow_id = payload.get('workflow_id')

        with self.workflows_lock:
            workflow = self.workflows.get(workflow_id)

            if workflow and workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.CANCELLED

                self.respond(message, {
                    'success': True,
                    'workflow_id': workflow_id,
                    'message': 'Workflow cancelled'
                })
            else:
                self.respond(message, {
                    'success': False,
                    'error': 'Workflow not found or not running'
                })

    def _handle_workflow_status(self, message: Message):
        """Handle workflow status request"""
        payload = message.payload
        workflow_id = payload.get('workflow_id')

        with self.workflows_lock:
            workflow = self.workflows.get(workflow_id)

            if workflow:
                status_info = {
                    'workflow_id': workflow.workflow_id,
                    'name': workflow.name,
                    'status': workflow.status.value,
                    'num_steps': len(workflow.steps),
                    'completed_steps': sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED),
                    'failed_steps': sum(1 for s in workflow.steps if s.status == StepStatus.FAILED),
                    'created_at': workflow.created_at,
                    'started_at': workflow.started_at,
                    'completed_at': workflow.completed_at
                }

                self.respond(message, {
                    'success': True,
                    'status': status_info
                })
            else:
                self.respond(message, {
                    'success': False,
                    'error': 'Workflow not found'
                })

    def _handle_step_result(self, message: Message):
        """Handle step execution result"""
        payload = message.payload
        workflow_id = payload.get('workflow_id')
        step_id = payload.get('step_id')
        success = payload.get('success', False)
        result = payload.get('result', {})
        error = payload.get('error')

        with self.workflows_lock:
            workflow = self.workflows.get(workflow_id)

            if workflow:
                # Find and update step
                for step in workflow.steps:
                    if step.step_id == step_id:
                        if success:
                            step.status = StepStatus.COMPLETED
                            step.result = result
                        else:
                            step.status = StepStatus.FAILED
                            step.error = error
                        step.end_time = time.time()
                        break

    def _create_workflow(self, name: str, description: str, steps_data: List[Dict]) -> Workflow:
        """Create a new workflow from definition"""
        workflow_id = str(uuid.uuid4())

        steps = []
        for step_data in steps_data:
            step = WorkflowStep(
                step_id=step_data.get('step_id', str(uuid.uuid4())),
                name=step_data.get('name', 'Untitled Step'),
                agent_id=step_data.get('agent_id', ''),
                topic=step_data.get('topic', ''),
                payload=step_data.get('payload', {}),
                dependencies=step_data.get('dependencies', []),
                timeout=step_data.get('timeout', 30.0),
                max_retries=step_data.get('max_retries', 3)
            )
            steps.append(step)

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=steps
        )

        return workflow

    def _start_executor(self):
        """Start workflow executor thread"""
        self.executor_thread = threading.Thread(
            target=self._executor_loop,
            name=f"{self.agent_id}_executor",
            daemon=True
        )
        self.executor_thread.start()

    def _stop_executor(self):
        """Stop workflow executor thread"""
        if self.executor_thread and self.executor_thread.is_alive():
            self.execution_queue.put(None)  # Sentinel
            self.executor_thread.join(timeout=5.0)

    def _executor_loop(self):
        """Main executor loop"""
        while True:
            try:
                workflow_id = self.execution_queue.get(timeout=1.0)

                if workflow_id is None:  # Sentinel to stop
                    break

                # Execute workflow
                self._execute_workflow(workflow_id)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in executor loop: {e}")

    def _execute_workflow(self, workflow_id: str):
        """Execute a workflow"""
        with self.workflows_lock:
            workflow = self.workflows.get(workflow_id)

        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return

        # Update status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = time.time()

        with self.stats_lock:
            self.stats['workflows_executed'] += 1

        # Publish workflow started event
        self.publish(
            "workflow.started",
            {
                'workflow_id': workflow.workflow_id,
                'workflow_name': workflow.name,
                'num_steps': len(workflow.steps)
            },
            priority=Priority.MEDIUM
        )

        try:
            # Execute steps
            completed_steps = set()

            while len(completed_steps) < len(workflow.steps):
                if workflow.status == WorkflowStatus.CANCELLED:
                    break

                # Find next executable steps
                executable_steps = self._find_executable_steps(workflow, completed_steps)

                if not executable_steps:
                    # Check if we're stuck (no executable steps but not all completed)
                    if len(completed_steps) < len(workflow.steps):
                        # Some steps are blocked by failed dependencies
                        workflow.status = WorkflowStatus.FAILED
                        break
                    else:
                        break

                # Execute steps
                for step in executable_steps:
                    self._execute_step(workflow, step)

                    if step.status == StepStatus.COMPLETED:
                        completed_steps.add(step.step_id)
                    elif step.status == StepStatus.FAILED:
                        # Check if we should continue on failure
                        if step.step_id not in [s.step_id for s in workflow.steps if s.dependencies]:
                            # This step has no dependents, mark as completed
                            completed_steps.add(step.step_id)
                        else:
                            # Workflow failed
                            workflow.status = WorkflowStatus.FAILED
                            break

                # Small delay between batches
                time.sleep(0.1)

            # Finalize workflow
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.COMPLETED
                with self.stats_lock:
                    self.stats['workflows_completed'] += 1

            elif workflow.status == WorkflowStatus.FAILED:
                with self.stats_lock:
                    self.stats['workflows_failed'] += 1

            workflow.completed_at = time.time()

            # Update stats
            with self.stats_lock:
                duration = workflow.completed_at - workflow.started_at
                self.stats['total_steps_executed'] += len(completed_steps)

                # Update average duration
                total_workflows = self.stats['workflows_completed'] + self.stats['workflows_failed']
                if total_workflows > 0:
                    self.stats['avg_workflow_duration'] = (
                        (self.stats['avg_workflow_duration'] * (total_workflows - 1) + duration) /
                        total_workflows
                    )

            # Publish workflow completed event
            self.publish(
                "workflow.completed",
                {
                    'workflow_id': workflow.workflow_id,
                    'status': workflow.status.value,
                    'duration_seconds': workflow.completed_at - workflow.started_at,
                    'steps_completed': len(completed_steps),
                    'steps_total': len(workflow.steps)
                },
                priority=Priority.MEDIUM
            )

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = time.time()

            with self.stats_lock:
                self.stats['workflows_failed'] += 1

    def _find_executable_steps(self, workflow: Workflow, completed_steps: set) -> List[WorkflowStep]:
        """Find steps that can be executed now"""
        executable = []

        for step in workflow.steps:
            # Skip if already processed
            if step.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.RUNNING]:
                continue

            # Check if dependencies are satisfied
            dependencies_satisfied = all(
                dep_id in completed_steps for dep_id in step.dependencies
            )

            if dependencies_satisfied:
                executable.append(step)

        return executable

    def _execute_step(self, workflow: Workflow, step: WorkflowStep):
        """Execute a single workflow step"""
        step.status = StepStatus.RUNNING
        step.start_time = time.time()

        # Publish step started event
        self.publish(
            "workflow.step.started",
            {
                'workflow_id': workflow.workflow_id,
                'step_id': step.step_id,
                'step_name': step.name
            },
            priority=Priority.LOW
        )

        try:
            # Send request to agent
            response = self.request(
                step.topic,
                {
                    **step.payload,
                    'workflow_id': workflow.workflow_id,
                    'step_id': step.step_id
                },
                timeout=step.timeout,
                priority=Priority.MEDIUM
            )

            if response:
                # Process response
                if response.payload.get('success', False):
                    step.status = StepStatus.COMPLETED
                    step.result = response.payload
                else:
                    step.status = StepStatus.FAILED
                    step.error = response.payload.get('error', 'Unknown error')
            else:
                # Timeout
                step.status = StepStatus.FAILED
                step.error = "Request timeout"

                # Retry logic
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    step.status = StepStatus.PENDING
                    logger.warning(f"Retrying step {step.step_id} (attempt {step.retry_count}/{step.max_retries})")

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Error executing step {step.step_id}: {e}")

        step.end_time = time.time()

        # Publish step completed event
        self.publish(
            "workflow.step.completed",
            {
                'workflow_id': workflow.workflow_id,
                'step_id': step.step_id,
                'step_name': step.name,
                'status': step.status.value,
                'duration_seconds': step.end_time - step.start_time if step.start_time else 0
            },
            priority=Priority.LOW
        )


def create_audio_enhancement_workflow(audio_data: Any, sample_rate: int = 44100) -> Dict:
    """
    Create a workflow for comprehensive audio enhancement.

    This is an example workflow that demonstrates cross-agent coordination.
    """
    return {
        'name': 'Comprehensive Audio Enhancement',
        'description': 'Full audio enhancement pipeline with metadata extraction',
        'steps': [
            {
                'step_id': 'metadata_extract',
                'name': 'Extract Metadata',
                'agent_id': 'metadata_management_agent',
                'topic': 'metadata.extract.request',
                'payload': {
                    'audio_data': audio_data,
                    'sample_rate': sample_rate,
                    'deep_analysis': True
                },
                'dependencies': [],
                'timeout': 30.0
            },
            {
                'step_id': 'noise_reduction',
                'name': 'Reduce Noise',
                'agent_id': 'audio_enhancement_agent',
                'topic': 'audio.noise.reduction.request',
                'payload': {
                    'audio_data': audio_data,
                    'sample_rate': sample_rate,
                    'reduction_amount': 0.8
                },
                'dependencies': [],
                'timeout': 60.0
            },
            {
                'step_id': 'restoration',
                'name': 'Restore Audio',
                'agent_id': 'audio_enhancement_agent',
                'topic': 'audio.restoration.request',
                'payload': {
                    'audio_data': audio_data,
                    'sample_rate': sample_rate,
                    'restoration_type': 'auto'
                },
                'dependencies': ['noise_reduction'],
                'timeout': 60.0
            },
            {
                'step_id': 'tag_generation',
                'name': 'Generate Tags',
                'agent_id': 'metadata_management_agent',
                'topic': 'tags.generate.request',
                'payload': {
                    'metadata': {}  # Will be populated from metadata_extract result
                },
                'dependencies': ['metadata_extract'],
                'timeout': 10.0
            }
        ]
    }


def create_music_production_workflow(existing_stems: Dict, musical_context: Dict) -> Dict:
    """
    Create a workflow for AI-assisted music production.

    This workflow demonstrates content generation and enhancement.
    """
    return {
        'name': 'AI Music Production',
        'description': 'Generate missing musical elements and enhance arrangement',
        'steps': [
            {
                'step_id': 'analyze_arrangement',
                'name': 'Analyze Existing Arrangement',
                'agent_id': 'content_generation_agent',
                'topic': 'music.generation.arrangement.request',
                'payload': {
                    'existing_stems': existing_stems,
                    'params': {}
                },
                'dependencies': [],
                'timeout': 20.0
            },
            {
                'step_id': 'generate_drums',
                'name': 'Generate Drum Pattern',
                'agent_id': 'content_generation_agent',
                'topic': 'music.generation.drums.request',
                'payload': {
                    **musical_context,
                    'params': {'complexity': 'medium'}
                },
                'dependencies': ['analyze_arrangement'],
                'timeout': 30.0
            },
            {
                'step_id': 'generate_bass',
                'name': 'Generate Bass Line',
                'agent_id': 'content_generation_agent',
                'topic': 'music.generation.bass.request',
                'payload': {
                    **musical_context,
                    'params': {'pattern_style': 'root_fifth'}
                },
                'dependencies': ['analyze_arrangement'],
                'timeout': 30.0
            },
            {
                'step_id': 'enhance_audio',
                'name': 'Enhance Generated Audio',
                'agent_id': 'audio_enhancement_agent',
                'topic': 'audio.enhancement.request',
                'payload': {
                    'audio_data': None,  # Will be populated from generation results
                    'params': {'enhancement_profile': 'balanced'}
                },
                'dependencies': ['generate_drums', 'generate_bass'],
                'timeout': 60.0
            }
        ]
    }
