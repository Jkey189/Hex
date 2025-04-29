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
  - **Game Mode Dropdown**: Select the game mode ("Player vs Player", "Player vs AI", "AI vs AI").
  - **AI Difficulty Dropdown**: Select the AI's difficulty ("Easy", "Medium", "Difficult") when playing against or watching AI. This controls the AI's search depth.
  - **New Game Button**: Resets the board and starts a new game in the currently selected mode and difficulty.
  - **Move Navigation Buttons**: ("Previous Move", "Next Move") Allow stepping back and forth through the game's history.
  - **Turn Indicator/Game Status**: Displays whose turn it is or the game outcome.
- **Moves History View (Below Controls - Implicit)**: The board display updates when using navigation buttons. A label indicates if viewing history or the latest move.

### Playing Modes

The game offers three playing modes, selectable via the dropdown menu:

1.  **Player vs Player (PvP)**: Play against another human player on the same computer. Blue starts, and players alternate turns clicking empty cells.
2.  **Player vs AI (PvA)**: Play as Blue against the computer AI (Red). You click to make moves, and the AI automatically responds.
3.  **AI vs AI (AvA)**: Watch two AI players compete against each other. The game proceeds automatically after clicking "New Game".

When playing against or watching the AI (PvA or AvA modes), you can adjust the **AI Difficulty** using the dropdown menu (default is "Difficult"):
- **Easy**: AI searches 1 move ahead (Depth 1).
- **Medium**: AI searches 2 moves ahead (Depth 2).
- **Difficult**: AI searches 3 moves ahead (Depth 3).

Changing the mode or AI difficulty during a game will prompt you to confirm, as it requires starting a new game.

### Special Rules

**Pie Rule (Swap Rule)**

Hex implements the **pie rule** (also known as the swap rule) to balance the potential first-player advantage:

1.  The first player (Blue) makes their opening move.
2.  The second player (Red) then has a unique option *on their first turn only*:
    *   **In PvP mode**: The Red player can choose to **click on the cell occupied by Blue's first piece**. This action "swaps" the position – the piece becomes Red, and it's now Blue's turn. Alternatively, Red can ignore the swap and make a normal move in any empty cell.
    *   **In PvA and AvA modes**: The AI playing as Red will automatically evaluate whether to swap based on a simple heuristic (currently, it swaps if Blue's first move is near the center of the board). There is no manual swap button or choice for the player/observer in these modes.

This swap mechanism only applies to the second turn of the game. After Red's first move (whether it's a swap or a normal move), the game proceeds with players placing pieces in empty cells.

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

The core game logic resides in two main classes within `frontend/front.py`:

- **`HexGame`**: Handles the abstract game state:
  - Board representation (`self.board`)
  - Current player tracking (`self.is_black_turn`)
  - Move validation and execution (`make_move`)
  - Core swap implementation (`swap_move`)
  - Win condition checking (delegates to `backend.back.check_win`)
  - Game history tracking (`moves_history`, `board_states`)
  - Resetting the game (`reset`)
  - Converting state for the AI (`to_python_state`)

- **`HexBoard` (QWidget)**: Manages the visual representation and user interaction:
  - Renders the hexagonal grid (`paintEvent`, `draw_borders`, `draw_labels`)
  - Handles mouse clicks (`mousePressEvent`):
    - Determines clicked hexagon.
    - Calls `HexGame.make_move` for regular moves.
    - Implements the **click-to-swap logic for PvP mode** by calling `HexGame.swap_move` if conditions are met.
  - Triggers AI moves (`trigger_ai_move`):
    - Gets the current game state using `HexGame.to_python_state`.
    - Calls `backend.back.find_best_move` to get the AI's decision.
    - Implements the **automatic AI swap decision logic for PvA/AvA modes** before calling the main AI search.
    - Calls `HexGame.make_move` to apply the AI's chosen move.

The backend module (`backend/back.py`) provides the core AI search function (`find_best_move`) and the efficient win checking logic (`check_win`). It can optionally use a compiled C++ extension for performance.

### AI Implementation

The AI uses the alpha-beta pruning algorithm, an enhancement of the minimax algorithm that reduces the number of nodes evaluated in the search tree. The implementation (`backend/back.py` and optionally `backend/alpha-beta pruning/alpha-beta-pruning.cpp`) includes:

- **Alpha-Beta Search**: Core recursive search logic.
- **Heuristic Evaluation Function**: Estimates the value of non-terminal board states. The current evaluation considers factors like piece connectivity and proximity to the target edges (details in `backend/back.py::evaluate_board`).
- **Move Ordering**: A simple ordering is applied to potentially improve pruning efficiency (e.g., checking center moves first).
- **Iterative Deepening (Implied by Depth Parameter)**: The search depth is controlled by the **AI Difficulty** setting selected in the UI ("Easy"=1, "Medium"=2, "Difficult"=3).
- **(Optional) C++ Extension**: A `pybind11` C++ implementation of the alpha-beta search exists in `backend/alpha-beta pruning/` for significant performance gains, especially at higher depths. The Python backend (`back.py`) will automatically try to import and use this if it has been compiled.

Additionally, the **AI swap decision logic** (whether Red AI should swap on the second turn in PvA/AvA modes) is currently implemented within the `HexBoard.trigger_ai_move` method in `frontend/front.py` based on a simple heuristic.

### UI Components

The user interface is built with PyQt5 (`frontend/front.py`) and consists of:

- **`HexWindow` (QMainWindow)**: The main application window.
  - Sets up the overall layout (board, controls).
  - Manages UI elements like the mode dropdown (`QComboBox`), AI difficulty dropdown (`QComboBox`), buttons, and labels.
  - Connects UI signals (button clicks, value changes) to slots (`reset_game`, `change_game_mode`, `update_ai_difficulty`, `show_previous_move`, `show_next_move`).
  - Updates status labels (`update_turn_label`, `update_game_status`).
  - Initializes the `HexGame` and `HexBoard`.

- **`HexBoard` (QWidget)**: Renders the game board and handles direct board interaction.
  - Draws the hexagonal grid and pieces based on `HexGame` state.
  - Processes mouse clicks for player moves (PvP, PvA) and the PvP swap interaction.
  - Initiates AI turns when required (PvA, AvA).

The UI allows for:
- Selecting game modes (PvP, PvA, AvA).
- Adjusting AI difficulty ("Easy", "Medium", "Difficult").
- Playing moves by clicking hexagons.
- Visualizing the game state.
- Triggering the swap rule (via click in PvP, automatically by AI in PvA/AvA).
- Starting new games.
- Navigating through the move history.

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