"""
Stress Testing Suite for MAAPS

Tests system behavior under extreme load and resource constraints.
Run with: python tests/performance/stress_test.py
"""

import time
import psutil
import threading
import queue
import numpy as np
from typing import List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.system import create_system


class StressTest:
    """Stress testing suite"""

    def __init__(self):
        self.system = None
        self.results = []
        self.stop_flag = threading.Event()
        self.error_queue = queue.Queue()

    def setup(self):
        """Initialize system"""
        print("Initializing MAAPS system...")
        self.system = create_system()
        self.system.start()
        time.sleep(2)
        print("System ready\n")

    def teardown(self):
        """Cleanup"""
        print("\nShutting down...")
        self.stop_flag.set()
        if self.system:
            self.system.stop()
        print("Cleanup complete")

    def monitor_resources(self, duration: int = 60):
        """Monitor system resources during test"""
        process = psutil.Process()
        samples = []

        print(f"Monitoring resources for {duration}s...")
        start = time.time()

        while time.time() - start < duration and not self.stop_flag.is_set():
            sample = {
                'timestamp': time.time() - start,
                'cpu_percent': process.cpu_percent(interval=1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'threads': process.num_threads(),
                'system_cpu': psutil.cpu_percent(interval=None),
                'system_memory': psutil.virtual_memory().percent
            }
            samples.append(sample)
            time.sleep(1)

        return samples

    def worker_thread(self, worker_id: int, task_queue: queue.Queue, results_queue: queue.Queue):
        """Worker thread for concurrent operations"""
        sample_rate = 44100
        audio = np.random.randn(sample_rate * 2).astype(np.float32)

        while not self.stop_flag.is_set():
            try:
                task = task_queue.get(timeout=1)
                if task is None:
                    break

                start = time.time()

                # Perform operation
                if task['type'] == 'enhance':
                    result = self.system.enhance_audio(
                        audio_data=audio,
                        sample_rate=sample_rate,
                        params={'noise_reduction_amount': 0.7}
                    )
                elif task['type'] == 'generate':
                    result = self.system.generate_music(
                        instrument="piano",
                        tempo=120,
                        duration=2.0
                    )
                elif task['type'] == 'metadata':
                    result = self.system.extract_metadata(
                        audio_data=audio,
                        sample_rate=sample_rate
                    )

                elapsed = time.time() - start

                results_queue.put({
                    'worker_id': worker_id,
                    'task_type': task['type'],
                    'success': True,
                    'elapsed': elapsed
                })

            except queue.Empty:
                continue
            except Exception as e:
                self.error_queue.put({
                    'worker_id': worker_id,
                    'error': str(e),
                    'task': task
                })
                results_queue.put({
                    'worker_id': worker_id,
                    'task_type': task.get('type', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
            finally:
                task_queue.task_done()

    def test_concurrent_load(self, n_workers: int = 10, n_tasks: int = 100):
        """Test system under concurrent load"""
        print(f"\n{'='*60}")
        print(f"Concurrent Load Test: {n_workers} workers, {n_tasks} tasks")
        print(f"{'='*60}\n")

        task_queue = queue.Queue()
        results_queue = queue.Queue()

        # Create tasks
        task_types = ['enhance', 'generate', 'metadata']
        for i in range(n_tasks):
            task_queue.put({
                'id': i,
                'type': task_types[i % len(task_types)]
            })

        # Start workers
        workers = []
        start_time = time.time()

        for i in range(n_workers):
            worker = threading.Thread(
                target=self.worker_thread,
                args=(i, task_queue, results_queue),
                daemon=True
            )
            worker.start()
            workers.append(worker)

        # Monitor progress
        last_remaining = n_tasks
        while not task_queue.empty() and not self.stop_flag.is_set():
            remaining = task_queue.qsize()
            completed = n_tasks - remaining

            if remaining != last_remaining:
                progress = (completed / n_tasks) * 100
                print(f"  Progress: {completed}/{n_tasks} ({progress:.1f}%)")
                last_remaining = remaining

            time.sleep(1)

        # Wait for completion
        task_queue.join()
        elapsed = time.time() - start_time

        # Stop workers
        for _ in range(n_workers):
            task_queue.put(None)
        for worker in workers:
            worker.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Analyze
        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        avg_time = np.mean([r['elapsed'] for r in results if r['success'] and 'elapsed' in r])
        throughput = successful / elapsed

        print(f"\nResults:")
        print(f"  Total Tasks:    {n_tasks}")
        print(f"  Successful:     {successful}")
        print(f"  Failed:         {failed}")
        print(f"  Total Time:     {elapsed:.2f}s")
        print(f"  Avg Task Time:  {avg_time:.3f}s")
        print(f"  Throughput:     {throughput:.2f} tasks/sec")

        return {
            'n_workers': n_workers,
            'n_tasks': n_tasks,
            'successful': successful,
            'failed': failed,
            'elapsed': elapsed,
            'throughput': throughput,
            'avg_time': avg_time
        }

    def test_memory_stress(self, duration: int = 60):
        """Test system under memory pressure"""
        print(f"\n{'='*60}")
        print(f"Memory Stress Test: {duration}s duration")
        print(f"{'='*60}\n")

        sample_rate = 44100
        audio_blocks = []

        # Start resource monitoring
        monitor_thread = threading.Thread(
            target=lambda: self.monitor_resources(duration),
            daemon=True
        )
        monitor_thread.start()

        start = time.time()
        operations = 0

        try:
            while time.time() - start < duration and not self.stop_flag.is_set():
                # Generate large audio blocks
                audio = np.random.randn(sample_rate * 10).astype(np.float32)

                # Process
                result = self.system.enhance_audio(
                    audio_data=audio,
                    sample_rate=sample_rate,
                    params={'noise_reduction_amount': 0.7}
                )

                # Keep some results in memory
                if len(audio_blocks) < 10:
                    audio_blocks.append(result)

                operations += 1

                if operations % 10 == 0:
                    mem = psutil.Process().memory_info().rss / 1024 / 1024
                    print(f"  Operations: {operations}, Memory: {mem:.1f}MB")

        except Exception as e:
            print(f"  ERROR: {e}")

        elapsed = time.time() - start

        print(f"\nResults:")
        print(f"  Operations:  {operations}")
        print(f"  Duration:    {elapsed:.2f}s")
        print(f"  Rate:        {operations/elapsed:.2f} ops/sec")

        return {
            'operations': operations,
            'elapsed': elapsed,
            'rate': operations / elapsed
        }

    def test_sustained_load(self, duration: int = 300):
        """Test system under sustained load"""
        print(f"\n{'='*60}")
        print(f"Sustained Load Test: {duration}s duration")
        print(f"{'='*60}\n")

        sample_rate = 44100
        audio = np.random.randn(sample_rate * 3).astype(np.float32)

        start = time.time()
        operations = 0
        errors = 0
        response_times = []

        while time.time() - start < duration and not self.stop_flag.is_set():
            try:
                op_start = time.time()

                # Rotate through different operations
                op_type = operations % 3

                if op_type == 0:
                    self.system.enhance_audio(
                        audio_data=audio,
                        sample_rate=sample_rate,
                        params={'noise_reduction_amount': 0.7}
                    )
                elif op_type == 1:
                    self.system.generate_music(
                        instrument="piano",
                        tempo=120,
                        duration=2.0
                    )
                else:
                    self.system.extract_metadata(
                        audio_data=audio,
                        sample_rate=sample_rate
                    )

                op_time = time.time() - op_start
                response_times.append(op_time)
                operations += 1

                if operations % 50 == 0:
                    elapsed = time.time() - start
                    rate = operations / elapsed
                    avg_response = np.mean(response_times[-50:])
                    health = self.system.get_health()

                    print(f"  Time: {elapsed:.0f}s | "
                          f"Ops: {operations} | "
                          f"Rate: {rate:.2f}/s | "
                          f"Avg Response: {avg_response:.3f}s | "
                          f"Health: {health['health_score']}%")

            except Exception as e:
                errors += 1
                if errors % 10 == 0:
                    print(f"  WARNING: {errors} errors occurred")

        elapsed = time.time() - start

        print(f"\nResults:")
        print(f"  Duration:        {elapsed:.2f}s")
        print(f"  Operations:      {operations}")
        print(f"  Errors:          {errors}")
        print(f"  Success Rate:    {(operations-errors)/operations*100:.2f}%")
        print(f"  Throughput:      {operations/elapsed:.2f} ops/sec")
        print(f"  Avg Response:    {np.mean(response_times):.3f}s")
        print(f"  P95 Response:    {np.percentile(response_times, 95):.3f}s")
        print(f"  P99 Response:    {np.percentile(response_times, 99):.3f}s")

        return {
            'duration': elapsed,
            'operations': operations,
            'errors': errors,
            'throughput': operations / elapsed,
            'avg_response': np.mean(response_times),
            'p95_response': np.percentile(response_times, 95),
            'p99_response': np.percentile(response_times, 99)
        }

    def run_all(self):
        """Run all stress tests"""
        try:
            self.setup()

            # Concurrent load test
            self.test_concurrent_load(n_workers=5, n_tasks=50)
            time.sleep(5)

            self.test_concurrent_load(n_workers=10, n_tasks=100)
            time.sleep(5)

            # Memory stress test
            self.test_memory_stress(duration=30)
            time.sleep(5)

            # Sustained load test
            self.test_sustained_load(duration=60)

            print(f"\n{'='*60}")
            print("All stress tests completed!")
            print(f"{'='*60}")

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        finally:
            self.teardown()


if __name__ == "__main__":
    print("""
MAAPS Stress Testing Suite
===========================

This will run intensive stress tests:
  1. Concurrent load (5-10 workers)
  2. Memory stress (30s)
  3. Sustained load (60s)

Estimated time: 5-10 minutes
Press Ctrl+C to stop

""")

    input("Press Enter to start...")

    stress_test = StressTest()
    stress_test.run_all()
