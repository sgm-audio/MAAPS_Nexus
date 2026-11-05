from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.views.dashboard_view import DashboardView

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("MAAPS Nexus - Multi-Agent Audio Processing System")
        self.resize(1200, 800)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Initialize tabs
        self.dashboard_tab = DashboardView(self.controller)
        self.effects_tab = QWidget()
        self.looping_tab = QWidget()
        self.sync_tab = QWidget()
        self.automation_tab = QWidget()
        
        # Add tabs
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.effects_tab, "Effects Chain")
        self.tabs.addTab(self.looping_tab, "Live Looping")
        self.tabs.addTab(self.sync_tab, "Sync & Clock")
        self.tabs.addTab(self.automation_tab, "Automation")
        
        # Setup basic content for tabs (placeholders)
        # self._setup_placeholder(self.dashboard_tab, "Dashboard View")
        self._setup_placeholder(self.effects_tab, "Effects Chain View")
        self._setup_placeholder(self.looping_tab, "Live Looping View")
        self._setup_placeholder(self.sync_tab, "Sync & Clock View")
        self._setup_placeholder(self.automation_tab, "Performance Automation View")
        
    def _setup_placeholder(self, widget, text):
        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(20)
        label.setFont(font)
        layout.addWidget(label)
