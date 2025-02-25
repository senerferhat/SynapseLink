from typing import List, Dict, Pattern, Optional
import re
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from collections import deque
import weakref
from .config import PERFORMANCE_CONFIG

class OptimizedDataBuffer:
    def __init__(self, max_size: int = PERFORMANCE_CONFIG['buffer_size']):
        self.max_size = max_size
        self._buffer: deque[tuple[datetime, bytes]] = deque(maxlen=max_size)
        self._total_size = 0
        self._chunk_size = PERFORMANCE_CONFIG['chunk_size']

    def append(self, timestamp: datetime, data: bytes):
        self._buffer.append((timestamp, data))
        self._total_size += len(data)
        
        while self._total_size > self._chunk_size:
            _, removed_data = self._buffer.popleft()
            self._total_size -= len(removed_data)

    def get_data(self, start_time: datetime = None, end_time: datetime = None) -> list:
        return [
            (ts, data) for ts, data in self._buffer
            if (not start_time or ts >= start_time) and
               (not end_time or ts <= end_time)
        ]

    def clear_old_data(self, before_time: datetime):
        while self._buffer and self._buffer[0][0] < before_time:
            _, removed_data = self._buffer.popleft()
            self._total_size -= len(removed_data)

class DataProcessor(QObject):
    """Handles data processing, filtering, and analysis."""
    
    # Signals
    pattern_matched = pyqtSignal(str, str, bytes)  # port_name, pattern_name, data
    data_filtered = pyqtSignal(str, bytes)  # port_name, filtered_data
    error_detected = pyqtSignal(str, str)  # port_name, error_message

    def __init__(self):
        super().__init__()
        self.buffers: Dict[str, OptimizedDataBuffer] = {}
        self.cache = weakref.WeakValueDictionary()
        self.patterns: Dict[str, Pattern] = {}
        self.filters: Dict[str, Pattern] = {}

    def add_pattern(self, name: str, pattern: str) -> bool:
        """Add a pattern to match in the incoming data."""
        try:
            self.patterns[name] = re.compile(pattern.encode())
            return True
        except re.error:
            return False

    def remove_pattern(self, name: str) -> bool:
        """Remove a pattern from matching."""
        if name in self.patterns:
            del self.patterns[name]
            return True
        return False

    def add_filter(self, name: str, pattern: str) -> bool:
        """Add a filter for the data stream."""
        try:
            self.filters[name] = re.compile(pattern.encode())
            return True
        except re.error:
            return False

    def remove_filter(self, name: str) -> bool:
        """Remove a filter from the data stream."""
        if name in self.filters:
            del self.filters[name]
            return True
        return False

    def process_data(self, port_name: str, data: bytes) -> bytes:
        if port_name not in self.buffers:
            self.buffers[port_name] = OptimizedDataBuffer()
        
        timestamp = datetime.now()
        self.buffers[port_name].append(timestamp, data)
        return self._process_with_cache(port_name, data)

    def _process_with_cache(self, port_name: str, data: bytes) -> bytes:
        cache_key = (port_name, hash(data))
        if cache_key in self.cache:
            return self.cache[cache_key]

        processed_data = self._process_chunk(port_name, data)
        self.cache[cache_key] = processed_data
        return processed_data

    def _process_chunk(self, port_name: str, data: bytes) -> bytes:
        # Check patterns
        for name, pattern in self.patterns.items():
            if pattern.search(data):
                self.pattern_matched.emit(port_name, name, data)

        # Apply filters
        filtered_data = data
        for name, filter_pattern in self.filters.items():
            filtered_data = filter_pattern.sub(b'', filtered_data)
        
        if filtered_data != data:
            self.data_filtered.emit(port_name, filtered_data)

        return filtered_data

    def search_data(self, port_name: str, pattern: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[tuple]:
        """Search for pattern in stored data within the specified time range."""
        if port_name not in self.buffers:
            return []

        try:
            search_pattern = re.compile(pattern.encode())
        except re.error:
            return []

        results = []
        for timestamp, data in self.buffers[port_name].get_data(start_time, end_time):
            if search_pattern.search(data):
                results.append((timestamp, data))

        return results

    def export_data(self, port_name: str, format: str, filename: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> bool:
        """Export data in specified format (CSV, JSON, or XML)."""
        if port_name not in self.buffers:
            return False

        data_to_export = [
            {
                'timestamp': timestamp.isoformat(),
                'data': data.hex(),
                'ascii': data.decode('ascii', errors='replace')
            }
            for timestamp, data in self.buffers[port_name].get_data(start_time, end_time)
        ]

        try:
            if format.lower() == 'csv':
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'data', 'ascii'])
                    writer.writeheader()
                    writer.writerows(data_to_export)

            elif format.lower() == 'json':
                with open(filename, 'w') as f:
                    json.dump(data_to_export, f, indent=2)

            elif format.lower() == 'xml':
                root = ET.Element('data')
                for entry in data_to_export:
                    packet = ET.SubElement(root, 'packet')
                    for key, value in entry.items():
                        elem = ET.SubElement(packet, key)
                        elem.text = str(value)
                tree = ET.ElementTree(root)
                tree.write(filename, encoding='utf-8', xml_declaration=True)

            else:
                return False

            return True

        except Exception:
            return False

    def get_statistics(self, port_name: str,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> Dict:
        """Calculate statistics for the data stream."""
        if port_name not in self.buffers:
            return {}

        data = [
            len(data)
            for timestamp, data in self.buffers[port_name].get_data(start_time, end_time)
        ]

        if not data:
            return {}

        return {
            'total_bytes': sum(data),
            'packet_count': len(data),
            'avg_packet_size': sum(data) / len(data),
            'min_packet_size': min(data),
            'max_packet_size': max(data),
            'std_dev_packet_size': np.std(data)
        }

    def clear_data(self, port_name: str = None):
        """Clear stored data for specified port or all ports."""
        if port_name:
            if port_name in self.buffers:
                self.buffers[port_name] = OptimizedDataBuffer()
        else:
            self.buffers.clear()

    def get_data_for_visualization(self, port_name: str,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None) -> pd.DataFrame:
        if port_name not in self.buffers:
            return pd.DataFrame()

        data = self.buffers[port_name].get_data(start_time, end_time)
        
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=['timestamp', 'data'])
        df['data_size'] = df['data'].apply(len)
        return df 