from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QPushButton, QTextEdit, QLabel, QLineEdit,
                               QFileDialog, QMessageBox, QGroupBox, QListWidget,
                               QSpinBox, QComboBox, QFormLayout, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
import json
from datetime import datetime

class ScriptEditor(QWidget):
    """Script editor widget with Python syntax highlighting."""
    
    def __init__(self, automation_manager, parent=None):
        super().__init__(parent)
        self.automation_manager = automation_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Editor controls
        controls_layout = QHBoxLayout()
        
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Script Name")
        controls_layout.addWidget(self.script_name)
        
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_script)
        controls_layout.addWidget(load_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_script)
        controls_layout.addWidget(save_button)
        
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_script)
        controls_layout.addWidget(run_button)
        
        layout.addLayout(controls_layout)

        # Script editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Enter your Python script here...")
        layout.addWidget(self.editor)

        # Output view
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        clear_button = QPushButton("Clear Output")
        clear_button.clicked.connect(self.output_text.clear)
        output_layout.addWidget(clear_button)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Connect signals
        self.automation_manager.script_output.connect(self.on_script_output)
        self.automation_manager.automation_error.connect(self.on_automation_error)

    def load_script(self):
        """Load a script from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Script", "", "Python Files (*.py)"
        )
        if filename:
            script = self.automation_manager.script_engine.load_script(filename)
            if script is not None:
                self.editor.setPlainText(script)
                self.script_name.setText(filename)
            else:
                QMessageBox.warning(self, "Error", "Failed to load script.")

    def save_script(self):
        """Save the current script to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Script", "", "Python Files (*.py)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.editor.toPlainText())
                self.script_name.setText(filename)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save script: {str(e)}")

    def run_script(self):
        """Run the current script."""
        script = self.editor.toPlainText()
        if not script:
            return

        # Prepare API for the script
        api = {
            'datetime': datetime,
            'json': json,
            # Add more API functions as needed
        }

        script_id = self.script_name.text() or "unnamed_script"
        self.automation_manager.run_script(script_id, script, api)

    def on_script_output(self, script_id: str, output: str):
        """Handle script output."""
        self.output_text.append(f"[{script_id}] {output}")

    def on_automation_error(self, error: str):
        """Handle automation errors."""
        self.output_text.append(f"Error: {error}")

class MacroRecorder(QWidget):
    """Macro recording and playback interface."""
    
    def __init__(self, automation_manager, parent=None):
        super().__init__(parent)
        self.automation_manager = automation_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Controls
        controls_layout = QHBoxLayout()
        
        self.macro_name = QLineEdit()
        self.macro_name.setPlaceholderText("Macro Name")
        controls_layout.addWidget(self.macro_name)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.setCheckable(True)
        self.record_button.toggled.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_button)
        
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_macro)
        controls_layout.addWidget(load_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_macro)
        controls_layout.addWidget(save_button)
        
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_macro)
        controls_layout.addWidget(play_button)
        
        layout.addLayout(controls_layout)

        # Recorded actions list
        self.action_list = QListWidget()
        layout.addWidget(self.action_list)

        # Scheduling
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QFormLayout()
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(60)
        schedule_layout.addRow("Interval (seconds):", self.interval_spin)
        
        schedule_button = QPushButton("Schedule")
        schedule_button.clicked.connect(self.schedule_macro)
        schedule_layout.addRow("", schedule_button)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        # Connect signals
        self.automation_manager.macro_started.connect(self.on_macro_started)
        self.automation_manager.macro_finished.connect(self.on_macro_finished)
        self.automation_manager.automation_error.connect(self.on_automation_error)

    def toggle_recording(self, checked: bool):
        """Start or stop macro recording."""
        if checked:
            self.automation_manager.start_macro_recording()
            self.record_button.setText("Stop Recording")
        else:
            self.automation_manager.stop_macro_recording()
            self.record_button.setText("Start Recording")
            self.refresh_action_list()

    def refresh_action_list(self):
        """Refresh the list of recorded actions."""
        self.action_list.clear()
        for action in self.automation_manager.macro_recorder.actions:
            self.action_list.addItem(
                f"{action['type']} - Delay: {action['delay']:.2f}s"
            )

    def load_macro(self):
        """Load a macro from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Macro", "", "Macro Files (*.json)"
        )
        if filename:
            if self.automation_manager.load_macro(filename):
                self.macro_name.setText(filename)
                self.refresh_action_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to load macro.")

    def save_macro(self):
        """Save the current macro to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Macro", "", "Macro Files (*.json)"
        )
        if filename:
            if self.automation_manager.save_macro(filename):
                self.macro_name.setText(filename)
            else:
                QMessageBox.warning(self, "Error", "Failed to save macro.")

    def play_macro(self):
        """Play the current macro."""
        name = self.macro_name.text() or "unnamed_macro"
        self.automation_manager.play_macro(name, self.handle_action)

    def schedule_macro(self):
        """Schedule the current macro for repeated execution."""
        name = self.macro_name.text() or "unnamed_macro"
        interval = self.interval_spin.value()

        task_id = f"macro_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        schedule = {'interval': interval}
        action = {
            'type': 'macro',
            'name': name,
            'handler': self.handle_action
        }

        if self.automation_manager.schedule_task(task_id, schedule, action):
            QMessageBox.information(self, "Success",
                                  f"Macro scheduled to run every {interval} seconds.")
        else:
            QMessageBox.warning(self, "Error", "Failed to schedule macro.")

    def handle_action(self, action_type: str, params: dict):
        """Handle macro action execution."""
        # Implement action handling based on your application's needs
        pass

    def on_macro_started(self, name: str):
        """Handle macro start event."""
        self.action_list.addItem(f"Started macro: {name}")

    def on_macro_finished(self, name: str):
        """Handle macro finish event."""
        self.action_list.addItem(f"Finished macro: {name}")

    def on_automation_error(self, error: str):
        """Handle automation errors."""
        self.action_list.addItem(f"Error: {error}")

class AutomationView(QWidget):
    """Main automation interface combining script editor and macro recorder."""
    
    def __init__(self, automation_manager, parent=None):
        super().__init__(parent)
        self.automation_manager = automation_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()
        
        # Add script editor
        script_editor = ScriptEditor(self.automation_manager)
        tab_widget.addTab(script_editor, "Script Editor")
        
        # Add macro recorder
        macro_recorder = MacroRecorder(self.automation_manager)
        tab_widget.addTab(macro_recorder, "Macro Recorder")
        
        layout.addWidget(tab_widget) 