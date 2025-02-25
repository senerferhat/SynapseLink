from typing import Dict, List, Optional
import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt6.QtCore import QObject, pyqtSignal

class SecurityManager(QObject):
    """Manages security features including authentication, access control, and encryption."""
    
    # Signals
    auth_status_changed = pyqtSignal(str, bool)  # username, is_authenticated
    access_denied = pyqtSignal(str, str)  # username, resource
    security_error = pyqtSignal(str)  # error_message

    def __init__(self, config_file: str = 'security_config.json'):
        super().__init__()
        self.config_file = config_file
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.encryption_keys: Dict[str, bytes] = {}
        self.load_config()

    def load_config(self):
        """Load security configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.users = config.get('users', {})
            else:
                # Create default admin user if no config exists
                self.users = {
                    'admin': {
                        'password_hash': self._hash_password('admin'),
                        'role': 'admin',
                        'permissions': ['*']
                    }
                }
                self.save_config()
        except Exception as e:
            self.security_error.emit(f"Error loading security config: {str(e)}")

    def save_config(self):
        """Save security configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'users': self.users}, f, indent=2)
        except Exception as e:
            self.security_error.emit(f"Error saving security config: {str(e)}")

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        if username not in self.users:
            self.auth_status_changed.emit(username, False)
            return False

        if self._hash_password(password) == self.users[username]['password_hash']:
            # Create session
            session = {
                'timestamp': datetime.now(),
                'token': os.urandom(32).hex()
            }
            self.sessions[username] = session
            self.auth_status_changed.emit(username, True)
            return True

        self.auth_status_changed.emit(username, False)
        return False

    def logout(self, username: str):
        """Log out a user."""
        if username in self.sessions:
            del self.sessions[username]
        self.auth_status_changed.emit(username, False)

    def is_authenticated(self, username: str) -> bool:
        """Check if a user is authenticated."""
        return username in self.sessions

    def check_permission(self, username: str, resource: str) -> bool:
        """Check if a user has permission to access a resource."""
        if not self.is_authenticated(username):
            return False

        user = self.users.get(username)
        if not user:
            return False

        permissions = user['permissions']
        
        # Admin has all permissions
        if user['role'] == 'admin' or '*' in permissions:
            return True

        # Check specific permissions
        return resource in permissions

    def add_user(self, admin_username: str, new_username: str, password: str,
                role: str = 'user', permissions: List[str] = None) -> bool:
        """Add a new user (requires admin privileges)."""
        if not self.check_permission(admin_username, 'user_management'):
            self.access_denied.emit(admin_username, 'user_management')
            return False

        if new_username in self.users:
            self.security_error.emit(f"User {new_username} already exists")
            return False

        self.users[new_username] = {
            'password_hash': self._hash_password(password),
            'role': role,
            'permissions': permissions or []
        }
        self.save_config()
        return True

    def remove_user(self, admin_username: str, username: str) -> bool:
        """Remove a user (requires admin privileges)."""
        if not self.check_permission(admin_username, 'user_management'):
            self.access_denied.emit(admin_username, 'user_management')
            return False

        if username not in self.users:
            return False

        del self.users[username]
        if username in self.sessions:
            del self.sessions[username]
        self.save_config()
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if not self.authenticate(username, old_password):
            return False

        self.users[username]['password_hash'] = self._hash_password(new_password)
        self.save_config()
        return True

    def setup_encryption(self, port_name: str) -> bool:
        """Set up encryption for a serial port."""
        try:
            # Generate a new encryption key
            key = Fernet.generate_key()
            self.encryption_keys[port_name] = key
            return True
        except Exception as e:
            self.security_error.emit(f"Error setting up encryption: {str(e)}")
            return False

    def encrypt_data(self, port_name: str, data: bytes) -> Optional[bytes]:
        """Encrypt data for transmission."""
        if port_name not in self.encryption_keys:
            return data

        try:
            f = Fernet(self.encryption_keys[port_name])
            return f.encrypt(data)
        except Exception as e:
            self.security_error.emit(f"Encryption error: {str(e)}")
            return None

    def decrypt_data(self, port_name: str, data: bytes) -> Optional[bytes]:
        """Decrypt received data."""
        if port_name not in self.encryption_keys:
            return data

        try:
            f = Fernet(self.encryption_keys[port_name])
            return f.decrypt(data)
        except Exception as e:
            self.security_error.emit(f"Decryption error: {str(e)}")
            return None 