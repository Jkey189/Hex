"""
Python interface for the Hex game backend.
This module provides a clean interface for the frontend to interact with the optimized C++ backend.
"""
import sys, os
from collections import deque

# Add paths to find our C++ module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "alpha-beta pruning"))

# Try to import the C++ module
try:
    from backend.alpha_beta_pruning import hex_cpp
    USE_CPP_IMPLEMENTATION = True
    print("C++ acceleration module loaded successfully from backend")
except ImportError:
    try:
        import hex_cpp
        USE_CPP_IMPLEMENTATION = True
        print("C++ acceleration module loaded successfully")
    except ImportError:
        print("Warning: C++ acceleration module not available, using Python implementation")
        USE_CPP_IMPLEMENTATION = False

# Define constants that match C++ enum values
EMPTY = 0
PLAYER1 = 1  # Blue player
PLAYER2 = 2  # Red player

# Hex grid neighbor directions (6 neighbors)
HEX_DIRECTIONS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

class HexState:
    """Represents the state of a Hex game, compatible with both Python and C++ backends."""
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
        
        # Create C++ board if available
        if USE_CPP_IMPLEMENTATION:
            self.cpp_board = hex_cpp.HexBoard(size)
    
    def copy(self):
        """Creates a deep copy of the game state"""
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        
        if USE_CPP_IMPLEMENTATION:
            new_state.cpp_board.set_board(new_state.board)
            
        return new_state
    
    def sync_cpp_board(self):
        """Synchronizes the C++ board with the Python board"""
        if USE_CPP_IMPLEMENTATION:
            self.cpp_board.set_board(self.board)
    
    def update_from_cpp_board(self):
        """Updates the Python board from the C++ board"""
        if USE_CPP_IMPLEMENTATION:
            self.board = self.cpp_board.get_board()

def check_win(board, player):
    """
    Checks if player has a winning path on the board.
    Player 1 (Blue): Connects top to bottom
    Player 2 (Red): Connects left to right
    """
    if USE_CPP_IMPLEMENTATION:
        try:
            size = len(board)
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(board)
            return cpp_board.check_win(player)
        except Exception as e:
            print(f"C++ check_win failed: {e}, falling back to Python implementation")
            # Fall back to Python implementation
            pass
    
    # Python implementation using BFS
    size = len(board)
    queue = deque()
    visited = set()
    
    if player == 1:  # Blue: top-to-bottom
        # Add all player stones in the top row to the queue
        for col in range(size):
            if board[0][col] == player:
                queue.append((0, col))
                visited.add((0, col))
        target_check = lambda r, c: r == size - 1  # Check if reached bottom row
    else:  # Red: left-to-right
        # Add all player stones in the leftmost column to the queue
        for row in range(size):
            if board[row][0] == player:
                queue.append((row, 0))
                visited.add((row, 0))
        target_check = lambda r, c: c == size - 1  # Check if reached rightmost column
    
    # No starting stones found
    if not queue:
        return False
    
    # BFS to find a path
    while queue:
        row, col = queue.popleft()
        
        # Check win condition
        if target_check(row, col):
            return True
        
        # Check all six neighboring hexagons
        for dr, dc in HEX_DIRECTIONS:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < size and 0 <= new_col < size and 
                board[new_row][new_col] == player and 
                (new_row, new_col) not in visited):
                visited.add((new_row, new_col))
                queue.append((new_row, new_col))
    
    # No path found
    return False

def find_best_move(state, depth=3):
    """
    Finds the best move for the current player using the alpha-beta pruning algorithm.
    Uses the C++ implementation if available, otherwise falls back to Python.
    
    Parameters:
        state: Current game state (HexState object)
        depth: Search depth for the algorithm
    
    Returns:
        (row, col): The coordinates of the best move
    """
    player = 1 if state.is_black_turn else 2
    size = state.size
    
    # Handle empty board special case - play in center
    if all(state.board[r][c] == 0 for r in range(size) for c in range(size)):
        center = size // 2
        return (center, center)
    
    # Use C++ implementation if available
    if USE_CPP_IMPLEMENTATION:
        try:
            # Make sure the C++ board is in sync with Python board
            state.sync_cpp_board()
            
            # Adjust depth based on board size for performance
            adjusted_depth = min(depth, 4 if size <= 7 else 3 if size <= 9 else 2)
            
            # Call the C++ algorithm to find the best move
            cpp_player = PLAYER1 if player == 1 else PLAYER2
            row, col = hex_cpp.find_best_move(state.cpp_board, adjusted_depth, cpp_player)
            return (row, col)
        except Exception as e:
            print(f"C++ find_best_move failed: {e}, falling back to Python implementation")
            # Fall back to Python implementation
    
    # Python implementation (fallback)
    return python_find_best_move(state, depth)

