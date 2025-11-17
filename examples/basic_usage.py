"""
Basic Usage Examples for the Multi-Agent Audio Processing System

Demonstrates common workflows and agent interactions.
"""

import sys
import os
import time
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.system import create_system
from src.orchestration import create_audio_enhancement_workflow, create_music_production_workflow


def example_1_basic_system_startup():
    """Example 1: Basic system startup and health check"""
    print("\n" + "="*60)
    print("Example 1: Basic System Startup and Health Check")
    print("="*60 + "\n")

    # Create and start the system
    system = create_system()

    try:
        # Start the system
        system.start()
        print("[OK] System started successfully")

        # Wait a moment for agents to fully initialize
        time.sleep(2)

        # Get system health
        health = system.get_health()
        print(f"\n[OK] System Health:")
        print(f"  - Health Score: {health['health_score']:.1f}%")
        print(f"  - Total Agents: {health['agents_total']}")
        print(f"  - Healthy Agents: {health['agents_healthy']}")
        print(f"  - Uptime: {health['system_uptime_seconds']:.1f} seconds")

        # Get all agent statuses
        agents = system.get_all_agents()
        print(f"\n[OK] Agent Statuses:")
        for agent in agents:
            print(f"  - {agent['agent_name']}: {agent['state']}")

        print("\n[OK] Example 1 completed successfully!")

    finally:
        # Always stop the system
        system.stop()
        print("\n[OK] System stopped")


