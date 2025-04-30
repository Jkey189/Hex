# Hex Game

A Python implementation of the Hex board game with AI using alpha-beta pruning and a C++ backend for performance.

## Running the Game

Due to a known issue with setuptools conflicts when running `front.py` directly, use one of the following methods to launch the game:

### Method 1: Run a Python command directly

```bash
cd "/Users/olegrodin/Visual Studio Code Projects/School/Hex"
PYTHONPATH=$PWD python3 -c "from PyQt5.QtWidgets import QApplication; from frontend.front import HexWindow; app = QApplication([]); window = HexWindow(); window.show(); app.exec_()"
```

### Method 2: Use the frontend module

```bash
cd "/Users/olegrodin/Visual Studio Code Projects/School/Hex/frontend"
PYTHONPATH=.. python3 -c "from front import QApplication, HexWindow; app = QApplication([]); window = HexWindow(); window.show(); app.exec_()"
```

## C++ Extension

The game uses a C++ extension compiled with pybind11 for the alpha-beta pruning algorithm. The extension has been successfully compiled for macOS with Apple Silicon (arm64) architecture.
