from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QGroupBox, QTextEdit,
                               QListWidget, QDateTimeEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime
import re

class SearchFilterDialog(QDialog):
    def __init__(self, data_processor, port_name, parent=None):
        super().__init__(parent)
        self.data_processor = data_processor
        self.port_name = port_name
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setWindowTitle("Search and Filter")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)

        # Search group
        search_group = self.create_search_group()
        layout.addWidget(search_group)

        # Filter group
        filter_group = self.create_filter_group()
        layout.addWidget(filter_group)

        # Pattern group
        pattern_group = self.create_pattern_group()
        layout.addWidget(pattern_group)

        # Results
        results_group = self.create_results_group()
        layout.addWidget(results_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)

    def create_search_group(self):
        group = QGroupBox("Search")
        layout = QVBoxLayout()

        # Search pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern:"))
        self.search_pattern = QLineEdit()
        pattern_layout.addWidget(self.search_pattern)
        layout.addLayout(pattern_layout)

        # Time range
        time_layout = QHBoxLayout()
        
        time_layout.addWidget(QLabel("From:"))
        self.start_time = QDateTimeEdit(QDateTime.currentDateTime().addSecs(-3600))
        time_layout.addWidget(self.start_time)
        
        time_layout.addWidget(QLabel("To:"))
        self.end_time = QDateTimeEdit(QDateTime.currentDateTime())
        time_layout.addWidget(self.end_time)
        
        layout.addLayout(time_layout)

        # Search options
        options_layout = QHBoxLayout()
        
        self.case_sensitive = QCheckBox("Case Sensitive")
        options_layout.addWidget(self.case_sensitive)
        
        self.regex_search = QCheckBox("Use Regex")
        options_layout.addWidget(self.regex_search)
        
        layout.addLayout(options_layout)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        group.setLayout(layout)
        return group

    def create_filter_group(self):
        group = QGroupBox("Filters")
        layout = QVBoxLayout()

        # Filter list
        self.filter_list = QListWidget()
        layout.addWidget(self.filter_list)

        # Add filter controls
        filter_controls = QHBoxLayout()
        
        self.filter_pattern = QLineEdit()
        filter_controls.addWidget(self.filter_pattern)
        
        add_filter = QPushButton("Add Filter")
        add_filter.clicked.connect(self.add_filter)
        filter_controls.addWidget(add_filter)
        
        remove_filter = QPushButton("Remove Filter")
        remove_filter.clicked.connect(self.remove_filter)
        filter_controls.addWidget(remove_filter)
        
        layout.addLayout(filter_controls)

        group.setLayout(layout)
        return group

    def create_pattern_group(self):
        group = QGroupBox("Pattern Matching")
        layout = QVBoxLayout()

        # Pattern list
        self.pattern_list = QListWidget()
        layout.addWidget(self.pattern_list)

        # Add pattern controls
        pattern_controls = QHBoxLayout()
        
        self.pattern_name = QLineEdit()
        self.pattern_name.setPlaceholderText("Pattern Name")
        pattern_controls.addWidget(self.pattern_name)
        
        self.pattern_value = QLineEdit()
        self.pattern_value.setPlaceholderText("Pattern Value")
        pattern_controls.addWidget(self.pattern_value)
        
        add_pattern = QPushButton("Add Pattern")
        add_pattern.clicked.connect(self.add_pattern)
        pattern_controls.addWidget(add_pattern)
        
        remove_pattern = QPushButton("Remove Pattern")
        remove_pattern.clicked.connect(self.remove_pattern)
        pattern_controls.addWidget(remove_pattern)
        
        layout.addLayout(pattern_controls)

        group.setLayout(layout)
        return group

    def create_results_group(self):
        group = QGroupBox("Results")
        layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        self.data_processor.pattern_matched.connect(self.handle_pattern_match)
        self.data_processor.data_filtered.connect(self.handle_filtered_data)

    def perform_search(self):
        pattern = self.search_pattern.text()
        if not pattern:
            return

        if not self.regex_search.isChecked():
            pattern = re.escape(pattern)
        
        if not self.case_sensitive.isChecked():
            pattern = f"(?i){pattern}"

        results = self.data_processor.search_data(
            self.port_name,
            pattern,
            self.start_time.dateTime().toPyDateTime(),
            self.end_time.dateTime().toPyDateTime()
        )

        self.display_results(results)

    def display_results(self, results):
        self.results_text.clear()
        for timestamp, data in results:
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = data.hex()
            
            self.results_text.append(f"[{timestamp}] {text}")

    def add_filter(self):
        pattern = self.filter_pattern.text()
        if not pattern:
            return

        try:
            if self.data_processor.add_filter(pattern, pattern):
                self.filter_list.addItem(pattern)
                self.filter_pattern.clear()
        except re.error:
            QMessageBox.warning(self, "Invalid Filter", 
                              "The filter pattern is not a valid regular expression.")

    def remove_filter(self):
        current = self.filter_list.currentItem()
        if current:
            pattern = current.text()
            if self.data_processor.remove_filter(pattern):
                self.filter_list.takeItem(self.filter_list.row(current))

    def add_pattern(self):
        name = self.pattern_name.text()
        pattern = self.pattern_value.text()
        if not name or not pattern:
            return

        try:
            if self.data_processor.add_pattern(name, pattern):
                self.pattern_list.addItem(f"{name}: {pattern}")
                self.pattern_name.clear()
                self.pattern_value.clear()
        except re.error:
            QMessageBox.warning(self, "Invalid Pattern", 
                              "The pattern is not a valid regular expression.")

    def remove_pattern(self):
        current = self.pattern_list.currentItem()
        if current:
            name = current.text().split(':')[0]
            if self.data_processor.remove_pattern(name):
                self.pattern_list.takeItem(self.pattern_list.row(current))

    @pyqtSlot(str, str, bytes)
    def handle_pattern_match(self, port, pattern_name, data):
        if port != self.port_name:
            return
        
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = data.hex()
        
        self.results_text.append(
            f"Pattern '{pattern_name}' matched: {text}"
        )

    @pyqtSlot(str, bytes)
    def handle_filtered_data(self, port, data):
        if port != self.port_name:
            return
        
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = data.hex()
        
        self.results_text.append(f"Filtered data: {text}") 