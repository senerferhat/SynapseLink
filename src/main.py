#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import qdarkstyle

# Add src directory to Python path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    sys.path.append(os.path.join(sys._MEIPASS, 'src'))
else:
    # Running from source
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.main_window import MainWindow
from src.ui.splash_screen import SplashScreen

def main():
    # Enable High DPI display
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Create the application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("SynapseLink")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SynapseLink")
    app.setOrganizationDomain("synapselink.org")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set the default style to dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Create main window
    main_window = MainWindow()

    # When splash screen progress is complete, finish splash
    def check_splash_progress():
        if splash.progress >= 100:
            splash.timer.stop()
            splash.finish(main_window)
        else:
            app.processEvents()

    splash.timer.timeout.connect(check_splash_progress)

    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 