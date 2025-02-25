# SynapseLink

A powerful cross-platform serial port monitoring and analysis application with advanced features for data visualization, protocol analysis, and automation.

## Features

- **Multi-Connection Support**
  - Monitor multiple serial ports simultaneously
  - Split-view capability for side-by-side port monitoring
  - Configurable connection parameters for each port

- **Advanced Data Analysis**
  - Real-time data visualization with multiple plot types
  - Protocol analysis with frame detection
  - Data filtering and pattern matching
  - Export data in various formats (CSV, JSON, XML)

- **Memory Management**
  - Optimized data buffering
  - Automatic memory cleanup
  - Data archiving for long-term storage

- **Security Features**
  - User authentication system
  - Port-specific encryption
  - Role-based access control
  - Secure session management

- **Automation Capabilities**
  - Macro recording and playback
  - Scripting support
  - Scheduled tasks
  - Custom automation workflows

- **User Interface**
  - Modern, intuitive interface
  - Dark/Light theme support
  - Customizable layouts
  - Dockable windows

## Installation

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SynapseLink.git
cd SynapseLink
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python src/main.py
```

### Building Executable

To create a standalone executable:
```bash
python build.py
```
The executable will be created in the `dist` directory.

## Development

### Project Structure
```
SynapseLink/
├── src/
│   ├── core/           # Core functionality
│   │   ├── serial_manager.py
│   │   ├── data_processor.py
│   │   ├── protocol_analyzer.py
│   │   ├── security_manager.py
│   │   ├── automation_manager.py
│   │   └── session_manager.py
│   ├── ui/            # User interface components
│   │   ├── main_window.py
│   │   ├── connection_tab.py
│   │   ├── visualization_widget.py
│   │   └── ...
│   └── main.py        # Application entry point
├── tests/             # Test files
├── docs/              # Documentation
├── requirements.txt   # Project dependencies
└── README.md         # This file
```

### Key Components

- **SerialManager**: Handles serial port connections and communications
- **DataProcessor**: Processes and analyzes incoming data
- **ProtocolAnalyzer**: Detects and analyzes communication protocols
- **SecurityManager**: Manages authentication and encryption
- **AutomationManager**: Handles macros, scripts, and scheduled tasks
- **SessionManager**: Manages application state and data persistence

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the GUI framework
- pyserial for serial communication
- QDarkStyle for theming
- All other contributors and package maintainers 