def example_2_audio_enhancement():
    """Example 2: Audio enhancement workflow"""
    print("\n" + "="*60)
    print("Example 2: Audio Enhancement")
    print("="*60 + "\n")

    system = create_system()

    try:
        system.start()
        time.sleep(2)

        # Create synthetic audio with noise
        sample_rate = 44100
        duration = 2.0  # seconds
        num_samples = int(sample_rate * duration)

        # Generate a simple sine wave
        frequency = 440  # Hz (A4 note)
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Add some noise
        noise = np.random.normal(0, 0.05, num_samples)
        noisy_audio = audio_data + noise

        print(f"[OK] Created test audio: {duration}s @ {sample_rate}Hz with added noise")

        # Enhance the audio
        print("\n... Enhancing audio...")
        result = system.enhance_audio(
            audio_data=noisy_audio.tolist(),
            sample_rate=sample_rate,
            params={
                'noise_reduction_amount': 0.8,
                'declicking_sensitivity': 0.5,
                'enhancement_profile': 'balanced'
            }
        )

        if result.get('success'):
            print("[OK] Audio enhancement completed!")
            print(f"\n  Quality Improvements:")
            improvements = result.get('quality_improvement', {})
            print(f"  - SNR Improvement: {improvements.get('snr_improvement_db', 0):.2f} dB")
            print(f"  - Dynamic Range: {improvements.get('dynamic_range_improvement_db', 0):.2f} dB")

            processing_chain = result.get('processing_chain', [])
            print(f"\n  Processing Chain: {', '.join(processing_chain)}")
            print(f"  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
        else:
            print(f"[FAIL] Enhancement failed: {result.get('error')}")

        print("\n[OK] Example 2 completed successfully!")

    finally:
        system.stop()


def example_3_music_generation():
    """Example 3: AI music generation"""
    print("\n" + "="*60)
    print("Example 3: AI Music Generation")
    print("="*60 + "\n")

    system = create_system()

    try:
        system.start()
        time.sleep(2)

        # Define musical context
        musical_context = {
            'key': 'C major',
            'tempo': 120.0,
            'time_signature': '4/4',
            'chord_progression': ['C', 'Am', 'F', 'G'],
            'genre': 'pop',
            'length_bars': 8
        }

        print("[OK] Musical Context:")
        print(f"  - Key: {musical_context['key']}")
        print(f"  - Tempo: {musical_context['tempo']} BPM")
        print(f"  - Chord Progression: {', '.join(musical_context['chord_progression'])}")

        # Generate melody
        print("\n... Generating melody...")
        melody_result = system.generate_music(
            content_type='melody',
            musical_context=musical_context,
            params={'temperature': 0.8}
        )

        if melody_result.get('success'):
            print("[OK] Melody generated!")
            melody_notes = melody_result.get('melody_notes', [])
            print(f"  - Number of notes: {len(melody_notes)}")
            print(f"  - Processing time: {melody_result.get('processing_time_seconds', 0):.2f}s")

        # Generate drum pattern
        print("\n... Generating drum pattern...")
        drums_result = system.generate_music(
            content_type='drums',
            musical_context=musical_context,
            params={'complexity': 'medium'}
        )

        if drums_result.get('success'):
            print("[OK] Drum pattern generated!")
            drum_pattern = drums_result.get('drum_pattern', {})
            print(f"  - Kick hits: {len(drum_pattern.get('kick', []))}")
            print(f"  - Snare hits: {len(drum_pattern.get('snare', []))}")
            print(f"  - Hi-hat hits: {len(drum_pattern.get('hihat', []))}")
            print(f"  - Processing time: {drums_result.get('processing_time_seconds', 0):.2f}s")

        # Generate bass line
        print("\n... Generating bass line...")
        bass_result = system.generate_music(
            content_type='bass',
            musical_context=musical_context,
            params={'pattern_style': 'root_fifth'}
        )

        if bass_result.get('success'):
            print("[OK] Bass line generated!")
            bass_notes = bass_result.get('bass_notes', [])
            print(f"  - Number of notes: {len(bass_notes)}")
            print(f"  - Processing time: {bass_result.get('processing_time_seconds', 0):.2f}s")

        print("\n[OK] Example 3 completed successfully!")

    finally:
        system.stop()


def example_4_metadata_management():
    """Example 4: Metadata extraction and search"""
    print("\n" + "="*60)
    print("Example 4: Metadata Management")
    print("="*60 + "\n")

    system = create_system()

    try:
        system.start()
        time.sleep(2)

        # Create test audio
        sample_rate = 44100
        duration = 3.0
        num_samples = int(sample_rate * duration)

        # Create a musical tone
        frequency = 440
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)

        print("[OK] Created test audio for metadata extraction")

        # Extract metadata
        print("\n... Extracting metadata...")
        metadata_result = system.extract_metadata(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate,
            deep_analysis=True
        )

        if metadata_result.get('success'):
            metadata = metadata_result.get('metadata', {})
            print("[OK] Metadata extracted!")
            print(f"\n  Basic Info:")
            print(f"  - Duration: {metadata.get('duration', 0):.2f}s")
            print(f"  - Sample Rate: {metadata.get('sample_rate')}Hz")
            print(f"  - Channels: {metadata.get('channels')}")
            print(f"  - Checksum: {metadata.get('checksum', '')[:16]}...")

            if metadata.get('tempo'):
                print(f"\n  Musical Features:")
                print(f"  - Tempo: {metadata.get('tempo', 0):.1f} BPM")
                print(f"  - Key: {metadata.get('key', 'Unknown')}")
                print(f"  - Energy Level: {metadata.get('energy_level', 0):.3f}")
                print(f"  - Quality Score: {metadata.get('quality_score', 0):.3f}")

        # Search for audio files
        print("\n... Searching metadata...")
        search_result = system.search_metadata(
            query="audio",
            filters={}
        )

        if search_result.get('success'):
            results = search_result.get('results', [])
            print(f"[OK] Search completed!")
            print(f"  - Found {search_result.get('count', 0)} results")

        print("\n[OK] Example 4 completed successfully!")

    finally:
        system.stop()


