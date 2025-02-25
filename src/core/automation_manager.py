from typing import Dict, List, Optional, Any, Callable
import os
import json
import time
from datetime import datetime
import threading
import queue
import importlib.util
from PyQt6.QtCore import QObject, pyqtSignal

class MacroRecorder:
    """Records and plays back user actions."""
    
    def __init__(self):
        self.actions: List[Dict] = []
        self.recording = False
        self.current_timestamp = None

    def start_recording(self):
        """Start recording user actions."""
        self.actions.clear()
        self.recording = True
        self.current_timestamp = time.time()

    def stop_recording(self):
        """Stop recording user actions."""
        self.recording = False
        self.current_timestamp = None

    def record_action(self, action_type: str, params: Dict):
        """Record a user action."""
        if not self.recording:
            return

        self.actions.append({
            'type': action_type,
            'params': params,
            'delay': time.time() - self.current_timestamp
        })
        self.current_timestamp = time.time()

    def save_macro(self, filename: str) -> bool:
        """Save recorded macro to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.actions, f, indent=2)
            return True
        except Exception:
            return False

    def load_macro(self, filename: str) -> bool:
        """Load macro from file."""
        try:
            with open(filename, 'r') as f:
                self.actions = json.load(f)
            return True
        except Exception:
            return False

class ScriptEngine:
    """Handles Python script execution."""
    
    def __init__(self):
        self.globals = {}
        self.locals = {}
        self.running_scripts: Dict[str, threading.Thread] = {}
        self.script_output: Dict[str, queue.Queue] = {}

    def load_script(self, filename: str) -> Optional[str]:
        """Load a Python script from file."""
        try:
            with open(filename, 'r') as f:
                return f.read()
        except Exception:
            return None

    def run_script(self, script_id: str, code: str, api: Dict[str, Any]) -> bool:
        """Run a Python script with the provided API."""
        try:
            # Create output queue
            self.script_output[script_id] = queue.Queue()
            
            # Prepare globals
            self.globals.update(api)
            self.globals['print'] = lambda *args: self.script_output[script_id].put(
                ' '.join(str(arg) for arg in args)
            )

            # Create and start script thread
            thread = threading.Thread(
                target=self._run_script_thread,
                args=(script_id, code),
                daemon=True
            )
            self.running_scripts[script_id] = thread
            thread.start()
            return True

        except Exception:
            return False

    def _run_script_thread(self, script_id: str, code: str):
        """Execute script in a separate thread."""
        try:
            exec(code, self.globals, self.locals)
        except Exception as e:
            self.script_output[script_id].put(f"Error: {str(e)}")
        finally:
            if script_id in self.running_scripts:
                del self.running_scripts[script_id]

    def stop_script(self, script_id: str):
        """Stop a running script."""
        if script_id in self.running_scripts:
            # Can't actually stop the thread, but can remove it from running scripts
            del self.running_scripts[script_id]

    def get_output(self, script_id: str) -> List[str]:
        """Get script output."""
        if script_id not in self.script_output:
            return []

        output = []
        while not self.script_output[script_id].empty():
            output.append(self.script_output[script_id].get())
        return output

class AutomationManager(QObject):
    """Manages automation features including macros and scripting."""
    
    # Signals
    macro_started = pyqtSignal(str)  # macro_name
    macro_finished = pyqtSignal(str)  # macro_name
    script_output = pyqtSignal(str, str)  # script_id, output
    automation_error = pyqtSignal(str)  # error_message

    def __init__(self):
        super().__init__()
        self.macro_recorder = MacroRecorder()
        self.script_engine = ScriptEngine()
        self.scheduled_tasks: Dict[str, Dict] = {}
        self.task_timer = None
        self.running = True
        self.start_timer()

    def start_timer(self):
        """Start the task checking timer."""
        self.task_timer = threading.Timer(1.0, self._check_scheduled_tasks)
        self.task_timer.daemon = True  # Make it a daemon thread
        self.task_timer.start()

    def stop_timer(self):
        """Stop the task checking timer."""
        self.running = False
        if self.task_timer:
            self.task_timer.cancel()
            self.task_timer = None

    def start_macro_recording(self):
        """Start recording a new macro."""
        self.macro_recorder.start_recording()

    def stop_macro_recording(self):
        """Stop recording the current macro."""
        self.macro_recorder.stop_recording()

    def save_macro(self, filename: str) -> bool:
        """Save the recorded macro to a file."""
        return self.macro_recorder.save_macro(filename)

    def load_macro(self, filename: str) -> bool:
        """Load a macro from a file."""
        return self.macro_recorder.load_macro(filename)

    def play_macro(self, name: str, action_handler: Callable[[str, Dict], None]):
        """Play back a recorded macro."""
        self.macro_started.emit(name)
        
        try:
            for action in self.macro_recorder.actions:
                # Wait for the specified delay
                time.sleep(action['delay'])
                
                # Execute the action
                action_handler(action['type'], action['params'])
            
            self.macro_finished.emit(name)
            return True

        except Exception as e:
            self.automation_error.emit(f"Error playing macro: {str(e)}")
            return False

    def run_script(self, script_id: str, code: str, api: Dict[str, Any]) -> bool:
        """Run a Python script."""
        success = self.script_engine.run_script(script_id, code, api)
        if not success:
            self.automation_error.emit(f"Failed to run script {script_id}")
        return success

    def stop_script(self, script_id: str):
        """Stop a running script."""
        self.script_engine.stop_script(script_id)

    def schedule_task(self, task_id: str, schedule: Dict, action: Dict) -> bool:
        """Schedule a task for execution."""
        try:
            self.scheduled_tasks[task_id] = {
                'schedule': schedule,
                'action': action,
                'last_run': None
            }
            return True
        except Exception as e:
            self.automation_error.emit(f"Error scheduling task: {str(e)}")
            return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return True
        return False

    def _check_scheduled_tasks(self):
        """Check and execute scheduled tasks."""
        try:
            if not self.running:
                return

            now = datetime.now()
            for task_id, task in self.scheduled_tasks.items():
                schedule = task['schedule']
                last_run = task['last_run']

                # Check if task should run
                should_run = False
                if not last_run:
                    should_run = True
                elif 'interval' in schedule:
                    # Time-based scheduling
                    interval = schedule['interval']
                    if (now - last_run).total_seconds() >= interval:
                        should_run = True
                elif 'cron' in schedule:
                    # TODO: Implement cron-style scheduling
                    pass

                if should_run:
                    # Execute task
                    action = task['action']
                    if action['type'] == 'macro':
                        self.play_macro(action['name'], action['handler'])
                    elif action['type'] == 'script':
                        self.run_script(action['script_id'], action['code'], action['api'])
                    
                    task['last_run'] = now

        except Exception as e:
            self.automation_error.emit(f"Error in task scheduler: {str(e)}")
        finally:
            # Only reschedule if still running
            if self.running:
                self.start_timer()

    def __del__(self):
        """Clean up resources."""
        self.stop_timer() 