from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a basic pixmap if no splash image exists
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.GlobalColor.darkBlue)
        super().__init__(pixmap)
        
        # Create layout widget
        layout_widget = QWidget(self)
        layout = QVBoxLayout(layout_widget)
        
        # Add title
        title = QLabel("SynapseLink")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add loading text
        self.loading_label = QLabel("Loading...")
        self.loading_label.setStyleSheet("QLabel { color: white; }")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Position the layout widget
        layout_widget.setGeometry(10, 10, 380, 180)
        
        # Initialize progress
        self.progress = 0
        self.loading_steps = [
            "Initializing application...",
            "Loading configuration...",
            "Setting up managers...",
            "Preparing user interface...",
            "Starting application..."
        ]
        self.current_step = 0
        
        # Setup timer for progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100ms

    def update_progress(self):
        """Update the progress bar and loading text."""
        if self.progress < 100:
            self.progress += 2
            self.progress_bar.setValue(self.progress)
            
            # Update loading text at certain intervals
            step_size = 100 // len(self.loading_steps)
            current_step = self.progress // step_size
            if current_step < len(self.loading_steps) and current_step != self.current_step:
                self.current_step = current_step
                self.loading_label.setText(self.loading_steps[current_step])
        else:
            self.timer.stop() 