def example_5_workflow_execution():
    """Example 5: Execute a multi-step workflow"""
    print("\n" + "="*60)
    print("Example 5: Workflow Execution")
    print("="*60 + "\n")

    system = create_system()

    try:
        system.start()
        time.sleep(2)

        # Create test audio
        sample_rate = 44100
        duration = 1.0
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Create workflow
        workflow_def = create_audio_enhancement_workflow(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate
        )

        print("[OK] Created workflow definition:")
        print(f"  - Name: {workflow_def['name']}")
        print(f"  - Steps: {len(workflow_def['steps'])}")

        # Create the workflow
        print("\n... Creating workflow...")
        workflow_id = system.create_workflow(workflow_def)
        print(f"[OK] Workflow created: {workflow_id}")

        # Execute the workflow
        print("\n... Executing workflow...")
        success = system.execute_workflow(workflow_id)

        if success:
            print("[OK] Workflow queued for execution")

            # Monitor workflow progress
            print("\n... Monitoring workflow progress...")
            for i in range(30):  # Monitor for up to 30 seconds
                time.sleep(1)

                status = system.get_workflow_status(workflow_id)
                if status:
                    workflow_status = status['status']
                    completed_steps = status['completed_steps']
                    total_steps = status['steps_total']

                    print(f"  Progress: {completed_steps}/{total_steps} steps ({workflow_status})", end='\r')

                    if workflow_status in ['completed', 'failed', 'cancelled']:
                        print()  # New line
                        break

            # Get final status
            final_status = system.get_workflow_status(workflow_id)
            if final_status:
                print(f"\n[OK] Workflow {final_status['status']}")
                print(f"  - Steps completed: {final_status['completed_steps']}/{final_status['steps_total']}")
                if final_status.get('started_at'):
                    duration = (final_status.get('completed_at', 0) or time.time()) - final_status['started_at']
                    print(f"  - Duration: {duration:.2f}s")

        print("\n[OK] Example 5 completed successfully!")

    finally:
        system.stop()


def example_6_resource_monitoring():
    """Example 6: System resource monitoring"""
    print("\n" + "="*60)
    print("Example 6: Resource Monitoring")
    print("="*60 + "\n")

    system = create_system()

    try:
        system.start()
        time.sleep(2)

        print("... Getting resource metrics...")
        metrics_result = system.get_resource_metrics()

        if metrics_result.get('success'):
            metrics = metrics_result.get('metrics', {})
            print("[OK] Resource Metrics:")
            print(f"  - CPU Usage: {metrics.get('cpu_usage_percent', 0):.1f}%")
            print(f"  - Memory Usage: {metrics.get('memory_usage_percent', 0):.1f}%")
            print(f"  - GPU Usage: {metrics.get('gpu_usage_percent', 0):.1f}%")
            print(f"  - GPU Memory: {metrics.get('gpu_memory_percent', 0):.1f}%")

            # Get system health
            health = system.get_health()
            bus_metrics = health.get('message_bus_metrics', {})

            print(f"\n[OK] Message Bus Metrics:")
            print(f"  - Messages Published: {bus_metrics.get('messages_published', 0)}")
            print(f"  - Messages Delivered: {bus_metrics.get('messages_delivered', 0)}")
            print(f"  - Messages Failed: {bus_metrics.get('messages_failed', 0)}")
            print(f"  - Avg Latency: {bus_metrics.get('avg_latency_ms', 0):.2f}ms")

        print("\n[OK] Example 6 completed successfully!")

    finally:
        system.stop()


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Multi-Agent Audio Processing System - Examples")
    print("="*60)

    examples = [
        ("Basic System Startup", example_1_basic_system_startup),
        ("Audio Enhancement", example_2_audio_enhancement),
        ("AI Music Generation", example_3_music_generation),
        ("Metadata Management", example_4_metadata_management),
        ("Workflow Execution", example_5_workflow_execution),
        ("Resource Monitoring", example_6_resource_monitoring),
    ]

    for i, (name, example_func) in enumerate(examples, 1):
        print(f"\n\nRunning Example {i}: {name}")
        try:
            example_func()
        except Exception as e:
            print(f"\n[FAIL] Example {i} failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("All Examples Completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
