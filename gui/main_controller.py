from PySide6.QtCore import QObject, Slot
from gui.backend_adapter import MessageBusAdapter
import logging

logger = logging.getLogger(__name__)

class MainController(QObject):
    """
    Central controller for GUI state and backend communication
    """

    def __init__(self):
        super().__init__()
        self.adapter = MessageBusAdapter()

        # Connect adapter signals to local handlers (which will then update UI models)
        self.adapter.tempo_changed.connect(self._on_tempo_changed)
        self.adapter.scene_triggered.connect(self._on_scene_triggered)
        self.adapter.agent_status_changed.connect(self._on_agent_status_changed)
        self.adapter.log_message.connect(self._on_log_message)

    def start(self):
        """Start the controller and adapter"""
        self.adapter.start()
        logger.info("MainController started")

    def stop(self):
        """Stop the controller and adapter"""
        self.adapter.stop()

    @Slot(float)
    def _on_tempo_changed(self, bpm: float):
        logger.debug(f"Tempo changed to {bpm}")
        # Here we would update the model or emit a signal for the view

    @Slot(str, str)
    def _on_scene_triggered(self, scene_id: str, scene_name: str):
        logger.info(f"Scene triggered: {scene_name} ({scene_id})")

    @Slot(str, str)
    def _on_agent_status_changed(self, agent_id: str, status: str):
        logger.info(f"Agent {agent_id} status: {status}")

    @Slot(str, str)
    def _on_log_message(self, level: str, message: str):
        # Could forward to a log view
        pass
        
    # Public methods for Views to call
    def set_tempo(self, bpm: float):
        self.adapter.publish_gui_event("sync.tempo.set", {
            'bpm': bpm,
            'time_signature': '4/4'
        })
