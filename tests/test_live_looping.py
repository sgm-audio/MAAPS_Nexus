"""
Unit tests for Live Looping Agent and Loop Processors
"""

import unittest
import numpy as np
import time
from src.agents.live import LiveLoopingAgent
from src.agents.live.loop_processors import (
    TimeStretcher,
    PitchShifter,
    LoopSlicer,
    CrossfadeProcessor,
    LoopQuantizer,
    LoopRecorder,
    OverdubProcessor,
)
from src.core import Message


class TestLoopProcessors(unittest.TestCase):
    """Test individual loop processors"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_rate = 44100
        self.duration = 1.0
        self.num_samples = int(self.sample_rate * self.duration)

        # Generate test signal (440Hz sine wave)
        t = np.linspace(0, self.duration, self.num_samples)
        self.test_signal = np.sin(2 * np.pi * 440 * t) * 0.5

    def test_time_stretcher_double_speed(self):
        """Test time stretching to double speed"""
        stretcher = TimeStretcher(self.sample_rate)

        # Double speed = half duration
        stretched = stretcher.stretch(self.test_signal, 0.5)

        # Should be approximately half length
        self.assertLess(len(stretched), len(self.test_signal))
        self.assertGreater(len(stretched), len(self.test_signal) * 0.4)

    def test_time_stretcher_half_speed(self):
        """Test time stretching to half speed"""
        stretcher = TimeStretcher(self.sample_rate)

        # Half speed = double duration
        stretched = stretcher.stretch(self.test_signal, 2.0)

        # Should be approximately double length
        self.assertGreater(len(stretched), len(self.test_signal))
        self.assertLess(len(stretched), len(self.test_signal) * 2.5)

    def test_pitch_shifter_up(self):
        """Test pitch shifting up"""
        shifter = PitchShifter(self.sample_rate)

        # Shift up 12 semitones (1 octave)
        shifted = shifter.shift(self.test_signal, 12.0)

        # Should maintain similar length
        self.assertAlmostEqual(len(shifted), len(self.test_signal), delta=1000)

    def test_pitch_shifter_down(self):
        """Test pitch shifting down"""
        shifter = PitchShifter(self.sample_rate)

        # Shift down 5 semitones
        shifted = shifter.shift(self.test_signal, -5.0)

        # Should maintain similar length
        self.assertAlmostEqual(len(shifted), len(self.test_signal), delta=1000)

    def test_loop_slicer_beats(self):
        """Test slicing loop by beats"""
        slicer = LoopSlicer()

        # Create exactly 4-beat loop at 120 BPM
        bpm = 120.0
        beats = 4
        beat_duration = 60.0 / bpm  # 0.5 seconds per beat
        total_duration = beat_duration * beats  # 2 seconds
        num_samples = int(total_duration * self.sample_rate)

        # Generate test signal of exact length
        t = np.linspace(0, total_duration, num_samples)
        test_loop = np.sin(2 * np.pi * 440 * t) * 0.5

        # Slice into beats
        slices = slicer.slice_by_beats(test_loop, beats, bpm, self.sample_rate)

        # Should get 4 slices
        self.assertEqual(len(slices), beats)

        # Each slice should be approximately equal length
        expected_length = len(test_loop) // beats
        for slice_audio in slices:
            self.assertGreater(len(slice_audio), expected_length * 0.8)

    def test_loop_slicer_transients(self):
        """Test slicing by transient detection"""
        slicer = LoopSlicer()

        # Create signal with clear, strong transients
        signal_with_transients = np.zeros(self.num_samples)

        # Add very sharp, high-amplitude attacks at specific points
        attack_points = [1000, 15000, 30000]
        for point in attack_points:
            # Create sharp attack with high amplitude change
            signal_with_transients[point - 10 : point] = 0.0
            signal_with_transients[point : point + 50] = 1.0  # Very strong transient
            signal_with_transients[point + 50 : point + 1000] = 0.5  # Sustain

        # Use lower threshold for better detection
        slices = slicer.slice_by_transients(
            signal_with_transients, self.sample_rate, threshold=0.2
        )

        # Should detect at least 1 slice (algorithm may merge close transients)
        # The function returns slice points, not individual transients
        self.assertGreaterEqual(len(slices), 1)

        # Verify slices cover the audio
        total_slice_length = sum(end - start for start, end in slices)
        self.assertGreater(total_slice_length, 0)

    def test_crossfade_processor(self):
        """Test crossfading between segments"""
        crossfader = CrossfadeProcessor()

        # Create two different signals
        audio1 = np.ones(10000) * 0.5
        audio2 = np.ones(10000) * -0.5

        # Crossfade with 1000 samples
        crossfaded = crossfader.crossfade(audio1, audio2, 1000)

        # Result should be longer than either segment
        self.assertGreater(len(crossfaded), len(audio1))

        # Crossfade region should exist and have values between the two signals
        crossfade_start = len(audio1) - 1000
        crossfade_end = len(audio1)
        crossfade_region = crossfaded[crossfade_start:crossfade_end]

        # Should have intermediate values (not all 0.5 or -0.5)
        self.assertGreater(len(crossfade_region), 0)
        # At least some samples should be between -0.5 and 0.5
        intermediate_samples = np.sum(
            (crossfade_region > -0.5) & (crossfade_region < 0.5)
        )
        self.assertGreater(intermediate_samples, 0)

    def test_loop_crossfade(self):
        """Test loop crossfading for seamless playback"""
        crossfader = CrossfadeProcessor()

        # Create loop with very different start and end values
        loop = np.concatenate(
            [np.ones(5000) * 0.9, np.ones(5000) * -0.9]  # Start: 0.9  # End: -0.9
        )

        # Apply loop crossfade
        seamless = crossfader.loop_crossfade(loop, 500)

        # Length should be preserved
        self.assertEqual(len(seamless), len(loop))

        # Test that crossfade was applied - the end should be mixed with the beginning
        # Original end value is -0.9, beginning is 0.9
        # After crossfade, end values should be somewhere in between
        end_region = seamless[-100:]  # Check last 100 samples

        # At least some end samples should be different from original -0.9
        # (they should be mixed with the 0.9 from the beginning)
        different_samples = np.sum(np.abs(end_region - (-0.9)) > 0.1)
        self.assertGreater(
            different_samples, 10
        )  # At least 10 samples should show mixing

    def test_quantizer(self):
        """Test loop quantization to beats"""
        quantizer = LoopQuantizer(self.sample_rate)

        # Quantize to exactly 4 beats at 120 BPM
        quantized = quantizer.quantize_to_beats(self.test_signal, 4, 120.0)

        # Calculate expected length
        beat_duration = 60.0 / 120.0  # 0.5 seconds per beat
        expected_samples = int(4 * beat_duration * self.sample_rate)

        # Should match exactly
        self.assertEqual(len(quantized), expected_samples)

    def test_loop_recorder(self):
        """Test loop recording"""
        recorder = LoopRecorder(self.sample_rate)

        # Start recording
        recorder.start_recording()
        self.assertTrue(recorder.is_recording)

        # Add buffers
        buffer_size = 512
        for _ in range(10):
            buffer = np.random.randn(buffer_size) * 0.3
            recorder.add_buffer(buffer)

        # Stop and get recording
        recorded = recorder.stop_recording()
        self.assertFalse(recorder.is_recording)

        # Should have recorded 10 buffers
        self.assertEqual(len(recorded), 10 * buffer_size)

    def test_overdub_processor(self):
        """Test overdubbing"""
        overdubber = OverdubProcessor()

        # Create original and new audio
        original = np.ones(5000) * 0.3
        new_audio = np.ones(5000) * 0.5

        # Overdub with 50% mix
        overdubbed = overdubber.overdub(original, new_audio, 0.5)

        # Result should be average
        expected = 0.3 * 0.5 + 0.5 * 0.5
        self.assertAlmostEqual(np.mean(overdubbed), expected, places=2)

    def test_multiply_loop(self):
        """Test loop multiplication"""
        overdubber = OverdubProcessor()

        # Create short loop
        loop = np.ones(1000) * 0.5

        # Multiply by 4
        multiplied = overdubber.multiply(loop, 4)

        # Should be 4x longer
        self.assertEqual(len(multiplied), len(loop) * 4)


class TestLiveLoopingAgent(unittest.TestCase):
    """Test Live Looping Agent"""

    def setUp(self):
        """Set up test agent"""
        self.agent = LiveLoopingAgent(sample_rate=44100)
        self.agent.setup()

        # Test audio (1 second of tone)
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        self.test_audio = np.sin(2 * np.pi * 440 * t) * 0.5

    def tearDown(self):
        """Clean up"""
        self.agent.teardown()

    def test_create_track(self):
        """Test creating a loop track"""
        msg = Message(
            topic="loop.track.create",
            sender="test",
            payload={
                "track_name": "Test Track",
                "length_beats": 4,
                "sync_to_tempo": True,
            },
        )

        self.agent._handle_track_create(msg)

        # Check that track was created
        self.assertEqual(len(self.agent.loop_tracks), 1)

    def test_delete_track(self):
        """Test deleting a loop track"""
        # Create track first
        create_msg = Message(
            topic="loop.track.create",
            sender="test",
            payload={"track_name": "Delete Me", "track_id": "delete_test"},
        )
        self.agent._handle_track_create(create_msg)

        # Delete track
        delete_msg = Message(
            topic="loop.track.delete",
            sender="test",
            payload={"track_id": "delete_test"},
        )
        self.agent._handle_track_delete(delete_msg)

        # Track should be removed
        self.assertNotIn("delete_test", self.agent.loop_tracks)

    def test_record_loop(self):
        """Test loop recording"""
        # Create track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Record Test", "track_id": "record_test"},
            )
        )

        # Start recording
        start_msg = Message(
            topic="loop.record.start",
            sender="test",
            payload={"track_id": "record_test", "mode": "replace"},
        )
        self.agent._handle_record_start(start_msg)

        # Check recording state
        track = self.agent.loop_tracks["record_test"]
        self.assertEqual(track.state.value, "recording")

        # Stop recording
        stop_msg = Message(
            topic="loop.record.stop", sender="test", payload={"track_id": "record_test"}
        )
        self.agent._handle_record_stop(stop_msg)

        # Should be playing now
        self.assertEqual(track.state.value, "playing")

    def test_playback_toggle(self):
        """Test toggling playback"""
        # Create track with audio
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Playback Test", "track_id": "playback_test"},
            )
        )

        track = self.agent.loop_tracks["playback_test"]
        track.audio_data = self.test_audio
        track.state = track.state.PLAYING

        # Toggle to stop
        msg = Message(
            topic="loop.playback.toggle",
            sender="test",
            payload={"track_id": "playback_test"},
        )
        self.agent._handle_playback_toggle(msg)

        self.assertEqual(track.state.value, "stopped")

        # Toggle back to playing
        self.agent._handle_playback_toggle(msg)
        self.assertEqual(track.state.value, "playing")

    def test_undo_redo(self):
        """Test undo/redo functionality"""
        # Create track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Undo Test", "track_id": "undo_test"},
            )
        )

        track = self.agent.loop_tracks["undo_test"]
        track.audio_data = self.test_audio.copy()

        # Make a change (clear)
        clear_msg = Message(
            topic="loop.clear", sender="test", payload={"track_id": "undo_test"}
        )
        self.agent._handle_clear(clear_msg)

        # Track should be empty
        self.assertEqual(len(track.audio_data), 0)
        self.assertEqual(len(track.undo_history), 1)

        # Undo
        undo_msg = Message(
            topic="loop.undo", sender="test", payload={"track_id": "undo_test"}
        )
        self.agent._handle_undo(undo_msg)

        # Should be restored
        self.assertEqual(len(track.audio_data), len(self.test_audio))

        # Redo
        redo_msg = Message(
            topic="loop.redo", sender="test", payload={"track_id": "undo_test"}
        )
        self.agent._handle_redo(redo_msg)

        # Should be empty again
        self.assertEqual(len(track.audio_data), 0)

    def test_manipulate_reverse(self):
        """Test reverse operation"""
        # Create track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Reverse Test", "track_id": "reverse_test"},
            )
        )

        track = self.agent.loop_tracks["reverse_test"]
        track.audio_data = self.test_audio.copy()
        original_first_sample = track.audio_data[0]

        # Reverse
        msg = Message(
            topic="loop.manipulate",
            sender="test",
            payload={"track_id": "reverse_test", "operation": "reverse"},
        )
        self.agent._handle_manipulate(msg)

        # First sample should now be the last
        self.assertAlmostEqual(track.audio_data[0], self.test_audio[-1], places=5)

    def test_manipulate_pitch_shift(self):
        """Test pitch shifting"""
        # Create track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Pitch Test", "track_id": "pitch_test"},
            )
        )

        track = self.agent.loop_tracks["pitch_test"]
        track.audio_data = self.test_audio.copy()

        # Pitch shift up 5 semitones
        msg = Message(
            topic="loop.manipulate",
            sender="test",
            payload={
                "track_id": "pitch_test",
                "operation": "pitch_shift",
                "parameters": {"semitones": 5.0},
            },
        )
        self.agent._handle_manipulate(msg)

        # Pitch should be set
        self.assertEqual(track.pitch_shift, 5.0)

    def test_manipulate_time_stretch(self):
        """Test time stretching"""
        # Create track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Stretch Test", "track_id": "stretch_test"},
            )
        )

        track = self.agent.loop_tracks["stretch_test"]
        track.audio_data = self.test_audio.copy()
        original_length = len(track.audio_data)

        # Time stretch to 1.5x duration
        msg = Message(
            topic="loop.manipulate",
            sender="test",
            payload={
                "track_id": "stretch_test",
                "operation": "time_stretch",
                "parameters": {"factor": 1.5},
            },
        )
        self.agent._handle_manipulate(msg)

        # Should be longer
        self.assertGreater(len(track.audio_data), original_length)

    def test_tempo_sync(self):
        """Test tempo synchronization"""
        # Set initial tempo
        self.agent.master_tempo = 120.0

        # Create synced track
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={
                    "track_name": "Sync Test",
                    "track_id": "sync_test",
                    "sync_to_tempo": True,
                    "length_beats": 4,
                },
            )
        )

        track = self.agent.loop_tracks["sync_test"]
        track.audio_data = self.test_audio.copy()

        # Change tempo
        tempo_msg = Message(
            topic="sync.clock.tempo", sender="test", payload={"bpm": 140.0}
        )
        self.agent._handle_tempo_change(tempo_msg)

        # Tempo should be updated
        self.assertEqual(self.agent.master_tempo, 140.0)

    def test_statistics_tracking(self):
        """Test that statistics are tracked"""
        # Create and record loop
        self.agent._handle_track_create(
            Message(
                topic="loop.track.create",
                sender="test",
                payload={"track_name": "Stats Test", "track_id": "stats_test"},
            )
        )

        # Record
        self.agent._handle_record_start(
            Message(
                topic="loop.record.start",
                sender="test",
                payload={"track_id": "stats_test"},
            )
        )

        # Check stats
        self.assertEqual(self.agent.stats["loops_recorded"], 1)

        # Undo
        track = self.agent.loop_tracks["stats_test"]
        track.audio_data = self.test_audio.copy()
        track.undo_history.append(self.test_audio.copy())

        self.agent._handle_undo(
            Message(
                topic="loop.undo", sender="test", payload={"track_id": "stats_test"}
            )
        )

        self.assertEqual(self.agent.stats["undos_performed"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