def python_find_best_move(state, depth=3):
    """Python implementation of the alpha-beta pruning algorithm (used as fallback)"""
    player = 1 if state.is_black_turn else 2
    size = state.size
    board = [row[:] for row in state.board]
    
    # Check for empty board - play in center
    if all(board[r][c] == 0 for r in range(size) for c in range(size)):
        center = size // 2
        return (center, center)
    
    # Get valid moves
    valid_moves = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    
    # Check for winning moves
    for r, c in valid_moves:
        board[r][c] = player
        if check_win(board, player):
            board[r][c] = 0  # Revert move
            return (r, c)
        board[r][c] = 0  # Revert move
    
    # Check for blocking opponent's winning moves
    opponent = 3 - player
    for r, c in valid_moves:
        board[r][c] = opponent
        if check_win(board, opponent):
            board[r][c] = 0  # Revert move
            return (r, c)
        board[r][c] = 0  # Revert move
    
    # Adjust depth based on board size for performance
    adjusted_depth = min(depth, 4 if size <= 7 else 3 if size <= 9 else 2)
    
    # Run minimax with alpha-beta pruning
    best_score = float('-inf')
    best_move = None
    
    # Sort moves to try center and near-center positions first
    center = size // 2
    valid_moves.sort(key=lambda move: abs(move[0] - center) + abs(move[1] - center))
    
    for r, c in valid_moves:
        board[r][c] = player
        score = minimax(board, adjusted_depth - 1, float('-inf'), float('inf'), 
                       False, player, opponent)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move if best_move else valid_moves[0] if valid_moves else (-1, -1)

def minimax(board, depth, alpha, beta, is_maximizing, player, opponent):
    """Helper function for minimax with alpha-beta pruning (Python implementation)"""
    size = len(board)
    
    # Check terminal conditions
    if check_win(board, player):
        return 100
    if check_win(board, opponent):
        return -100
    if depth == 0:
        return evaluate_board(board, player, opponent)
    
    valid_moves = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    if not valid_moves:
        return evaluate_board(board, player, opponent)
    
    if is_maximizing:
        value = float('-inf')
        for r, c in valid_moves:
            board[r][c] = player
            value = max(value, minimax(board, depth-1, alpha, beta, False, player, opponent))
            board[r][c] = 0
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for r, c in valid_moves:
            board[r][c] = opponent
            value = min(value, minimax(board, depth-1, alpha, beta, True, player, opponent))
            board[r][c] = 0
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def evaluate_board(board, player, opponent):
    """Heuristic evaluation of board state (Python implementation)"""
    size = len(board)
    player_score = opponent_score = 0
    
    # Count piece advantage
    for r in range(size):
        for c in range(size):
            if board[r][c] == player:
                player_score += 1
                # Bonus for edge pieces
                if (player == 1 and (r == 0 or r == size-1)) or (player == 2 and (c == 0 or c == size-1)):
                    player_score += 2
                # Bonus for central positioning
                center_dist = abs(r - size//2) + abs(c - size//2)
                player_score += (size - center_dist) // 2
                
                # Bonus for connections
                for dr, dc in HEX_DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player:
                        player_score += 1
                        
            elif board[r][c] == opponent:
                opponent_score += 1
                # Bonus for edge pieces
                if (opponent == 1 and (r == 0 or r == size-1)) or (opponent == 2 and (c == 0 or c == size-1)):
                    opponent_score += 2
                # Bonus for central positioning
                center_dist = abs(r - size//2) + abs(c - size//2)
                opponent_score += (size - center_dist) // 2
                
                # Bonus for connections
                for dr, dc in HEX_DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == opponent:
                        opponent_score += 1
    
    return player_score - opponent_score
