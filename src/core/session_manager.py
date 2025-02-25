from typing import Dict, Any
import json
import os
from datetime import datetime, timedelta
import psutil
import gc
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from .config import PERFORMANCE_CONFIG

class MemoryManager:
    def __init__(self, threshold_mb: int = PERFORMANCE_CONFIG['memory_threshold']):
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(seconds=PERFORMANCE_CONFIG['cleanup_interval'])
        self.logger = logging.getLogger(__name__)

    def check_memory_usage(self) -> bool:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        if memory_info.rss > self.threshold_bytes:
            self.logger.warning(f"Memory usage exceeded threshold: {memory_info.rss / 1024 / 1024:.2f}MB")
            return True
        return False

    def cleanup(self):
        gc.collect()
        self.last_cleanup = datetime.now()

class SessionManager(QObject):
    """Manages application session state."""
    
    # Signals
    session_loaded = pyqtSignal(dict)  # session_data
    session_saved = pyqtSignal(str)    # session_file
    session_error = pyqtSignal(str)    # error_message

    def __init__(self, app_data_dir: str):
        super().__init__()
        self.app_data_dir = app_data_dir
        self.memory_manager = MemoryManager()
        self.ensure_directories()
        self._start_memory_monitor()

    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, 'sessions'), exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, 'config'), exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, 'logs'), exist_ok=True)

    def _start_memory_monitor(self):
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self._check_memory)
        self.memory_timer.start(30000)  # Check every 30 seconds

    def _check_memory(self):
        if self.memory_manager.check_memory_usage():
            self._optimize_memory()

    def _optimize_memory(self):
        # Serialize old data to disk if needed
        self._serialize_old_data()
        self.memory_manager.cleanup()

    def _serialize_old_data(self):
        current_time = datetime.now()
        archive_path = os.path.join(self.app_data_dir, 'archive')
        os.makedirs(archive_path, exist_ok=True)

        # Archive data older than 1 hour
        cutoff_time = current_time - timedelta(hours=1)
        
        for port_name, buffer in self.data_processor.buffers.items():
            old_data = buffer.get_data(end_time=cutoff_time)
            if old_data:
                archive_file = os.path.join(
                    archive_path,
                    f"{port_name}_{cutoff_time.strftime('%Y%m%d_%H%M%S')}.json"
                )
                try:
                    with open(archive_file, 'w') as f:
                        json.dump([
                            {
                                'timestamp': ts.isoformat(),
                                'data': data.hex()
                            }
                            for ts, data in old_data
                        ], f)
                    buffer.clear_old_data(cutoff_time)
                except Exception as e:
                    self.session_error.emit(f"Failed to archive data: {str(e)}")

    def save_session(self, session_data: Dict[str, Any], filename: str = None) -> bool:
        """Save current session state."""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.join(self.app_data_dir, 'sessions', f'session_{timestamp}.json')

            # Ensure the session directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Optimize memory before saving
            self._optimize_memory()

            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)

            self.session_saved.emit(filename)
            return True

        except Exception as e:
            self.session_error.emit(f"Failed to save session: {str(e)}")
            return False

    def load_session(self, filename: str) -> Dict[str, Any]:
        """Load a saved session state."""
        try:
            with open(filename, 'r') as f:
                session_data = json.load(f)
            
            self.session_loaded.emit(session_data)
            return session_data

        except Exception as e:
            self.session_error.emit(f"Failed to load session: {str(e)}")
            return {}

    def get_recent_sessions(self, max_count: int = 10) -> list:
        """Get list of recent session files."""
        sessions_dir = os.path.join(self.app_data_dir, 'sessions')
        if not os.path.exists(sessions_dir):
            return []

        sessions = []
        for file in os.listdir(sessions_dir):
            if file.endswith('.json'):
                full_path = os.path.join(sessions_dir, file)
                sessions.append({
                    'path': full_path,
                    'name': file,
                    'date': datetime.fromtimestamp(os.path.getmtime(full_path))
                })

        # Sort by date, newest first
        sessions.sort(key=lambda x: x['date'], reverse=True)
        return sessions[:max_count]

    def get_app_data_path(self, *paths: str) -> str:
        """Get full path within app data directory."""
        return os.path.join(self.app_data_dir, *paths)

    def __del__(self):
        if hasattr(self, 'memory_timer'):
            self.memory_timer.stop() 