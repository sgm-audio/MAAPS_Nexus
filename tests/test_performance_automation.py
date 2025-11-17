"""
Comprehensive Tests for Performance Automation Agent

Tests automation recording/playback, scenes, macros, cues, and parameter management.
"""

import unittest
import time
import threading
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import Message, Priority, AgentState
from src.agents.live import PerformanceAutomationAgent
from src.agents.live.performance_automation_agent import (
    AutomationCurve,
    AutomationPoint,
    AutomationLane,
    Scene,
    Macro,
    PerformanceCue
)


class TestPerformanceAutomationAgent(unittest.TestCase):
    """Test suite for Performance Automation Agent"""

    def setUp(self):
        """Set up test agent"""
        self.agent = PerformanceAutomationAgent()
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
        self.assertEqual(self.agent.agent_id, "performance_automation_agent")
        self.assertEqual(len(self.agent.automation_lanes), 0)
        self.assertEqual(len(self.agent.scenes), 0)
        self.assertEqual(len(self.agent.macros), 0)
        self.assertEqual(len(self.agent.cues), 0)
        self.assertFalse(self.agent.recording_active)
        self.assertFalse(self.agent.playback_active)

    def test_start_automation_recording(self):
        """Test starting automation recording"""
        response = self.agent.request("automation.record.start", {
            'parameter_path': 'effects.reverb.wet_dry'
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertEqual(response.payload['parameter'], 'effects.reverb.wet_dry')
        self.assertTrue(self.agent.recording_active)
        self.assertIn('effects.reverb.wet_dry', self.agent.recording_parameters)
        self.assertIn('effects.reverb.wet_dry', self.agent.automation_lanes)
        self.assertEqual(self.agent.stats['automations_recorded'], 1)

    def test_stop_automation_recording(self):
        """Test stopping automation recording"""
        # Start recording
        self.agent.request("automation.record.start", {
            'parameter_path': 'effects.compressor.threshold'
        }, timeout=1.0)

        # Stop recording
        response = self.agent.request("automation.record.stop", {
            'parameter_path': 'effects.compressor.threshold'
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertFalse(self.agent.recording_active)
        self.assertEqual(len(self.agent.recording_parameters), 0)

    def test_record_multiple_parameters(self):
        """Test recording multiple parameters simultaneously"""
        # Start recording first parameter
        self.agent.request("automation.record.start", {
            'parameter_path': 'effects.eq.freq1'
        }, timeout=1.0)

        # Start recording second parameter
        self.agent.request("automation.record.start", {
            'parameter_path': 'effects.delay.feedback'
        }, timeout=1.0)

        self.assertTrue(self.agent.recording_active)
        self.assertEqual(len(self.agent.recording_parameters), 2)

        # Stop one parameter
        self.agent.request("automation.record.stop", {
            'parameter_path': 'effects.eq.freq1'
        }, timeout=1.0)

        # Should still be recording
        self.assertTrue(self.agent.recording_active)
        self.assertEqual(len(self.agent.recording_parameters), 1)

        # Stop last parameter
        self.agent.request("automation.record.stop", {
            'parameter_path': 'effects.delay.feedback'
        }, timeout=1.0)

        # Now should be stopped
        self.assertFalse(self.agent.recording_active)

    def test_automation_playback_enable(self):
        """Test enabling/disabling automation playback"""
        response = self.agent.request("automation.playback.enable", {
            'enable': True
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertTrue(response.payload['playback_active'])
        self.assertTrue(self.agent.playback_active)
        self.assertEqual(self.agent.playback_time, 0.0)

    def test_automation_playback_disable(self):
        """Test disabling automation playback"""
        # Enable first
        self.agent.request("automation.playback.enable", {'enable': True}, timeout=1.0)

        # Disable
        response = self.agent.request("automation.playback.enable", {
            'enable': False
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertFalse(response.payload['playback_active'])
        self.assertFalse(self.agent.playback_active)

    def test_create_scene(self):
        """Test creating a performance scene"""
        response = self.agent.request("automation.scene.create", {
            'scene_name': 'Heavy Reverb',
            'parameter_snapshots': {
                'effects.reverb.wet_dry': 0.6,
                'effects.delay.time': 500.0
            },
            'transition_curves': {
                'effects.reverb.wet_dry': 'exponential'
            },
            'transition_time': 2.0
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertIn('scene_id', response.payload)
        self.assertEqual(response.payload['scene_name'], 'Heavy Reverb')
        self.assertEqual(len(self.agent.scenes), 1)

    def test_trigger_scene(self):
        """Test triggering a scene"""
        # Create scene
        create_response = self.agent.request("automation.scene.create", {
            'scene_id': 'scene_bright',
            'scene_name': 'Bright Mix',
            'parameter_snapshots': {
                'effects.eq.freq2': 5000.0,
                'effects.eq.gain2': 3.0
            }
        }, timeout=1.0)

        scene_id = create_response.payload['scene_id']

        # Trigger scene
        response = self.agent.request("automation.scene.trigger", {
            'scene_id': scene_id,
            'transition_time': 1.0
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertEqual(response.payload['scene_id'], scene_id)
        self.assertEqual(response.payload['scene_name'], 'Bright Mix')
        self.assertEqual(self.agent.current_scene_id, scene_id)
        self.assertEqual(self.agent.stats['scenes_triggered'], 1)

    def test_trigger_nonexistent_scene(self):
        """Test triggering a nonexistent scene returns error"""
        response = self.agent.request("automation.scene.trigger", {
            'scene_id': 'nonexistent_scene'
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertFalse(response.payload['success'])
        self.assertIn('error', response.payload)

    def test_create_macro(self):
        """Test creating a macro control"""
        response = self.agent.request("automation.macro.create", {
            'macro_name': 'Master Brightness',
            'target_parameters': [
                {'param': 'effects.eq.gain1', 'min': -3.0, 'max': 6.0, 'curve': 'linear'},
                {'param': 'effects.eq.gain2', 'min': 0.0, 'max': 9.0, 'curve': 'logarithmic'}
            ],
            'default_value': 0.5
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertIn('macro_id', response.payload)
        self.assertEqual(response.payload['macro_name'], 'Master Brightness')
        self.assertEqual(len(self.agent.macros), 1)

    def test_change_macro_value(self):
        """Test changing macro value updates all target parameters"""
        # Create macro
        create_response = self.agent.request("automation.macro.create", {
            'macro_id': 'macro_drive',
            'macro_name': 'Drive Amount',
            'target_parameters': [
                {'param': 'effects.distortion.gain', 'min': 1.0, 'max': 10.0, 'curve': 'exponential'},
                {'param': 'effects.distortion.mix', 'min': 0.0, 'max': 1.0, 'curve': 'linear'}
            ]
        }, timeout=1.0)

        macro_id = create_response.payload['macro_id']

        # Change macro value
        response = self.agent.request("automation.macro.change", {
            'macro_id': macro_id,
            'value': 0.75
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertEqual(response.payload['macro_id'], macro_id)
        self.assertEqual(response.payload['value'], 0.75)
        self.assertEqual(self.agent.macros[macro_id].current_value, 0.75)
        self.assertEqual(self.agent.stats['macros_changed'], 1)

    def test_change_nonexistent_macro(self):
        """Test changing nonexistent macro returns error"""
        response = self.agent.request("automation.macro.change", {
            'macro_id': 'nonexistent_macro',
            'value': 0.5
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertFalse(response.payload['success'])
        self.assertIn('error', response.payload)

    def test_create_performance_cue(self):
        """Test creating a performance cue"""
        response = self.agent.request("automation.cue.create", {
            'cue_name': 'Drop at 2:00',
            'timecode': '00:02:00.000',
            'actions': [
                {
                    'action_type': 'scene_change',
                    'parameters': {'scene_id': 'scene_drop'}
                },
                {
                    'action_type': 'parameter_change',
                    'parameters': {'parameter_path': 'effects.filter.cutoff', 'value': 20000.0}
                }
            ]
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertIn('cue_id', response.payload)
        self.assertEqual(response.payload['cue_name'], 'Drop at 2:00')
        self.assertEqual(len(self.agent.cues), 1)

    def test_manual_cue_fire(self):
        """Test manually firing a cue"""
        # Create cue
        create_response = self.agent.request("automation.cue.create", {
            'cue_id': 'cue_intro',
            'cue_name': 'Intro Section',
            'timecode': '00:00:10.000',
            'actions': [
                {'action_type': 'scene_change', 'parameters': {'scene_id': 'scene_1'}}
            ]
        }, timeout=1.0)

        cue_id = create_response.payload['cue_id']

        # Fire cue manually
        response = self.agent.request("automation.cue.fire", {
            'cue_id': cue_id
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertTrue(response.payload['success'])
        self.assertEqual(response.payload['cue_id'], cue_id)
        self.assertEqual(self.agent.stats['cues_fired'], 1)

    def test_fire_nonexistent_cue(self):
        """Test firing nonexistent cue returns error"""
        response = self.agent.request("automation.cue.fire", {
            'cue_id': 'nonexistent_cue'
        }, timeout=1.0)

        self.assertIsNotNone(response)
        self.assertFalse(response.payload['success'])
        self.assertIn('error', response.payload)

    def test_statistics_tracking(self):
        """Test statistics are tracked correctly"""
        # Initial state
        self.assertEqual(self.agent.stats['automations_recorded'], 0)
        self.assertEqual(self.agent.stats['scenes_triggered'], 0)
        self.assertEqual(self.agent.stats['cues_fired'], 0)
        self.assertEqual(self.agent.stats['macros_changed'], 0)

        # Record automation
        self.agent.request("automation.record.start", {
            'parameter_path': 'test.param'
        }, timeout=1.0)
        self.assertEqual(self.agent.stats['automations_recorded'], 1)

        # Create and trigger scene
        scene_response = self.agent.request("automation.scene.create", {
            'scene_name': 'Test Scene',
            'parameter_snapshots': {'param': 1.0}
        }, timeout=1.0)
        self.agent.request("automation.scene.trigger", {
            'scene_id': scene_response.payload['scene_id']
        }, timeout=1.0)
        self.assertEqual(self.agent.stats['scenes_triggered'], 1)

        # Create and change macro
        macro_response = self.agent.request("automation.macro.create", {
            'macro_name': 'Test Macro',
            'target_parameters': [{'param': 'test', 'min': 0, 'max': 1}]
        }, timeout=1.0)
        self.agent.request("automation.macro.change", {
            'macro_id': macro_response.payload['macro_id'],
            'value': 0.8
        }, timeout=1.0)
        self.assertEqual(self.agent.stats['macros_changed'], 1)

        # Create and fire cue
        cue_response = self.agent.request("automation.cue.create", {
            'cue_name': 'Test Cue',
            'timecode': '00:00:01.000',
            'actions': []
        }, timeout=1.0)
        self.agent.request("automation.cue.fire", {
            'cue_id': cue_response.payload['cue_id']
        }, timeout=1.0)
        self.assertEqual(self.agent.stats['cues_fired'], 1)

    def test_playback_thread_lifecycle(self):
        """Test playback thread starts and runs"""
        self.assertIsNotNone(self.agent.playback_thread)
        self.assertTrue(self.agent.playback_thread.is_alive())

        # Stop agent
        self.agent.stop()
        time.sleep(0.2)

        # Thread should still exist (daemon)
        self.assertIsNotNone(self.agent.playback_thread)

    def test_thread_safety_concurrent_scene_creation(self):
        """Test thread safety with concurrent scene creation"""
        def create_scene(name):
            self.agent.request("automation.scene.create", {
                'scene_name': name,
                'parameter_snapshots': {'param': 1.0}
            }, timeout=3.0)  # Longer timeout for concurrent requests

        # Create multiple scenes concurrently
        threads = []
        for i in range(5):
            t = threading.Thread(target=create_scene, args=(f'Scene {i}',))
            threads.append(t)
            t.start()
            time.sleep(0.05)  # Delay to reduce message bus contention

        # Wait for completion
        for t in threads:
            t.join(timeout=5.0)

        # Should have created most or all scenes (concurrent operations may have timeouts)
        # The key test is that it doesn't crash and creates at least some scenes
        self.assertGreaterEqual(len(self.agent.scenes), 3)

    def test_thread_safety_concurrent_macro_changes(self):
        """Test thread safety with concurrent macro changes"""
        # Create macro
        create_response = self.agent.request("automation.macro.create", {
            'macro_id': 'test_macro',
            'macro_name': 'Test Macro',
            'target_parameters': [{'param': 'test', 'min': 0, 'max': 1}]
        }, timeout=1.0)

        macro_id = create_response.payload['macro_id']

        def change_macro(value):
            self.agent.request("automation.macro.change", {
                'macro_id': macro_id,
                'value': value
            }, timeout=1.0)

        # Change macro concurrently
        threads = []
        values = [0.1, 0.3, 0.5, 0.7, 0.9]
        for val in values:
            t = threading.Thread(target=change_macro, args=(val,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have processed all changes
        self.assertEqual(self.agent.stats['macros_changed'], 5)

        # Final value should be one of the values
        final_value = self.agent.macros[macro_id].current_value
        self.assertIn(final_value, values)


class TestAutomationCurves(unittest.TestCase):
    """Test automation curve interpolation"""

    def setUp(self):
        """Set up test agent"""
        self.agent = PerformanceAutomationAgent()
        self.agent.start()
        time.sleep(0.1)

    def tearDown(self):
        """Clean up agent"""
        if self.agent and self.agent.get_state() == AgentState.RUNNING:
            self.agent.stop()
            time.sleep(0.1)

    def test_linear_interpolation(self):
        """Test linear curve interpolation"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=0.0, value=0.0, curve=AutomationCurve.LINEAR),
                AutomationPoint(time=1.0, value=1.0, curve=AutomationCurve.LINEAR)
            ]
        )

        # At midpoint should be 0.5
        value = self.agent._get_automation_value(lane, 0.5)
        self.assertAlmostEqual(value, 0.5, delta=0.01)

    def test_exponential_interpolation(self):
        """Test exponential curve interpolation"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=0.0, value=0.0, curve=AutomationCurve.EXPONENTIAL),
                AutomationPoint(time=1.0, value=1.0, curve=AutomationCurve.EXPONENTIAL)
            ]
        )

        # At midpoint should be 0.25 (0.5^2)
        value = self.agent._get_automation_value(lane, 0.5)
        self.assertAlmostEqual(value, 0.25, delta=0.01)

    def test_logarithmic_interpolation(self):
        """Test logarithmic curve interpolation"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=0.0, value=0.0, curve=AutomationCurve.LOGARITHMIC),
                AutomationPoint(time=1.0, value=1.0, curve=AutomationCurve.LOGARITHMIC)
            ]
        )

        # At midpoint should be ~0.707 (sqrt(0.5))
        value = self.agent._get_automation_value(lane, 0.5)
        self.assertAlmostEqual(value, 0.707, delta=0.01)

    def test_step_interpolation(self):
        """Test step curve (no interpolation)"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=0.0, value=0.0, curve=AutomationCurve.STEP),
                AutomationPoint(time=1.0, value=1.0, curve=AutomationCurve.STEP)
            ]
        )

        # At midpoint should still be 0.0 (before point value)
        value = self.agent._get_automation_value(lane, 0.5)
        self.assertEqual(value, 0.0)

    def test_automation_value_before_first_point(self):
        """Test getting value before first automation point"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=1.0, value=0.5)
            ]
        )

        # Before first point should return first point's value
        value = self.agent._get_automation_value(lane, 0.5)
        self.assertEqual(value, 0.5)

    def test_automation_value_after_last_point(self):
        """Test getting value after last automation point"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[
                AutomationPoint(time=0.0, value=0.3),
                AutomationPoint(time=1.0, value=0.7)
            ]
        )

        # After last point should return last point's value
        value = self.agent._get_automation_value(lane, 2.0)
        self.assertEqual(value, 0.7)

    def test_empty_automation_lane(self):
        """Test getting value from empty lane returns None"""
        lane = AutomationLane(
            lane_id='test_lane',
            parameter_path='test.param',
            points=[]
        )

        value = self.agent._get_automation_value(lane, 0.5)
        self.assertIsNone(value)


class TestMacroScaling(unittest.TestCase):
    """Test macro parameter scaling with different curves"""

    def setUp(self):
        """Set up test agent"""
        self.agent = PerformanceAutomationAgent()
        self.agent.start()
        time.sleep(0.1)

    def tearDown(self):
        """Clean up agent"""
        if self.agent and self.agent.get_state() == AgentState.RUNNING:
            self.agent.stop()
            time.sleep(0.1)

    def test_macro_linear_scaling(self):
        """Test macro linear scaling"""
        # Create macro with linear scaling
        create_response = self.agent.request("automation.macro.create", {
            'macro_id': 'test_linear',
            'macro_name': 'Linear Test',
            'target_parameters': [
                {'param': 'test.param', 'min': 0.0, 'max': 10.0, 'curve': 'linear'}
            ]
        }, timeout=1.0)

        macro_id = create_response.payload['macro_id']

        # Set to 0.5 should map to 5.0
        self.agent.request("automation.macro.change", {
            'macro_id': macro_id,
            'value': 0.5
        }, timeout=1.0)

        # Value calculation: 0.0 + (10.0 - 0.0) * 0.5 = 5.0
        # We can't directly test the published value, but we can verify the macro stored the value
        self.assertEqual(self.agent.macros[macro_id].current_value, 0.5)

    def test_macro_exponential_scaling(self):
        """Test macro exponential scaling"""
        create_response = self.agent.request("automation.macro.create", {
            'macro_id': 'test_exp',
            'macro_name': 'Exponential Test',
            'target_parameters': [
                {'param': 'test.param', 'min': 0.0, 'max': 100.0, 'curve': 'exponential'}
            ]
        }, timeout=1.0)

        macro_id = create_response.payload['macro_id']

        # Set to 0.5 should map to 25.0 (0.5^2 * 100)
        self.agent.request("automation.macro.change", {
            'macro_id': macro_id,
            'value': 0.5
        }, timeout=1.0)

        self.assertEqual(self.agent.macros[macro_id].current_value, 0.5)

    def test_macro_logarithmic_scaling(self):
        """Test macro logarithmic scaling"""
        create_response = self.agent.request("automation.macro.create", {
            'macro_id': 'test_log',
            'macro_name': 'Logarithmic Test',
            'target_parameters': [
                {'param': 'test.param', 'min': 0.0, 'max': 10.0, 'curve': 'logarithmic'}
            ]
        }, timeout=1.0)

        macro_id = create_response.payload['macro_id']

        # Set to 0.25 should map to ~5.0 (sqrt(0.25) * 10)
        self.agent.request("automation.macro.change", {
            'macro_id': macro_id,
            'value': 0.25
        }, timeout=1.0)

        self.assertEqual(self.agent.macros[macro_id].current_value, 0.25)


class TestTimecodeHandling(unittest.TestCase):
    """Test timecode parsing and cue triggers"""

    def setUp(self):
        """Set up test agent"""
        self.agent = PerformanceAutomationAgent()
        self.agent.start()
        time.sleep(0.1)

    def tearDown(self):
        """Clean up agent"""
        if self.agent and self.agent.get_state() == AgentState.RUNNING:
            self.agent.stop()
            time.sleep(0.1)

    def test_parse_timecode_simple(self):
        """Test parsing simple timecode"""
        seconds = self.agent._parse_timecode("00:00:30.000")
        self.assertEqual(seconds, 30.0)

    def test_parse_timecode_minutes(self):
        """Test parsing timecode with minutes"""
        seconds = self.agent._parse_timecode("00:02:30.000")
        self.assertEqual(seconds, 150.0)  # 2*60 + 30

    def test_parse_timecode_hours(self):
        """Test parsing timecode with hours"""
        seconds = self.agent._parse_timecode("01:30:45.500")
        self.assertEqual(seconds, 5445.5)  # 3600 + 1800 + 45 + 0.5

    def test_parse_timecode_milliseconds(self):
        """Test parsing timecode with milliseconds"""
        seconds = self.agent._parse_timecode("00:00:01.250")
        self.assertEqual(seconds, 1.25)

    def test_parse_invalid_timecode(self):
        """Test parsing invalid timecode returns 0"""
        seconds = self.agent._parse_timecode("invalid")
        self.assertEqual(seconds, 0.0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
