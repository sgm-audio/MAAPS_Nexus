"""
Live Effects Chain Agent - Example Usage

This example demonstrates how to use the Live Effects Chain Agent for
real-time audio effects processing in live performance scenarios.
"""

import sys
import os
import numpy as np
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import get_message_bus, Message, Priority
from src.agents.live import LiveEffectsChainAgent


def example_basic_chain():
    """Example 1: Create a basic vocal processing chain"""
    print("=" * 60)
    print("Example 1: Basic Vocal Processing Chain")
    print("=" * 60)

    # Initialize agent
    agent = LiveEffectsChainAgent(sample_rate=44100)
    bus = get_message_bus()

    # Start agent
    agent.start()

    # Create vocal chain: Gate -> Compressor -> EQ -> Reverb
    chain_msg = Message(
        topic="effects.chain.create",
        sender="example_app",
        payload={
            'chain_name': 'Professional Vocal Chain',
            'routing': 'series',
            'effects': [
                {
                    'type': 'gate',
                    'parameters': {
                        'threshold': -40.0,
                        'ratio': 10.0,
                        'attack': 1.0,
                        'release': 100.0
                    }
                },
                {
                    'type': 'compressor',
                    'parameters': {
                        'threshold': -18.0,
                        'ratio': 4.0,
                        'attack': 5.0,
                        'release': 50.0,
                        'knee': 3.0,
                        'makeup_gain': 6.0
                    }
                },
                {
                    'type': 'eq_parametric',
                    'parameters': {
                        'freq1': 100.0,
                        'gain1': -3.0,
                        'q1': 0.7,
                        'freq2': 3000.0,
                        'gain2': 2.5,
                        'q2': 1.2
                    }
                },
                {
                    'type': 'reverb',
                    'parameters': {
                        'room_size': 0.6,
                        'damping': 0.7,
                        'wet_dry': 0.25
                    }
                }
            ]
        }
    )

    response = agent.request("effects.chain.create", chain_msg.payload, timeout=2.0)
    print(f"[OK] Created chain: {response.payload}")

    # Generate test audio (1 second of tone)
    sample_rate = 44100
    duration = 1.0
    frequency = 440.0  # A4
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t) * 0.5

    # Process audio
    print(f"\nProcessing {len(audio)} samples...")
    process_msg = Message(
        topic="audio.live.process",
        sender="example_app",
        payload={'audio_data': audio.tolist()}
    )

    response = agent.request("audio.live.process", process_msg.payload, timeout=5.0)
    processed = np.array(response.payload['processed_audio'])

    print(f"[OK] Processed audio: {len(processed)} samples")
    print(f"  Input RMS: {np.sqrt(np.mean(audio**2)):.4f}")
    print(f"  Output RMS: {np.sqrt(np.mean(processed**2)):.4f}")

    # Get agent statistics
    stats = agent.stats
    print(f"\nPerformance Metrics:")
    print(f"  Effects processed: {stats['effects_processed']}")
    print(f"  Peak latency: {stats['peak_latency_ms']:.2f} ms")

    agent.stop()
    print("\n[OK] Example 1 complete!\n")


def example_preset_management():
    """Example 2: Preset management and recall"""
    print("=" * 60)
    print("Example 2: Preset Management")
    print("=" * 60)

    agent = LiveEffectsChainAgent(sample_rate=44100)
    agent.start()

    # Create multiple chains
    for i, chain_name in enumerate(['Clean', 'Heavy', 'Ambient']):
        effects = []

        if chain_name == 'Clean':
            effects = [
                {'type': 'compressor', 'parameters': {'threshold': -20.0, 'ratio': 2.0}},
                {'type': 'eq_parametric', 'parameters': {'freq1': 5000.0, 'gain1': 1.5}}
            ]
        elif chain_name == 'Heavy':
            effects = [
                {'type': 'distortion', 'parameters': {'drive': 25.0, 'tone': 0.6}},
                {'type': 'eq_parametric', 'parameters': {'freq1': 2000.0, 'gain1': 3.0}}
            ]
        else:  # Ambient
            effects = [
                {'type': 'chorus', 'parameters': {'rate': 1.2, 'depth': 7.0}},
                {'type': 'reverb', 'parameters': {'room_size': 0.9, 'wet_dry': 0.5}},
                {'type': 'delay', 'parameters': {'delay_time': 450.0, 'feedback': 0.4}}
            ]

        response = agent.request("effects.chain.create", {
            'chain_name': chain_name,
            'effects': effects
        }, timeout=2.0)
        print(f"[OK] Created '{chain_name}' chain")

    # Save current state as preset
    response = agent.request("effects.preset.save", {
        'preset_name': 'My Performance Setup',
        'description': 'Three chains for different song sections',
        'tags': ['live', 'performance', 'guitar']
    }, timeout=2.0)
    print(f"\n[OK] Saved preset: {response.payload['preset_name']}")

    # Recall preset (with transition)
    print("\nRecalling preset with 2-second transition...")
    response = agent.request("effects.preset.recall", {
        'preset_name': 'My Performance Setup',
        'transition_time': 2.0
    }, timeout=5.0)
    print(f"[OK] Preset recalled: {response.payload}")

    agent.stop()
    print("\n[OK] Example 2 complete!\n")


