from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QLabel, QGroupBox,
                               QProgressBar)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QThreadPool, QRunnable, QObject
import pyqtgraph as pg
import numpy as np
from datetime import datetime, timedelta
from typing import Generator, Optional
import traceback
from ..core.config import PERFORMANCE_CONFIG

class ChunkedDataHandler:
    def __init__(self, chunk_size: int = PERFORMANCE_CONFIG['chunk_size']):
        self.chunk_size = chunk_size
        self.current_chunk = []
        self.chunk_count = 0

    def process_large_dataset(self, data_generator: Generator[bytes, None, None]):
        current_size = 0
        
        for data_chunk in data_generator:
            current_size += len(data_chunk)
            self.current_chunk.append(data_chunk)

            if current_size >= self.chunk_size:
                yield self._process_chunk(b''.join(self.current_chunk))
                self.current_chunk = []
                current_size = 0

        if self.current_chunk:
            yield self._process_chunk(b''.join(self.current_chunk))

    def _process_chunk(self, chunk: bytes) -> np.ndarray:
        return np.frombuffer(chunk, dtype=np.uint8)

class DataProcessWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit((e, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class VisualizationWidget(QWidget):
    # Signals
    update_requested = pyqtSignal()  # Signal to request data update

    def __init__(self, data_processor, parent=None):
        super().__init__(parent)
        self.data_processor = data_processor
        self.chunked_handler = ChunkedDataHandler()
        self.plot_decimation = PERFORMANCE_CONFIG['plot_decimation']
        self.threadpool = QThreadPool()
        self.setup_ui()
        self.setup_plot()
        self.current_port = None
        self.update_timer = pg.QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(1000)  # Update every second

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('default')
        self.plot_widget.setLabel('left', 'Bytes')
        self.plot_widget.setLabel('bottom', 'Time')
        layout.addWidget(self.plot_widget)

    def create_control_panel(self):
        control_group = QGroupBox("Visualization Controls")
        control_layout = QHBoxLayout()

        # Time range selection
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time Range:"))
        self.time_range = QComboBox()
        self.time_range.addItems(['1 minute', '5 minutes', '15 minutes', '1 hour', 'All'])
        self.time_range.currentTextChanged.connect(self.update_plot)
        time_layout.addWidget(self.time_range)
        control_layout.addLayout(time_layout)

        # Plot type selection
        plot_type_layout = QHBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type = QComboBox()
        self.plot_type.addItems(['Line', 'Scatter', 'Bar'])
        self.plot_type.currentTextChanged.connect(self.update_plot_type)
        plot_type_layout.addWidget(self.plot_type)
        control_layout.addLayout(plot_type_layout)

        # Data type selection
        data_type_layout = QHBoxLayout()
        data_type_layout.addWidget(QLabel("Data Type:"))
        self.data_type = QComboBox()
        self.data_type.addItems(['Packet Size', 'Packet Rate', 'Cumulative'])
        self.data_type.currentTextChanged.connect(self.update_plot)
        data_type_layout.addWidget(self.data_type)
        control_layout.addLayout(data_type_layout)

        control_group.setLayout(control_layout)
        return control_group

    def setup_plot(self):
        self.plot = self.plot_widget.plot([], [], pen=pg.mkPen('b', width=2))
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.enableAutoRange()

    def set_port(self, port_name: str):
        """Set the port to visualize data from."""
        self.current_port = port_name
        self.update_plot()

    def get_time_range(self):
        """Get the start time based on selected range."""
        range_text = self.time_range.currentText()
        now = datetime.now()
        
        if range_text == '1 minute':
            return now - timedelta(minutes=1)
        elif range_text == '5 minutes':
            return now - timedelta(minutes=5)
        elif range_text == '15 minutes':
            return now - timedelta(minutes=15)
        elif range_text == '1 hour':
            return now - timedelta(hours=1)
        else:
            return None

    def update_plot(self):
        if not self.current_port:
            return

        # Create worker for background processing
        worker = DataProcessWorker(self._process_plot_data)
        worker.signals.result.connect(self._update_plot_data)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.finished.connect(self._processing_finished)

        self.progress_bar.show()
        self.threadpool.start(worker)

    def _process_plot_data(self):
        df = self._get_decimated_data()
        if df.empty:
            return None

        timestamps = df['timestamp'].values
        data_type = self.data_type.currentText()
        
        if data_type == 'Packet Size':
            y_data = df['data_size'].values
        elif data_type == 'Packet Rate':
            # Calculate packets per second using numpy
            time_diff = np.diff(timestamps.astype(np.float64))
            y_data = 1.0 / time_diff
            timestamps = timestamps[1:]
        else:  # Cumulative
            y_data = np.cumsum(df['data_size'].values)

        return timestamps, y_data

    def _get_decimated_data(self):
        data = self.data_processor.get_data_for_visualization(
            self.current_port,
            start_time=self.get_time_range()
        )
        
        if len(data) > self.plot_decimation:
            # Use efficient decimation with numpy
            indices = np.linspace(0, len(data)-1, self.plot_decimation, dtype=int)
            return data.iloc[indices]
        return data

    @pyqtSlot(object)
    def _update_plot_data(self, result):
        if not result:
            return

        timestamps, y_data = result
        plot_type = self.plot_type.currentText()

        self.plot_widget.clear()
        if plot_type == 'Line':
            self.plot = self.plot_widget.plot(timestamps, y_data, pen=pg.mkPen('b', width=2))
        elif plot_type == 'Scatter':
            self.plot = self.plot_widget.plot(timestamps, y_data, pen=None, symbol='o', symbolSize=5)
        else:  # Bar
            self.plot = self.plot_widget.plot(timestamps, y_data, stepMode="center", fillLevel=0, brush=(0,0,255,150))

    @pyqtSlot(int)
    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot()
    def _processing_finished(self):
        self.progress_bar.hide()

    def update_plot_type(self):
        plot_type = self.plot_type.currentText()
        
        self.plot_widget.clear()
        if plot_type == 'Line':
            self.plot = self.plot_widget.plot([], [], pen=pg.mkPen('b', width=2))
        elif plot_type == 'Scatter':
            self.plot = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5)
        else:  # Bar
            self.plot = self.plot_widget.plot([], [], stepMode="center", fillLevel=0, brush=(0,0,255,150))

        self.update_plot() 

    def update_display(self):
        """Update the visualization display."""
        self.update_plot()

    def clear(self):
        """Clear the plot data."""
        self.plot.setData([], [])

    def __del__(self):
        """Cleanup when widget is destroyed."""
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None 