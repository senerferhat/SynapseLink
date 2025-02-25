import unittest
from unittest.mock import Mock, patch
from src.core.serial_manager import SerialManager

class TestSerialManager(unittest.TestCase):
    def setUp(self):
        self.serial_manager = SerialManager()

    @patch('serial.tools.list_ports.comports')
    def test_list_ports(self, mock_comports):
        # Mock the serial ports
        mock_port = Mock()
        mock_port.device = 'COM1'
        mock_port.description = 'Test Port'
        mock_comports.return_value = [mock_port]

        # Test the list_ports method
        ports = self.serial_manager.list_ports()
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0], ('COM1', 'Test Port'))

    def test_port_settings(self):
        # Test default port settings
        settings = self.serial_manager.get_port_settings('COM1')
        self.assertIsNone(settings)  # Should be None when port is not connected

    def test_connection_status(self):
        # Test connection status for non-existent port
        self.assertFalse(self.serial_manager.is_connected('COM1'))

if __name__ == '__main__':
    unittest.main() 