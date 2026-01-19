from PySide6.QtCore import QObject, Signal
import logging
from typing import Dict, Any

from src.core.message_bus import get_message_bus
from src.core.message_types import Message, Priority

logger = logging.getLogger(__name__)

class MessageBusAdapter(QObject):
    """
    Thread-safe adapter between message bus and Qt GUI.
    """
    
    # Qt Signals (thread-safe)
    tempo_changed = Signal(float)  # BPM
    scene_triggered = Signal(str, str)  # scene_id, scene_name
    loop_recorded = Signal(str, float)  # track_id, duration
    effect_parameter_changed = Signal(str, str, float)  # chain, param, value
    agent_status_changed = Signal(str, str)  # agent_id, status
    meter_update = Signal(str, float, float)  # meter_id, level_l, level_r
    log_message = Signal(str, str) # level, message

    def __init__(self):
        super().__init__()
        self.message_bus = get_message_bus()
        self.running = False
        self.agent_id = "gui_adapter"

    def start(self):
        """Subscribe to relevant topics"""
        if self.running:
            return
            
        self.running = True
        
        # Subscribe to all relevant topics
        self.message_bus.subscribe("sync.clock.tempo", self.agent_id, self._on_message)
        self.message_bus.subscribe("automation.scene.triggered", self.agent_id, self._on_message)
        self.message_bus.subscribe("loop.record.stopped", self.agent_id, self._on_message)
        self.message_bus.subscribe("effects.parameter.change", self.agent_id, self._on_message)
        self.message_bus.subscribe("system.agent.*", self.agent_id, self._on_message)
        self.message_bus.subscribe("log.event.*", self.agent_id, self._on_message)
        
        logger.info("GUI Adapter started listening to message bus")

    def stop(self):
        """Unsubscribe"""
        self.running = False
        try:
            self.message_bus.unsubscribe("sync.clock.tempo", self.agent_id)
            self.message_bus.unsubscribe("automation.scene.triggered", self.agent_id)
            self.message_bus.unsubscribe("loop.record.stopped", self.agent_id)
            self.message_bus.unsubscribe("effects.parameter.change", self.agent_id)
            self.message_bus.unsubscribe("system.agent.*", self.agent_id)
            self.message_bus.unsubscribe("log.event.*", self.agent_id)
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
        
    def _on_message(self, message: Message):
        """Callback from message bus (runs in dispatcher thread)"""
        try:
            if message.topic == "sync.clock.tempo":
                bpm = message.payload.get('bpm', 120.0)
                self.tempo_changed.emit(bpm)
                
            elif message.topic == "automation.scene.triggered":
                scene_id = message.payload.get('scene_id', '')
                scene_name = message.payload.get('scene_name', '')
                self.scene_triggered.emit(scene_id, scene_name)
                
            elif message.topic.startswith("system.agent."):
                agent_id = message.payload.get('agent_id', '')
                status = message.topic.split('.')[-1] # e.g. started, stopped
                self.agent_status_changed.emit(agent_id, status)
                
            elif message.topic.startswith("log.event."):
                level = message.topic.split('.')[-1].upper()
                msg = message.payload.get('message', '')
                self.log_message.emit(level, msg)

        except Exception as e:
            logger.error(f"Error processing message in GUI adapter: {e}")

    def publish_gui_event(self, topic: str, payload: dict):
        """Thread-safe message publishing from GUI"""
        message = Message(
            topic=topic,
            sender=self.agent_id,
            payload=payload,
            priority=Priority.MEDIUM
        )
        self.message_bus.publish(message)
