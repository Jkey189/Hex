import sys, copy, random, os
from collections import deque

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "alpha-beta pruning"))

try:
    # First try importing the .so file directly from the backend directory
    import hex_cpp
    USE_CPP_IMPLEMENTATION = True
    print("Successfully imported hex_cpp module from main directory")
except ImportError:
    try:
        # Try to import from the subdirectory
        from backend import alpha_beta_pruning
        USE_CPP_IMPLEMENTATION = Tru
        print("Successfully imported alpha_beta_pruning module")
    except ImportError:
        try:
            # Another attempt from the alpha-beta pruning subdirectory
            import alpha_beta_pruning as hex_cpp
            USE_CPP_IMPLEMENTATION = True
            print("Successfully imported hex_cpp module from subdirectory")
        except ImportError:
            print("Failed to import C++ implementation, falling back to Python")
            USE_CPP_IMPLEMENTATION = False

# Force C++ implementation to be used
USE_CPP_IMPLEMENTATION = True

DIRECTIONS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

class HexState:
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
    
    def copy(self):
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

def _check_win_bfs(board, player):
    """
    Breadth-First Search to check for a winning path for the given player.
    
    In Hex:
    - Player 1 (Blue) wins by connecting top and bottom edges
    - Player 2 (Red) wins by connecting left and right edges
    
    Args:
        board: 2D game board where 0=empty, 1=blue, 2=red
        player: Player ID (1 for Blue, 2 for Red)
        
    Returns:
        bool: True if player has a winning path, False otherwise
    """
    size = len(board)
    visited = set()  # Track visited cells
    
    # Create a queue for BFS and add starting positions
    queue = deque()
    
    # Initialize differently depending on player:
    if player == 1:  # Blue: needs to connect top and bottom
        # Add all Blue stones in the top row to the queue
        for col in range(size):
            if board[0][col] == player:
                queue.append((0, col))
                visited.add((0, col))
    else:  # Red: needs to connect left and right
        # Add all Red stones in the leftmost column to the queue
        for row in range(size):
            if board[row][0] == player:
                queue.append((row, 0))
                visited.add((row, 0))
    
    # No starting stones found
    if not queue:
        return False
    
    # Run BFS
    while queue:
        row, col = queue.popleft()
        
        # Check for victory (reaching the opposite edge)
        if (player == 1 and row == size - 1) or (player == 2 and col == size - 1):
            return True
        
        # Check all six neighboring hexagons
        for dr, dc in DIRECTIONS:
            new_row, new_col = row + dr, col + dc
            
            # Check if position is valid and contains player's stone and hasn't been visited
            if (0 <= new_row < size and 0 <= new_col < size and 
                board[new_row][new_col] == player and 
                (new_row, new_col) not in visited):
                visited.add((new_row, new_col))
                queue.append((new_row, new_col))
    
    # If we exhausted the queue without finding a path to the opposite edge
    return False

def has_winning_path(board, player):
    """Check if player has a winning path using BFS."""
    return _check_win_bfs(board, player)

def evaluate(board, is_black_turn):
    """Simple evaluation function for Hex game."""
    player = 1 if is_black_turn else 2
    opponent = 3 - player
    
    # Check for win
    if has_winning_path(board, player):
        return 1000
    if has_winning_path(board, opponent):
        return -1000
    
    # Simple heuristic based on piece count and edge control
    size = len(board)
    player_score = 0
    opponent_score = 0
    
    # Count pieces and edge control
    for i in range(size):
        for j in range(size):
            if board[i][j] == player:
                player_score += 1
                # Bonus for edge pieces (relevant to win condition)
                if player == 1 and (i == 0 or i == size-1):  # Blue: top/bottom
                    player_score += 2
                elif player == 2 and (j == 0 or j == size-1):  # Red: left/right
                    player_score += 2
            elif board[i][j] == opponent:
                opponent_score += 1
                # Bonus for edge pieces (relevant to win condition)
                if opponent == 1 and (i == 0 or i == size-1):  # Blue: top/bottom
                    opponent_score += 2
                elif opponent == 2 and (j == 0 or j == size-1):  # Red: left/right
                    opponent_score += 2
    
    return player_score - opponent_score

def is_terminal(board):
    """Check if the game is over."""
    return has_winning_path(board, 1) or has_winning_path(board, 2)

def get_valid_moves(board):
    """Get all valid moves (empty cells)."""
    size = len(board)
    moves = []
    for i in range(size):
        for j in range(size):
            if board[i][j] == 0:
                moves.append((i, j))
    return moves

