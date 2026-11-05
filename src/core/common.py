"""
Common utilities and shared patterns for the multi-agent system.

Provides reusable components for:
- Thread-safe metrics collection
- Queue-based processing workers
- Configuration management
- Logging utilities
"""

import threading
import queue
import time
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ThreadSafeMetrics:
    """
    Thread-safe metrics collector for agents.

    Provides atomic operations for collecting and retrieving metrics
    without race conditions.
    """

    def __init__(self, initial_metrics: Optional[Dict[str, Any]] = None):
        self._metrics: Dict[str, Any] = initial_metrics or {}
        self._lock = threading.Lock()

    def increment(self, key: str, value: float = 1.0) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._metrics[key] = self._metrics.get(key, 0) + value

    def set(self, key: str, value: Any) -> None:
        """Set a metric value."""
        with self._lock:
            self._metrics[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a metric value."""
        with self._lock:
            return self._metrics.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all metrics."""
        with self._lock:
            return self._metrics.copy()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple metrics at once."""
        with self._lock:
            self._metrics.update(updates)

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()


@dataclass
class ProcessingJob:
    """Base class for processing jobs."""

    job_id: str
    job_type: str
    created_at: float = field(default_factory=time.time)
    priority: int = 0


class ProcessingWorker(ABC, Generic[T]):
    """
    Abstract base class for queue-based processing workers.

    Handles the common pattern of queue-based job processing with:
    - Thread lifecycle management
    - Graceful shutdown
    - Error handling
    - Metrics collection
    """

    def __init__(
        self, worker_name: str, max_queue_size: int = 1000, daemon: bool = True
    ):
        self.worker_name = worker_name
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._thread: Optional[threading.Thread] = None
        self._daemon = daemon
        self._running = False
        self._stop_event = threading.Event()
        self.metrics = ThreadSafeMetrics(
            {"jobs_processed": 0, "jobs_failed": 0, "total_processing_time": 0.0}
        )

    def start(self) -> None:
        """Start the processing worker thread."""
        if self._running:
            logger.warning(f"Worker {self.worker_name} already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name=self.worker_name, daemon=self._daemon
        )
        self._thread.start()
        logger.info(f"Started worker: {self.worker_name}")

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the processing worker gracefully.

        Args:
            timeout: Maximum time to wait for shutdown

        Returns:
            True if stopped successfully, False if timeout
        """
        if not self._running:
            return True

        self._running = False
        self._stop_event.set()

        # Signal queue to wake up
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(
                    f"Worker {self.worker_name} did not stop within {timeout}s"
                )
                return False

        logger.info(f"Stopped worker: {self.worker_name}")
        return True

    def submit(self, job: T, timeout: Optional[float] = None) -> bool:
        """
        Submit a job to the processing queue.

        Args:
            job: The job to process
            timeout: Maximum time to wait if queue is full

        Returns:
            True if job was queued successfully
        """
        if not self._running:
            logger.error(f"Cannot submit to stopped worker: {self.worker_name}")
            return False

        try:
            if timeout:
                self.queue.put(job, timeout=timeout)
            else:
                self.queue.put_nowait(job)
            return True
        except queue.Full:
            logger.warning(f"Queue full for worker: {self.worker_name}")
            return False

    def _run(self) -> None:
        """Main processing loop - runs in separate thread."""
        logger.info(f"Worker {self.worker_name} started processing")

        while self._running and not self._stop_event.is_set():
            try:
                job = self.queue.get(timeout=0.5)

                if job is None:  # Sentinel value
                    break

                start_time = time.time()

                try:
                    self._process_job(job)
                    self.metrics.increment("jobs_processed")
                except Exception as e:
                    logger.error(f"Error processing job in {self.worker_name}: {e}")
                    self.metrics.increment("jobs_failed")
                    self._handle_error(job, e)

                processing_time = time.time() - start_time
                self.metrics.increment("total_processing_time", processing_time)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in worker {self.worker_name}: {e}")

        logger.info(f"Worker {self.worker_name} stopped processing")

    @abstractmethod
    def _process_job(self, job: T) -> None:
        """
        Process a single job. Override this method.

        Args:
            job: The job to process
        """
        pass

    def _handle_error(self, job: T, error: Exception) -> None:
        """
        Handle processing errors. Override for custom error handling.

        Args:
            job: The job that failed
            error: The exception that occurred
        """
        pass


@dataclass
class Configuration:
    """Configuration container with dot notation access."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value with dot notation support."""
        keys = key.split(".")
        target = self._data

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def merge(self, other: "Configuration") -> None:
        """Merge another configuration into this one."""
        self._merge_dict(self._data, other._data)

    def _merge_dict(self, base: Dict, override: Dict) -> None:
        """Recursively merge dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()


class AgentLogger:
    """
    Structured logging utility for agents.

    Provides consistent logging format with agent context.
    """

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self._logger = logging.getLogger(f"agent.{agent_id}")

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self._log("DEBUG", message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self._log("INFO", message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self._log("WARNING", message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        self._log("ERROR", message, context)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, context)

    def _log(self, level: str, message: str, context: Optional[Dict[str, Any]]) -> None:
        """Internal logging method."""
        log_context = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            **(context or {}),
        }

        self._logger.log(
            getattr(logging, level),
            f"[{self.agent_id}] {message}",
            extra={"context": log_context},
        )


@contextmanager
def timing_context(operation_name: str):
    """
    Context manager for timing operations.

    Usage:
        with timing_context('my_operation') as elapsed:
            # do work
        print(f"Operation took {elapsed():.2f}s")
    """
    start = time.perf_counter()
    elapsed = lambda: time.perf_counter() - start

    try:
        yield elapsed
    finally:
        duration = elapsed()
        logger.debug(f"Operation '{operation_name}' took {duration:.3f}s")


def safe_json_serialize(obj: Any) -> Any:
    """
    Safely serialize objects for JSON encoding.

    Handles common non-serializable types like numpy arrays.
    """
    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(safe_json_serialize(v) for v in obj)

    return obj
