from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
                               QTreeWidgetItem, QLabel, QPushButton, QGroupBox,
                               QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, pyqtSlot
from datetime import datetime
from core.protocol_analyzer import ProtocolFrame

class ProtocolView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Frame list group
        frame_group = QGroupBox("Protocol Frames")
        frame_layout = QVBoxLayout()

        # Create tree widget for frames
        self.frame_tree = QTreeWidget()
        self.frame_tree.setHeaderLabels([
            "Timestamp", "Protocol", "Type", "Length", "Status"
        ])
        self.frame_tree.currentItemChanged.connect(self.on_frame_selected)
        frame_layout.addWidget(self.frame_tree)

        frame_group.setLayout(frame_layout)
        splitter.addWidget(frame_group)

        # Details group
        details_group = QGroupBox("Frame Details")
        details_layout = QVBoxLayout()

        # Create text edit for frame details
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)

        # Error log group
        error_group = QGroupBox("Error Log")
        error_layout = QVBoxLayout()

        # Create text edit for error log
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        error_layout.addWidget(self.error_log)

        # Clear button
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_error_log)
        error_layout.addWidget(clear_button)

        error_group.setLayout(error_layout)
        splitter.addWidget(error_group)

        # Set splitter sizes
        splitter.setSizes([200, 150, 100])

    def add_frame(self, frame: ProtocolFrame):
        """Add a protocol frame to the tree widget."""
        item = QTreeWidgetItem(self.frame_tree)
        item.setText(0, frame.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        item.setText(1, frame.protocol)
        item.setText(2, frame.frame_type)
        item.setText(3, str(len(frame.data)))
        item.setText(4, "Error" if frame.errors else "OK")
        
        # Store frame data for details view
        item.setData(0, Qt.ItemDataRole.UserRole, frame)
        
        # Auto-scroll to new item
        self.frame_tree.scrollToItem(item)

    def add_error(self, error_type: str, description: str):
        """Add an error to the error log."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.error_log.append(f"[{timestamp}] {error_type}: {description}")

    def clear_error_log(self):
        """Clear the error log."""
        self.error_log.clear()

    def on_frame_selected(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Display details of the selected frame."""
        if not current:
            self.details_text.clear()
            return

        frame: ProtocolFrame = current.data(0, Qt.ItemDataRole.UserRole)
        if not frame:
            return

        # Format frame details
        details = []
        details.append(f"Timestamp: {frame.timestamp}")
        details.append(f"Protocol: {frame.protocol}")
        details.append(f"Frame Type: {frame.frame_type}")
        details.append(f"Data Length: {len(frame.data)} bytes")
        details.append(f"\nRaw Data (Hex):\n{frame.data.hex(' ')}")
        
        if frame.parsed_data:
            details.append("\nParsed Data:")
            for key, value in frame.parsed_data.items():
                details.append(f"{key}: {value}")
        
        if frame.errors:
            details.append("\nErrors:")
            for error in frame.errors:
                details.append(f"- {error}")

        self.details_text.setPlainText('\n'.join(details)) 