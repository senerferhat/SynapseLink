import os
import subprocess
from pathlib import Path

def compile_resources():
    """Compile Qt resources into a Python module."""
    current_dir = Path(__file__).parent
    rcc_file = current_dir / 'resources.qrc'
    py_file = current_dir / 'resources_rc.py'
    
    try:
        # Try using PyQt6's rcc tool
        subprocess.run(['pyside6-rcc', '-o', str(py_file), str(rcc_file)], check=True)
        print(f"Successfully compiled resources to {py_file}")
        
        # Update imports to work with PyQt6
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('PySide6', 'PyQt6')
        
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Updated imports for PyQt6 compatibility")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Failed to compile resources. Make sure PyQt6 is installed.")
        return False
    
    return True

if __name__ == '__main__':
    compile_resources() 