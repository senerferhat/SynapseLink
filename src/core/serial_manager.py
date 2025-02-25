import serial
import serial.tools.list_ports
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional, Tuple
import threading
import queue
import time

class SerialManager(QObject):
    """Manages serial port connections and communications."""
    
    # Signals for various events
    data_received = pyqtSignal(str, bytes)  # port_name, data
    connection_status_changed = pyqtSignal(str, bool)  # port_name, is_connected
    error_occurred = pyqtSignal(str, str)  # port_name, error_message

    def __init__(self):
        super().__init__()
        self.connections: Dict[str, serial.Serial] = {}
        self.read_threads: Dict[str, threading.Thread] = {}
        self.running: Dict[str, bool] = {}
        self.data_queues: Dict[str, queue.Queue] = {}

    def list_ports(self) -> List[Tuple[str, str]]:
        """Returns a list of available serial ports."""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description))
        return ports

    def open_connection(self, port_name: str, baud_rate: int = 9600,
                       data_bits: int = 8, stop_bits: int = 1,
                       parity: str = 'N', flow_control: bool = False) -> bool:
        """Opens a new serial connection with the specified parameters."""
        try:
            if port_name in self.connections:
                return False

            ser = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=data_bits,
                stopbits=stop_bits,
                parity=parity,
                xonxoff=flow_control,
                timeout=0.1
            )

            self.connections[port_name] = ser
            self.running[port_name] = True
            self.data_queues[port_name] = queue.Queue()

            # Start read thread
            read_thread = threading.Thread(
                target=self._read_loop,
                args=(port_name,),
                daemon=True
            )
            self.read_threads[port_name] = read_thread
            read_thread.start()

            self.connection_status_changed.emit(port_name, True)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, str(e))
            return False

    def close_connection(self, port_name: str) -> bool:
        """Closes the specified serial connection."""
        if port_name not in self.connections:
            return False

        self.running[port_name] = False
        self.read_threads[port_name].join(timeout=1.0)
        
        try:
            self.connections[port_name].close()
            del self.connections[port_name]
            del self.read_threads[port_name]
            del self.running[port_name]
            del self.data_queues[port_name]
            
            self.connection_status_changed.emit(port_name, False)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, str(e))
            return False

    def write_data(self, port_name: str, data: bytes) -> bool:
        """Writes data to the specified serial port."""
        if port_name not in self.connections:
            return False

        try:
            self.connections[port_name].write(data)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, str(e))
            return False

    def _read_loop(self, port_name: str):
        """Background thread for reading data from the serial port."""
        while self.running.get(port_name, False):
            try:
                if port_name not in self.connections:
                    break

                ser = self.connections[port_name]
                if not ser.is_open:
                    break

                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    self.data_queues[port_name].put(data)
                    self.data_received.emit(port_name, data)
                else:
                    time.sleep(0.01)  # Prevent CPU hogging

            except serial.SerialException as e:
                self.error_occurred.emit(port_name, f"Read error: {str(e)}")
                self.running[port_name] = False
                break

    def get_connection_status(self, port_name: str) -> bool:
        """Returns the connection status for the specified port."""
        return port_name in self.connections and self.connections[port_name].is_open

    def get_port_settings(self, port_name: str) -> Optional[Dict]:
        """Returns the current settings for the specified port."""
        if port_name not in self.connections:
            return None

        ser = self.connections[port_name]
        return {
            'baud_rate': ser.baudrate,
            'data_bits': ser.bytesize,
            'stop_bits': ser.stopbits,
            'parity': ser.parity,
            'flow_control': ser.xonxoff
        }

    def __del__(self):
        """Cleanup when the object is destroyed."""
        for port_name in list(self.connections.keys()):
            self.close_connection(port_name)

    def is_connected(self, port_name: str) -> bool:
        """Check if a port is connected."""
        return port_name in self.connections and self.connections[port_name].is_open

    def connect_port(self, port_name: str, settings: dict) -> bool:
        """Connect to a serial port with the specified settings."""
        try:
            # Check if port is already connected
            if port_name in self.connections:
                if self.connections[port_name].is_open:
                    return True
                # Try to reopen existing connection
                try:
                    self.connections[port_name].open()
                    self.connection_status_changed.emit(port_name, True)
                    return True
                except serial.SerialException as e:
                    self.error_occurred.emit(port_name, f"Failed to reopen port: {str(e)}")
                    return False

            # Create new connection
            ser = serial.Serial(
                port=port_name,
                baudrate=settings.get('baudrate', 9600),
                bytesize=settings.get('bytesize', 8),
                stopbits=settings.get('stopbits', 1),
                parity=settings.get('parity', 'N'),
                xonxoff=settings.get('flow_control', False),
                timeout=0.1
            )

            self.connections[port_name] = ser
            self.running[port_name] = True
            self.data_queues[port_name] = queue.Queue()

            # Start read thread
            read_thread = threading.Thread(
                target=self._read_loop,
                args=(port_name,),
                daemon=True
            )
            self.read_threads[port_name] = read_thread
            read_thread.start()

            self.connection_status_changed.emit(port_name, True)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, f"Connection error: {str(e)}")
            return False
        except ValueError as e:
            self.error_occurred.emit(port_name, f"Invalid settings: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(port_name, f"Unexpected error: {str(e)}")
            return False

    def disconnect_port(self, port_name: str) -> bool:
        """Disconnect from a serial port."""
        if port_name not in self.connections:
            return False

        try:
            # Stop read thread
            self.running[port_name] = False
            if port_name in self.read_threads:
                self.read_threads[port_name].join(timeout=1.0)
            
            # Close port
            if self.connections[port_name].is_open:
                self.connections[port_name].close()
            
            # Clean up resources
            del self.connections[port_name]
            if port_name in self.read_threads:
                del self.read_threads[port_name]
            if port_name in self.running:
                del self.running[port_name]
            if port_name in self.data_queues:
                del self.data_queues[port_name]
            
            self.connection_status_changed.emit(port_name, False)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, f"Disconnect error: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(port_name, f"Unexpected error: {str(e)}")
            return False

    def send_data(self, port_name: str, data: bytes) -> bool:
        """Send data through the specified serial port."""
        if port_name not in self.connections:
            self.error_occurred.emit(port_name, "Port not connected")
            return False

        try:
            if not self.connections[port_name].is_open:
                self.error_occurred.emit(port_name, "Port is closed")
                return False

            bytes_written = self.connections[port_name].write(data)
            return bytes_written == len(data)

        except serial.SerialException as e:
            self.error_occurred.emit(port_name, f"Send error: {str(e)}")
            return False 