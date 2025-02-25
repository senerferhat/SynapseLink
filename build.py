import PyInstaller.__main__
import os
import sys
from src.resources.compile_resources import compile_resources

def build():
    # First compile resources
    if not compile_resources():
        print("Failed to compile resources. Build aborted.")
        sys.exit(1)

    # Get the absolute path to the resources directory
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'resources')

    PyInstaller.__main__.run([
        'src/main.py',
        '--name=SynapseLink',
        '--windowed',
        '--onefile',
        f'--add-data=src/resources;src/resources',
        '--paths=src',
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=pymodbus',
        '--hidden-import=cryptography',
        '--hidden-import=qdarkstyle',
        '--hidden-import=src.ui.main_window',
        '--hidden-import=src.ui.connection_dialog',
        '--hidden-import=src.ui.connection_tab',
        '--hidden-import=src.ui.protocol_view',
        '--hidden-import=src.ui.auth_dialog',
        '--hidden-import=src.ui.security_dialog',
        '--hidden-import=src.ui.automation_view',
        '--hidden-import=src.ui.splash_screen',
        '--hidden-import=src.resources.resources_rc',
        '--collect-submodules=src',
        '--collect-data=src',
        f'--icon={os.path.join(resources_dir, "icon.ico")}',
        '--clean',
        '--noconfirm',
    ])

if __name__ == '__main__':
    build() 