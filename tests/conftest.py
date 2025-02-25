import pytest
from PyQt6.QtWidgets import QApplication
import sys

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def mock_serial_port(mocker):
    """Create a mock serial port for testing."""
    mock = mocker.patch('serial.Serial')
    mock.return_value.is_open = False
    mock.return_value.read.return_value = b''
    return mock

@pytest.fixture
def temp_app_dir(tmp_path):
    """Create a temporary directory for application data."""
    app_dir = tmp_path / "synapselink"
    app_dir.mkdir()
    return str(app_dir) 