from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox, QTabWidget,
                               QWidget, QFormLayout, QComboBox, QListWidget)
from PyQt6.QtCore import pyqtSignal

class LoginDialog(QDialog):
    """Dialog for user authentication."""
    
    login_successful = pyqtSignal(str)  # username

    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.security_manager = security_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Login")
        layout = QVBoxLayout(self)

        # Login form
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        form_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.try_login)
        button_layout.addWidget(login_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def try_login(self):
        """Attempt to log in with provided credentials."""
        username = self.username_edit.text()
        password = self.password_edit.text()

        if self.security_manager.authenticate(username, password):
            self.login_successful.emit(username)
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed",
                              "Invalid username or password.")

class UserManagementDialog(QDialog):
    """Dialog for managing users and permissions."""

    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.security_manager = security_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("User Management")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Users tab
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        
        # User list
        self.user_list = QListWidget()
        self.refresh_user_list()
        users_layout.addWidget(self.user_list)

        # User form
        form_layout = QFormLayout()
        
        self.new_username = QLineEdit()
        form_layout.addRow("Username:", self.new_username)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.new_password)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        form_layout.addRow("Role:", self.role_combo)
        
        users_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add User")
        add_button.clicked.connect(self.add_user)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove User")
        remove_button.clicked.connect(self.remove_user)
        button_layout.addWidget(remove_button)
        
        users_layout.addLayout(button_layout)
        
        tab_widget.addTab(users_tab, "Users")

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def refresh_user_list(self):
        """Refresh the list of users."""
        self.user_list.clear()
        for username, data in self.security_manager.users.items():
            self.user_list.addItem(f"{username} ({data['role']})")

    def add_user(self):
        """Add a new user."""
        username = self.new_username.text()
        password = self.new_password.text()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Error",
                              "Please provide both username and password.")
            return

        # Get current user (admin)
        admin_username = next((user for user, data in self.security_manager.users.items()
                             if data['role'] == 'admin'), None)
        
        if not admin_username:
            QMessageBox.warning(self, "Error", "No admin user found.")
            return

        permissions = ['*'] if role == 'admin' else ['read', 'write']
        if self.security_manager.add_user(admin_username, username, password,
                                        role, permissions):
            self.refresh_user_list()
            self.new_username.clear()
            self.new_password.clear()
        else:
            QMessageBox.warning(self, "Error",
                              "Failed to add user. Check if username already exists.")

    def remove_user(self):
        """Remove the selected user."""
        current_item = self.user_list.currentItem()
        if not current_item:
            return

        username = current_item.text().split(' ')[0]
        
        # Get current user (admin)
        admin_username = next((user for user, data in self.security_manager.users.items()
                             if data['role'] == 'admin'), None)
        
        if not admin_username:
            QMessageBox.warning(self, "Error", "No admin user found.")
            return

        if username == admin_username:
            QMessageBox.warning(self, "Error", "Cannot remove admin user.")
            return

        if QMessageBox.question(self, "Confirm Removal",
                              f"Are you sure you want to remove user {username}?",
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.security_manager.remove_user(admin_username, username):
                self.refresh_user_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove user.") 