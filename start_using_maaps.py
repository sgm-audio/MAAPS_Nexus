"""
MAAPS - Practical Usage Demonstration
Start using the Multi-Agent Audio Processing System

This script demonstrates common real-world usage patterns.
"""

import numpy as np
import time
from src.system import create_system


def demo_1_quick_health_check():
    """Quick health check - verify system is operational"""
    print("\n" + "="*60)
    print("DEMO 1: Quick Health Check")
    print("="*60)

    with create_system() as system:
        health = system.get_health()

        print(f"\n[OK] System Health: {health['health_score']:.1f}%")
        print(f"[OK] Agents Running: {health['agents_healthy']}/{health['agents_total']}")
        print(f"[OK] System Uptime: {health['system_uptime_seconds']:.1f} seconds")

        if health['health_score'] == 100.0:
            print("\n[SUCCESS] System is fully operational!")
        else:
            print(f"\n[WARNING] System health is {health['health_score']}%")

        return health['health_score'] == 100.0


def demo_2_process_audio():
    """Process audio - enhancement workflow"""
    print("\n" + "="*60)
    print("DEMO 2: Audio Enhancement")
    print("="*60)

    with create_system() as system:
        # Create test audio: 2 seconds, 440 Hz (A note)
        print("\n[1/4] Creating test audio signal...")
        sample_rate = 44100
        duration = 2.0
        frequency = 440.0  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Add some noise to demonstrate enhancement
        noise = np.random.normal(0, 0.05, audio.shape)
        noisy_audio = audio + noise

        print(f"    - Sample rate: {sample_rate} Hz")
        print(f"    - Duration: {duration} seconds")
        print(f"    - Frequency: {frequency} Hz")
        print(f"    - Samples: {len(noisy_audio)}")

        # Enhance the audio
        print("\n[2/4] Enhancing audio with noise reduction...")
        start_time = time.time()

        result = system.enhance_audio(
            audio_data=noisy_audio.tolist(),
            sample_rate=sample_rate,
            params={
                'noise_reduction_amount': 0.8,
                'preserve_transients': True,
                'declicking_sensitivity': 0.5
            }
        )

        processing_time = time.time() - start_time

        print(f"    - Processing time: {processing_time:.2f} seconds")
        print(f"    - Enhanced samples: {len(result.get('enhanced_audio', []))}")

        # Show results
        print("\n[3/4] Enhancement results:")
        if 'processing_time_ms' in result:
            print(f"    - Agent processing time: {result['processing_time_ms']:.1f} ms")
        print(f"    - Status: {result.get('status', 'completed')}")

        print("\n[4/4] Audio enhancement complete!")
        print(f"[SUCCESS] Audio processed in {processing_time:.2f}s")

        return result


def demo_3_generate_music():
    """Generate music - AI composition"""
    print("\n" + "="*60)
    print("DEMO 3: AI Music Generation")
    print("="*60)

    with create_system() as system:
        # Define musical context
        print("\n[1/3] Setting up musical context...")
        musical_context = {
            'key': 'C major',
            'tempo': 120.0,
            'time_signature': '4/4',
            'chord_progression': ['C', 'Am', 'F', 'G'],
            'length_bars': 8
        }

        print(f"    - Key: {musical_context['key']}")
        print(f"    - Tempo: {musical_context['tempo']} BPM")
        print(f"    - Chords: {', '.join(musical_context['chord_progression'])}")
        print(f"    - Length: {musical_context['length_bars']} bars")

        # Generate melody
        print("\n[2/3] Generating musical content...")
        print("    - Generating melody...")
        melody_start = time.time()
        melody = system.generate_music('melody', musical_context)
        melody_time = time.time() - melody_start

        print(f"      [OK] Melody generated in {melody_time:.2f}s")

        # Generate drums
        print("    - Generating drum pattern...")
        drums_start = time.time()
        drums = system.generate_music('drums', musical_context)
        drums_time = time.time() - drums_start

        print(f"      [OK] Drums generated in {drums_time:.2f}s")

        # Generate bass
        print("    - Generating bass line...")
        bass_start = time.time()
        bass = system.generate_music('bass', musical_context)
        bass_time = time.time() - bass_start

        print(f"      [OK] Bass generated in {bass_time:.2f}s")

        # Summary
        print("\n[3/3] Generation complete!")
        total_time = melody_time + drums_time + bass_time
        print(f"    - Total generation time: {total_time:.2f}s")
        print(f"    - Melody notes: {len(melody.get('notes', []))}")
        print(f"    - Drum events: {len(drums.get('notes', []))}")
        print(f"    - Bass notes: {len(bass.get('notes', []))}")

        print(f"\n[SUCCESS] Generated {musical_context['length_bars']}-bar composition!")

        return {
            'melody': melody,
            'drums': drums,
            'bass': bass
        }


