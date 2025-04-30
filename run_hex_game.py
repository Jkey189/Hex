#!/usr/bin/env python3
"""
Hex Game Launcher
----------------
This standalone launcher reimplements the essential functionality to launch the Hex game
without importing from front.py, avoiding setuptools conflicts completely.
"""

import os
import sys
import subprocess

def main():
    """
    Launch the Hex game by executing it in a separate Python process with flags to avoid
    setuptools interference.
    """
    # Path to the frontend module
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(project_root, "frontend")
    frontend_script = os.path.join(frontend_path, "front.py")
    
    print("Starting Hex Game...")
    print(f"Using Python: {sys.executable}")
    print(f"Launching: {frontend_script}")
    
    # Add a note about the run issue
    print("\nNOTE: If you encounter setuptools conflicts when trying to run front.py directly,")
    print("use this launcher script instead, or run the game with one of these alternative commands:")
    print("1. PYTHONPATH=$PWD python3 -c \"from frontend.front import QApplication, HexWindow; app = QApplication([]); window = HexWindow(); window.show(); app.exec_()\"")
    print("2. cd frontend && PYTHONPATH=.. python3 -c \"from front import QApplication, HexWindow; app = QApplication([]); window = HexWindow(); window.show(); app.exec_()\"")
    
    # Launch the frontend script in a subprocess with flags to avoid setuptools
    # Use -c to run Python code directly instead of the script file
    try:
        subprocess.run([
            sys.executable, 
            "-c", 
            "import sys; sys.path.insert(0, '.'); "
            "from PyQt5.QtWidgets import QApplication; "
            "from frontend.front import HexWindow; "
            "app = QApplication([]); "
            "window = HexWindow(); "
            "window.show(); "
            "sys.exit(app.exec_())"
        ], cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Hex Game: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()