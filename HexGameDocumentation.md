# Hex Game - User and Developer Documentation

## Table of Contents
1. [How to Play](#how-to-play)
   - [Game Rules](#game-rules)
   - [Installation](#installation)
   - [Game Interface](#game-interface)
   - [Playing Modes](#playing-modes)
   - [Special Rules](#special-rules)
2. [Codebase Documentation](#codebase-documentation)
   - [Project Structure](#project-structure)
   - [Game Logic](#game-logic)
   - [AI Implementation](#ai-implementation)
   - [UI Components](#ui-components)
   - [Building the C++ Component](#building-the-c-component)
   - [Key Algorithms](#key-algorithms)

## How to Play

### Game Rules

Hex is a classic strategy board game played on a hexagonal grid. The goal is different for each player:

- **Blue Player**: Connect the top and bottom edges of the board with a continuous chain of blue pieces.
- **Red Player**: Connect the left and right edges of the board with a continuous chain of red pieces.

The game is turn-based, with each player placing one piece of their color on any empty cell during their turn. The first player to complete their connection wins. The game is always decisive - there are no draws in Hex!

### Installation

To run the Hex game, you'll need Python 3.6+ with the following dependencies:
- PyQt5
- pybind11 (for the C++ AI component)

1. Clone or download the repository
2. Install the required dependencies:
   ```
   pip install PyQt5 pybind11
   ```
3. Build the C++ module (optional, for enhanced AI performance):
   ```
   cd backend/alpha-beta\ pruning
   python setup.py build_ext --inplace
   cp *.so ../ 
   ```
4. Run the game:
   ```
   python frontend/front.py
   ```

### Game Interface

The game interface consists of three main sections:

- **Game Board (Left)**: The hexagonal grid where you play. Blue borders are at the top and bottom, red borders are on the left and right.
- **Control Panel (Bottom-Left)**: Contains game controls including:
  - Game mode toggle (1 vs 1 or Player vs AI)
  - AI difficulty setting (when playing against AI)
  - Swap button (for the second player after the first move)
  - New Game button
- **Moves History (Right)**: Shows a chronological list of all moves played, with navigation buttons to review previous positions.

### Playing Modes

The game offers two playing modes:

1. **Two Player Mode**: Play against another human player on the same computer.
2. **Play vs AI Mode**: Play against the computer AI, which uses alpha-beta pruning algorithm to find optimal moves.

To switch between modes, click the "Play vs AI" / "Play 1 vs 1" button.

When playing against the AI, you can adjust the difficulty level (1-4):
- Level 1: Easiest - AI searches only 1 move ahead
- Level 2: Easy - Searches 2 moves ahead
- Level 3: Medium - Searches 3 moves ahead (default)
- Level 4: Hard - Searches 4 moves ahead

### Special Rules

Hex implements the **pie rule** (also known as the swap rule) to balance the first-player advantage:
1. The first player makes their move
2. The second player can either:
   - Make their own move as usual, or
   - Choose to "swap" and take over the first player's position and color

This option appears as the "Swap First Move" button for the second player after the first move has been made.

## Codebase Documentation

### Project Structure

The project is organized into two main directories:

- **frontend/**: Contains the UI code and game visualization
  - `front.py`: Main game interface implemented using PyQt5
  
- **backend/**: Contains the game logic and AI algorithms
  - `back.py`: Python implementation of the game logic and AI
  - `alpha-beta pruning/`: C++ implementation of the AI algorithm for better performance
    - `alpha-beta-pruning.cpp`: C++ source code with alpha-beta pruning algorithm
    - `setup.py`: Build script for the C++ extension

### Game Logic

The core game logic is implemented in the `HexGame` class in `front.py`. This class handles:

- Board state management
- Move validation and execution
- Win condition checking
- Swap rule implementation
- Game history tracking

The backend implementation provides AI functionality and win checking, with two interchangeable versions:
- Pure Python implementation in `back.py`
- C++ implementation in `alpha-beta-pruning.cpp` (used when available for better performance)

### AI Implementation

The AI uses the alpha-beta pruning algorithm, an enhancement of the minimax algorithm that reduces the number of nodes evaluated in the search tree. Key AI components include:

- **Iterative Deepening**: Searches deeper levels incrementally for better time management
- **Transposition Table**: Caches previously evaluated positions to avoid redundant calculations
- **Move Ordering**: Examines more promising moves first to improve pruning efficiency
- **Position Evaluation**: Uses multiple heuristics to evaluate non-terminal board positions:
  - Connectivity: Rewards connected pieces
  - Edge Control: Values pieces on the goal edges
  - Shortest Path: Considers the minimal number of moves needed to connect sides

The C++ implementation provides significant performance improvements over the Python version, especially at higher difficulty levels.

### UI Components

The user interface is built with PyQt5 and consists of:

- **HexBoard**: Widget that renders the hexagonal game board and handles player input
- **HexWindow**: Main window that manages game controls and displays game information

The UI allows for:
- Playing moves by clicking on hexagons
- Visualizing the game state with colored pieces
- Tracking move history
- Navigating through previous moves
- Switching game modes
- Adjusting AI difficulty

### Building the C++ Component

The C++ component uses pybind11 to create Python bindings for the alpha-beta pruning algorithm. To build:

1. Navigate to the `backend/alpha-beta pruning` directory
2. Run `python setup.py build_ext --inplace`
3. Copy the generated `.so` file to the `backend` directory

The setup script configures the compiler to use C++11 with optimization flag `-O3` for maximum performance.

### Key Algorithms

1. **Hex Connection Detection** (Union-Find algorithm)
   - Used to efficiently detect winning connections
   - Each player's pieces are grouped into connected components
   - If a component connects both target edges, that player wins

2. **Alpha-Beta Pruning**
   - Recursively searches the game tree to find optimal moves
   - Uses pruning to skip evaluation of moves that won't affect the final decision
   - Enhanced with transposition table and move ordering optimizations

3. **Position Evaluation**
   - Evaluates non-terminal positions using multiple heuristics
   - Connectivity: Rewards larger connected groups of pieces
   - Path Analysis: Calculates the shortest path between edges
   - Edge Control: Values pieces placed on goal edges

The code includes detailed comments to explain these algorithms and other important implementation details.