from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QPushButton, QLabel, QLineEdit, QCheckBox,
                               QGroupBox, QFormLayout, QListWidget, QMessageBox,
                               QComboBox, QWidget)
from PyQt6.QtCore import Qt
import serial.tools.list_ports

class SecuritySettingsDialog(QDialog):
    """Dialog for managing security settings."""
    
    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.security_manager = security_manager
        self.setWindowTitle("Security Settings")
        self.setup_ui()
        self.load_settings()
        self.refresh_ports()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create encryption settings group
        encryption_group = QGroupBox("Encryption Settings")
        encryption_layout = QVBoxLayout()

        # Port list
        port_label = QLabel("Available Ports:")
        self.port_list = QListWidget()
        self.port_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Refresh ports button
        refresh_button = QPushButton("Refresh Ports")
        refresh_button.clicked.connect(self.refresh_ports)

        encryption_layout.addWidget(port_label)
        encryption_layout.addWidget(self.port_list)
        encryption_layout.addWidget(refresh_button)

        # Global encryption enable
        self.encryption_enabled = QCheckBox("Enable Encryption")
        encryption_layout.addWidget(self.encryption_enabled)

        encryption_group.setLayout(encryption_layout)
        layout.addWidget(encryption_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def refresh_ports(self):
        """Refresh the list of available ports."""
        self.port_list.clear()
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            item = port.device
            list_item = QListWidget.QListWidgetItem(item)
            self.port_list.addItem(list_item)
            
            # Check if port is encrypted
            if self.security_manager.is_port_encrypted(port.device):
                list_item.setSelected(True)

    def load_settings(self):
        """Load current security settings."""
        self.encryption_enabled.setChecked(self.security_manager.is_encryption_enabled())
        
    def save_settings(self):
        """Save security settings."""
        try:
            # Update global encryption setting
            self.security_manager.set_encryption_enabled(self.encryption_enabled.isChecked())
            
            # Update port-specific encryption settings
            selected_ports = [item.text() for item in self.port_list.selectedItems()]
            all_ports = [self.port_list.item(i).text() for i in range(self.port_list.count())]
            
            for port in all_ports:
                self.security_manager.set_port_encryption(port, port in selected_ports)
            
            QMessageBox.information(self, "Success", "Security settings saved successfully")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save security settings: {str(e)}")

    def create_encryption_tab(self) -> QWidget:
        """Create the encryption settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Port encryption group
        port_group = QGroupBox("Port Encryption")
        port_layout = QFormLayout()

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        port_layout.addRow("Port:", self.port_combo)

        enable_button = QPushButton("Enable Encryption")
        enable_button.clicked.connect(self.enable_port_encryption)
        port_layout.addRow("", enable_button)

        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        # Encrypted ports list
        list_group = QGroupBox("Encrypted Ports")
        list_layout = QVBoxLayout()

        self.encrypted_ports = QListWidget()
        list_layout.addWidget(self.encrypted_ports)

        remove_button = QPushButton("Remove Encryption")
        remove_button.clicked.connect(self.remove_port_encryption)
        list_layout.addWidget(remove_button)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        return tab

    def create_permissions_tab(self) -> QWidget:
        """Create the permissions settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # User selection
        form_layout = QFormLayout()
        
        self.user_combo = QComboBox()
        self.refresh_user_list()
        self.user_combo.currentTextChanged.connect(self.on_user_selected)
        form_layout.addRow("User:", self.user_combo)
        
        layout.addLayout(form_layout)

        # Permissions group
        perms_group = QGroupBox("Permissions")
        perms_layout = QVBoxLayout()

        self.perm_checkboxes = {}
        permissions = [
            "read", "write", "execute_scripts",
            "record_macros", "manage_users", "view_logs"
        ]

        for perm in permissions:
            checkbox = QCheckBox(perm.replace('_', ' ').title())
            checkbox.stateChanged.connect(
                lambda state, p=perm: self.on_permission_changed(p, state)
            )
            self.perm_checkboxes[perm] = checkbox
            perms_layout.addWidget(checkbox)

        perms_group.setLayout(perms_layout)
        layout.addWidget(perms_group)

        return tab

    def create_password_tab(self) -> QWidget:
        """Create the password change tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Current Password:", self.current_password)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("New Password:", self.new_password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Confirm Password:", self.confirm_password)

        change_button = QPushButton("Change Password")
        change_button.clicked.connect(self.change_password)
        layout.addRow("", change_button)

        return tab

    def refresh_user_list(self):
        """Refresh the list of users in the combo box."""
        self.user_combo.clear()
        for username in self.security_manager.users.keys():
            self.user_combo.addItem(username)

    def refresh_encrypted_ports(self):
        """Refresh the list of encrypted ports."""
        self.encrypted_ports.clear()
        for port in self.security_manager.encryption_keys.keys():
            self.encrypted_ports.addItem(port)

    def enable_port_encryption(self):
        """Enable encryption for the selected port."""
        port = self.port_combo.currentText()
        if not port:
            return

        if self.security_manager.setup_encryption(port):
            self.refresh_encrypted_ports()
            QMessageBox.information(self, "Success",
                                  f"Encryption enabled for port {port}")
        else:
            QMessageBox.warning(self, "Error",
                              f"Failed to enable encryption for port {port}")

    def remove_port_encryption(self):
        """Remove encryption from the selected port."""
        current = self.encrypted_ports.currentItem()
        if not current:
            return

        port = current.text()
        if port in self.security_manager.encryption_keys:
            del self.security_manager.encryption_keys[port]
            self.refresh_encrypted_ports()

    def on_user_selected(self, username: str):
        """Update permission checkboxes when a user is selected."""
        if not username:
            return

        user = self.security_manager.users.get(username)
        if not user:
            return

        permissions = user.get('permissions', [])
        for perm, checkbox in self.perm_checkboxes.items():
            checkbox.setChecked(perm in permissions or '*' in permissions)

    def on_permission_changed(self, permission: str, state: int):
        """Update user permissions when a checkbox is toggled."""
        username = self.user_combo.currentText()
        if not username:
            return

        user = self.security_manager.users.get(username)
        if not user:
            return

        permissions = set(user.get('permissions', []))
        if state == Qt.CheckState.Checked.value:
            permissions.add(permission)
        else:
            permissions.discard(permission)

        user['permissions'] = list(permissions)
        self.security_manager.save_config()

    def change_password(self):
        """Change the current user's password."""
        current = self.current_password.text()
        new = self.new_password.text()
        confirm = self.confirm_password.text()

        if not all([current, new, confirm]):
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        if new != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return

        username = self.user_combo.currentText()
        if self.security_manager.change_password(username, current, new):
            QMessageBox.information(self, "Success", "Password changed successfully.")
            self.current_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to change password.")

    def on_security_error(self, error: str):
        """Handle security-related errors."""
        QMessageBox.warning(self, "Security Error", error) 