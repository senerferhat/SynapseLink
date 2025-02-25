from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import struct
from pymodbus.exceptions import ModbusException
from pymodbus.utilities import hexlify_packets
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class ProtocolFrame:
    timestamp: datetime
    protocol: str
    frame_type: str
    data: bytes
    parsed_data: Dict
    errors: List[str]

class ProtocolAnalyzer(QObject):
    """Analyzes serial protocols and detects errors."""
    
    # Signals
    frame_detected = pyqtSignal(str, ProtocolFrame)  # port_name, frame
    error_detected = pyqtSignal(str, str, str)  # port_name, error_type, description

    def __init__(self):
        super().__init__()
        self.frame_buffer: Dict[str, List[bytes]] = {}
        self.last_byte: Dict[str, int] = {}

    def analyze_frame(self, port_name: str, data: bytes) -> Optional[ProtocolFrame]:
        """Analyze incoming data for protocol frames."""
        # Buffer the data
        if port_name not in self.frame_buffer:
            self.frame_buffer[port_name] = []
        self.frame_buffer[port_name].extend(data)

        # Try to detect protocol and extract frame
        frame = None
        
        # Try Modbus first
        modbus_frame = self._extract_modbus_frame(port_name)
        if modbus_frame:
            frame = modbus_frame
        else:
            # Try RS-232/485
            serial_frame = self._extract_serial_frame(port_name)
            if serial_frame:
                frame = serial_frame

        if frame:
            self.frame_detected.emit(port_name, frame)
            return frame
        return None

    def _extract_modbus_frame(self, port_name: str) -> Optional[ProtocolFrame]:
        """Try to extract a Modbus frame from the buffer."""
        buffer = bytes(self.frame_buffer[port_name])
        if len(buffer) < 4:  # Minimum Modbus frame size
            return None

        try:
            # Check for Modbus RTU frame
            if len(buffer) >= 4 and self._check_modbus_crc(buffer):
                # Try to decode as request or response
                try:
                    # Basic Modbus frame parsing
                    function_code = buffer[1] if len(buffer) > 1 else None
                    unit_id = buffer[0] if len(buffer) > 0 else None
                    data_payload = buffer[2:-2] if len(buffer) > 4 else b''
                    
                    parsed_data = {
                        'function_code': function_code,
                        'unit_id': unit_id,
                        'data': hexlify_packets(data_payload),
                        'crc': hexlify_packets(buffer[-2:])
                    }
                    
                    # Determine frame type based on function code
                    if function_code is not None:
                        if function_code & 0x80:  # Error response
                            frame_type = 'ModbusErrorResponse'
                            parsed_data['error_code'] = data_payload[0] if data_payload else None
                        else:
                            frame_type = 'ModbusRequest' if function_code < 0x80 else 'ModbusResponse'
                    else:
                        frame_type = 'Unknown'
                    
                    # Clear the processed bytes from buffer
                    self.frame_buffer[port_name] = self.frame_buffer[port_name][len(buffer):]
                    
                    return ProtocolFrame(
                        timestamp=datetime.now(),
                        protocol='Modbus RTU',
                        frame_type=frame_type,
                        data=buffer,
                        parsed_data=parsed_data,
                        errors=[]
                    )
                except ModbusException as e:
                    self.error_detected.emit(port_name, 'Modbus', str(e))

        except Exception as e:
            self.error_detected.emit(port_name, 'Modbus', f'Frame parsing error: {str(e)}')

        return None

    def _check_modbus_crc(self, data: bytes) -> bool:
        """Verify Modbus CRC."""
        if len(data) < 4:
            return False
        
        # Calculate CRC16
        crc = 0xFFFF
        for byte in data[:-2]:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1

        # Extract CRC from frame
        frame_crc = struct.unpack('<H', data[-2:])[0]
        
        return crc == frame_crc

    def _extract_serial_frame(self, port_name: str) -> Optional[ProtocolFrame]:
        """Try to extract an RS-232/485 frame from the buffer."""
        buffer = self.frame_buffer[port_name]
        if len(buffer) < 3:  # Minimum frame size (start + data + end)
            return None

        # Look for common frame patterns
        frame = None
        errors = []

        # Check for basic UART frame errors
        if port_name in self.last_byte:
            # Check for framing error (missing stop bit)
            if buffer[0] & 0x01:
                errors.append("Framing Error: Missing stop bit")
            
            # Check for break condition
            if buffer[0] == 0:
                errors.append("Break Condition Detected")

        # Try to detect standard serial frames
        try:
            # Look for start/end markers
            start_markers = [0x02, 0x01]  # STX, SOH
            end_markers = [0x03, 0x04]    # ETX, EOT

            for start in start_markers:
                try:
                    start_idx = buffer.index(start)
                    for end in end_markers:
                        try:
                            end_idx = buffer.index(end, start_idx + 1)
                            frame_data = bytes(buffer[start_idx:end_idx + 1])
                            
                            # Parse frame
                            parsed_data = {
                                'start_marker': hex(start),
                                'end_marker': hex(end),
                                'payload': hexlify_packets(frame_data[1:-1]),
                                'length': len(frame_data)
                            }

                            # Check parity if present
                            if len(frame_data) > 3:
                                parity = self._calculate_parity(frame_data[1:-2])
                                if frame_data[-2] != parity:
                                    errors.append("Parity Error")
                                parsed_data['parity'] = hex(parity)

                            # Clear processed bytes
                            self.frame_buffer[port_name] = buffer[end_idx + 1:]
                            
                            frame = ProtocolFrame(
                                timestamp=datetime.now(),
                                protocol='RS-232/485',
                                frame_type='Standard',
                                data=frame_data,
                                parsed_data=parsed_data,
                                errors=errors
                            )
                            break
                        except ValueError:
                            continue
                    if frame:
                        break
                except ValueError:
                    continue

        except Exception as e:
            self.error_detected.emit(port_name, 'Serial', f'Frame parsing error: {str(e)}')

        # Store last byte for next analysis
        if buffer:
            self.last_byte[port_name] = buffer[-1]

        return frame

    def _calculate_parity(self, data: bytes) -> int:
        """Calculate parity byte for serial data."""
        parity = 0
        for byte in data:
            parity ^= byte
        return parity

    def clear_buffer(self, port_name: str):
        """Clear the frame buffer for a port."""
        if port_name in self.frame_buffer:
            self.frame_buffer[port_name].clear()
        if port_name in self.last_byte:
            del self.last_byte[port_name] 