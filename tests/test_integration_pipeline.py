"""End-to-end integration tests for the multi-agent audio pipeline.

These tests exercise the full chain: audio in -> features -> RL action ->
HGO arbitration -> processed audio out. The goal is to catch regressions
in inter-component contracts that unit tests can miss.
"""
from __future__ import annotations

import time
import numpy as np
import pytest

from src.core.message_bus import MessageBus
from src.core.message_types import Message, MessageType, Topics
from src.agents.critic_agent import CriticAgent
from src.agents.eq_rl_agent import EQRLAgent, RLExperience as EQRLExperience
from src.agents.dynamics_rl_agent import DynamicsRLAgent
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
def audio_sine():
    sr = 44100
    return (0.5 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32)


@pytest.fixture
def audio_multitone():
    sr = 44100
    t = np.arange(sr) / sr
    return (
        0.2 * np.sin(2 * np.pi * 200 * t)
        + 0.2 * np.sin(2 * np.pi * 1000 * t)
        + 0.2 * np.sin(2 * np.pi * 5000 * t)
    ).astype(np.float32)


# ---------- E2E: critic loop ----------

class TestCriticLoop:
    def test_critic_judges_audio_returns_finite_score(self, bus, audio_sine):
        c = CriticAgent(agent_id="critic", message_bus=bus)
        result = c.judge_audio(audio_sine)
        assert hasattr(result, 'satisfaction_score')
        assert np.isfinite(result.satisfaction_score)
        assert -1.0 <= result.satisfaction_score <= 1.0

    def test_critic_extracts_consistent_features(self, bus, audio_sine):
        c = CriticAgent(agent_id="critic", message_bus=bus)
        f1 = c.extract_features(audio_sine)
        f2 = c.extract_features(audio_sine)
        # Same audio in -> same features out (deterministic)
        assert np.allclose(f1.to_vector(), f2.to_vector())


# ---------- E2E: EQ + critic via fallback features ----------

class TestEQCriticLoop:
    def test_eq_runs_one_step_with_local_fallback(self, bus, audio_sine):
        # No critic registered on bus — EQ uses its local feature fallback
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="critic-missing")
        features = eq.get_audio_features(audio_sine)
        assert features.shape == (17,)
        assert np.all(np.isfinite(features))

        # And we can select an action from those features (14-dim: 7 bands × 2 params)
        action, log_prob, value = eq.select_action(features, explore=False)
        assert action.shape == (14,)
        assert np.all(np.isfinite(action))
        assert np.isfinite(log_prob)
        assert np.isfinite(value)

    def test_eq_filter_chain_preserves_shape(self, bus, audio_sine):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="critic")
        # Apply a no-op EQ (gain 0 across all bands) — shape must be preserved
        out = eq.apply_eq(audio_sine, eq.current_eq)
        assert out.shape == audio_sine.shape
        assert np.all(np.isfinite(out))


# ---------- E2E: dynamics + critic ----------

class TestDynamicsCriticLoop:
    def test_dynamics_runs_one_step_with_local_fallback(self, bus, audio_sine):
        dy = DynamicsRLAgent(agent_id="dy", message_bus=bus, critic_agent_id="critic-missing")
        features = dy.get_audio_features(audio_sine)
        assert features.shape == (17,)
        action, log_prob, value = dy.select_action(features, explore=False)
        assert action.shape == (10,)
        assert np.isfinite(log_prob)
        assert np.isfinite(value)


# ---------- E2E: HGO coordinator orchestrating two agents ----------

