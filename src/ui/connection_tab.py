from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                               QComboBox, QPushButton, QLabel, QSpinBox,
                               QCheckBox, QGroupBox, QSplitter, QMenu, QToolBar,
                               QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont, QAction
import datetime

from .visualization_widget import VisualizationWidget
from .search_filter_dialog import SearchFilterDialog
from .protocol_view import ProtocolView
from core.protocol_analyzer import ProtocolFrame

class ConnectionTab(QWidget):
    """Tab widget for a single serial connection."""

    # Signals
    data_received = pyqtSignal(str, bytes)  # port_name, data
    data_sent = pyqtSignal(str, bytes)  # port_name, data
    connection_closed = pyqtSignal(str)  # port_name

    def __init__(self, serial_manager, data_processor, port_name, protocol_analyzer, security_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self.data_processor = data_processor
        self.port_name = port_name
        self.protocol_analyzer = protocol_analyzer
        self.security_manager = security_manager
        
        # Initialize UI
        self.setup_ui()
        
        # Setup signals after UI is initialized
        self.setup_signals()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # Create main splitter for data display and visualization
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(main_splitter)

        # Data display group
        display_group = QGroupBox("Data Display")
        display_layout = QVBoxLayout()

        # Display controls
        control_layout = QHBoxLayout()
        
        self.hex_view = QCheckBox("Hex View")
        control_layout.addWidget(self.hex_view)
        
        self.show_timestamp = QCheckBox("Show Timestamp")
        control_layout.addWidget(self.show_timestamp)
        
        self.auto_scroll = QCheckBox("Auto Scroll")
        self.auto_scroll.setChecked(True)
        control_layout.addWidget(self.auto_scroll)
        
        display_layout.addLayout(control_layout)

        # Data display
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        display_layout.addWidget(self.data_display)

        display_group.setLayout(display_layout)
        main_splitter.addWidget(display_group)

        # Visualization widget
        self.visualization = VisualizationWidget(self.data_processor)
        self.visualization.hide()  # Hidden by default
        main_splitter.addWidget(self.visualization)

        # Bottom panel with input and send controls
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def create_toolbar(self):
        toolbar = QToolBar()
        
        # Search and Filter button
        self.search_button = QPushButton("Search && Filter")
        toolbar.addWidget(self.search_button)

        toolbar.addSeparator()

        # Export actions
        export_menu = QMenu("Export", self)
        
        export_csv = QAction("Export as CSV", self)
        export_csv.triggered.connect(lambda: self.export_data('csv'))
        export_menu.addAction(export_csv)
        
        export_json = QAction("Export as JSON", self)
        export_json.triggered.connect(lambda: self.export_data('json'))
        export_menu.addAction(export_json)
        
        export_xml = QAction("Export as XML", self)
        export_xml.triggered.connect(lambda: self.export_data('xml'))
        export_menu.addAction(export_xml)

        export_action = toolbar.addAction("Export")
        export_action.setMenu(export_menu)

        toolbar.addSeparator()

        # Add visualization toggle
        self.visualization_button = QPushButton("Visualization")
        self.visualization_button.setCheckable(True)
        self.visualization_button.toggled.connect(self.toggle_visualization)
        toolbar.addWidget(self.visualization_button)

        # Add protocol toggle
        self.protocol_button = QPushButton("Protocol")
        self.protocol_button.setCheckable(True)
        toolbar.addWidget(self.protocol_button)

        toolbar.addSeparator()

        # Add encryption toggle
        self.encryption_button = QPushButton("Encryption")
        self.encryption_button.setCheckable(True)
        self.encryption_button.toggled.connect(self.toggle_encryption)
        toolbar.addWidget(self.encryption_button)

        return toolbar

    def create_control_panel(self):
        """Create the connection control panel."""
        group = QGroupBox("Connection Settings")
        layout = QHBoxLayout()

        # Port settings
        settings_layout = QHBoxLayout()

        # Baud rate selection
        baud_layout = QVBoxLayout()
        baud_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_rate = QComboBox()
        self.baud_rate.addItems(['9600', '19200', '38400', '57600', '115200'])
        baud_layout.addWidget(self.baud_rate)
        settings_layout.addLayout(baud_layout)

        # Data bits selection
        data_layout = QVBoxLayout()
        data_layout.addWidget(QLabel("Data Bits:"))
        self.data_bits = QComboBox()
        self.data_bits.addItems(['8', '7', '6', '5'])
        data_layout.addWidget(self.data_bits)
        settings_layout.addLayout(data_layout)

        # Stop bits selection
        stop_layout = QVBoxLayout()
        stop_layout.addWidget(QLabel("Stop Bits:"))
        self.stop_bits = QComboBox()
        self.stop_bits.addItems(['1', '1.5', '2'])
        stop_layout.addWidget(self.stop_bits)
        settings_layout.addLayout(stop_layout)

        # Parity selection
        parity_layout = QVBoxLayout()
        parity_layout.addWidget(QLabel("Parity:"))
        self.parity = QComboBox()
        self.parity.addItems(['None', 'Even', 'Odd', 'Mark', 'Space'])
        parity_layout.addWidget(self.parity)
        settings_layout.addLayout(parity_layout)

        layout.addLayout(settings_layout)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setCheckable(True)
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        group.setLayout(layout)
        return group

    def create_bottom_panel(self):
        bottom_group = QGroupBox("Send Data")
        bottom_layout = QHBoxLayout()

        # Input field
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(60)
        bottom_layout.addWidget(self.input_field)

        # Send controls
        send_layout = QVBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_data)
        send_layout.addWidget(self.send_button)

        self.send_hex = QCheckBox("Send as Hex")
        send_layout.addWidget(self.send_hex)

        bottom_layout.addLayout(send_layout)
        
        bottom_group.setLayout(bottom_layout)
        return bottom_group

    def setup_signals(self):
        """Setup signal connections."""
        # Serial manager signals
        self.serial_manager.data_received.connect(self.handle_received_data)
        self.serial_manager.connection_status_changed.connect(self.handle_connection_status)
        self.serial_manager.error_occurred.connect(self.handle_error)

        # Protocol analyzer signals
        self.protocol_analyzer.frame_detected.connect(self.on_frame_detected)
        self.protocol_analyzer.error_detected.connect(self.on_error_detected)

        # Security manager signals
        self.security_manager.security_error.connect(self.on_security_error)

        # UI signals
        self.send_button.clicked.connect(self.send_data)
        self.search_button.clicked.connect(self.show_search_dialog)
        
        # Visualization signals
        if hasattr(self, 'visualization'):
            self.visualization.update_requested.connect(self.update_display)

    @pyqtSlot(str, bytes)
    def handle_received_data(self, port, data):
        if port != self.port_name:
            return

        # Process data through filters and patterns
        processed_data = self.data_processor.process_data(port, data)

        if self.hex_view.isChecked():
            display_text = ' '.join(f'{b:02X}' for b in processed_data)
        else:
            try:
                display_text = processed_data.decode('utf-8')
            except UnicodeDecodeError:
                display_text = ' '.join(f'{b:02X}' for b in processed_data)

        if self.show_timestamp.isChecked():
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            display_text = f'[{timestamp}] {display_text}'

        self.data_display.moveCursor(QTextCursor.MoveOperation.End)
        self.data_display.insertPlainText(display_text)
        
        if self.auto_scroll.isChecked():
            self.data_display.moveCursor(QTextCursor.MoveOperation.End)

        # Analyze received data
        if self.protocol_button.isChecked():
            self.protocol_analyzer.analyze_frame(self.port_name, data)

    @pyqtSlot(str, bool)
    def handle_connection_status(self, port, connected):
        """Handle connection status changes."""
        if port != self.port_name:
            return
            
        if connected:
            self.connect_button.setChecked(True)
            self.connect_button.setText("Disconnect")
            self.status_label.setText(f"Connected to {port}")
            self.encryption_button.setEnabled(True)
        else:
            self.connect_button.setChecked(False)
            self.connect_button.setText("Connect")
            self.status_label.setText(f"Disconnected from {port}")
            self.encryption_button.setEnabled(False)
            self.encryption_button.setChecked(False)

    @pyqtSlot(str, str)
    def handle_error(self, port, error):
        """Handle serial port errors."""
        if port != self.port_name:
            return
            
        self.status_label.setText(f"Error: {error}")
        self.connect_button.setChecked(False)
        self.connect_button.setText("Connect")
        self.encryption_button.setEnabled(False)
        self.encryption_button.setChecked(False)

    def export_data(self, format_type):
        """Export data in the specified format."""
        file_filters = {
            'csv': 'CSV Files (*.csv)',
            'json': 'JSON Files (*.json)',
            'xml': 'XML Files (*.xml)'
        }

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            file_filters[format_type]
        )

        if filename:
            self.data_processor.export_data(self.port_name, format_type, filename)

    def toggle_connection(self):
        """Toggle the serial connection."""
        try:
            if self.serial_manager.is_connected(self.port_name):
                if self.serial_manager.disconnect_port(self.port_name):
                    self.connect_button.setChecked(False)
                    self.connect_button.setText("Connect")
                    self.status_label.setText(f"Disconnected from {self.port_name}")
                    self.encryption_button.setEnabled(False)
            else:
                # Map parity selection to PySerial values
                parity_map = {
                    'None': 'N',
                    'Even': 'E',
                    'Odd': 'O',
                    'Mark': 'M',
                    'Space': 'S'
                }
                
                settings = {
                    'baudrate': int(self.baud_rate.currentText()),
                    'bytesize': int(self.data_bits.currentText()),
                    'stopbits': float(self.stop_bits.currentText()),
                    'parity': parity_map[self.parity.currentText()].upper()  # Ensure uppercase
                }
                
                if self.serial_manager.connect_port(self.port_name, settings):
                    self.connect_button.setChecked(True)
                    self.connect_button.setText("Disconnect")
                    self.status_label.setText(f"Connected to {self.port_name}")
                    self.encryption_button.setEnabled(True)
                else:
                    self.connect_button.setChecked(False)
                    self.status_label.setText(f"Failed to connect to {self.port_name}")
        except Exception as e:
            self.handle_error(self.port_name, str(e))
            self.connect_button.setChecked(False)
            self.status_label.setText(f"Error: {str(e)}")

    def toggle_encryption(self, checked):
        """Toggle encryption for the connection."""
        try:
            if checked:
                if self.security_manager.setup_encryption(self.port_name):
                    self.status_label.setText("Encryption enabled")
                else:
                    self.encryption_button.setChecked(False)
                    self.status_label.setText("Failed to enable encryption")
            else:
                if self.port_name in self.security_manager.encryption_keys:
                    del self.security_manager.encryption_keys[self.port_name]
                    self.status_label.setText("Encryption disabled")
                self.encryption_button.setChecked(False)
            
            # Update the button appearance based on state
            self.encryption_button.setStyleSheet(
                "background-color: #4CAF50;" if checked else ""
            )
        except Exception as e:
            self.handle_error(self.port_name, str(e))
            self.encryption_button.setChecked(False)
            self.encryption_button.setStyleSheet("")

    def send_data(self):
        """Send data through the serial port."""
        if not self.serial_manager.is_connected(self.port_name):
            return

        data = self.input_field.toPlainText()
        if not data:
            return

        if self.send_hex.isChecked():
            try:
                # Convert hex string to bytes
                data = bytes.fromhex(data.replace(' ', ''))
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid hex format")
                return
        else:
            data = data.encode()

        # Send through security manager for encryption if enabled
        if self.encryption_button.isChecked():
            data = self.security_manager.encrypt_data(self.port_name, data)

        self.serial_manager.send_data(self.port_name, data)
        self.data_sent.emit(self.port_name, data)
        
        if not self.send_hex.isChecked():
            self.input_field.clear()

    def clear_display(self):
        """Clear the data display."""
        self.data_display.clear()
        self.data_processor.clear_data(self.port_name)
        if hasattr(self, 'visualization'):
            self.visualization.clear()
        if hasattr(self, 'protocol_view'):
            self.protocol_view.clear()

    def show_search_dialog(self):
        """Show search and filter dialog."""
        dialog = SearchFilterDialog(self.data_processor, self.port_name, self)
        dialog.exec()

    def apply_search_filters(self, filters):
        """Apply search filters to the data display."""
        self.data_processor.set_filters(filters)
        self.update_display()

    def update_display(self):
        """Update the data display with filtered content."""
        if not hasattr(self, 'data_display'):
            return
        
        cursor = self.data_display.textCursor()
        current_position = cursor.position()
        
        # Get filtered data from processor
        filtered_data = self.data_processor.get_filtered_data(self.port_name)
        
        # Update display
        self.data_display.clear()
        self.data_display.setPlainText(filtered_data)
        
        # Restore cursor position if auto-scroll is off
        if not self.auto_scroll.isChecked():
            cursor.setPosition(current_position)
            self.data_display.setTextCursor(cursor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.data_display.setTextCursor(cursor)

    def toggle_visualization(self, checked):
        """Toggle the visualization widget visibility."""
        if hasattr(self, 'visualization'):
            self.visualization.setVisible(checked)
            if checked:
                self.visualization.set_port(self.port_name)
                self.visualization.update_display()

    def on_frame_detected(self, port: str, frame: ProtocolFrame):
        """Handle detected protocol frame."""
        if port == self.port_name and self.protocol_button.isChecked():
            self.protocol_view.add_frame(frame)

    def on_error_detected(self, port: str, error_type: str, description: str):
        """Handle protocol error."""
        if port == self.port_name and self.protocol_button.isChecked():
            self.protocol_view.add_error(error_type, description)

    def on_security_error(self, error: str):
        """Handle security-related errors."""
        QMessageBox.warning(self, "Security Error", error)

    def close_connection(self):
        """Clean up resources when closing the connection."""
        # Stop visualization updates
        if hasattr(self, 'visualization') and self.visualization:
            self.visualization.update_timer.stop()
            self.visualization.update_timer = None
        
        # Clean up security
        if self.port_name in self.security_manager.encryption_keys:
            del self.security_manager.encryption_keys[self.port_name]
        
        # Clear protocol buffer
        self.protocol_analyzer.clear_buffer(self.port_name)
        
        # Emit closed signal
        self.connection_closed.emit(self.port_name)

    def closeEvent(self, event):
        """Handle widget close event."""
        self.close_connection()
        super().closeEvent(event) 