def demo_4_metadata_extraction():
    """Extract metadata from audio"""
    print("\n" + "="*60)
    print("DEMO 4: Metadata Extraction")
    print("="*60)

    with create_system() as system:
        # Create test audio
        print("\n[1/3] Creating test audio...")
        sample_rate = 44100
        duration = 1.0
        audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))

        print(f"    - Duration: {duration}s")
        print(f"    - Sample rate: {sample_rate} Hz")

        # Extract metadata
        print("\n[2/3] Extracting metadata...")
        start_time = time.time()

        metadata = system.extract_metadata(
            audio_data=audio.tolist(),
            sample_rate=sample_rate,
            deep_analysis=True
        )

        extraction_time = time.time() - start_time

        # Display results
        print("\n[3/3] Metadata extracted:")

        if 'musical_features' in metadata:
            print("\n    Musical Features:")
            musical = metadata['musical_features']
            if 'tempo' in musical:
                print(f"      - Tempo: {musical['tempo']:.1f} BPM")
            if 'key' in musical:
                print(f"      - Key: {musical['key']}")
            if 'time_signature' in musical:
                print(f"      - Time Signature: {musical['time_signature']}")

        if 'technical_features' in metadata:
            print("\n    Technical Features:")
            technical = metadata['technical_features']
            if 'sample_rate' in technical:
                print(f"      - Sample Rate: {technical['sample_rate']} Hz")
            if 'duration_seconds' in technical:
                print(f"      - Duration: {technical['duration_seconds']:.2f}s")
            if 'channels' in technical:
                print(f"      - Channels: {technical['channels']}")

        if 'quality_metrics' in metadata:
            print("\n    Quality Metrics:")
            quality = metadata['quality_metrics']
            if 'peak_amplitude' in quality:
                print(f"      - Peak Amplitude: {quality['peak_amplitude']:.3f}")
            if 'rms_level' in quality:
                print(f"      - RMS Level: {quality['rms_level']:.3f}")

        print(f"\n    - Extraction time: {extraction_time:.2f}s")
        print(f"\n[SUCCESS] Metadata extraction complete!")

        return metadata


def demo_5_resource_monitoring():
    """Monitor system resources"""
    print("\n" + "="*60)
    print("DEMO 5: Resource Monitoring")
    print("="*60)

    with create_system() as system:
        print("\n[1/2] Getting resource metrics...")

        metrics = system.get_resource_metrics()

        print("\n[2/2] Current resource usage:")
        if 'metrics' in metrics:
            m = metrics['metrics']
            print(f"    - CPU Usage: {m.get('cpu_usage_percent', 0):.1f}%")
            print(f"    - Memory Usage: {m.get('memory_usage_percent', 0):.1f}%")
            print(f"    - GPU Usage: {m.get('gpu_usage_percent', 0):.1f}%")
            print(f"    - Disk Usage: {m.get('disk_usage_percent', 0):.1f}%")

            # Resource status
            cpu = m.get('cpu_usage_percent', 0)
            memory = m.get('memory_usage_percent', 0)

            print("\n    Resource Status:")
            if cpu < 50:
                print(f"      [OK] CPU usage is normal ({cpu:.1f}%)")
            elif cpu < 85:
                print(f"      [WARNING] CPU usage is elevated ({cpu:.1f}%)")
            else:
                print(f"      [ALERT] CPU usage is high ({cpu:.1f}%)")

            if memory < 70:
                print(f"      [OK] Memory usage is normal ({memory:.1f}%)")
            elif memory < 90:
                print(f"      [WARNING] Memory usage is elevated ({memory:.1f}%)")
            else:
                print(f"      [ALERT] Memory usage is high ({memory:.1f}%)")

        print(f"\n[SUCCESS] Resource monitoring complete!")

        return metrics


