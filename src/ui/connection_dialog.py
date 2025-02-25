from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import Qt

class ConnectionDialog(QDialog):
    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self.selected_port = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("New Serial Connection")
        self.setModal(True)
        
        layout = QVBoxLayout(self)

        # Port selection group
        port_group = QGroupBox("Select Port")
        port_layout = QVBoxLayout()

        # Port combo box
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_row.addWidget(self.port_combo)

        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_ports)
        port_row.addWidget(refresh_button)

        port_layout.addLayout(port_row)
        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.accept)
        connect_button.setDefault(True)
        button_layout.addWidget(connect_button)

        layout.addLayout(button_layout)

    def refresh_ports(self):
        self.port_combo.clear()
        for port, description in self.serial_manager.list_ports():
            self.port_combo.addItem(f"{port} - {description}", port)

    def get_selected_port(self):
        if self.port_combo.currentData():
            return self.port_combo.currentData()
        return None 