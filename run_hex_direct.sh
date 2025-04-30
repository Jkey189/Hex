#!/bin/bash
# Direct Hex Game Runner
# This script creates a simple wrapper that bypasses the setuptools issue

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "Starting Hex Game with setuptools bypass..."

# Create a temporary Python script that bypasses the setuptools in back.py
TEMP_SCRIPT="${SCRIPT_DIR}/tmp_runner.py"

cat > "${TEMP_SCRIPT}" << 'EOF'
#!/usr/bin/env python3
"""
Temporary runner for Hex Game that works around the setuptools issue
"""
import sys
import os
import importlib.util
import types

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Initializing Hex Game...")

# Create a mock setuptools module to prevent actual setup from running
class MockSetup:
    def __init__(self, *args, **kwargs):
        pass

class MockExtension:
    def __init__(self, *args, **kwargs):
        pass

class MockSetuptools:
    def setup(self, *args, **kwargs):
        return None
        
    def Extension(self, *args, **kwargs):
        return MockExtension()

# Create a mock pybind11 module
class MockPybind11:
    @staticmethod
    def get_include():
        return ""

# Create mocked modules
sys.modules['setuptools'] = MockSetuptools()
sys.modules['pybind11'] = MockPybind11()

# Import backend with setuptools mocked
from backend import back
from PyQt5.QtWidgets import QApplication
from frontend.front import HexWindow

# Start the application
app = QApplication([])
window = HexWindow()
window.show()
sys.exit(app.exec_())
EOF

# Make it executable
chmod +x "${TEMP_SCRIPT}"

# Run the script
python3 "${TEMP_SCRIPT}"

# Clean up
rm -f "${TEMP_SCRIPT}"