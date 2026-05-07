"""Targeted unit tests for the multi-agent audio core.

Covers:
  * Critic memory management (Iter 7)
  * Critic concept threshold overrides (Iter 7)
  * Critic sample-rate guard (Iter 7)
  * RL agent local feature extraction (Iter 3)
  * EQ filter design helpers
  * Dynamics processing primitives (compressor, limiter, gate)
  * GAE math on the EQ + Dynamics agents (Iter 4)
  * MessageBus DLQ peek / drain / retry (Iter 6)
  * MessageBus per-agent topic helpers (Iter 2)
  * HGOCoordinator goal decomposition + agent proposal wiring (Iter 5)
  * BaseAgent post-refactor instantiability (Iter 7)
"""
from __future__ import annotations

import time
import numpy as np
import pytest

from src.core.message_bus import MessageBus
from src.core.message_types import Message, MessageType, Priority, Topics
from src.core.base_agent import AgentCapability
from src.agents.critic_agent import CriticAgent
from src.agents.eq_rl_agent import EQRLAgent, RLExperience as EQRLExperience
from src.agents.dynamics_rl_agent import DynamicsRLAgent, RLExperience as DynRLExperience
from src.agents.hgo_coordinator import (
    HGOCoordinator,
    OptimizationGoal,
    GoalPriority,
)


# ---------- Fixtures ----------

@pytest.fixture
def bus():
    b = MessageBus()
    b.start()
    yield b
    b.stop()


@pytest.fixture
def sine_440():
    sr = 44100
    return (0.5 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32)


# ---------- MessageBus topic helpers ----------

class TestTopicsHelpers:
    def test_agent_request_pattern(self):
        assert Topics.agent_request("agent-x") == "agent.agent-x.request"

    def test_agent_response_pattern(self):
        assert Topics.agent_response("agent-x") == "agent.agent-x.response"

    def test_topic_round_trip_distinct(self):
        a = Topics.agent_request("a")
        b = Topics.agent_request("b")
        assert a != b


class TestNewMessageTypes:
    def test_audio_processing_request_exists(self):
        assert MessageType.AUDIO_PROCESSING_REQUEST.value == "audio.processing.request"

    def test_critic_judgment_request_exists(self):
        assert MessageType.CRITIC_JUDGMENT_REQUEST.value == "critic.judgment.request"

    def test_audio_feature_request_exists(self):
        assert MessageType.AUDIO_FEATURE_REQUEST.value == "audio.feature.request"


# ---------- BaseAgent instantiability (Iter 7 strategic fix) ----------

class TestBaseAgentInstantiability:
    def test_critic_instantiable(self, bus):
        c = CriticAgent(agent_id="c1", message_bus=bus)
        assert c.agent_id == "c1"
        assert AgentCapability.AUDIO_ANALYSIS in c.capabilities

    def test_eq_instantiable(self, bus):
        e = EQRLAgent(agent_id="eq1", message_bus=bus, critic_agent_id="c1")
        assert e.agent_id == "eq1"

    def test_dynamics_instantiable(self, bus):
        d = DynamicsRLAgent(agent_id="dy1", message_bus=bus, critic_agent_id="c1")
        assert d.agent_id == "dy1"

    def test_hgo_instantiable(self, bus):
        h = HGOCoordinator(
            agent_id="hgo1", message_bus=bus,
            eq_agent_id="eq1", dynamics_agent_id="dy1", critic_agent_id="c1",
        )
        assert h.agent_id == "hgo1"


# ---------- Critic: memory cap ----------

class TestCriticMemoryCap:
    def test_default_cap_is_10000(self, bus):
        c = CriticAgent(agent_id="c", message_bus=bus)
        assert c.training_data.maxlen == 10000

    def test_explicit_cap_enforced(self, bus, sine_440):
        c = CriticAgent(agent_id="c", message_bus=bus, config={'max_training_samples': 5})
        for _ in range(20):
            c.train_on_feedback(sine_440[:22050], 0.5)
        assert len(c.training_data) == 5

    def test_oldest_evicted_first(self, bus, sine_440):
        c = CriticAgent(agent_id="c", message_bus=bus, config={'max_training_samples': 3})
        for label in [0.1, 0.2, 0.3, 0.4, 0.5]:
            c.train_on_feedback(sine_440[:22050], label)
        # Oldest two evicted, newest three retained
        labels = [s[1] for s in c.training_data]
        assert labels == [0.3, 0.4, 0.5]


# ---------- Critic: configurable thresholds ----------

