from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QMenuBar, QMenu, 
                               QToolBar, QDockWidget, QStatusBar, QMessageBox,
                               QFileDialog, QVBoxLayout, QWidget, QDialog,
                               QSplitter, QPushButton)
from PyQt6.QtCore import Qt, QSettings, pyqtSlot, QSize
from PyQt6.QtGui import QAction, QIcon
import os
import sys
import qdarkstyle
from pathlib import Path
from datetime import datetime
import json

from src.ui.connection_dialog import ConnectionDialog
from src.ui.connection_tab import ConnectionTab
from src.ui.protocol_view import ProtocolView
from src.ui.auth_dialog import LoginDialog, UserManagementDialog
from src.ui.security_dialog import SecuritySettingsDialog
from src.ui.automation_view import AutomationView
from src.ui.tab_selection_dialog import TabSelectionDialog
from src.core.serial_manager import SerialManager
from src.core.data_processor import DataProcessor
from src.core.protocol_analyzer import ProtocolAnalyzer
from src.core.security_manager import SecurityManager
from src.core.automation_manager import AutomationManager
from src.core.session_manager import SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SynapseLink")
        
        # Initialize app data directory
        self.app_data_dir = self._get_app_data_dir()
        
        # Initialize managers
        self.settings = QSettings("SynapseLink", "SynapseLink")
        self.session_manager = SessionManager(self.app_data_dir)
        self.serial_manager = SerialManager()
        self.data_processor = DataProcessor()
        self.protocol_analyzer = ProtocolAnalyzer()
        self.security_manager = SecurityManager()
        self.automation_manager = AutomationManager()
        
        # Create split view button (before toolbar creation)
        self.split_view_button = QPushButton("Enable Split View")
        self.split_view_button.setCheckable(True)
        self.split_view_button.setChecked(False)  # Start with split view disabled
        
        # Initialize UI components
        self.setup_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()
        
        # Set central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.main_splitter)

        # Create left and right tab widgets
        self.left_tabs = QTabWidget()
        self.right_tabs = QTabWidget()
        self.left_tabs.setTabsClosable(True)
        self.right_tabs.setTabsClosable(True)
        
        # Add tab widgets to splitter
        self.main_splitter.addWidget(self.left_tabs)
        self.main_splitter.addWidget(self.right_tabs)
        
        # Initialize split view state
        self.right_tabs.hide()
        self.main_splitter.setSizes([1200, 0])
        
        # Connect signals
        self.left_tabs.tabCloseRequested.connect(lambda idx: self.close_tab(idx, is_left=True))
        self.right_tabs.tabCloseRequested.connect(lambda idx: self.close_tab(idx, is_left=False))
        self.split_view_button.clicked.connect(self.toggle_split_view)

        # Create automation view (hidden by default)
        self.automation_view = AutomationView(self.automation_manager)
        self.automation_view.hide()
        self.layout.addWidget(self.automation_view)

        # Create protocol view dock
        self.protocol_dock = QDockWidget("Protocol Analysis", self)
        self.protocol_view = ProtocolView()
        self.protocol_dock.setWidget(self.protocol_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.protocol_dock)
        self.protocol_dock.hide()

        # Apply initial theme
        self.apply_theme()

        # Setup signals
        self.setup_signals()

        # Restore window geometry
        self.restore_geometry()

        # Hide window initially if security is enabled
        if self.settings.value("security_enabled", True, type=bool):
            self.hide()
            self.show_login_dialog()
        else:
            self.show()

    def setup_ui(self):
        """Initialize the user interface."""
        self.setMinimumSize(1200, 800)
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks |
            QMainWindow.DockOption.AllowNestedDocks |
            QMainWindow.DockOption.AllowTabbedDocks
        )

    def create_actions(self):
        """Create application actions."""
        # File actions
        self.new_connection_action = QAction(QIcon(":/icons/icons/new_connection.png"), "New Connection", self)
        self.new_connection_action.setShortcut("Ctrl+N")
        self.new_connection_action.triggered.connect(self.new_connection)

        self.save_session_action = QAction(QIcon(":/icons/icons/save.png"), "Save Session", self)
        self.save_session_action.setShortcut("Ctrl+S")
        self.save_session_action.triggered.connect(self.save_session)

        self.load_session_action = QAction(QIcon(":/icons/icons/load.png"), "Load Session", self)
        self.load_session_action.setShortcut("Ctrl+O")
        self.load_session_action.triggered.connect(self.load_session)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # View actions
        self.toggle_dark_mode_action = QAction(QIcon(":/icons/icons/dark_mode.png"), "Toggle Dark Mode", self)
        self.toggle_dark_mode_action.setShortcut("Ctrl+D")
        self.toggle_dark_mode_action.triggered.connect(self.toggle_dark_mode)

        self.toggle_protocol_view_action = QAction(QIcon(":/icons/icons/protocol.png"), "Protocol Analysis", self)
        self.toggle_protocol_view_action.setCheckable(True)
        self.toggle_protocol_view_action.triggered.connect(self.toggle_protocol_view)

        self.toggle_automation_view_action = QAction(QIcon(":/icons/icons/automation.png"), "Automation", self)
        self.toggle_automation_view_action.setCheckable(True)
        self.toggle_automation_view_action.triggered.connect(self.toggle_automation_view)

        # Tools actions
        self.security_settings_action = QAction(QIcon(":/icons/icons/security.png"), "Security Settings", self)
        self.security_settings_action.triggered.connect(self.show_security_settings)

        self.user_management_action = QAction(QIcon(":/icons/icons/user.png"), "User Management", self)
        self.user_management_action.triggered.connect(self.show_user_management)

    def create_menus(self):
        """Create application menus."""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_connection_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.save_session_action)
        self.file_menu.addAction(self.load_session_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.toggle_dark_mode_action)
        self.view_menu.addAction(self.toggle_protocol_view_action)
        self.view_menu.addAction(self.toggle_automation_view_action)

        # Tools menu
        self.tools_menu = self.menuBar().addMenu("&Tools")
        self.tools_menu.addAction(self.security_settings_action)
        self.tools_menu.addAction(self.user_management_action)

    def create_toolbars(self):
        """Create application toolbars."""
        # Main toolbar
        self.main_toolbar = QToolBar("Main", self)
        self.addToolBar(self.main_toolbar)
        self.main_toolbar.addAction(self.new_connection_action)
        self.main_toolbar.addAction(self.save_session_action)
        self.main_toolbar.addAction(self.load_session_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addWidget(self.split_view_button)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.toggle_protocol_view_action)
        self.main_toolbar.addAction(self.toggle_automation_view_action)

    def create_status_bar(self):
        """Create application status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def new_connection(self):
        """Show dialog to create a new connection."""
        dialog = ConnectionDialog(self.serial_manager, self)
        if dialog.exec():
            port = dialog.get_selected_port()
            if port:
                self.create_connection_tab(port)

    def create_connection_tab(self, port):
        """Create a new connection tab."""
        tab = ConnectionTab(
            self.serial_manager,
            self.data_processor,
            port,
            self.protocol_analyzer,
            self.security_manager
        )
        
        # Add to the tab widget with fewer tabs
        if self.left_tabs.count() <= self.right_tabs.count():
            self.left_tabs.addTab(tab, port)
            self.left_tabs.setCurrentWidget(tab)
        else:
            self.right_tabs.addTab(tab, port)
            self.right_tabs.setCurrentWidget(tab)

    def close_tab(self, index, is_left=True):
        """Close a connection tab."""
        tab_widget = self.left_tabs if is_left else self.right_tabs
        tab = tab_widget.widget(index)
        if isinstance(tab, ConnectionTab):
            if self.serial_manager.get_connection_status(tab.port_name):
                self.serial_manager.close_connection(tab.port_name)
        tab_widget.removeTab(index)

    def toggle_dark_mode(self):
        """Toggle between light and dark themes."""
        self.settings.setValue("dark_mode", not self.is_dark_mode())
        self.apply_theme()

    def is_dark_mode(self):
        """Check if dark mode is enabled."""
        return self.settings.value("dark_mode", True, type=bool)

    def apply_theme(self):
        """Apply the current theme."""
        if self.is_dark_mode():
            self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        else:
            self.setStyleSheet("")

    def toggle_protocol_view(self, checked):
        """Toggle protocol analysis view."""
        if checked:
            self.protocol_dock.show()
        else:
            self.protocol_dock.hide()

    def toggle_automation_view(self, checked):
        """Toggle automation view."""
        if checked:
            self.automation_view.show()
        else:
            self.automation_view.hide()

    def show_security_settings(self):
        """Show security settings dialog."""
        dialog = SecuritySettingsDialog(self.security_manager, self)
        dialog.exec()

    def show_user_management(self):
        """Show user management dialog."""
        dialog = UserManagementDialog(self.security_manager, self)
        dialog.exec()

    def show_login_dialog(self):
        """Show login dialog."""
        dialog = LoginDialog(self.security_manager, self)
        dialog.login_successful.connect(self.on_login_successful)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.close()

    def on_login_successful(self, username: str):
        """Handle successful login."""
        self.status_bar.showMessage(f"Logged in as {username}")
        self.show()

    def save_session(self):
        """Save current session state."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Session",
            os.path.join(self.session_manager.get_app_data_path('sessions')),
            "Session Files (*.json)"
        )
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            
            session_data = self._get_session_data()
            if self.session_manager.save_session(session_data, filename):
                self.settings.setValue("last_session", filename)
                self.status_bar.showMessage(f"Session saved to {filename}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save session")

    def load_session(self):
        """Load a saved session."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Session",
            os.path.join(self.session_manager.get_app_data_path('sessions')),
            "Session Files (*.json)"
        )
        if filename:
            self._load_session_file(filename)

    def _get_session_data(self):
        """Get current session state data."""
        session_data = {
            'connections': [],
            'window': {
                'geometry': self.saveGeometry().toBase64().data().decode(),
                'state': self.saveState().toBase64().data().decode(),
                'dark_mode': self.is_dark_mode()
            },
            'views': {
                'protocol_view': not self.protocol_dock.isHidden(),
                'automation_view': not self.automation_view.isHidden()
            },
            'automation': {
                'macros': self.automation_manager.macro_recorder.actions,
                'scheduled_tasks': self.automation_manager.scheduled_tasks
            }
        }

        # Save connection tabs
        for i in range(self.left_tabs.count()):
            tab = self.left_tabs.widget(i)
            if isinstance(tab, ConnectionTab):
                session_data['connections'].append({
                    'port': tab.port_name,
                    'settings': tab.get_settings()
                })

        return session_data

    def _load_session_file(self, filename):
        """Load session from a file."""
        session_data = self.session_manager.load_session(filename)
        if session_data:
            self._restore_session_data(session_data)
            self.settings.setValue("last_session", filename)
            self.status_bar.showMessage(f"Session loaded from {filename}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load session")

    def _restore_session_data(self, session_data):
        """Restore session from saved data."""
        # Restore window state
        if 'window' in session_data:
            window = session_data['window']
            if 'geometry' in window:
                self.restoreGeometry(bytes(window['geometry'], 'utf-8'))
            if 'state' in window:
                self.restoreState(bytes(window['state'], 'utf-8'))
            if 'dark_mode' in window:
                self.settings.setValue("dark_mode", window['dark_mode'])
                self.apply_theme()

        # Restore views
        if 'views' in session_data:
            views = session_data['views']
            self.toggle_protocol_view_action.setChecked(views.get('protocol_view', False))
            self.toggle_automation_view_action.setChecked(views.get('automation_view', False))

        # Restore connections
        if 'connections' in session_data:
            for conn in session_data['connections']:
                port = conn['port']
                if port:
                    tab = self.create_connection_tab(port)
                    if tab and 'settings' in conn:
                        tab.apply_settings(conn['settings'])

        # Restore automation
        if 'automation' in session_data:
            auto = session_data['automation']
            if 'macros' in auto:
                self.automation_manager.macro_recorder.actions = auto['macros']
            if 'scheduled_tasks' in auto:
                self.automation_manager.scheduled_tasks = auto['scheduled_tasks']

    def setup_signals(self):
        """Setup signal connections."""
        # Serial manager signals
        self.serial_manager.connection_status_changed.connect(self.handle_connection_status)
        self.serial_manager.error_occurred.connect(self.handle_error)

        # Protocol analyzer signals
        self.protocol_analyzer.frame_detected.connect(self.handle_protocol_frame)
        self.protocol_analyzer.error_detected.connect(self.handle_protocol_error)

        # Security manager signals
        self.security_manager.auth_status_changed.connect(self.handle_auth_status)
        self.security_manager.access_denied.connect(self.handle_access_denied)
        self.security_manager.security_error.connect(self.handle_security_error)

        # Automation manager signals
        self.automation_manager.macro_started.connect(self.handle_macro_started)
        self.automation_manager.macro_finished.connect(self.handle_macro_finished)
        self.automation_manager.automation_error.connect(self.handle_automation_error)

        # Session manager signals
        self.session_manager.session_error.connect(self.handle_session_error)

    @pyqtSlot(str, bool)
    def handle_connection_status(self, port: str, connected: bool):
        """Handle connection status changes."""
        status = "Connected" if connected else "Disconnected"
        self.status_bar.showMessage(f"{port}: {status}")

    @pyqtSlot(str, str)
    def handle_error(self, port: str, error: str):
        """Handle errors from various components."""
        QMessageBox.warning(self, "Error", f"{port}: {error}")

    @pyqtSlot(str, object)
    def handle_protocol_frame(self, port: str, frame):
        """Handle detected protocol frames."""
        self.protocol_view.add_frame(frame)

    @pyqtSlot(str, str, str)
    def handle_protocol_error(self, port: str, error_type: str, description: str):
        """Handle protocol analysis errors."""
        self.protocol_view.add_error(error_type, description)
        QMessageBox.warning(self, "Protocol Error", f"{port} - {error_type}: {description}")

    @pyqtSlot(str, bool)
    def handle_auth_status(self, username: str, is_authenticated: bool):
        """Handle authentication status changes."""
        status = "authenticated" if is_authenticated else "logged out"
        self.status_bar.showMessage(f"User {username} {status}")

    @pyqtSlot(str, str)
    def handle_access_denied(self, username: str, resource: str):
        """Handle access denied events."""
        QMessageBox.warning(self, "Access Denied", f"User {username} denied access to {resource}")

    @pyqtSlot(str)
    def handle_security_error(self, error: str):
        """Handle security-related errors."""
        QMessageBox.warning(self, "Security Error", error)

    @pyqtSlot(str)
    def handle_macro_started(self, name: str):
        """Handle macro execution start."""
        self.status_bar.showMessage(f"Running macro: {name}")

    @pyqtSlot(str)
    def handle_macro_finished(self, name: str):
        """Handle macro execution completion."""
        self.status_bar.showMessage(f"Macro completed: {name}")

    @pyqtSlot(str)
    def handle_automation_error(self, error: str):
        """Handle automation-related errors."""
        QMessageBox.warning(self, "Automation Error", error)

    @pyqtSlot(str)
    def handle_session_error(self, error: str):
        """Handle session-related errors."""
        QMessageBox.warning(self, "Session Error", error)

    def closeEvent(self, event):
        """Handle application close event."""
        # Close all serial connections
        for i in range(self.left_tabs.count()):
            tab = self.left_tabs.widget(i)
            if isinstance(tab, ConnectionTab):
                if self.serial_manager.get_connection_status(tab.port_name):
                    self.serial_manager.close_connection(tab.port_name)
        
        # Save window state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # Stop automation manager
        self.automation_manager.stop_timer()
        
        event.accept()

    def _get_app_data_dir(self) -> str:
        """Get the application data directory."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running from source
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Use appropriate app data location based on OS
        if sys.platform == 'win32':
            app_data = os.path.join(os.environ['APPDATA'], 'SynapseLink')
        elif sys.platform == 'darwin':
            app_data = os.path.expanduser('~/Library/Application Support/SynapseLink')
        else:  # Linux and other Unix
            app_data = os.path.expanduser('~/.synapselink')
            
        return app_data

    def restore_geometry(self):
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def toggle_split_view(self, checked):
        """Toggle between split view and single view."""
        if checked:
            # Show tab selection dialog
            if self.left_tabs.count() > 0:
                dialog = TabSelectionDialog(self.left_tabs, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_indices = dialog.get_selected_indices()
                    
                    # Move selected tabs to right side
                    for index in sorted(selected_indices, reverse=True):
                        tab = self.left_tabs.widget(index)
                        title = self.left_tabs.tabText(index)
                        self.left_tabs.removeTab(index)
                        self.right_tabs.addTab(tab, title)
                    
                    # Show right side and adjust splitter
                    self.right_tabs.show()
                    self.main_splitter.setSizes([600, 600])
                    self.split_view_button.setText("Disable Split View")
                else:
                    # If dialog was cancelled, uncheck the button
                    self.split_view_button.setChecked(False)
            else:
                # If no tabs to split, uncheck the button
                self.split_view_button.setChecked(False)
                QMessageBox.information(self, "Split View", "No tabs available to split.")
        else:
            # Move all tabs to left widget and hide right widget
            while self.right_tabs.count() > 0:
                tab = self.right_tabs.widget(0)
                title = self.right_tabs.tabText(0)
                self.right_tabs.removeTab(0)
                self.left_tabs.addTab(tab, title)
            self.right_tabs.hide()
            self.main_splitter.setSizes([1200, 0])
            self.split_view_button.setText("Enable Split View")

    def move_tab_to_other_side(self, index, from_left=True):
        """Move a tab from one side to the other."""
        source = self.left_tabs if from_left else self.right_tabs
        target = self.right_tabs if from_left else self.left_tabs
        
        if index >= 0 and index < source.count():
            tab = source.widget(index)
            title = source.tabText(index)
            source.removeTab(index)
            target.addTab(tab, title)
            target.setCurrentWidget(tab) 