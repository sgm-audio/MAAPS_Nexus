"""
Unit tests for the MAAPS Nexus system orchestrator.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from src.nexus_system import MAAPSNexusSystem
from src.core.audio_ontology import AudioState, AudioAttribute


class TestMAAPSNexusSystem:
    """Test suite for MAAPSNexusSystem class."""
    
    @pytest.fixture
    def mock_ray(self):
        """Mock Ray initialization and methods."""
        with patch('src.nexus_system.ray') as mock_ray:
            mock_ray.is_initialized.return_value = False
            mock_ray.init.return_value = None
            mock_ray.get.return_value = Mock()
            yield mock_ray
    
    @pytest.fixture
    def mock_cluster_manager(self):
        """Mock RayClusterManager."""
        with patch('src.nexus_system.RayClusterManager') as mock:
            mock_instance = Mock()
            mock_instance.initialize.return_value = None
            mock_instance.get_cluster_info.return_value = {'available_resources': {'CPU': 4}}
            mock_instance.shutdown.return_value = None
            mock.return_value = mock_instance
            yield mock
    
    @pytest.fixture
    def mock_ontology(self):
        """Mock AudioOntologyManager."""
        with patch('src.nexus_system.AudioOntologyManager') as mock:
            mock_instance = Mock()
            mock_instance.get_attribute_correlation.return_value = -0.8
            mock.return_value = mock_instance
            yield mock
    
    @pytest.fixture
    def mock_agents(self):
        """Mock all agent classes."""
        with patch('src.nexus_system.CriticAgent') as mock_critic, \
             patch('src.nexus_system.EQRLAgent') as mock_eq, \
             patch('src.nexus_system.DynamicsRLAgent') as mock_dynamics, \
             patch('src.nexus_system.HGOCoordinator') as mock_coordinator:
            
            # Setup mock agent instances
            mock_critic_instance = Mock()
            mock_critic_instance.evaluate.remote.return_value = Mock(reward=0.5)
            mock_critic.return_value = mock_critic_instance
            
            mock_eq_instance = Mock()
            mock_eq_instance.process_audio.remote.return_value = (np.zeros(512), np.zeros(8))
            mock_eq_instance.store_experience.remote.return_value = None
            mock_eq_instance.train_step.remote.return_value = None
            mock_eq.return_value = mock_eq_instance
            
            mock_dynamics_instance = Mock()
            mock_dynamics_instance.process_audio.remote.return_value = (np.zeros(512), np.zeros(7))
            mock_dynamics_instance.store_experience.remote.return_value = None
            mock_dynamics_instance.train_step.remote.return_value = None
            mock_dynamics.return_value = mock_dynamics_instance
            
            mock_coordinator_instance = Mock()
            mock_coordinator_instance.coordinate.remote.return_value = Mock(
                approved_proposals=[]
            )
            mock_coordinator_instance.get_statistics.remote.return_value = {}
            mock_coordinator_instance.register_agent.remote.return_value = None
            mock_coordinator.return_value = mock_coordinator_instance
            
            yield {
                'critic': mock_critic,
                'eq': mock_eq,
                'dynamics': mock_dynamics,
                'coordinator': mock_coordinator
            }
    
    @pytest.fixture
    def mock_plugin_comm(self):
        """Mock plugin communicators."""
        with patch('src.nexus_system.StreamingPluginCommunicator') as mock_streaming, \
             patch('src.nexus_system.AraPluginCommunicator') as mock_ara:
            
            mock_streaming_instance = Mock()
            mock_streaming_instance.start.return_value = None
            mock_streaming_instance.get_audio_for_processing.return_value = np.zeros((512, 2))
            mock_streaming_instance.send_processed_audio.return_value = None
            mock_streaming_instance.close.return_value = None
            mock_streaming_instance.get_latency_info.return_value = {'latency_ms': 1.0}
            mock_streaming.return_value = mock_streaming_instance
            
            mock_ara_instance = Mock()
            mock_ara_instance.start.return_value = None
            mock_ara_instance.stop.return_value = None
            mock_ara.return_value = mock_ara_instance
            
            yield {
                'streaming': mock_streaming,
                'ara': mock_ara
            }
    
    def test_system_initialization_test_mode(self, mock_ray, mock_cluster_manager, 
                                          mock_ontology, mock_agents, mock_plugin_comm):
        """Test system initialization in test mode."""
        system = MAAPSNexusSystem(
            plugin_mode="none",
            num_cpus=2,
            buffer_size=512,
            sample_rate=44100
        )
        
        # Verify initialization
        assert system.buffer_size == 512
        assert system.sample_rate == 44100
        assert system.plugin_mode == "none"
        assert system.total_frames_processed == 0
        assert system.total_training_steps == 0
        
        # Verify cluster initialized
        mock_cluster_manager.assert_called_once_with(num_cpus=2, num_gpus=None)
        mock_cluster_manager.return_value.initialize.assert_called_once()
        
        # Verify ontology initialized
        mock_ontology.assert_called_once()
        
        # Verify agents initialized
        assert system.critic_agent is not None
        assert system.eq_agent is not None
        assert system.dynamics_agent is not None
        assert system.coordinator is not None
        
        # Verify no plugin communicators for none mode
        assert system.streaming_comm is None
        assert system.ara_comm is None
    
    def test_system_initialization_vst3_mode(self, mock_ray, mock_cluster_manager, 
                                           mock_ontology, mock_agents, mock_plugin_comm):
        """Test system initialization in VST3 mode."""
        system = MAAPSNexusSystem(
            plugin_mode="vst3",
            num_cpus=2,
            buffer_size=512,
            sample_rate=44100
        )
        
        # Verify streaming communicator initialized
        assert system.streaming_comm is not None
        mock_plugin_comm['streaming'].return_value.start.assert_called_once()
        
        # Verify ARA communicator not initialized
        assert system.ara_comm is None
    
    def test_system_initialization_ara_mode(self, mock_ray, mock_cluster_manager, 
                                          mock_ontology, mock_agents, mock_plugin_comm):
        """Test system initialization in ARA mode."""
        system = MAAPSNexusSystem(
            plugin_mode="ara",
            num_cpus=2,
            buffer_size=512,
            sample_rate=44100
        )
        
        # Verify ARA communicator initialized
        assert system.ara_comm is not None
        mock_plugin_comm['ara'].return_value.start.assert_called_once()
        
        # Verify streaming communicator not initialized
        assert system.streaming_comm is None
    
    def test_process_audio_frame_success(self, mock_ray, mock_cluster_manager, 
                                       mock_ontology, mock_agents, mock_plugin_comm):
        """Test successful audio frame processing."""
        system = MAAPSNexusSystem(plugin_mode="none")
        
        # Create test audio
        audio_input = np.random.randn(512, 2) * 0.1  # stereo audio
        current_state = AudioState()
        for attr in AudioAttribute:
            current_state.set_attribute(attr, 0.5)
        
        # Process audio frame
        processed_audio, new_state = system.process_audio_frame(audio_input, current_state)
        
        # Verify outputs
        assert processed_audio is not None
        assert isinstance(processed_audio, np.ndarray)
        assert processed_audio.shape == audio_input.shape  # Should maintain shape
        
        assert isinstance(new_state, AudioState)
        
        # Verify agent methods were called
        mock_agents['eq'].return_value.process_audio.remote.assert_called_once()
        mock_agents['dynamics'].return_value.process_audio.remote.assert_called_once()
        mock_agents['coordinator'].return_value.coordinate.remote.assert_called_once()
        mock_agents['critic'].return_value.evaluate.remote.assert_called_once()
        
        # Verify stats incremented
        assert system.total_frames_processed == 1
    
    def test_process_audio_frame_agents_not_initialized(self, mock_ray, mock_cluster_manager, 
                                                      mock_ontology, mock_plugin_comm):
        """Test processing frame when agents not initialized."""
        system = MAAPSNexusSystem(plugin_mode="none")
        # Manually set agents to None to simulate failure
        system.eq_agent = None
        
        audio_input = np.random.randn(512, 2)
        current_state = AudioState()
        
        with pytest.raises(RuntimeError, match="Agents not initialized"):
            system.process_audio_frame(audio_input, current_state)
    
    def test_run_standalone_test(self, mock_ray, mock_cluster_manager, 
                                mock_ontology, mock_agents, mock_plugin_comm):
        """Test standalone test mode execution."""
        system = MAAPSNexusSystem(plugin_mode="none")
        
        # Run short test
        system.run_standalone_test(duration_seconds=0.1)  # Short duration for test
        
        # Verify processing occurred
        assert system.total_frames_processed > 0
        assert system.total_training_steps >= 0
    
    def test_shutdown(self, mock_ray, mock_cluster_manager, 
                     mock_ontology, mock_agents, mock_plugin_comm):
        """Test system shutdown."""
        system = MAAPSNexusSystem(plugin_mode="none")
        
        # Initialize plugin comm for testing
        system.streaming_comm = mock_plugin_comm['streaming'].return_value
        system.ara_comm = mock_plugin_comm['ara'].return_value
        
        # Shutdown
        system.shutdown()
        
        # Verify cleanup called
        mock_cluster_manager.return_value.shutdown.assert_called_once()
        mock_plugin_comm['streaming'].return_value.close.assert_called_once()
        mock_plugin_comm['ara'].return_value.stop.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])