def demo_6_complete_workflow():
    """Complete workflow: Process -> Generate -> Analyze"""
    print("\n" + "="*60)
    print("DEMO 6: Complete Production Workflow")
    print("="*60)

    with create_system() as system:
        print("\nThis demonstrates a complete audio production pipeline:")
        print("1. Create audio")
        print("2. Enhance audio quality")
        print("3. Extract metadata")
        print("4. Generate complementary music")
        print("5. Monitor resources")

        # Step 1: Create audio
        print("\n[Step 1/5] Creating source audio...")
        sample_rate = 44100
        duration = 1.0
        audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        print("    [OK] Audio created")

        # Step 2: Enhance
        print("\n[Step 2/5] Enhancing audio...")
        enhanced = system.enhance_audio(audio.tolist(), sample_rate)
        print("    [OK] Audio enhanced")

        # Step 3: Extract metadata
        print("\n[Step 3/5] Extracting metadata...")
        metadata = system.extract_metadata(enhanced.get('enhanced_audio', audio.tolist()), sample_rate)
        print("    [OK] Metadata extracted")

        # Step 4: Generate music
        print("\n[Step 4/5] Generating complementary music...")
        musical_context = {
            'key': 'C major',
            'tempo': 120.0,
            'chord_progression': ['C', 'F', 'G', 'C']
        }
        melody = system.generate_music('melody', musical_context)
        print("    [OK] Music generated")

        # Step 5: Check resources
        print("\n[Step 5/5] Checking resource usage...")
        metrics = system.get_resource_metrics()
        cpu = metrics['metrics'].get('cpu_usage_percent', 0)
        memory = metrics['metrics'].get('memory_usage_percent', 0)
        print(f"    [OK] CPU: {cpu:.1f}%, Memory: {memory:.1f}%")

        print("\n" + "="*60)
        print("[SUCCESS] Complete workflow finished!")
        print("="*60)
        print("\nWorkflow summary:")
        print(f"  - Audio processed: {duration}s @ {sample_rate} Hz")
        print(f"  - Enhancement: Complete")
        print(f"  - Metadata: {len(metadata)} categories")
        print(f"  - Music generated: {len(melody.get('notes', []))} notes")
        print(f"  - System health: {system.get_health()['health_score']:.1f}%")


def main():
    """Run all demonstrations"""
    print("\n" + "="*60)
    print("MAAPS - Practical Usage Demonstrations")
    print("Multi-Agent Audio Processing System")
    print("="*60)
    print("\nThese demos show you how to use MAAPS in real applications.")
    print("Each demo is self-contained and demonstrates key features.\n")

    try:
        # Demo 1: Health Check
        healthy = demo_1_quick_health_check()

        if not healthy:
            print("\n[WARNING] System health check failed. Please check configuration.")
            return

        # Demo 2: Audio Processing
        time.sleep(1)
        demo_2_process_audio()

        # Demo 3: Music Generation
        time.sleep(1)
        demo_3_generate_music()

        # Demo 4: Metadata
        time.sleep(1)
        demo_4_metadata_extraction()

        # Demo 5: Monitoring
        time.sleep(1)
        demo_5_resource_monitoring()

        # Demo 6: Complete Workflow
        time.sleep(1)
        demo_6_complete_workflow()

        # Final Summary
        print("\n\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Use these patterns in your own code")
        print("  2. Modify parameters to suit your needs")
        print("  3. Combine operations into custom workflows")
        print("  4. Deploy to production (see DEPLOYMENT.md)")
        print("\nFor more information:")
        print("  - Quick Reference: QUICK_REFERENCE.md")
        print("  - Full Deployment Guide: DEPLOYMENT.md")
        print("  - API Documentation: README.md")
        print("  - Example Code: examples/")

    except KeyboardInterrupt:
        print("\n\n[INFO] Demonstrations interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
