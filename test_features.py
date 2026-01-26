"""
Quick feature test for MAAPS Nexus
"""
import sys
import numpy as np
from src.system import create_system

print("\n" + "="*60)
print("MAAPS Nexus - Quick Feature Test")
print("="*60 + "\n")

# Create system
system = create_system()
system.start()

print("[OK] System started successfully!\n")

# Test 1: Health Check
print("1. SYSTEM HEALTH CHECK")
print("-" * 40)
health = system.get_health()
print(f"Health Score: {health['health_score']:.1f}%")
print(f"Active Agents: {health['agents_healthy']}/{health['agents_total']}")
print(f"Uptime: {health['system_uptime_seconds']:.1f} seconds")

# Test 2: Resource Monitoring
print("\n2. RESOURCE MONITORING")
print("-" * 40)
try:
    metrics = system.get_resource_metrics()
    if metrics.get('success'):
        m = metrics.get('metrics', {})
        print(f"CPU Usage: {m.get('cpu_usage_percent', 0):.1f}%")
        print(f"Memory Usage: {m.get('memory_usage_percent', 0):.1f}%")
        print(f"GPU Usage: {m.get('gpu_usage_percent', 0):.1f}%")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Audio Enhancement
print("\n3. AUDIO ENHANCEMENT TEST")
print("-" * 40)
# Create test audio (440 Hz sine wave with noise)
sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration))
clean_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
noisy_audio = clean_audio + np.random.normal(0, 0.05, len(clean_audio))

print(f"Processing {duration}s of audio @ {sample_rate}Hz...")
try:
    result = system.enhance_audio(
        audio_data=noisy_audio.tolist(),
        sample_rate=sample_rate,
        params={'noise_reduction_amount': 0.8}
    )
    if result.get('success'):
        improvements = result.get('quality_improvement', {})
        print(f"[OK] Enhancement completed!")
        print(f"SNR Improvement: {improvements.get('snr_improvement_db', 0):.2f} dB")
        print(f"Processing Time: {result.get('processing_time_seconds', 0):.3f}s")
    else:
        print(f"[FAIL] Failed: {result.get('error')}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 4: Music Generation
print("\n4. MUSIC GENERATION TEST")
print("-" * 40)
musical_context = {
    'key': 'C major',
    'tempo': 120.0,
    'chord_progression': ['C', 'Am', 'F', 'G'],
    'length_bars': 4
}
print(f"Generating melody in {musical_context['key']} @ {musical_context['tempo']} BPM...")

try:
    result = system.generate_music(
        content_type='melody',
        musical_context=musical_context
    )
    if result.get('success'):
        melody_notes = result.get('melody_notes', [])
        print(f"[OK] Melody generated!")
        print(f"Notes: {len(melody_notes)}")
        print(f"Processing Time: {result.get('processing_time_seconds', 0):.3f}s")
    else:
        print(f"[FAIL] Failed: {result.get('error')}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 5: Metadata Extraction
print("\n5. METADATA EXTRACTION TEST")
print("-" * 40)
try:
    result = system.extract_metadata(
        audio_data=clean_audio.tolist(),
        sample_rate=sample_rate,
        deep_analysis=True
    )
    if result.get('success'):
        metadata = result.get('metadata', {})
        print(f"[OK] Metadata extracted!")
        print(f"Duration: {metadata.get('duration', 0):.2f}s")
        print(f"Tempo: {metadata.get('tempo', 0):.1f} BPM")
        print(f"Key: {metadata.get('key', 'Unknown')}")
        print(f"Energy: {metadata.get('energy_level', 0):.3f}")
    else:
        print(f"[FAIL] Failed: {result.get('error')}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Cleanup
print("\n" + "="*60)
system.stop()
print("System stopped successfully")
print("="*60 + "\n")
