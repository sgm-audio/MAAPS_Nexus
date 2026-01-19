import sys
import os
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

from gui.main_controller import MainController

def main():
    # Set up environment
    os.environ["QT_API"] = "pyside6"
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("MAAPS Nexus")
    app.setOrganizationName("Hivyr")
    
    # Initialize controller
    controller = MainController()
    controller.start()
    
    # Create and show main window
    window = MainWindow(controller)
    window.show()
    
    # Run application
    try:
        sys.exit(app.exec())
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