def example_scene_management():
    """Example 3: Scene-based effect changes for live performance"""
    print("=" * 60)
    print("Example 3: Scene Management for Live Performance")
    print("=" * 60)

    agent = LiveEffectsChainAgent(sample_rate=44100)
    agent.start()

    # Create a chain
    response = agent.request("effects.chain.create", {
        'chain_name': 'Master Chain',
        'effects': [
            {
                'effect_id': 'comp1',
                'type': 'compressor',
                'parameters': {'threshold': -20.0, 'ratio': 4.0}
            },
            {
                'effect_id': 'reverb1',
                'type': 'reverb',
                'parameters': {'room_size': 0.3, 'wet_dry': 0.2}
            }
        ]
    }, timeout=2.0)
    print(f"[OK] Created chain")

    # Create scenes for different song sections
    scenes = [
        {
            'scene_name': 'Verse',
            'effect_states': {
                'comp1': {'parameters': {'threshold': -20.0}},
                'reverb1': {'parameters': {'room_size': 0.3, 'wet_dry': 0.15}}
            },
            'transitions': {'room_size': 1.0}  # 1 second transition
        },
        {
            'scene_name': 'Chorus',
            'effect_states': {
                'comp1': {'parameters': {'threshold': -18.0}},
                'reverb1': {'parameters': {'room_size': 0.7, 'wet_dry': 0.4}}
            },
            'transitions': {'room_size': 0.5}
        }
    ]

    scene_ids = []
    for scene in scenes:
        response = agent.request("effects.scene.create", scene, timeout=2.0)
        scene_ids.append(response.payload['scene_id'])
        print(f"[OK] Created scene: {scene['scene_name']}")

    # Switch between scenes
    print("\nSwitching scenes...")
    for i, scene_id in enumerate(scene_ids):
        response = agent.request("effects.scene.change", {
            'scene_id': scene_id,
            'transition_time': 1.5
        }, timeout=3.0)
        print(f"  -> {response.payload['scene_name']}")
        time.sleep(0.5)

    agent.stop()
    print("\n[OK] Example 3 complete!\n")


def example_parameter_automation():
    """Example 4: Automated parameter changes"""
    print("=" * 60)
    print("Example 4: Parameter Automation")
    print("=" * 60)

    agent = LiveEffectsChainAgent(sample_rate=44100)
    agent.start()

    # Create chain with filter
    response = agent.request("effects.chain.create", {
        'chain_name': 'Filter Sweep',
        'effects': [
            {
                'effect_id': 'filter1',
                'type': 'eq_parametric',
                'parameters': {'freq1': 200.0, 'gain1': 10.0, 'q1': 3.0}
            }
        ]
    }, timeout=2.0)
    print(f"[OK] Created filter chain")

    # Automate frequency sweep
    print("\nAutomating frequency sweep from 200Hz to 5kHz over 3 seconds...")
    response = agent.request("effects.parameter.change", {
        'effect_id': 'filter1',
        'parameter': 'freq1',
        'value': 5000.0,
        'ramp_time': 3.0,
        'curve': 'exponential'  # Exponential for frequency sweep
    }, timeout=1.0)
    print(f"[OK] Started automation")

    # Wait for automation to complete
    time.sleep(3.5)

    stats = agent.stats
    print(f"\nAutomations completed: {stats['automations_completed']}")

    agent.stop()
    print("\n[OK] Example 4 complete!\n")


