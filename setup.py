from setuptools import setup, find_packages
import PyInstaller.__main__
import sys
import os

def build_exe():
    """Build executable using PyInstaller."""
    PyInstaller.__main__.run([
        'src/main.py',                      # Script to bundle
        '--name=SynapseLink',               # Name of the executable
        '--windowed',                       # GUI mode
        '--onefile',                        # Create a single executable
        '--icon=resources/icon.ico',        # Application icon
        '--add-data=resources;resources',   # Include resources
        '--hidden-import=PyQt6',
        '--hidden-import=pymodbus',
        '--hidden-import=cryptography',
        '--hidden-import=qdarkstyle',
        '--clean',                          # Clean cache
        '--noconfirm',                      # Replace existing spec/build
    ])

if __name__ == '__main__':
    # Setup the package
    setup(
        name="SynapseLink",
        version="1.0.0",
        packages=find_packages(),
        install_requires=[
            'PyQt6>=6.4.0',
            'pyserial>=3.5',
            'pymodbus>=3.8.6',
            'cryptography>=42.0.0',
            'qdarkstyle>=3.1',
            'PyInstaller>=6.3.0'
        ],
        python_requires='>=3.8',
        entry_points={
            'console_scripts': [
                'synapselink=src.main:main',
            ],
        },
        author="Your Name",
        description="Serial Port Communication and Protocol Analysis Tool",
        keywords="serial, communication, protocol, analysis",
        project_urls={
            "Source": "https://github.com/yourusername/SynapseLink",
        },
    )

    # Build executable if requested
    if len(sys.argv) > 1 and sys.argv[1] == 'build_exe':
        build_exe() 