def alpha_beta(board, depth, alpha, beta, is_maximizing_player, current_player_turn):
    """
    Alpha-beta pruning algorithm for Hex.

    Args:
        board: The current board state.
        depth: Remaining search depth.
        alpha: Alpha value for the maximizing player.
        beta: Beta value for the minimizing player.
        is_maximizing_player: True if the current node is maximizing, False otherwise.
        current_player_turn: The player whose turn it is in this board state (1 for Blue, 2 for Red).

    Returns:
        A tuple (score, best_move). Score is relative to player 1 (Blue).
    """
    size = len(board)
    player = current_player_turn # Player to make a move in this state
    opponent = 3 - player

    # Terminal condition: depth limit or game over
    if depth == 0 or is_terminal(board):
        score = evaluate(board, current_player_turn == 1)
        return score, None

    # Get valid moves
    valid_moves = get_valid_moves(board)

    # If no valid moves, just evaluate
    if not valid_moves:
        eval_score = evaluate(board, True)
        return eval_score, None

    # Move ordering heuristic: Try center moves first
    center = size // 2
    valid_moves.sort(key=lambda move: abs(move[0] - center) + abs(move[1] - center))

    best_move = None

    if is_maximizing_player: # Maximizing Player 1's score
        max_eval = float('-inf')
        for move in valid_moves:
            r, c = move
            board[r][c] = player # Make move for the current player
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False, opponent)
            board[r][c] = 0 # Undo move

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Beta cutoff
        return max_eval, best_move
    else: # Minimizing Player 1's score (Maximizing Player 2's score)
        min_eval = float('inf')
        for move in valid_moves:
            r, c = move
            board[r][c] = player # Make move for the current player
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True, opponent)
            board[r][c] = 0 # Undo move

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Alpha cutoff
        return min_eval, best_move

def find_best_move(state, depth=3):
    player = 1 if state.is_black_turn else 2
    size = len(state.board)
    empty_count = sum(row.count(0) for row in state.board)
    
    # Get valid empty cells first as a fallback
    empty_cells = []
    for row in range(size):
        for col in range(size):
            if state.board[row][col] == 0:
                empty_cells.append((row, col))
    
    if not empty_cells:
        return (-1, -1)  # No valid moves
    
    # Handle special cases for beginning moves
    if empty_count == size * size:
        center = size // 2
        return (center, center)  # Play in the center for the first move
    
    if empty_count == size * size - 1 and player == 2:
        # If player 1 played first, find their move and respond appropriately
        first_move = None
        for r in range(size):
            for c in range(size):
                if state.board[r][c] == 1:
                    first_move = (r, c)
                    break
            if first_move:
                break
        
        if first_move:
            center = size // 2
            # If first move was in center, play adjacent
            if first_move[0] == center and first_move[1] == center:
                return (center, center+1)
            # Otherwise, play in center
            else:
                return (center, center)
    
    # Use C++ implementation if available and enabled
    if USE_CPP_IMPLEMENTATION:
        try:
            print("Using C++ alpha-beta pruning for move finding")
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(state.board)
            cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
            
            # Find best move using alpha-beta pruning
            row, col = hex_cpp.find_best_move(cpp_board, depth, cpp_player)
            print(f"C++ algorithm chose move: {row}, {col}")
            return (row, col)
        except Exception as e:
            print(f"Error in C++ implementation: {e}")
            import traceback
            traceback.print_exc()
    
    # Use Python implementation
    if not USE_CPP_IMPLEMENTATION:
        try:
            adjusted_depth = min(depth, 4 if size <= 7 else 3 if size <= 9 else 2)
            board_copy = [row[:] for row in state.board]
            current_player = 1 if state.is_black_turn else 2
            score, move = alpha_beta(board_copy, adjusted_depth, float('-inf'), float('inf'),
                                     state.is_black_turn, current_player)
            if move and 0 <= move[0] < size and 0 <= move[1] < size and state.board[move[0]][move[1]] == 0:
                return move
        except Exception as e:
            print(f"Error in Python alpha-beta implementation: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to simple heuristic if both methods failed
    center = size // 2
    empty_cells.sort(key=lambda pos: abs(pos[0] - center) + abs(pos[1] - center))
    for row, col in empty_cells:
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and state.board[nr][nc] == player:
                return (row, col)
    return empty_cells[0] if empty_cells else (-1, -1)

def check_win(board, player):
    """
    Checks if the specified player has a winning path on the board.
    
    For player 1 (Blue): Checks for a connected path from top to bottom
    For player 2 (Red): Checks for a connected path from left to right
    
    Uses C++ implementation if available, falls back to Python BFS implementation.
    
    Args:
        board: 2D game board where 0=empty, 1=blue, 2=red
        player: Player ID (1 for Blue, 2 for Red)
        
    Returns:
        bool: True if player has a winning path, False otherwise
    """
    # Try to use C++ implementation for better performance
    if USE_CPP_IMPLEMENTATION:
        try:
            # Convert to C++ board representation
            size = len(board)
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(board)
            
            # Select the appropriate player enum
            cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
            
            # Call C++ implementation
            return cpp_board.check_win(cpp_player)
        except Exception as e:
            print(f"Error in C++ win checking: {e}. Falling back to Python.")
            # Fall through to Python implementation on error
    
    # Python implementation using BFS
    return has_winning_path(board, player)
