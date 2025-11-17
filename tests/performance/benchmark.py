"""
Performance Benchmark Suite for MAAPS

Measures execution time and resource usage for core operations.
Run with: python tests/performance/benchmark.py
"""

import time
import psutil
import numpy as np
from typing import Dict, List, Callable, Any
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.system import create_system
from src.agents.audio_enhancement_agent import AudioEnhancementAgent
from src.agents.content_generation_agent import ContentGenerationAgent
from src.agents.metadata_management_agent import MetadataManagementAgent


class PerformanceBenchmark:
    """Performance benchmarking suite"""

    def __init__(self):
        self.system = None
        self.results = []
        self.process = psutil.Process()

    def setup(self):
        """Initialize system"""
        print("Setting up MAAPS system...")
        self.system = create_system()
        self.system.start()
        time.sleep(2)  # Let system stabilize
        print("System ready\n")

    def teardown(self):
        """Cleanup system"""
        print("\nShutting down system...")
        if self.system:
            self.system.stop()
        print("Cleanup complete")

    def measure(self, name: str, func: Callable, iterations: int = 10) -> Dict[str, Any]:
        """Measure execution time and resource usage"""
        print(f"Benchmarking: {name}")
        print(f"  Running {iterations} iterations...")

        times = []
        cpu_usage = []
        memory_usage = []

        # Warm-up run
        try:
            func()
        except Exception as e:
            print(f"  WARNING: Warm-up failed: {e}")

        # Benchmark runs
        for i in range(iterations):
            # Measure resources before
            cpu_before = self.process.cpu_percent()
            mem_before = self.process.memory_info().rss / 1024 / 1024  # MB

            # Execute and time
            start = time.perf_counter()
            try:
                func()
                success = True
            except Exception as e:
                print(f"  ERROR in iteration {i+1}: {e}")
                success = False
            end = time.perf_counter()

            # Measure resources after
            cpu_after = self.process.cpu_percent()
            mem_after = self.process.memory_info().rss / 1024 / 1024  # MB

            if success:
                times.append(end - start)
                cpu_usage.append(cpu_after - cpu_before)
                memory_usage.append(mem_after - mem_before)

            # Progress indicator
            if (i + 1) % max(1, iterations // 10) == 0:
                print(f"  Progress: {i+1}/{iterations}")

        if not times:
            print(f"  FAILED: No successful iterations\n")
            return None

        # Calculate statistics
        result = {
            'name': name,
            'iterations': len(times),
            'time_avg': np.mean(times),
            'time_std': np.std(times),
            'time_min': np.min(times),
            'time_max': np.max(times),
            'time_p50': np.percentile(times, 50),
            'time_p95': np.percentile(times, 95),
            'time_p99': np.percentile(times, 99),
            'cpu_avg': np.mean(cpu_usage),
            'memory_avg': np.mean(memory_usage),
            'throughput': 1.0 / np.mean(times) if np.mean(times) > 0 else 0
        }

        print(f"  Average: {result['time_avg']*1000:.2f}ms")
        print(f"  95th percentile: {result['time_p95']*1000:.2f}ms")
        print(f"  Throughput: {result['throughput']:.2f} ops/sec\n")

        self.results.append(result)
        return result

    def benchmark_audio_enhancement(self):
        """Benchmark audio enhancement operations"""
        print("\n" + "="*60)
        print("AUDIO ENHANCEMENT BENCHMARKS")
        print("="*60 + "\n")

        # Generate test audio
        sample_rate = 44100

        # 1 second audio
        audio_1s = np.random.randn(sample_rate).astype(np.float32)

        # 5 second audio
        audio_5s = np.random.randn(sample_rate * 5).astype(np.float32)

        # 10 second audio
        audio_10s = np.random.randn(sample_rate * 10).astype(np.float32)

        # Benchmark different durations
        self.measure(
            "Audio Enhancement (1s)",
            lambda: self.system.enhance_audio(
                audio_data=audio_1s,
                sample_rate=sample_rate,
                params={'noise_reduction_amount': 0.7}
            ),
            iterations=20
        )

        self.measure(
            "Audio Enhancement (5s)",
            lambda: self.system.enhance_audio(
                audio_data=audio_5s,
                sample_rate=sample_rate,
                params={'noise_reduction_amount': 0.7}
            ),
            iterations=10
        )

        self.measure(
            "Audio Enhancement (10s)",
            lambda: self.system.enhance_audio(
                audio_data=audio_10s,
                sample_rate=sample_rate,
                params={'noise_reduction_amount': 0.7}
            ),
            iterations=5
        )

    def benchmark_music_generation(self):
        """Benchmark music generation operations"""
        print("\n" + "="*60)
        print("MUSIC GENERATION BENCHMARKS")
        print("="*60 + "\n")

        self.measure(
            "Generate Melody (2s)",
            lambda: self.system.generate_music(
                instrument="piano",
                key="C",
                tempo=120,
                duration=2.0
            ),
            iterations=15
        )

        self.measure(
            "Generate Melody (5s)",
            lambda: self.system.generate_music(
                instrument="synth",
                key="G",
                tempo=140,
                duration=5.0
            ),
            iterations=10
        )

        self.measure(
            "Generate Drums (4s)",
            lambda: self.system.generate_music(
                instrument="drums",
                tempo=120,
                duration=4.0,
                complexity=0.7
            ),
            iterations=10
        )

    def benchmark_metadata_extraction(self):
        """Benchmark metadata extraction operations"""
        print("\n" + "="*60)
        print("METADATA EXTRACTION BENCHMARKS")
        print("="*60 + "\n")

        sample_rate = 44100
        audio_5s = np.random.randn(sample_rate * 5).astype(np.float32)

        self.measure(
            "Extract Basic Metadata",
            lambda: self.system.extract_metadata(
                audio_data=audio_5s,
                sample_rate=sample_rate,
                include_spectral=False,
                include_temporal=True,
                include_harmonic=False
            ),
            iterations=15
        )

        self.measure(
            "Extract Full Metadata",
            lambda: self.system.extract_metadata(
                audio_data=audio_5s,
                sample_rate=sample_rate,
                include_spectral=True,
                include_temporal=True,
                include_harmonic=True
            ),
            iterations=10
        )

    def benchmark_workflows(self):
        """Benchmark complete workflow execution"""
        print("\n" + "="*60)
        print("WORKFLOW BENCHMARKS")
        print("="*60 + "\n")

        sample_rate = 44100
        audio_3s = np.random.randn(sample_rate * 3).astype(np.float32)

        workflow_def = {
            'name': 'benchmark_workflow',
            'steps': [
                {
                    'agent': 'audio_enhancement',
                    'operation': 'enhance',
                    'params': {'noise_reduction_amount': 0.7}
                },
                {
                    'agent': 'metadata_management',
                    'operation': 'extract_features',
                    'params': {}
                }
            ]
        }

        self.measure(
            "Complete Workflow (Enhancement + Metadata)",
            lambda: self.system.execute_workflow(
                workflow=workflow_def,
                input_data={'audio_data': audio_3s, 'sample_rate': sample_rate}
            ),
            iterations=10
        )

    def benchmark_concurrent_operations(self):
        """Benchmark concurrent processing"""
        print("\n" + "="*60)
        print("CONCURRENCY BENCHMARKS")
        print("="*60 + "\n")

        import concurrent.futures

        sample_rate = 44100
        audio_2s = np.random.randn(sample_rate * 2).astype(np.float32)

        def concurrent_enhance(n_tasks: int):
            """Run n concurrent enhancement tasks"""
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_tasks) as executor:
                futures = [
                    executor.submit(
                        self.system.enhance_audio,
                        audio_data=audio_2s,
                        sample_rate=sample_rate,
                        params={'noise_reduction_amount': 0.7}
                    )
                    for _ in range(n_tasks)
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                return results

        self.measure(
            "Concurrent Enhancement (2 tasks)",
            lambda: concurrent_enhance(2),
            iterations=8
        )

        self.measure(
            "Concurrent Enhancement (4 tasks)",
            lambda: concurrent_enhance(4),
            iterations=5
        )

        self.measure(
            "Concurrent Enhancement (8 tasks)",
            lambda: concurrent_enhance(8),
            iterations=3
        )

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60 + "\n")

        if not self.results:
            print("No results to display")
            return

        # Sort by average time
        sorted_results = sorted(self.results, key=lambda x: x['time_avg'])

        print(f"{'Benchmark':<45} {'Avg (ms)':<12} {'P95 (ms)':<12} {'Ops/sec':<10}")
        print("-" * 80)

        for result in sorted_results:
            print(f"{result['name']:<45} "
                  f"{result['time_avg']*1000:>10.2f}  "
                  f"{result['time_p95']*1000:>10.2f}  "
                  f"{result['throughput']:>10.2f}")

        print("\nPerformance Tiers:")
        print("  Excellent: < 100ms")
        print("  Good:      100-500ms")
        print("  Acceptable: 500-1000ms")
        print("  Slow:      > 1000ms")

        # Performance analysis
        excellent = sum(1 for r in self.results if r['time_avg'] < 0.1)
        good = sum(1 for r in self.results if 0.1 <= r['time_avg'] < 0.5)
        acceptable = sum(1 for r in self.results if 0.5 <= r['time_avg'] < 1.0)
        slow = sum(1 for r in self.results if r['time_avg'] >= 1.0)

        print(f"\nResults Distribution:")
        print(f"  Excellent:  {excellent}")
        print(f"  Good:       {good}")
        print(f"  Acceptable: {acceptable}")
        print(f"  Slow:       {slow}")

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save results to file"""
        filepath = os.path.join("tests", "performance", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': self.results
            }, f, indent=2)

        print(f"\nResults saved to: {filepath}")

    def run_all(self):
        """Run all benchmarks"""
        try:
            self.setup()

            self.benchmark_audio_enhancement()
            self.benchmark_music_generation()
            self.benchmark_metadata_extraction()
            self.benchmark_workflows()
            self.benchmark_concurrent_operations()

            self.print_summary()
            self.save_results()

        finally:
            self.teardown()


if __name__ == "__main__":
    print("""
MAAPS Performance Benchmark Suite
==================================

This will benchmark all core operations and save results.
Estimated time: 3-5 minutes

""")

    benchmark = PerformanceBenchmark()
    benchmark.run_all()

    print("\nBenchmark complete!")
