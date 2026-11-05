from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout
from PySide6.QtCore import Qt

class DashboardView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        
        # 1. Agent Status Panel
        status_group = QGroupBox("Active Agents Status")
        status_layout = QHBoxLayout(status_group)
        
        self.status_labels = {}
        agents = ["Effects Chain", "Looping", "Sync Clock"]
        for agent in agents:
            agent_layout = QVBoxLayout()
            name_label = QLabel(agent)
            name_label.setStyleSheet("font-weight: bold;")
            status_label = QLabel("● Unknown")
            self.status_labels[agent] = status_label
            
            agent_layout.addWidget(name_label)
            agent_layout.addWidget(status_label)
            status_layout.addLayout(agent_layout)
            
        layout.addWidget(status_group)
        
        # 2. Performance Metrics
        perf_group = QGroupBox("System Performance")
        perf_layout = QGridLayout(perf_group)
        
        perf_layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        perf_layout.addWidget(QLabel("[||||||||||] 45%"), 0, 1) # Placeholder
        perf_layout.addWidget(QLabel("Memory:"), 1, 0)
        perf_layout.addWidget(QLabel("[|||||.....] 25%"), 1, 1) # Placeholder
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
