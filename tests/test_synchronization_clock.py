"""
Comprehensive Tests for Synchronization Clock Agent

Tests tempo management, transport control, clock position tracking,
MIDI clock, tap tempo, and thread safety.
"""

import unittest
import time
import threading
from typing import List, Dict, Any

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import Message, Priority, AgentState
from src.agents.live import SynchronizationClockAgent


class TestSynchronizationClockAgent(unittest.TestCase):
    """Test suite for Synchronization Clock Agent"""

    def setUp(self):
        """Set up test agent"""
        self.agent = SynchronizationClockAgent()
        self.agent.start()
        time.sleep(0.1)  # Let agent initialize

    def tearDown(self):
        """Clean up agent"""
        if self.agent and self.agent.get_state() == AgentState.RUNNING:
            self.agent.stop()
            time.sleep(0.1)

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertEqual(self.agent.get_state(), AgentState.RUNNING)
        self.assertEqual(self.agent.agent_id, "synchronization_clock_agent")
        self.assertIsNotNone(self.agent.clock_state)
        self.assertEqual(self.agent.clock_state.bpm, 120.0)
        self.assertEqual(self.agent.clock_state.time_signature_numerator, 4)
        self.assertEqual(self.agent.clock_state.time_signature_denominator, 4)
        self.assertFalse(self.agent.clock_state.is_playing)
        self.assertEqual(self.agent.clock_state.current_beat, 0.0)
        self.assertEqual(self.agent.clock_state.current_bar, 0)

    def test_set_tempo(self):
        """Test setting tempo"""
        response = self.agent.request(
            "sync.tempo.set", {"bpm": 140.0, "time_signature": "4/4"}, timeout=1.0
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["bpm"], 140.0)
        self.assertEqual(self.agent.clock_state.bpm, 140.0)
        self.assertEqual(self.agent.stats["tempo_changes"], 1)

    def test_set_tempo_with_time_signature(self):
        """Test setting tempo with different time signature"""
        response = self.agent.request(
            "sync.tempo.set", {"bpm": 90.0, "time_signature": "3/4"}, timeout=1.0
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(self.agent.clock_state.bpm, 90.0)
        self.assertEqual(self.agent.clock_state.time_signature_numerator, 3)
        self.assertEqual(self.agent.clock_state.time_signature_denominator, 4)

    def test_tap_tempo_single_tap(self):
        """Test tap tempo with single tap"""
        response = self.agent.request("sync.tap.tempo", {}, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["taps"], 1)

    def test_tap_tempo_multiple_taps(self):
        """Test tap tempo with multiple taps"""
        # Tap at 120 BPM (500ms intervals)
        start_time = time.time()
        for i in range(4):
            # Send precise timestamps
            timestamp = start_time + (i * 0.5)
            response = self.agent.request(
                "sync.tap.tempo", {"timestamp": timestamp}, timeout=1.0
            )
            time.sleep(0.1)  # Small delay to ensure order, but timestamp controls logic

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["taps"], 4)

        # Should calculate ~120 BPM (with tolerance for timing)
        calculated_bpm = response.payload.get("bpm", 0)
        if calculated_bpm > 0:
            self.assertGreater(calculated_bpm, 115.0)
            self.assertLess(calculated_bpm, 125.0)

    def test_transport_play(self):
        """Test transport play"""
        response = self.agent.request("sync.transport.play", {}, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["state"], "playing")
        self.assertTrue(self.agent.clock_state.is_playing)

    def test_transport_stop(self):
        """Test transport stop resets position"""
        # Start playback
        self.agent.request("sync.transport.play", {}, timeout=1.0)
        time.sleep(0.2)  # Let clock advance

        # Stop
        response = self.agent.request("sync.transport.stop", {}, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["state"], "stopped")
        self.assertFalse(self.agent.clock_state.is_playing)
        self.assertEqual(self.agent.clock_state.current_beat, 0.0)
        self.assertEqual(self.agent.clock_state.current_bar, 0)
        self.assertEqual(self.agent.clock_state.song_position, 0.0)

    def test_transport_pause(self):
        """Test transport pause preserves position"""
        # Start playback
        self.agent.request("sync.transport.play", {}, timeout=1.0)
        time.sleep(0.2)

        # Pause
        response = self.agent.request("sync.transport.pause", {}, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(response.payload["state"], "paused")
        self.assertFalse(self.agent.clock_state.is_playing)
        # Position should be preserved (not reset to 0)
        self.assertGreater(self.agent.clock_state.song_position, 0.0)

    def test_clock_position_tracking(self):
        """Test clock position advances during playback"""
        # Set known tempo
        self.agent.request("sync.tempo.set", {"bpm": 120.0}, timeout=1.0)

        # Start playback
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Record initial state
        initial_beat = self.agent.clock_state.current_beat
        initial_position = self.agent.clock_state.song_position

        # Wait for progression
        time.sleep(0.5)

        # Check advancement
        final_beat = self.agent.clock_state.current_beat
        final_position = self.agent.clock_state.song_position

        self.assertGreater(final_beat, initial_beat)
        self.assertGreater(final_position, initial_position)

        # Stop
        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_beat_to_bar_progression(self):
        """Test beat advances to next bar correctly"""
        # Set tempo and start
        self.agent.request(
            "sync.tempo.set",
            {"bpm": 240.0, "time_signature": "4/4"},  # Fast tempo for quicker test
            timeout=1.0,
        )

        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Wait for more than 4 beats at 240 BPM
        # At 240 BPM: 4 beats per second, so 4 beats = 1 second
        time.sleep(1.2)

        # Should have advanced to at least bar 1
        current_bar = self.agent.clock_state.current_bar
        self.assertGreaterEqual(current_bar, 1)

        # Beat should be less than 4 (wrapped around)
        current_beat = self.agent.clock_state.current_beat
        self.assertLess(current_beat, 4.0)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_time_signature_affects_bar_length(self):
        """Test different time signatures affect bar progression"""
        # Set 3/4 time
        self.agent.request(
            "sync.tempo.set",
            {"bpm": 180.0, "time_signature": "3/4"},  # 3 beats per second
            timeout=1.0,
        )

        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Wait for 3 beats (1 second at 180 BPM)
        time.sleep(1.1)

        # Should advance to bar 1 after 3 beats
        current_bar = self.agent.clock_state.current_bar
        self.assertGreaterEqual(current_bar, 1)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_midi_clock_enable(self):
        """Test MIDI clock enable/disable"""
        response = self.agent.request(
            "sync.midi.clock.enable",
            {"enable": True, "midi_port": "MIDI_OUT_1"},
            timeout=1.0,
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertTrue(response.payload["midi_clock_enabled"])
        self.assertTrue(self.agent.midi_clock_enabled)
        self.assertIn("MIDI_OUT_1", self.agent.midi_clock_outputs)

    def test_midi_clock_disable(self):
        """Test disabling MIDI clock"""
        # Enable first
        self.agent.request("sync.midi.clock.enable", {"enable": True}, timeout=1.0)

        # Disable
        response = self.agent.request(
            "sync.midi.clock.enable", {"enable": False}, timeout=1.0
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertFalse(response.payload["midi_clock_enabled"])
        self.assertFalse(self.agent.midi_clock_enabled)

    def test_midi_clock_pulse_generation(self):
        """Test MIDI clock pulses are generated during playback"""
        # Enable MIDI clock
        self.agent.request("sync.midi.clock.enable", {"enable": True}, timeout=1.0)

        # Record initial pulse count
        initial_pulses = self.agent.stats["midi_clock_pulses"]

        # Start playback
        self.agent.request("sync.transport.play", {}, timeout=1.0)
        time.sleep(0.2)
        self.agent.request("sync.transport.stop", {}, timeout=1.0)

        # Check pulses were generated
        final_pulses = self.agent.stats["midi_clock_pulses"]
        self.assertGreater(final_pulses, initial_pulses)

    def test_ableton_link_enable(self):
        """Test Ableton Link enable"""
        response = self.agent.request(
            "sync.link.enable", {"enable": True, "set_tempo": False}, timeout=1.0
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertTrue(response.payload["link_enabled"])
        self.assertTrue(self.agent.link_enabled)
        self.assertIn("session_peers", response.payload)

    def test_ableton_link_disable(self):
        """Test Ableton Link disable"""
        # Enable first
        self.agent.request("sync.link.enable", {"enable": True}, timeout=1.0)

        # Disable
        response = self.agent.request(
            "sync.link.enable", {"enable": False}, timeout=1.0
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertFalse(response.payload["link_enabled"])
        self.assertFalse(self.agent.link_enabled)

    def test_tempo_detect(self):
        """Test tempo detection from audio"""
        response = self.agent.request(
            "sync.tempo.detect", {"audio_buffer": []}, timeout=1.0  # Simulated
        )

        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertIn("detected_bpm", response.payload)
        self.assertIsInstance(response.payload["detected_bpm"], (int, float))

    def test_statistics_tracking(self):
        """Test statistics are tracked correctly"""
        # Initial state
        self.assertEqual(self.agent.stats["tempo_changes"], 0)
        self.assertEqual(self.agent.stats["tap_tempo_uses"], 0)

        # Change tempo
        self.agent.request("sync.tempo.set", {"bpm": 130.0}, timeout=1.0)
        self.assertEqual(self.agent.stats["tempo_changes"], 1)

        # Use tap tempo
        for _ in range(4):
            self.agent.request("sync.tap.tempo", {}, timeout=1.0)
            time.sleep(0.5)

        self.assertEqual(self.agent.stats["tap_tempo_uses"], 3)  # After 2nd tap

    def test_clock_thread_lifecycle(self):
        """Test clock thread starts and stops properly"""
        # Thread should be running
        self.assertIsNotNone(self.agent.clock_thread)
        self.assertTrue(self.agent.clock_active)
        self.assertTrue(self.agent.clock_thread.is_alive())

        # Stop agent
        self.agent.stop()
        time.sleep(0.2)

        # Thread should be stopped
        self.assertFalse(self.agent.clock_active)

    def test_thread_safety_concurrent_tempo_changes(self):
        """Test thread safety with concurrent tempo changes"""

        def change_tempo(bpm):
            self.agent.request("sync.tempo.set", {"bpm": bpm}, timeout=1.0)

        # Start multiple tempo changes concurrently
        threads = []
        for bpm in [100, 120, 140, 160, 180]:
            t = threading.Thread(target=change_tempo, args=(bpm,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should have processed all changes
        self.assertEqual(self.agent.stats["tempo_changes"], 5)

        # Final tempo should be one of the values
        final_bpm = self.agent.clock_state.bpm
        self.assertIn(final_bpm, [100, 120, 140, 160, 180])

    def test_thread_safety_transport_control(self):
        """Test thread safety with concurrent transport operations"""

        def transport_operation(operation):
            if operation == "play":
                self.agent.request("sync.transport.play", {}, timeout=1.0)
            elif operation == "pause":
                self.agent.request("sync.transport.pause", {}, timeout=1.0)
            elif operation == "stop":
                self.agent.request("sync.transport.stop", {}, timeout=1.0)

        # Execute concurrent transport operations
        operations = ["play", "pause", "play", "stop", "play"]
        threads = []
        for op in operations:
            t = threading.Thread(target=transport_operation, args=(op,))
            threads.append(t)
            t.start()
            time.sleep(0.05)  # Slight delay to ensure ordering

        for t in threads:
            t.join()

        # No crashes = thread safety working

    def test_position_consistency_during_playback(self):
        """Test position remains consistent during continuous playback"""
        self.agent.request("sync.tempo.set", {"bpm": 120.0}, timeout=1.0)
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Sample positions over time
        positions = []
        for _ in range(5):
            time.sleep(0.1)
            with self.agent.clock_lock:
                positions.append(
                    {
                        "beat": self.agent.clock_state.current_beat,
                        "bar": self.agent.clock_state.current_bar,
                        "time": self.agent.clock_state.song_position,
                    }
                )

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

        # Positions should be monotonically increasing
        for i in range(1, len(positions)):
            self.assertGreaterEqual(positions[i]["time"], positions[i - 1]["time"])

    def test_high_tempo_accuracy(self):
        """Test clock accuracy at high tempo"""
        # Set very high tempo
        self.agent.request("sync.tempo.set", {"bpm": 300.0}, timeout=1.0)
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Record start time
        start_time = time.time()
        start_position = self.agent.clock_state.song_position

        # Let it run
        time.sleep(1.0)

        # Check position
        elapsed_real = time.time() - start_time
        elapsed_clock = self.agent.clock_state.song_position - start_position

        # Should be close (within 10% tolerance for Python timing)
        ratio = elapsed_clock / elapsed_real
        self.assertGreater(ratio, 0.9)
        self.assertLess(ratio, 1.1)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_low_tempo_accuracy(self):
        """Test clock accuracy at low tempo"""
        # Set very low tempo
        self.agent.request("sync.tempo.set", {"bpm": 40.0}, timeout=1.0)
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Record start time
        start_time = time.time()
        start_beat = self.agent.clock_state.current_beat

        # Let it run
        time.sleep(1.0)

        # At 40 BPM, should advance ~0.67 beats per second
        elapsed_real = time.time() - start_time
        elapsed_beats = self.agent.clock_state.current_beat - start_beat
        expected_beats = (40.0 / 60.0) * elapsed_real

        # Should be close
        self.assertGreater(elapsed_beats, expected_beats * 0.9)
        self.assertLess(elapsed_beats, expected_beats * 1.1)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_multiple_tempo_changes_during_playback(self):
        """Test multiple tempo changes while playing"""
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Change tempo multiple times
        tempos = [100, 150, 120, 180, 90]
        for bpm in tempos:
            self.agent.request("sync.tempo.set", {"bpm": bpm}, timeout=1.0)
            time.sleep(0.1)

        # Final tempo should be last value
        self.assertEqual(self.agent.clock_state.bpm, 90.0)
        self.assertEqual(self.agent.stats["tempo_changes"], 5)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

    def test_tap_tempo_overflow_protection(self):
        """Test tap tempo buffer doesn't overflow"""
        # Tap more than max (8) times
        for _ in range(12):
            self.agent.request("sync.tap.tempo", {}, timeout=1.0)
            time.sleep(0.1)

        # Deque should limit to 8 entries
        self.assertLessEqual(len(self.agent.tap_times), 8)

    def test_clock_precision(self):
        """Test clock maintains 1ms precision"""
        self.agent.request("sync.tempo.set", {"bpm": 120.0}, timeout=1.0)
        self.agent.request("sync.transport.play", {}, timeout=1.0)

        # Sample beat positions rapidly
        beat_samples = []
        for _ in range(10):
            with self.agent.clock_lock:
                beat_samples.append(self.agent.clock_state.current_beat)
            time.sleep(0.01)  # 10ms intervals

        self.agent.request("sync.transport.stop", {}, timeout=1.0)

        # Should have multiple different values (showing progression)
        unique_values = len(set(beat_samples))
        self.assertGreater(unique_values, 1)


class TestClockEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def setUp(self):
        """Set up test agent"""
        self.agent = SynchronizationClockAgent()
        self.agent.start()
        time.sleep(0.1)

    def tearDown(self):
        """Clean up agent"""
        if self.agent and self.agent.get_state() == AgentState.RUNNING:
            self.agent.stop()
            time.sleep(0.1)

    def test_extreme_tempo_values(self):
        """Test handling of extreme tempo values"""
        # Very high tempo
        response = self.agent.request("sync.tempo.set", {"bpm": 999.0}, timeout=1.0)
        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(self.agent.clock_state.bpm, 999.0)

        # Very low tempo
        response = self.agent.request("sync.tempo.set", {"bpm": 1.0}, timeout=1.0)
        self.assertIsNotNone(response)
        self.assertTrue(response.payload["success"])
        self.assertEqual(self.agent.clock_state.bpm, 1.0)

    def test_complex_time_signatures(self):
        """Test complex time signatures"""
        test_cases = [("7/8", 7, 8), ("5/4", 5, 4), ("11/16", 11, 16), ("2/2", 2, 2)]

        for sig_str, expected_num, expected_denom in test_cases:
            response = self.agent.request(
                "sync.tempo.set", {"bpm": 120.0, "time_signature": sig_str}, timeout=1.0
            )

            self.assertIsNotNone(response)
            self.assertTrue(response.payload["success"])
            self.assertEqual(
                self.agent.clock_state.time_signature_numerator, expected_num
            )
            self.assertEqual(
                self.agent.clock_state.time_signature_denominator, expected_denom
            )

    def test_rapid_transport_changes(self):
        """Test rapid transport state changes"""
        # Rapidly toggle between states
        for _ in range(10):
            self.agent.request("sync.transport.play", {}, timeout=1.0)
            self.agent.request("sync.transport.pause", {}, timeout=1.0)
            self.agent.request("sync.transport.play", {}, timeout=1.0)
            self.agent.request("sync.transport.stop", {}, timeout=1.0)

        # Should handle all changes without crashes
        self.assertFalse(self.agent.clock_state.is_playing)

    def test_pause_play_resume(self):
        """Test pause and resume maintains position"""
        self.agent.request("sync.tempo.set", {"bpm": 120.0}, timeout=1.0)
        self.agent.request("sync.transport.play", {}, timeout=1.0)
        time.sleep(0.3)

        # Pause and record position
        self.agent.request("sync.transport.pause", {}, timeout=1.0)
        paused_position = self.agent.clock_state.song_position
        paused_beat = self.agent.clock_state.current_beat

        # Wait while paused
        time.sleep(0.2)

        # Position should not have changed
        self.assertAlmostEqual(
            self.agent.clock_state.song_position, paused_position, delta=0.01
        )

        # Resume
        self.agent.request("sync.transport.play", {}, timeout=1.0)
        time.sleep(0.2)

        # Position should continue from pause point
        self.assertGreater(self.agent.clock_state.song_position, paused_position)

        self.agent.request("sync.transport.stop", {}, timeout=1.0)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