def example_ab_comparison():
    """Example 5: A/B comparison for effect testing"""
    print("=" * 60)
    print("Example 5: A/B Comparison")
    print("=" * 60)

    agent = LiveEffectsChainAgent(sample_rate=44100)
    agent.start()

    # Create initial chain
    agent.request("effects.chain.create", {
        'chain_name': 'Test Chain',
        'effects': [
            {'type': 'compressor', 'parameters': {'threshold': -20.0, 'ratio': 4.0}}
        ]
    }, timeout=2.0)
    print("[OK] Created chain")

    # Save as state A
    response = agent.request("effects.ab.compare", {'action': 'set_a'}, timeout=1.0)
    print(f"[OK] Saved state A")

    # Modify compression
    agent.request("effects.chain.update", {
        'chain_id': list(agent.effect_chains.keys())[0],
        'threshold': -15.0,
        'ratio': 6.0
    }, timeout=1.0)
    print("  Modified compression settings")

    # Save as state B
    agent.request("effects.ab.compare", {'action': 'set_b'}, timeout=1.0)
    print(f"[OK] Saved state B")

    # Toggle between A and B
    print("\nToggling between A and B:")
    for i in range(4):
        response = agent.request("effects.ab.compare", {'action': 'toggle'}, timeout=1.0)
        print(f"  -> State {response.payload['current_state'].upper()}")
        time.sleep(0.5)

    agent.stop()
    print("\n[OK] Example 5 complete!\n")


def example_performance_monitoring():
    """Example 6: Performance monitoring and latency tracking"""
    print("=" * 60)
    print("Example 6: Performance Monitoring")
    print("=" * 60)

    agent = LiveEffectsChainAgent(sample_rate=44100)
    agent.start()

    # Create heavy processing chain
    agent.request("effects.chain.create", {
        'chain_name': 'Heavy Processing',
        'effects': [
            {'type': 'gate', 'parameters': {'threshold': -40.0}},
            {'type': 'compressor', 'parameters': {'threshold': -20.0}},
            {'type': 'eq_parametric', 'parameters': {'freq1': 1000.0, 'gain1': 3.0}},
            {'type': 'reverb', 'parameters': {'room_size': 0.8}},
            {'type': 'delay', 'parameters': {'delay_time': 500.0}},
            {'type': 'chorus', 'parameters': {'rate': 2.0}}
        ]
    }, timeout=2.0)
    print("[OK] Created heavy processing chain with 6 effects")

    # Process multiple buffers
    print("\nProcessing 10 audio buffers...")
    sample_rate = 44100
    buffer_size = 512  # Typical live buffer size

    for i in range(10):
        # Generate test audio
        audio = np.random.randn(buffer_size) * 0.3

        # Process
        response = agent.request("audio.live.process", {
            'audio_data': audio.tolist()
        }, timeout=2.0)

        if i == 0:
            print(f"  First buffer processed")

    # Get detailed statistics
    stats = agent.stats
    print(f"\nPerformance Metrics:")
    print(f"  Buffers processed: {stats['effects_processed']}")
    print(f"  Total processing time: {stats['total_processing_time_ms']:.2f} ms")
    print(f"  Average per buffer: {stats['total_processing_time_ms'] / max(stats['effects_processed'], 1):.2f} ms")
    print(f"  Peak latency: {stats['peak_latency_ms']:.4f} ms")
    print(f"  Target latency: < 2.0 ms per effect")

    if stats['peak_latency_ms'] < 2.0:
        print(f"  [OK] PASSED: Peak latency within target!")
    else:
        print(f"  [WARN] WARNING: Peak latency exceeds target")

    agent.stop()
    print("\n[OK] Example 6 complete!\n")


def run_all_examples():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("LIVE EFFECTS CHAIN AGENT - EXAMPLES")
    print("=" * 60 + "\n")

    examples = [
        example_basic_chain,
        example_preset_management,
        example_scene_management,
        example_parameter_automation,
        example_ab_comparison,
        example_performance_monitoring
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"[FAIL] Error in {example_func.__name__}: {e}\n")

    print("=" * 60)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Run individual example
    # example_basic_chain()
    # example_preset_management()
    # example_scene_management()
    # example_parameter_automation()
    # example_ab_comparison()
    # example_performance_monitoring()

    # Or run all
    run_all_examples()
