"""
Director state machine for camera switching logic

Implements a rule-based state machine that decides when and how to switch
between cameras based on active speaker detection results.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from collections import deque
import time

from .profiles import SwitchRule


class DirectorState(Enum):
    """Director states for camera switching"""

    IDLE = "idle"  # No active speakers detected
    LOCKED = "locked"  # Locked on active speaker (enforcing min dwell time)
    READY = "ready"  # Can switch to new speaker (dwell time met)
    TRANSITIONING = "transitioning"  # Mid-switch cooldown


@dataclass
class DetectionResult:
    """
    Detection result for a single camera

    This is a placeholder that will be populated by the detector module.
    """

    camera_id: str
    audio_score: float  # 0.0 to 1.0
    visual_score: float  # 0.0 to 1.0
    fused_score: float  # 0.0 to 1.0 (weighted combination)
    face_detected: bool
    timestamp: float


@dataclass
class DirectorDecision:
    """Decision result from state machine"""

    current_camera: str
    should_switch: bool
    target_camera: Optional[str]
    reason: str  # "new_speaker", "dwell_expired", "variety", "idle_timeout", etc.
    confidence: float
    state: DirectorState


class DirectorStateMachine:
    """
    Rule-based state machine for camera switching

    States:
        IDLE: No active speakers
        LOCKED: On active speaker (enforcing min dwell time)
        READY: Can switch to new speaker
        TRANSITIONING: Mid-switch cooldown

    Transitions:
        IDLE → LOCKED: Speaker detected (score > threshold)
        LOCKED → LOCKED: Same speaker still active (refresh dwell timer)
        LOCKED → READY: Dwell time expired
        READY → LOCKED: New speaker detected (different camera)
        LOCKED → TRANSITIONING → LOCKED: Switch triggered
    """

    def __init__(self, rules: SwitchRule, default_camera: str = "camera_0"):
        """
        Initialize state machine

        Args:
            rules: Switching rules configuration
            default_camera: Default camera ID to use when idle
        """
        self.rules = rules
        self.default_camera = default_camera

        # State tracking
        self.state = DirectorState.IDLE
        self.current_camera = default_camera
        self.state_start_time = time.time()
        self.last_decision_time = time.time()

        # History tracking
        self.camera_usage: Dict[str, float] = {}  # camera_id -> last used time
        self.switch_history: deque = deque(maxlen=20)  # Recent switches

        # Transition target
        self._transition_target: Optional[str] = None

    def process(self, detections: Dict[str, DetectionResult]) -> DirectorDecision:
        """
        Process detections and make switching decision

        Args:
            detections: Detection results per camera

        Returns:
            DirectorDecision with switching recommendation
        """
        now = time.time()
        time_in_state = now - self.state_start_time

        # Find best candidate
        best_camera, best_score = self._find_best_candidate(detections)

        # State machine logic
        if self.state == DirectorState.IDLE:
            decision = self._handle_idle_state(best_camera, best_score, now)
        elif self.state == DirectorState.LOCKED:
            decision = self._handle_locked_state(
                best_camera, best_score, time_in_state, now
            )
        elif self.state == DirectorState.READY:
            decision = self._handle_ready_state(best_camera, best_score, now)
        elif self.state == DirectorState.TRANSITIONING:
            decision = self._handle_transitioning_state(time_in_state, now)
        else:
            # Fallback to idle if unknown state
            self.state = DirectorState.IDLE
            decision = DirectorDecision(
                current_camera=self.current_camera,
                should_switch=False,
                target_camera=None,
                reason="unknown_state_fallback",
                confidence=0.0,
                state=self.state,
            )

        self.last_decision_time = now
        return decision

    def _handle_idle_state(
        self, best_camera: str, best_score: float, now: float
    ) -> DirectorDecision:
        """
        Handle IDLE state logic

        Transition to LOCKED if speaker detected above threshold
        """
        if best_score >= self.rules.switch_threshold:
            # Transition to LOCKED on active speaker
            self._transition_to(DirectorState.LOCKED, best_camera, now)
            return DirectorDecision(
                current_camera=self.current_camera,
                should_switch=True,
                target_camera=best_camera,
                reason="speaker_detected_from_idle",
                confidence=best_score,
                state=self.state,
            )
        else:
            # Stay idle, ensure default camera
            if self.current_camera != self.default_camera:
                return DirectorDecision(
                    current_camera=self.current_camera,
                    should_switch=True,
                    target_camera=self.default_camera,
                    reason="return_to_default",
                    confidence=0.0,
                    state=self.state,
                )
            else:
                return DirectorDecision(
                    current_camera=self.current_camera,
                    should_switch=False,
                    target_camera=None,
                    reason="idle",
                    confidence=best_score,
                    state=self.state,
                )

    def _handle_locked_state(
        self, best_camera: str, best_score: float, time_in_state: float, now: float
    ) -> DirectorDecision:
        """
        Handle LOCKED state logic

        Enforce minimum dwell time, check for max dwell time,
        evaluate if a switch should occur.
        """
        # Check if max dwell time exceeded (force variety)
        if time_in_state >= self.rules.max_dwell_time:
            if (
                best_camera != self.current_camera
                and best_score >= self.rules.switch_threshold * 0.7
            ):
                # Force switch for variety
                return self._execute_switch(
                    best_camera, "max_dwell_time_variety", best_score, now
                )

        # Check if min dwell time met
        if time_in_state >= self.rules.min_dwell_time:
            # Transition to READY state
            self.state = DirectorState.READY
            # Continue processing in READY state
            return self._handle_ready_state(best_camera, best_score, now)

        # Still in minimum dwell period
        if best_camera == self.current_camera:
            # Same speaker still active - stay locked
            return DirectorDecision(
                current_camera=self.current_camera,
                should_switch=False,
                target_camera=None,
                reason="locked_on_speaker",
                confidence=best_score,
                state=self.state,
            )
        else:
            # Different speaker detected but in min dwell - ignore
            return DirectorDecision(
                current_camera=self.current_camera,
                should_switch=False,
                target_camera=None,
                reason="min_dwell_not_met",
                confidence=best_score,
                state=self.state,
            )

    def _handle_ready_state(
        self, best_camera: str, best_score: float, now: float
    ) -> DirectorDecision:
        """
        Handle READY state logic

        Can accept switches to new speakers, or return to idle if no activity
        """
        # Check for idle timeout
        time_since_decision = now - self.last_decision_time
        if best_score < self.rules.switch_threshold * 0.5:
            if time_since_decision >= self.rules.idle_timeout:
                # No significant activity - return to idle
                self._transition_to(DirectorState.IDLE, self.current_camera, now)
                return DirectorDecision(
                    current_camera=self.current_camera,
                    should_switch=False,
                    target_camera=None,
                    reason="idle_timeout",
                    confidence=best_score,
                    state=self.state,
                )

        # Check if should switch
        if best_camera != self.current_camera:
            # Apply hysteresis
            effective_threshold = self.rules.switch_threshold + self.rules.hysteresis

            if best_score >= effective_threshold:
                # Switch to new speaker
                return self._execute_switch(best_camera, "new_speaker", best_score, now)

        # Stay on current camera
        return DirectorDecision(
            current_camera=self.current_camera,
            should_switch=False,
            target_camera=None,
            reason="ready_no_switch",
            confidence=best_score,
            state=self.state,
        )

    def _handle_transitioning_state(
        self, time_in_state: float, now: float
    ) -> DirectorDecision:
        """
        Handle TRANSITIONING state logic

        Wait for cooldown period, then transition to LOCKED
        """
        if time_in_state >= self.rules.transition_cooldown:
            # Cooldown complete - transition to LOCKED on target camera
            self._transition_to(DirectorState.LOCKED, self._transition_target, now)
            self._transition_target = None

        return DirectorDecision(
            current_camera=self.current_camera,
            should_switch=False,
            target_camera=None,
            reason="transitioning",
            confidence=0.0,
            state=self.state,
        )

    def _find_best_candidate(
        self, detections: Dict[str, DetectionResult]
    ) -> Tuple[str, float]:
        """
        Find best camera candidate with variety bonus

        Args:
            detections: Detection results per camera

        Returns:
            Tuple of (camera_id, adjusted_score)
        """
        if not detections:
            return self.current_camera, 0.0

        best_camera = self.current_camera
        best_score = 0.0

        now = time.time()

        for camera_id, detection in detections.items():
            adjusted_score = detection.fused_score

            # Apply variety bonus for cameras not recently used
            last_used = self.camera_usage.get(camera_id, 0.0)
            time_since_use = now - last_used

            # Bonus increases with time since last use
            if time_since_use > 10.0 and camera_id != self.current_camera:
                adjusted_score += self.rules.variety_bonus

            # Track best candidate
            if adjusted_score > best_score:
                best_camera = camera_id
                best_score = adjusted_score

        return best_camera, best_score

    def _execute_switch(
        self, target: str, reason: str, confidence: float, now: float
    ) -> DirectorDecision:
        """
        Execute camera switch

        Args:
            target: Target camera ID
            reason: Reason for switch
            confidence: Confidence score
            now: Current timestamp

        Returns:
            DirectorDecision indicating switch
        """
        # Record switch in history
        self.switch_history.append(
            {
                "from": self.current_camera,
                "to": target,
                "time": now,
                "reason": reason,
            }
        )

        # Update camera usage
        self.camera_usage[target] = now

        # Set transition target
        self._transition_target = target

        # Transition to TRANSITIONING state
        self._transition_to(DirectorState.TRANSITIONING, target, now)

        return DirectorDecision(
            current_camera=target,  # Switch happens immediately
            should_switch=True,
            target_camera=target,
            reason=reason,
            confidence=confidence,
            state=self.state,
        )

    def _transition_to(self, new_state: DirectorState, camera: str, now: float) -> None:
        """
        Transition to new state

        Args:
            new_state: New state to transition to
            camera: Camera to set as current
            now: Current timestamp
        """
        self.state = new_state
        self.current_camera = camera
        self.state_start_time = now

    def get_stats(self) -> Dict:
        """
        Get state machine statistics

        Returns:
            Dictionary of statistics
        """
        return {
            "current_state": self.state.value,
            "current_camera": self.current_camera,
            "time_in_state": time.time() - self.state_start_time,
            "total_switches": len(self.switch_history),
            "camera_usage": self.camera_usage.copy(),
            "recent_switches": list(self.switch_history),
        }

    def reset(self) -> None:
        """Reset state machine to initial state"""
        self.state = DirectorState.IDLE
        self.current_camera = self.default_camera
        self.state_start_time = time.time()
        self.camera_usage.clear()
        self.switch_history.clear()
        self._transition_target = None
