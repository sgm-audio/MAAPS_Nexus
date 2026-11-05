"""
Performance Profiling and Analysis for MAAPS

Uses cProfile and memory_profiler to identify bottlenecks.
Run with: python tests/performance/profile_analysis.py
"""

import cProfile
import pstats
import io
import time
import numpy as np
import sys
import os
from memory_profiler import profile as memory_profile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.system import create_system


class ProfileAnalysis:
    """Performance profiling and analysis"""

    def __init__(self):
        self.system = None
        self.profilers = {}

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
        if self.system:
            self.system.stop()

    def profile_audio_enhancement(self):
        """Profile audio enhancement operation"""
        print("=" * 60)
        print("Profiling: Audio Enhancement")
        print("=" * 60 + "\n")

        sample_rate = 44100
        audio = np.random.randn(sample_rate * 5).astype(np.float32)

        # CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()

        # Run operation
        for _ in range(10):
            self.system.enhance_audio(
                audio_data=audio,
                sample_rate=sample_rate,
                params={"noise_reduction_amount": 0.7},
            )

        profiler.disable()

        # Print stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats("cumulative")
        ps.print_stats(20)  # Top 20 functions

        print(s.getvalue())

        # Save detailed stats
        ps.dump_stats("tests/performance/audio_enhancement_profile.prof")
        print(
            "\nDetailed profile saved to: tests/performance/audio_enhancement_profile.prof"
        )
        print(
            "View with: python -m pstats tests/performance/audio_enhancement_profile.prof\n"
        )

    def profile_music_generation(self):
        """Profile music generation operation"""
        print("=" * 60)
        print("Profiling: Music Generation")
        print("=" * 60 + "\n")

        profiler = cProfile.Profile()
        profiler.enable()

        # Run operation
        for _ in range(15):
            self.system.generate_music(
                instrument="piano", key="C", tempo=120, duration=3.0
            )

        profiler.disable()

        # Print stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats("cumulative")
        ps.print_stats(20)

        print(s.getvalue())

        ps.dump_stats("tests/performance/music_generation_profile.prof")
        print(
            "\nDetailed profile saved to: tests/performance/music_generation_profile.prof\n"
        )

    def profile_metadata_extraction(self):
        """Profile metadata extraction operation"""
        print("=" * 60)
        print("Profiling: Metadata Extraction")
        print("=" * 60 + "\n")

        sample_rate = 44100
        audio = np.random.randn(sample_rate * 5).astype(np.float32)

        profiler = cProfile.Profile()
        profiler.enable()

        # Run operation
        for _ in range(10):
            self.system.extract_metadata(
                audio_data=audio,
                sample_rate=sample_rate,
                include_spectral=True,
                include_temporal=True,
                include_harmonic=True,
            )

        profiler.disable()

        # Print stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats("cumulative")
        ps.print_stats(20)

        print(s.getvalue())

        ps.dump_stats("tests/performance/metadata_extraction_profile.prof")
        print(
            "\nDetailed profile saved to: tests/performance/metadata_extraction_profile.prof\n"
        )

    def analyze_hotspots(self):
        """Analyze performance hotspots across all operations"""
        print("=" * 60)
        print("Performance Hotspot Analysis")
        print("=" * 60 + "\n")

        # Combine stats from all profiles
        stats = pstats.Stats("tests/performance/audio_enhancement_profile.prof")

        try:
            stats.add("tests/performance/music_generation_profile.prof")
            stats.add("tests/performance/metadata_extraction_profile.prof")
        except:
            pass

        print("Top 30 Functions by Cumulative Time:\n")
        stats.strip_dirs()
        stats.sort_stats("cumulative")
        stats.print_stats(30)

        print("\n" + "=" * 60)
        print("Top 30 Functions by Total Time:\n")
        stats.sort_stats("tottime")
        stats.print_stats(30)

        print("\n" + "=" * 60)
        print("Functions Called Most Frequently:\n")
        stats.sort_stats("ncalls")
        stats.print_stats(30)

    def memory_analysis(self):
        """Analyze memory usage patterns"""
        print("\n" + "=" * 60)
        print("Memory Usage Analysis")
        print("=" * 60 + "\n")

        import tracemalloc

        sample_rate = 44100
        audio = np.random.randn(sample_rate * 5).astype(np.float32)

        # Start tracing
        tracemalloc.start()

        # Take snapshot before
        snapshot_before = tracemalloc.take_snapshot()

        # Run operations
        print("Running operations...")
        for i in range(20):
            self.system.enhance_audio(
                audio_data=audio,
                sample_rate=sample_rate,
                params={"noise_reduction_amount": 0.7},
            )
            if (i + 1) % 5 == 0:
                print(f"  Completed {i+1}/20 operations")

        # Take snapshot after
        snapshot_after = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

        print("\nTop 20 Memory Allocations:\n")
        for stat in top_stats[:20]:
            print(f"{stat}")

        # Current memory usage
        current, peak = tracemalloc.get_traced_memory()
        print(f"\n Current memory: {current / 1024 / 1024:.2f} MB")
        print(f"Peak memory:    {peak / 1024 / 1024:.2f} MB")

        tracemalloc.stop()

    def generate_report(self):
        """Generate performance analysis report"""
        print("\n" + "=" * 60)
        print("Generating Performance Report")
        print("=" * 60 + "\n")

        report_path = "tests/performance/PERFORMANCE_REPORT.md"

        with open(report_path, "w") as f:
            f.write("# MAAPS Performance Analysis Report\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            f.write(
                "This report contains detailed performance profiling data for MAAPS.\n\n"
            )

            f.write("## Profile Files\n\n")
            f.write(
                "- `audio_enhancement_profile.prof` - Audio enhancement profiling\n"
            )
            f.write("- `music_generation_profile.prof` - Music generation profiling\n")
            f.write(
                "- `metadata_extraction_profile.prof` - Metadata extraction profiling\n\n"
            )

            f.write("## Viewing Profiles\n\n")
            f.write("```bash\n")
            f.write("# Interactive viewer\n")
            f.write(
                "python -m pstats tests/performance/audio_enhancement_profile.prof\n\n"
            )
            f.write("# Commands in pstats:\n")
            f.write("#   sort cumulative  - Sort by cumulative time\n")
            f.write("#   stats 20         - Show top 20 functions\n")
            f.write("#   callers <func>   - Show who calls this function\n")
            f.write("#   callees <func>   - Show what this function calls\n")
            f.write("```\n\n")

            f.write("## Visualization\n\n")
            f.write("Install snakeviz for visual profiling:\n")
            f.write("```bash\n")
            f.write("pip install snakeviz\n")
            f.write("snakeviz tests/performance/audio_enhancement_profile.prof\n")
            f.write("```\n\n")

            f.write("## Optimization Recommendations\n\n")
            f.write("1. Review functions with high cumulative time\n")
            f.write("2. Look for redundant computations\n")
            f.write("3. Consider caching frequently computed values\n")
            f.write("4. Optimize hot loops identified in profiling\n")
            f.write("5. Review memory allocation patterns\n")
            f.write("6. Consider parallel processing for independent operations\n\n")

        print(f"Report saved to: {report_path}")

    def run_all(self):
        """Run all profiling analyses"""
        try:
            self.setup()

            # CPU profiling
            self.profile_audio_enhancement()
            self.profile_music_generation()
            self.profile_metadata_extraction()

            # Hotspot analysis
            self.analyze_hotspots()

            # Memory analysis
            self.memory_analysis()

            # Generate report
            self.generate_report()

            print("\n" + "=" * 60)
            print("Profiling Complete!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Review profile files with: python -m pstats <profile_file>")
            print("2. Visualize with: snakeviz <profile_file>")
            print("3. Check PERFORMANCE_REPORT.md for recommendations")

        finally:
            self.teardown()


if __name__ == "__main__":
    print("""
MAAPS Performance Profiling Suite
==================================

This will profile:
  - Audio enhancement operations
  - Music generation operations
  - Metadata extraction operations
  - Memory usage patterns

Estimated time: 2-3 minutes

""")

    profiler = ProfileAnalysis()
    profiler.run_all()