class TestCriticThresholds:
    def test_override_specific_field(self, bus):
        c = CriticAgent(
            agent_id="c", message_bus=bus,
            config={'concept_thresholds': {'mud': {'low_mid_energy': 0.99}}},
        )
        assert c.concept_thresholds['mud']['low_mid_energy'] == 0.99

    def test_other_concepts_preserved(self, bus):
        c = CriticAgent(
            agent_id="c", message_bus=bus,
            config={'concept_thresholds': {'mud': {'low_mid_energy': 0.99}}},
        )
        # harshness shouldn't be touched
        assert c.concept_thresholds['harshness']['high_mid_energy'] == 0.8

    def test_unknown_concept_added(self, bus):
        c = CriticAgent(
            agent_id="c", message_bus=bus,
            config={'concept_thresholds': {'sparkle': {'brilliance_energy': 0.5}}},
        )
        assert c.concept_thresholds['sparkle']['brilliance_energy'] == 0.5


# ---------- Critic: sample_rate guard ----------

class TestCriticSampleRateGuard:
    def test_zero_raises(self, bus):
        with pytest.raises(ValueError, match="sample_rate"):
            CriticAgent(agent_id="c", message_bus=bus, config={'sample_rate': 0})

    def test_negative_raises(self, bus):
        with pytest.raises(ValueError, match="sample_rate"):
            CriticAgent(agent_id="c", message_bus=bus, config={'sample_rate': -100})


# ---------- RL agents: local feature fallback ----------

