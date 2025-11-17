"""
My Audio Application - Template
Start building your own audio processing application with MAAPS

Customize this template for your specific needs.
"""

import numpy as np
from src.system import create_system


def my_audio_processor():
    """
    Example: Process your own audio files

    Replace this with your actual audio processing logic
    """
    print("Starting audio processor...")

    with create_system() as system:
        # Check system is healthy
        health = system.get_health()
        print(f"System Health: {health['health_score']}%")

        if health['health_score'] < 100:
            print("Warning: System not at full health")
            return

        # YOUR CODE HERE:
        # ---------------

        # Example 1: Load your audio
        # audio_data = load_your_audio_file("path/to/file.wav")
        # sample_rate = 44100

        # For demo purposes, create test audio
        sample_rate = 44100
        duration = 2.0
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))

        # Example 2: Enhance the audio
        print("Enhancing audio...")
        enhanced = system.enhance_audio(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate,
            params={
                'noise_reduction_amount': 0.8,  # Adjust 0.0-1.0
                'preserve_transients': True,
                'declicking_sensitivity': 0.5    # Adjust 0.0-1.0
            }
        )

        print(f"Audio enhanced! Processing time: {enhanced.get('processing_time_ms', 0):.1f}ms")

        # Example 3: Extract metadata
        print("Extracting metadata...")
        metadata = system.extract_metadata(
            audio_data=enhanced['enhanced_audio'],
            sample_rate=sample_rate,
            deep_analysis=True
        )

        print(f"Metadata extracted: {len(metadata)} categories")

        # Example 4: Save or use the results
        # save_audio(enhanced['enhanced_audio'], "output.wav")
        # save_metadata(metadata, "metadata.json")

        print("Processing complete!")

        return {
            'enhanced_audio': enhanced,
            'metadata': metadata
        }


def my_music_generator():
    """
    Example: Generate AI music

    Customize the musical parameters for your needs
    """
    print("Starting music generator...")

    with create_system() as system:
        # Define your musical parameters
        musical_context = {
            'key': 'C major',           # Change key
            'tempo': 120.0,             # Change tempo (BPM)
            'time_signature': '4/4',    # Change time signature
            'chord_progression': ['C', 'Am', 'F', 'G'],  # Change chords
            'length_bars': 8            # Change length
        }

        print(f"Generating music in {musical_context['key']} at {musical_context['tempo']} BPM...")

        # Generate melody
        melody = system.generate_music('melody', musical_context)
        print(f"Melody: {len(melody.get('notes', []))} notes")

        # Generate drums
        drums = system.generate_music('drums', musical_context)
        print(f"Drums: {len(drums.get('notes', []))} events")

        # Generate bass
        bass = system.generate_music('bass', musical_context)
        print(f"Bass: {len(bass.get('notes', []))} notes")

        # Save or use the results
        # export_to_midi(melody, "melody.mid")
        # export_to_midi(drums, "drums.mid")
        # export_to_midi(bass, "bass.mid")

        print("Music generation complete!")

        return {
            'melody': melody,
            'drums': drums,
            'bass': bass
        }


def my_complete_workflow():
    """
    Example: Complete audio production workflow

    Combines multiple operations into a pipeline
    """
    print("Starting complete workflow...")

    with create_system() as system:
        # Step 1: Input audio
        print("\n[1/5] Loading audio...")
        sample_rate = 44100
        audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate))
        print("  [OK] Audio loaded")

        # Step 2: Enhance audio
        print("\n[2/5] Enhancing audio...")
        enhanced = system.enhance_audio(audio.tolist(), sample_rate)
        print("  [OK] Enhancement complete")

        # Step 3: Extract metadata
        print("\n[3/5] Analyzing audio...")
        metadata = system.extract_metadata(enhanced['enhanced_audio'], sample_rate)
        print("  [OK] Analysis complete")

        # Step 4: Generate complementary music
        print("\n[4/5] Generating music...")
        music = system.generate_music('melody', {
            'key': 'C major',
            'tempo': 120.0,
            'chord_progression': ['C', 'F', 'G', 'C']
        })
        print("  [OK] Music generated")

        # Step 5: Monitor system
        print("\n[5/5] Checking system health...")
        health = system.get_health()
        metrics = system.get_resource_metrics()
        print(f"  [OK] Health: {health['health_score']}%")
        print(f"  [OK] CPU: {metrics['metrics']['cpu_usage_percent']:.1f}%")

        print("\n[SUCCESS] Workflow complete!")

        return {
            'enhanced': enhanced,
            'metadata': metadata,
            'music': music,
            'health': health
        }


def main():
    """
    Main entry point - choose your workflow
    """
    print("="*60)
    print("My Audio Application")
    print("Powered by MAAPS")
    print("="*60)

    # Uncomment the function you want to run:

    # Option 1: Process audio
    result = my_audio_processor()

    # Option 2: Generate music
    # result = my_music_generator()

    # Option 3: Complete workflow
    # result = my_complete_workflow()

    print("\n" + "="*60)
    print("Application finished!")
    print("="*60)


if __name__ == "__main__":
    main()
