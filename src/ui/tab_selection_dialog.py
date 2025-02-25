from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton,
                               QLabel, QHBoxLayout, QListWidgetItem)
from PyQt6.QtCore import Qt

class TabSelectionDialog(QDialog):
    def __init__(self, tabs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tabs for Split View")
        self.selected_indices = []
        self.setup_ui(tabs)

    def setup_ui(self, tabs):
        layout = QVBoxLayout(self)

        # Add instruction label
        label = QLabel("Select tabs to move to the right side:")
        layout.addWidget(label)

        # Create list widget for tab selection
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Add tabs to list
        for i in range(tabs.count()):
            item = QListWidgetItem(tabs.tabText(i))
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # Add buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

    def get_selected_indices(self):
        return [self.list_widget.row(item) for item in self.list_widget.selectedItems()] 