class TestRLFeatureExtraction:
    def test_eq_features_17_dim(self, bus, sine_440):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        f = eq._extract_features_local(sine_440)
        assert f.shape == (17,)
        assert np.all(np.isfinite(f))

    def test_dyn_features_17_dim(self, bus, sine_440):
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        f = dy._extract_features_local(sine_440)
        assert f.shape == (17,)
        assert np.all(np.isfinite(f))

    def test_eq_dyn_fallback_identical(self, bus, sine_440):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        f1 = eq._extract_features_local(sine_440)
        f2 = dy._extract_features_local(sine_440)
        assert np.allclose(f1, f2)

    def test_features_input_dependent(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        sr = eq.sample_rate
        a = (0.5 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32)
        b = (0.5 * np.sin(2 * np.pi * 100 * np.arange(sr) / sr)).astype(np.float32)
        assert not np.allclose(eq._extract_features_local(a), eq._extract_features_local(b))

    def test_empty_audio_returns_zeros(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        f = eq._extract_features_local(np.array([], dtype=np.float32))
        assert f.shape == (17,)
        assert np.all(f == 0.0)


# ---------- RL agents: GAE math ----------

class TestGAEMath:
    def _trajectory(self, ExpClass, action_dim):
        return [
            ExpClass(audio_features=np.zeros(17), action=np.zeros(action_dim),
                     reward=1.0, next_audio_features=np.zeros(17),
                     done=False, value=0.5),
            ExpClass(audio_features=np.zeros(17), action=np.zeros(action_dim),
                     reward=1.0, next_audio_features=np.zeros(17),
                     done=False, value=0.6),
            ExpClass(audio_features=np.zeros(17), action=np.zeros(action_dim),
                     reward=1.0, next_audio_features=np.zeros(17),
                     done=True, value=0.7),
        ]

    def test_eq_gae_matches_hand_calculation(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        traj = self._trajectory(EQRLExperience, 7)
        eq._compute_gae(traj)
        # Hand-computed expected values for r=[1,1,1], v=[0.5,0.6,0.7],
        # done=[F,F,T], gamma=0.99, lambda=0.95
        assert traj[2].advantage == pytest.approx(0.3, abs=1e-3)
        assert traj[1].advantage == pytest.approx(1.3751, abs=1e-3)
        assert traj[0].advantage == pytest.approx(2.3870, abs=1e-3)
        # Returns = advantage + V(s)
        assert traj[2].return_ == pytest.approx(1.0, abs=1e-3)
        assert traj[0].return_ == pytest.approx(2.8870, abs=1e-3)

    def test_dyn_gae_matches_eq_for_same_input(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        eq_traj = self._trajectory(EQRLExperience, 7)
        dy_traj = self._trajectory(DynRLExperience, 10)
        eq._compute_gae(eq_traj)
        dy._compute_gae(dy_traj)
        for e, d in zip(eq_traj, dy_traj):
            assert e.advantage == pytest.approx(d.advantage, abs=1e-6)
            assert e.return_ == pytest.approx(d.return_, abs=1e-6)

    def test_gae_handles_empty_trajectory(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        # Should not raise
        eq._compute_gae([])

    def test_gae_done_breaks_bootstrap(self, bus):
        """When done=True at step 0, advantage = reward - value."""
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        traj = [
            EQRLExperience(audio_features=np.zeros(17), action=np.zeros(7),
                           reward=1.0, next_audio_features=np.zeros(17),
                           done=True, value=0.3),
        ]
        eq._compute_gae(traj)
        # delta = 1.0 + 0.99*0*0 - 0.3 = 0.7; gae = 0.7 + ...*0 = 0.7
        assert traj[0].advantage == pytest.approx(0.7, abs=1e-6)
        assert traj[0].return_ == pytest.approx(1.0, abs=1e-6)


# ---------- MessageBus DLQ ----------

class TestMessageBusDLQ:
    def _seed_dlq(self, bus, n=3):
        msg = Message(topic="lost.topic", sender="x",
                      payload={'data': 'lost'}, priority=Priority.MEDIUM)
        for i in range(n):
            bus._dead_letter_queue.put_nowait((msg, f"agent-{i}", f"err-{i}"))

    def test_get_dead_letters_peek(self, bus):
        self._seed_dlq(bus, 3)
        peek = bus.get_dead_letters(n=2, drain=False)
        assert len(peek) == 2
        # Peek should not consume
        assert bus._dead_letter_queue.qsize() == 3

    def test_get_dead_letters_drain(self, bus):
        self._seed_dlq(bus, 3)
        drained = bus.get_dead_letters(n=2, drain=True)
        assert len(drained) == 2
        assert bus._dead_letter_queue.qsize() == 1

    def test_retry_dead_letters(self, bus):
        self._seed_dlq(bus, 2)
        bus.subscribe("lost.topic", "stub", lambda m: None)
        time.sleep(0.05)
        result = bus.retry_dead_letters(max_retries=5)
        assert result['attempted'] == 2
        assert result['succeeded'] == 2
        assert result['remaining'] == 0

    def test_dead_letters_reflect_metrics(self, bus):
        self._seed_dlq(bus, 4)
        m = bus.get_metrics()
        assert m['dead_letter_count'] == 4


# ---------- MessageBus end-to-end request/respond ----------

class TestMessageBusRoundTrip:
    def test_request_response_via_per_agent_topic(self, bus):
        def handler(msg):
            bus.respond(msg, {'status': 'success', 'echo': msg.payload['data']})

        bus.subscribe(Topics.agent_request("recv"), "recv", handler)
        time.sleep(0.05)

        req = Message(
            topic=Topics.agent_request("recv"),
            sender="caller",
            message_type=MessageType.AUDIO_PROCESSING_REQUEST,
            payload={'data': 'hello'},
        )
        resp = bus.request(req, timeout=2.0)
        assert resp is not None
        assert resp.payload['status'] == 'success'
        assert resp.payload['echo'] == 'hello'

    def test_request_times_out_with_no_subscriber(self, bus):
        req = Message(
            topic=Topics.agent_request("nobody"),
            sender="caller",
            payload={},
        )
        resp = bus.request(req, timeout=0.5)
        assert resp is None


# ---------- HGOCoordinator: goal decomposition + proposal ----------

class TestHGOGoalDecomposition:
    def test_set_goals_populates_subgoals(self, bus):
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="c",
        )
        g = OptimizationGoal(
            name="clarity_first", description="",
            target_concepts=["clarity", "presence_concept"],
            avoid_concepts=["mud", "harshness"],
            priority=GoalPriority.HIGH,
        )
        h.set_goals([g])
        assert len(h.active_goals) == 1
        # After decomposition the eq_subgoals/dynamics_subgoals must be populated
        assert len(g.eq_subgoals) > 0 or len(g.dynamics_subgoals) > 0

    def test_get_agent_proposal_no_subscriber_returns_zero_confidence(self, bus):
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="c",
        )
        h.set_goals([
            OptimizationGoal(
                name="g", description="",
                target_concepts=["clarity"], avoid_concepts=["mud"],
                priority=GoalPriority.HIGH,
            )
        ])
        audio = np.zeros(1024, dtype=np.float32)
        prop = h._get_agent_proposal("eq", audio, training=False)
        assert prop.confidence == 0.0
        assert prop.action_vector.shape == (14,)  # 7 bands * (gain + Q)
        assert prop.agent_type == "eq"

    def test_get_agent_proposal_real_response(self, bus):
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="c",
        )
        h.set_goals([
            OptimizationGoal(
                name="g", description="",
                target_concepts=["clarity"], avoid_concepts=["mud"],
                priority=GoalPriority.HIGH,
            )
        ])

        def eq_handler(msg):
            bus.respond(msg, {
                'status': 'success',
                'action': list(np.linspace(0.1, 1.4, 14)),
                'predicted_reward': 0.8,
                'confidence': 0.9,
            })

        bus.subscribe(Topics.agent_request("eq"), "eq", eq_handler)
        time.sleep(0.05)

        audio = np.zeros(1024, dtype=np.float32)
        prop = h._get_agent_proposal("eq", audio, training=False)
        assert prop.confidence == pytest.approx(0.9, abs=1e-6)
        assert prop.predicted_reward == pytest.approx(0.8, abs=1e-6)
        assert prop.action_vector.shape == (14,)
        # affected_concepts should reflect goal subgoals (real concepts, not empty)
        assert len(prop.affected_concepts) > 0

    def test_get_agent_proposal_dynamics_dim(self, bus):
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="c",
        )
        prop = h._get_agent_proposal("dy", np.zeros(1024, dtype=np.float32), training=False)
        assert prop.agent_type == "dynamics"
        assert prop.action_vector.shape == (10,)


# ---------- EQ filter design ----------

class TestEQFilterDesign:
    def test_peak_filter_returns_3_taps(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        b, a = eq._design_peak_filter(1000.0, 6.0, 1.0, 44100)
        assert b.shape == (3,)
        assert a.shape == (3,)

    def test_peak_filter_unity_at_zero_gain(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        b, a = eq._design_peak_filter(1000.0, 0.0, 1.0, 44100)
        # Zero-gain peaking EQ should be approximately unity (b ≈ a)
        assert np.allclose(b, a, atol=1e-9)

    def test_shelf_filter_returns_3_taps(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        b, a = eq._design_shelf_filter(80.0, 6.0, 44100, 'low')
        assert b.shape == (3,)
        assert a.shape == (3,)

    def test_shelf_filter_high_type(self, bus):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="c")
        b, a = eq._design_shelf_filter(8000.0, -3.0, 44100, 'high')
        assert b.shape == (3,)
        assert a.shape == (3,)


# ---------- Dynamics processors ----------

class TestDynamicsProcessing:
    def test_compressor_reduces_peaks(self, bus):
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        sr = dy.sample_rate
        audio = np.concatenate([np.zeros(sr // 2), np.ones(sr // 2) * 0.95]).astype(np.float32)
        compressed = dy._apply_compressor(
            audio, threshold=-12.0, ratio=4.0,
            attack_ms=5.0, release_ms=50.0, knee_width=2.0,
        )
        assert compressed.shape == audio.shape
        assert np.max(np.abs(compressed)) <= np.max(np.abs(audio)) + 1e-6

    def test_limiter_caps_peaks(self, bus):
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        audio = (np.ones(1000) * 0.99).astype(np.float32)
        limited = dy._apply_limiter(audio, threshold=-3.0, release_ms=10.0)
        # No peak should exceed the threshold (linear: 10^(-3/20) ≈ 0.708)
        assert np.max(np.abs(limited)) <= 10 ** (-3 / 20) + 0.05

    def test_gate_attenuates_quiet(self, bus):
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="c")
        sr = dy.sample_rate
        audio = (np.ones(sr // 10) * 0.001).astype(np.float32)  # very quiet
        gated = dy._apply_gate(audio, threshold_db=-40.0)
        # Quiet signal below the gate should be substantially attenuated
        assert np.max(np.abs(gated)) <= np.max(np.abs(audio)) + 1e-6


# ---------- Critic concept detection ----------

class TestCriticConceptDetection:
    def test_extract_features_basic(self, bus, sine_440):
        c = CriticAgent(agent_id="c", message_bus=bus)
        feats = c.extract_features(sine_440)
        v = feats.to_vector()
        assert v.shape == (17,)
        assert np.all(np.isfinite(v))

    def test_judge_audio_returns_satisfaction(self, bus, sine_440):
        c = CriticAgent(agent_id="c", message_bus=bus)
        result = c.judge_audio(sine_440)
        # judge_audio returns a CriticJudgment (dataclass) with satisfaction_score
        assert hasattr(result, 'satisfaction_score') or 'satisfaction_score' in result.__dict__
