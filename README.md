# Hex Game

A Python implementation of the classic Hex board game with AI using alpha-beta pruning and a C++ backend for performance optimization.

![Hex Game](https://upload.wikimedia.org/wikipedia/commons/3/38/Hex-board-11x11-%282%29.jpg)

## About Hex

Hex is a strategy board game played on a hexagonal grid where:
- **Blue Player**: Aims to connect the top and bottom edges with a continuous chain of blue pieces
- **Red Player**: Aims to connect the left and right edges with a continuous chain of red pieces

The game always produces a winner - there are no draws in Hex!

## Features

- 📋 Multiple game modes: Player vs Player, Player vs AI, and AI vs AI
- 🤖 Three AI difficulty levels with alpha-beta pruning algorithm
- ⚡ C++ extension for enhanced AI performance
- 🔄 Move history navigation with undo/redo functionality
- ⚖️ Swap rule implementation to balance first-player advantage
- 🎮 Intuitive graphical interface built with PyQt5

## Requirements

- Python 3.6+
- PyQt5
- pybind11 (for the C++ component)

## Installation

```bash
# Install required dependencies
pip install PyQt5 pybind11

# Build the C++ extension (optional, for enhanced AI performance)
cd backend/alpha-beta\ pruning
python setup.py build_ext --inplace
cp *.so ../
```

## Running the Game

Due to setuptools conflicts in the Python environment, the game cannot be run directly with `python3 frontend/front.py`. Instead, use the following launcher:

```bash
./run_hex_direct.sh
```

This launcher creates a wrapper that bypasses the setuptools issue by temporarily mocking setuptools modules.

### The setuptools conflict issue

If you attempt to run the game directly, you may encounter this error:

```
usage: front.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
   or: front.py --help [cmd1 cmd2 ...]
   or: front.py --help-commands
   or: front.py cmd --help
error: no commands supplied
```

This happens because the Python environment has a deep integration with setuptools that's intercepting the script execution. The launcher script works around this issue.

## How to Play

1. **Start a game**: Launch the game using the run script and select your preferred game mode.
2. **Make a move**: Click on any empty hexagon on the board to place your piece.
3. **Swap rule**: In the second turn of the game, the Red player can optionally "swap" by clicking on Blue's first piece, effectively taking that position.
4. **Win the game**: Create a continuous path connecting your goal edges (top-bottom for Blue, left-right for Red).

### Game Controls

- **Game Mode**: Select between "Player vs Player", "Player vs AI", or "AI vs AI"
- **AI Difficulty**: Choose "Easy", "Medium", or "Difficult" when playing against or watching AI
- **New Game**: Reset the board and start a new game
- **Move Navigation**: Step backward and forward through the game's move history

## Project Structure

```
Hex/
├── frontend/          # UI code and visualization
│   └── front.py       # Main UI implementation with PyQt5
├── backend/           # Game logic and AI
│   ├── back.py        # Python implementation
│   └── alpha-beta pruning/  # C++ optimized algorithm
└── HexGameDocumentation.md  # Detailed documentation
```

## Technical Implementation

- **Game Logic**: Pure Python implementation of Hex rules and state management
- **AI**: Alpha-beta pruning algorithm with customizable search depth
- **UI**: PyQt5-based graphical interface with hexagonal grid rendering
- **Performance**: Optional C++ extension (built with pybind11) for faster AI calculations

## Further Documentation

For detailed information about the code architecture, algorithms, and development information, see the [HexGameDocumentation.md](HexGameDocumentation.md) file.

## License

This project is open-source software.
