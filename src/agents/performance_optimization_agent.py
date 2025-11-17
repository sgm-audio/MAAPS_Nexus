"""
Performance & Resource Optimization Agent

This agent handles:
- System resource monitoring (CPU, memory, GPU, disk, network)
- Intelligent task scheduling and load balancing
- Cache management and optimization
- Performance bottleneck detection
- Resource allocation optimization
"""

import threading
import time
import queue
import hashlib
import json
import pickle
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import deque
import logging

try:
    import psutil
    import GPUtil
except ImportError:
    psutil = None
    GPUtil = None

from ..core import BaseAgent, Message, Topics, Priority

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """System resource metrics"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    gpu_memory: float
    disk_io_read: float
    disk_io_write: float
    network_sent: float
    network_recv: float
    timestamp: float


@dataclass
class TaskInfo:
    """Information about a queued task"""
    task_id: str
    task_type: str
    priority: int
    estimated_duration: float
    resource_requirements: Dict[str, float]
    submission_time: float
    status: str = "queued"


@dataclass
class CacheEntry:
    """Cache entry information"""
    key: str
    data: Any
    size_bytes: int
    access_count: int
    last_accessed: float
    created_at: float


class PerformanceOptimizationAgent(BaseAgent):
    """
    Agent responsible for system performance optimization and resource management.

    Capabilities:
    - Real-time resource monitoring
    - Intelligent task scheduling
    - Cache management
    - Performance analysis
    - Bottleneck detection
    - Resource allocation optimization
    """

    def __init__(self):
        super().__init__(
            agent_id="performance_optimization_agent",
            agent_name="Performance & Resource Optimization Agent"
        )

        # Resource monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 1.0  # seconds
        self.resource_history = deque(maxlen=3600)  # Last hour of data

        # Current metrics
        self.current_metrics: Optional[ResourceMetrics] = None
        self.metrics_lock = threading.Lock()

        # Alert thresholds
        self.alert_thresholds = {
            'cpu_usage': 85.0,
            'memory_usage': 90.0,
            'gpu_usage': 90.0,
            'disk_io': 100 * 1024 * 1024,  # 100 MB/s
        }

        # Task scheduling
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: List[TaskInfo] = []
        self.scheduler_thread: Optional[threading.Thread] = None

        # Cache management
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_max_size = 500 * 1024 * 1024  # 500 MB
        self.cache_current_size = 0
        self.cache_lock = threading.Lock()

        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_evictions': 0,
            'tasks_scheduled': 0,
            'tasks_completed': 0,
            'avg_cpu_usage': 0.0,
            'avg_memory_usage': 0.0,
            'avg_gpu_usage': 0.0
        }
        self.stats_lock = threading.Lock()

    def setup(self):
        """Initialize the performance optimization agent"""
        # Subscribe to relevant topics
        self.subscribe("system.resource.request")
        self.subscribe("system.task.schedule")
        self.subscribe("system.cache.get")
        self.subscribe("system.cache.set")
        self.subscribe("system.cache.clear")
        self.subscribe("system.performance.analyze")
        self.subscribe("system.optimization.request")

        # Start resource monitoring
        self._start_monitoring()

        # Start task scheduler
        self._start_scheduler()

        self.log("INFO", "Performance Optimization Agent initialized successfully")

    def teardown(self):
        """Cleanup resources"""
        # Stop monitoring
        self._stop_monitoring()

        # Stop scheduler
        self._stop_scheduler()

        # Clear cache
        with self.cache_lock:
            self.memory_cache.clear()
            self.cache_current_size = 0

        self.log("INFO", "Performance Optimization Agent shutdown complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        try:
            if message.topic == "system.resource.request":
                self._handle_resource_request(message)
            elif message.topic == "system.task.schedule":
                self._handle_task_schedule(message)
            elif message.topic == "system.cache.get":
                self._handle_cache_get(message)
            elif message.topic == "system.cache.set":
                self._handle_cache_set(message)
            elif message.topic == "system.cache.clear":
                self._handle_cache_clear(message)
            elif message.topic == "system.performance.analyze":
                self._handle_performance_analyze(message)
            elif message.topic == "system.optimization.request":
                self._handle_optimization_request(message)
            else:
                self.log("WARNING", f"Unknown message topic: {message.topic}")

        except Exception as e:
            self.log("ERROR", f"Error handling message: {e}", {"topic": message.topic})

    def _handle_resource_request(self, message: Message):
        """Handle resource metrics request"""
        with self.metrics_lock:
            current = self.current_metrics

        if current:
            self.respond(message, {
                'success': True,
                'metrics': {
                    'cpu_usage_percent': current.cpu_usage,
                    'memory_usage_percent': current.memory_usage,
                    'gpu_usage_percent': current.gpu_usage,
                    'gpu_memory_percent': current.gpu_memory,
                    'disk_io_read_mbps': current.disk_io_read / (1024 * 1024),
                    'disk_io_write_mbps': current.disk_io_write / (1024 * 1024),
                    'timestamp': current.timestamp
                },
                'history_available': len(self.resource_history)
            })
        else:
            self.respond(message, {
                'success': False,
                'error': 'No metrics available yet'
            })

    def _handle_task_schedule(self, message: Message):
        """Handle task scheduling request"""
        payload = message.payload
        task_info = TaskInfo(
            task_id=payload.get('task_id', str(time.time())),
            task_type=payload.get('task_type', 'unknown'),
            priority=payload.get('priority', 5),
            estimated_duration=payload.get('estimated_duration', 60.0),
            resource_requirements=payload.get('resource_requirements', {}),
            submission_time=time.time()
        )

        # Add to queue (lower priority number = higher priority)
        self.task_queue.put((task_info.priority, task_info.submission_time, task_info))

        with self.stats_lock:
            self.stats['tasks_scheduled'] += 1

        self.respond(message, {
            'success': True,
            'task_id': task_info.task_id,
            'queue_position': self.task_queue.qsize(),
            'estimated_start_time': self._estimate_start_time(task_info)
        })

    def _handle_cache_get(self, message: Message):
        """Handle cache retrieval request"""
        payload = message.payload
        cache_key = payload.get('key')

        if not cache_key:
            self.respond(message, {
                'success': False,
                'error': 'No cache key provided'
            })
            return

        with self.cache_lock:
            entry = self.memory_cache.get(cache_key)

            if entry:
                # Update access stats
                entry.access_count += 1
                entry.last_accessed = time.time()

                with self.stats_lock:
                    self.stats['cache_hits'] += 1

                self.respond(message, {
                    'success': True,
                    'found': True,
                    'data': entry.data,
                    'access_count': entry.access_count
                })
            else:
                with self.stats_lock:
                    self.stats['cache_misses'] += 1

                self.respond(message, {
                    'success': True,
                    'found': False
                })

    def _handle_cache_set(self, message: Message):
        """Handle cache storage request"""
        payload = message.payload
        cache_key = payload.get('key')
        data = payload.get('data')

        if not cache_key or data is None:
            self.respond(message, {
                'success': False,
                'error': 'Missing key or data'
            })
            return

        # Estimate data size
        try:
            data_bytes = pickle.dumps(data)
            size_bytes = len(data_bytes)
        except:
            size_bytes = len(str(data).encode())

        with self.cache_lock:
            # Check if we need to evict entries
            while self.cache_current_size + size_bytes > self.cache_max_size and self.memory_cache:
                self._evict_cache_entry()

            # Add new entry
            entry = CacheEntry(
                key=cache_key,
                data=data,
                size_bytes=size_bytes,
                access_count=0,
                last_accessed=time.time(),
                created_at=time.time()
            )

            self.memory_cache[cache_key] = entry
            self.cache_current_size += size_bytes

        self.respond(message, {
            'success': True,
            'cached': True,
            'size_bytes': size_bytes,
            'cache_usage_percent': (self.cache_current_size / self.cache_max_size) * 100
        })

    def _handle_cache_clear(self, message: Message):
        """Handle cache clear request"""
        payload = message.payload
        clear_all = payload.get('clear_all', False)
        key = payload.get('key')

        with self.cache_lock:
            if clear_all:
                entries_cleared = len(self.memory_cache)
                self.memory_cache.clear()
                self.cache_current_size = 0
            elif key:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    self.cache_current_size -= entry.size_bytes
                    del self.memory_cache[key]
                    entries_cleared = 1
                else:
                    entries_cleared = 0
            else:
                entries_cleared = 0

        self.respond(message, {
            'success': True,
            'entries_cleared': entries_cleared
        })

    def _handle_performance_analyze(self, message: Message):
        """Handle performance analysis request"""
        # Calculate statistics from resource history
        analysis = self._analyze_performance_history()

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks()

        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(analysis, bottlenecks)

        self.respond(message, {
            'success': True,
            'analysis': analysis,
            'bottlenecks': bottlenecks,
            'recommendations': recommendations
        })

    def _handle_optimization_request(self, message: Message):
        """Handle optimization request"""
        payload = message.payload
        optimization_type = payload.get('type', 'general')

        if optimization_type == 'cache':
            result = self._optimize_cache()
        elif optimization_type == 'scheduler':
            result = self._optimize_scheduler()
        elif optimization_type == 'resources':
            result = self._optimize_resources()
        else:
            result = self._optimize_general()

        self.respond(message, {
            'success': True,
            'optimization_type': optimization_type,
            'result': result
        })

    # Resource monitoring

    def _start_monitoring(self):
        """Start resource monitoring thread"""
        if psutil is None:
            self.log("WARNING", "psutil not available - resource monitoring disabled")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"{self.agent_id}_monitor",
            daemon=True
        )
        self.monitoring_thread.start()

    def _stop_monitoring(self):
        """Stop resource monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()

                with self.metrics_lock:
                    self.current_metrics = metrics

                # Store in history
                self.resource_history.append(metrics)

                # Check thresholds and publish alerts
                self._check_thresholds(metrics)

                # Update statistics
                self._update_resource_stats(metrics)

                # Publish metrics event
                self.publish(
                    "system.resource.metrics",
                    {
                        'cpu': metrics.cpu_usage,
                        'memory': metrics.memory_usage,
                        'gpu': metrics.gpu_usage,
                        'timestamp': metrics.timestamp
                    },
                    priority=Priority.LOW
                )

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        cpu_usage = psutil.cpu_percent(interval=0.1) if psutil else 0.0
        memory = psutil.virtual_memory() if psutil else None
        memory_usage = memory.percent if memory else 0.0

        # GPU metrics
        gpu_usage = 0.0
        gpu_memory = 0.0
        try:
            if GPUtil is not None:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_usage = gpu.load * 100
                    gpu_memory = gpu.memoryUtil * 100
        except:
            pass

        # Disk I/O
        disk_io = psutil.disk_io_counters() if psutil else None
        disk_io_read = disk_io.read_bytes if disk_io else 0.0
        disk_io_write = disk_io.write_bytes if disk_io else 0.0

        # Network I/O
        net_io = psutil.net_io_counters() if psutil else None
        network_sent = net_io.bytes_sent if net_io else 0.0
        network_recv = net_io.bytes_recv if net_io else 0.0

        return ResourceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            gpu_usage=gpu_usage,
            gpu_memory=gpu_memory,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_sent=network_sent,
            network_recv=network_recv,
            timestamp=time.time()
        )

    def _check_thresholds(self, metrics: ResourceMetrics):
        """Check if metrics exceed thresholds and publish alerts"""
        alerts = []

        if metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append({
                'type': 'cpu_high',
                'value': metrics.cpu_usage,
                'threshold': self.alert_thresholds['cpu_usage']
            })

        if metrics.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append({
                'type': 'memory_high',
                'value': metrics.memory_usage,
                'threshold': self.alert_thresholds['memory_usage']
            })

        if metrics.gpu_usage > self.alert_thresholds['gpu_usage']:
            alerts.append({
                'type': 'gpu_high',
                'value': metrics.gpu_usage,
                'threshold': self.alert_thresholds['gpu_usage']
            })

        # Publish alerts
        for alert in alerts:
            self.publish(
                "system.resource.alert",
                alert,
                priority=Priority.HIGH
            )

    def _update_resource_stats(self, metrics: ResourceMetrics):
        """Update resource statistics"""
        with self.stats_lock:
            # Simple moving average
            alpha = 0.1
            self.stats['avg_cpu_usage'] = (
                alpha * metrics.cpu_usage +
                (1 - alpha) * self.stats.get('avg_cpu_usage', 0.0)
            )
            self.stats['avg_memory_usage'] = (
                alpha * metrics.memory_usage +
                (1 - alpha) * self.stats.get('avg_memory_usage', 0.0)
            )
            self.stats['avg_gpu_usage'] = (
                alpha * metrics.gpu_usage +
                (1 - alpha) * self.stats.get('avg_gpu_usage', 0.0)
            )

    # Task scheduling

    def _start_scheduler(self):
        """Start task scheduler thread"""
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name=f"{self.agent_id}_scheduler",
            daemon=True
        )
        self.scheduler_thread.start()

    def _stop_scheduler(self):
        """Stop task scheduler thread"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            # Add sentinel to stop
            self.task_queue.put((0, 0, None))
            self.scheduler_thread.join(timeout=2.0)

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while True:
            try:
                # Get next task (blocks with timeout)
                priority, submission_time, task_info = self.task_queue.get(timeout=1.0)

                if task_info is None:  # Sentinel to stop
                    break

                # Check if resources are available
                if self._can_execute_task(task_info):
                    # Mark as running
                    task_info.status = "running"
                    self.running_tasks[task_info.task_id] = task_info

                    # Publish task start event
                    self.publish(
                        "system.task.started",
                        {
                            'task_id': task_info.task_id,
                            'task_type': task_info.task_type
                        },
                        priority=Priority.MEDIUM
                    )

                    # Simulate task execution
                    # In production, this would delegate to appropriate agent
                    time.sleep(0.1)

                    # Mark as complete
                    task_info.status = "completed"
                    del self.running_tasks[task_info.task_id]
                    self.completed_tasks.append(task_info)

                    with self.stats_lock:
                        self.stats['tasks_completed'] += 1

                    # Publish completion event
                    self.publish(
                        "system.task.completed",
                        {
                            'task_id': task_info.task_id,
                            'task_type': task_info.task_type
                        },
                        priority=Priority.LOW
                    )
                else:
                    # Re-queue task
                    self.task_queue.put((priority, submission_time, task_info))
                    time.sleep(0.5)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

    def _can_execute_task(self, task_info: TaskInfo) -> bool:
        """Check if task can be executed given current resources"""
        if not self.current_metrics:
            return True  # Allow if no metrics available

        requirements = task_info.resource_requirements

        # Check CPU availability
        required_cpu = requirements.get('cpu_percent', 0)
        available_cpu = 100 - self.current_metrics.cpu_usage
        if required_cpu > available_cpu:
            return False

        # Check memory availability
        required_memory = requirements.get('memory_percent', 0)
        available_memory = 100 - self.current_metrics.memory_usage
        if required_memory > available_memory:
            return False

        # Check GPU availability
        required_gpu = requirements.get('gpu_percent', 0)
        available_gpu = 100 - self.current_metrics.gpu_usage
        if required_gpu > 0 and required_gpu > available_gpu:
            return False

        return True

    def _estimate_start_time(self, task_info: TaskInfo) -> float:
        """Estimate when task will start execution"""
        # Simplified: sum duration of higher priority tasks
        queue_time = 0.0

        with self.task_queue.mutex:
            for _, _, other_task in self.task_queue.queue:
                if other_task and other_task.priority < task_info.priority:
                    queue_time += other_task.estimated_duration

        return time.time() + queue_time

    # Cache management

    def _evict_cache_entry(self):
        """Evict least recently used cache entry"""
        if not self.memory_cache:
            return

        # Find LRU entry
        lru_key = None
        lru_time = float('inf')

        for key, entry in self.memory_cache.items():
            if entry.last_accessed < lru_time:
                lru_time = entry.last_accessed
                lru_key = key

        if lru_key:
            entry = self.memory_cache[lru_key]
            self.cache_current_size -= entry.size_bytes
            del self.memory_cache[lru_key]

            with self.stats_lock:
                self.stats['cache_evictions'] += 1

    # Performance analysis

    def _analyze_performance_history(self) -> Dict:
        """Analyze performance history"""
        if not self.resource_history:
            return {}

        history_list = list(self.resource_history)

        cpu_values = [m.cpu_usage for m in history_list]
        memory_values = [m.memory_usage for m in history_list]
        gpu_values = [m.gpu_usage for m in history_list]

        import numpy as np

        return {
            'cpu': {
                'avg': float(np.mean(cpu_values)),
                'max': float(np.max(cpu_values)),
                'min': float(np.min(cpu_values)),
                'std': float(np.std(cpu_values))
            },
            'memory': {
                'avg': float(np.mean(memory_values)),
                'max': float(np.max(memory_values)),
                'min': float(np.min(memory_values)),
                'std': float(np.std(memory_values))
            },
            'gpu': {
                'avg': float(np.mean(gpu_values)),
                'max': float(np.max(gpu_values)),
                'min': float(np.min(gpu_values)),
                'std': float(np.std(gpu_values))
            }
        }

    def _detect_bottlenecks(self) -> List[str]:
        """Detect system bottlenecks"""
        bottlenecks = []

        if not self.current_metrics:
            return bottlenecks

        if self.current_metrics.cpu_usage > 80:
            bottlenecks.append("CPU usage high")

        if self.current_metrics.memory_usage > 85:
            bottlenecks.append("Memory usage high")

        if self.current_metrics.gpu_usage > 85:
            bottlenecks.append("GPU usage high")

        # Check cache efficiency
        with self.stats_lock:
            total_accesses = self.stats['cache_hits'] + self.stats['cache_misses']
            if total_accesses > 100:
                hit_rate = self.stats['cache_hits'] / total_accesses
                if hit_rate < 0.5:
                    bottlenecks.append("Low cache hit rate")

        return bottlenecks

    def _generate_optimization_recommendations(self, analysis: Dict, bottlenecks: List[str]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if "CPU usage high" in bottlenecks:
            recommendations.append("Consider reducing concurrent tasks or upgrading CPU")

        if "Memory usage high" in bottlenecks:
            recommendations.append("Increase cache eviction rate or reduce memory-intensive operations")

        if "GPU usage high" in bottlenecks:
            recommendations.append("Batch GPU operations or consider multi-GPU setup")

        if "Low cache hit rate" in bottlenecks:
            recommendations.append("Increase cache size or improve cache key design")

        return recommendations

    def _optimize_cache(self) -> Dict:
        """Optimize cache performance"""
        with self.cache_lock:
            initial_size = len(self.memory_cache)

            # Remove entries with low access count
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                age = time.time() - entry.created_at
                if age > 3600 and entry.access_count < 2:  # Older than 1 hour, accessed < 2 times
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                entry = self.memory_cache[key]
                self.cache_current_size -= entry.size_bytes
                del self.memory_cache[key]

            final_size = len(self.memory_cache)

        return {
            'entries_removed': initial_size - final_size,
            'memory_freed_bytes': sum(
                self.memory_cache.get(k, CacheEntry('', None, 0, 0, 0, 0)).size_bytes
                for k in keys_to_remove
            )
        }

    def _optimize_scheduler(self) -> Dict:
        """Optimize task scheduler"""
        return {
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks)
        }

    def _optimize_resources(self) -> Dict:
        """Optimize resource usage"""
        return {
            'message': 'Resource optimization performed',
            'current_metrics': {
                'cpu': self.current_metrics.cpu_usage if self.current_metrics else 0,
                'memory': self.current_metrics.memory_usage if self.current_metrics else 0
            }
        }

    def _optimize_general(self) -> Dict:
        """Perform general optimization"""
        cache_result = self._optimize_cache()
        scheduler_result = self._optimize_scheduler()

        return {
            'cache_optimization': cache_result,
            'scheduler_optimization': scheduler_result
        }