class TestHGOFullCoordination:
    def test_hgo_collects_proposals_from_two_agents(self, bus, audio_sine):
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="critic",
        )
        h.set_goals([
            OptimizationGoal(
                name="clarity",
                description="more clarity",
                target_concepts=["clarity"],
                avoid_concepts=["mud"],
                priority=GoalPriority.HIGH,
            )
        ])

        # Register fake EQ agent on bus
        def eq_handler(msg):
            bus.respond(msg, {
                'status': 'success',
                'action': [0.1] * 14,
                'predicted_reward': 0.5,
                'confidence': 0.8,
            })

        def dy_handler(msg):
            bus.respond(msg, {
                'status': 'success',
                'action': [0.2] * 10,
                'predicted_reward': 0.4,
                'confidence': 0.7,
            })

        bus.subscribe(Topics.agent_request("eq"), "eq", eq_handler)
        bus.subscribe(Topics.agent_request("dy"), "dy", dy_handler)
        time.sleep(0.05)

        eq_prop = h._get_agent_proposal("eq", audio_sine, training=False)
        dy_prop = h._get_agent_proposal("dy", audio_sine, training=False)

        assert eq_prop.confidence == pytest.approx(0.8, abs=1e-6)
        assert dy_prop.confidence == pytest.approx(0.7, abs=1e-6)
        assert eq_prop.action_vector.shape == (14,)  # 7 bands * 2 params
        assert dy_prop.action_vector.shape == (10,)
        # Both proposals reference the goal's affected concepts
        assert len(eq_prop.affected_concepts) > 0
        assert len(dy_prop.affected_concepts) > 0

    def test_hgo_handles_partial_agent_failure(self, bus, audio_sine):
        """If only EQ responds, HGO should still produce a proposal for dyn (with conf=0.0)."""
        h = HGOCoordinator(
            agent_id="hgo", message_bus=bus,
            eq_agent_id="eq", dynamics_agent_id="dy", critic_agent_id="critic",
        )
        h.set_goals([
            OptimizationGoal(
                name="g", description="",
                target_concepts=["clarity"], avoid_concepts=[],
                priority=GoalPriority.HIGH,
            )
        ])

        bus.subscribe(
            Topics.agent_request("eq"),
            "eq",
            lambda msg: bus.respond(msg, {
                'status': 'success', 'action': [0.0] * 14,
                'predicted_reward': 0.0, 'confidence': 0.5,
            }),
        )
        time.sleep(0.05)

        eq_prop = h._get_agent_proposal("eq", audio_sine, training=False)
        dy_prop = h._get_agent_proposal("dy", audio_sine, training=False)

        assert eq_prop.confidence == 0.5      # real response
        assert dy_prop.confidence == 0.0      # marker for missing agent


# ---------- E2E: PPO step with GAE end-to-end ----------

class TestPPOIntegration:
    def test_compute_gae_then_train_no_crash(self, bus, audio_sine):
        eq = EQRLAgent(agent_id="eq", message_bus=bus, critic_agent_id="critic")
        # Build a small synthetic trajectory
        traj = []
        for i in range(8):
            traj.append(EQRLExperience(
                audio_features=eq._extract_features_local(audio_sine),
                action=np.random.uniform(-0.5, 0.5, 14).astype(np.float32),
                reward=float(np.random.randn() * 0.1),
                next_audio_features=eq._extract_features_local(audio_sine),
                done=(i == 7),
                log_prob=float(np.random.randn() * 0.1),
                value=float(np.random.randn() * 0.1),
            ))
        eq._compute_gae(traj)
        eq.replay_buffer.extend(traj)
        # Force batch_size to fit our buffer for the test
        eq.batch_size = len(eq.replay_buffer)
        stats = eq._train_on_buffer()
        # Should produce real loss numbers, not NaN
        assert 'policy_loss' in stats
        assert np.isfinite(stats['policy_loss'])
        assert np.isfinite(stats['value_loss'])
        assert np.isfinite(stats['entropy'])


# ---------- E2E: message bus roundtrip across the full chain ----------

class TestMessageBusEndToEnd:
    def test_request_with_correlation_id_routes_response(self, bus):
        received = []

        def echo(msg):
            received.append(msg.payload)
            bus.respond(msg, {'status': 'success', 'echo': msg.payload['n']})

        bus.subscribe(Topics.agent_request("echo"), "echo", echo)
        time.sleep(0.05)

        # Send 5 sequential requests; each must get its own correct response
        for n in range(5):
            req = Message(
                topic=Topics.agent_request("echo"),
                sender="caller",
                message_type=MessageType.AUDIO_PROCESSING_REQUEST,
                payload={'n': n},
            )
            resp = bus.request(req, timeout=1.0)
            assert resp is not None
            assert resp.payload['echo'] == n

        assert len(received) == 5

    def test_dlq_retry_round_trips_through_real_subscriber(self, bus):
        """Simulate a delivery failure, then retry and verify it succeeds."""
        msg = Message(
            topic=Topics.agent_request("retry-target"),
            sender="caller",
            payload={'data': 'first-try-failed'},
        )
        # Manually inject into DLQ as if delivery had failed
        bus._dead_letter_queue.put_nowait((msg, "retry-target", "transient_failure"))

        # Now register a subscriber and retry
        delivered = []
        bus.subscribe(
            Topics.agent_request("retry-target"),
            "retry-target",
            lambda m: delivered.append(m.payload),
        )
        time.sleep(0.05)

        result = bus.retry_dead_letters(max_retries=1)
        time.sleep(0.1)  # let dispatcher deliver

        assert result['attempted'] == 1
        assert result['succeeded'] == 1
        assert len(delivered) == 1
        assert delivered[0]['data'] == 'first-try-failed'
