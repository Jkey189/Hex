import sys, copy, random, os
from collections import deque

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import alpha_beta_pruning as hex_cpp
    USE_CPP_IMPLEMENTATION = True
except ImportError:
    try:
        import hex_cpp
        USE_CPP_IMPLEMENTATION = True
    except ImportError:
        USE_CPP_IMPLEMENTATION = False

# Temporarily force the use of Python implementation
USE_CPP_IMPLEMENTATION = False

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

def has_winning_path(board, player):
    """Check if player has a winning path using simple flood fill."""
    size = len(board)
    
    if player == 1:  # Blue player (connects top to bottom)
        # Check for any blue pieces on top edge
        has_top = False
        for j in range(size):
            if board[0][j] == player:
                has_top = True
                break
        
        if not has_top:
            return False
        
        # Check for any blue pieces on bottom edge
        has_bottom = False
        for j in range(size):
            if board[size-1][j] == player:
                has_bottom = True
                break
        
        if not has_bottom:
            return False
        
        # Do a flood fill from top edge to see if we can reach bottom edge
        visited = set()
        for j in range(size):
            if board[0][j] == player:
                if flood_fill(board, 0, j, player, visited, is_blue=True):
                    return True
                
    else:  # Red player (connects left to right)
        # Check for any red pieces on left edge
        has_left = False
        for i in range(size):
            if board[i][0] == player:
                has_left = True
                break
        
        if not has_left:
            return False
        
        # Check for any red pieces on right edge
        has_right = False
        for i in range(size):
            if board[i][size-1] == player:
                has_right = True
                break
        
        if not has_right:
            return False
        
        # Do a flood fill from left edge to see if we can reach right edge
        visited = set()
        for i in range(size):
            if board[i][0] == player:
                if flood_fill(board, i, 0, player, visited, is_blue=False):
                    return True
    
    return False

def flood_fill(board, row, col, player, visited, is_blue):
    """Flood fill algorithm to check for paths between edges."""
    size = len(board)
    visited.add((row, col))
    
    # Check if we've reached the opposite edge
    if (is_blue and row == size-1) or (not is_blue and col == size-1):
        return True
    
    # Check all six adjacent cells
    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and (nr, nc) not in visited:
            if flood_fill(board, nr, nc, player, visited, is_blue):
                return True
    
    return False

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

def alpha_beta(board, depth, alpha, beta, is_maximizing_player, is_black_turn):
    """Simple alpha-beta pruning algorithm for Hex."""
    size = len(board)
    
    # Terminal condition: depth limit or game over
    if depth == 0 or is_terminal(board):
        return evaluate(board, is_black_turn), None
    
    # Get valid moves
    valid_moves = get_valid_moves(board)
    
    # If no valid moves, just evaluate
    if not valid_moves:
        return evaluate(board, is_black_turn), None
    
    # Try to play near the center first for better pruning
    center = size // 2
    valid_moves.sort(key=lambda move: abs(move[0] - center) + abs(move[1] - center))
    
    if is_maximizing_player:
        value = float('-inf')
        best_move = None
        
        for move in valid_moves:
            # Make move
            i, j = move
            board[i][j] = 1 if is_black_turn else 2
            
            # Recursively evaluate
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False, not is_black_turn)
            
            # Undo move
            board[i][j] = 0
            
            # Update best score and move
            if eval_score > value:
                value = eval_score
                best_move = move
            
            # Alpha-beta pruning
            alpha = max(alpha, value)
            if beta <= alpha:
                break
                
        return value, best_move
    else:
        value = float('inf')
        best_move = None
        
        for move in valid_moves:
            # Make move
            i, j = move
            board[i][j] = 1 if is_black_turn else 2
            
            # Recursively evaluate
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True, not is_black_turn)
            
            # Undo move
            board[i][j] = 0
            
            # Update best score and move
            if eval_score < value:
                value = eval_score
                best_move = move
            
            # Alpha-beta pruning
            beta = min(beta, value)
            if beta <= alpha:
                break
                
        return value, best_move

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
    
    # Use Python implementation
    if not USE_CPP_IMPLEMENTATION:
        try:
            # Limit depth based on board size to prevent timeouts
            adjusted_depth = min(depth, 4 if size <= 7 else 3 if size <= 9 else 2)
            
            # Create a copy of the board for the algorithm to work with
            board_copy = [row[:] for row in state.board]
            
            # Run alpha-beta pruning
            _, move = alpha_beta(board_copy, adjusted_depth, float('-inf'), float('inf'), 
                                True, state.is_black_turn)
            
            if move and 0 <= move[0] < size and 0 <= move[1] < size and state.board[move[0]][move[1]] == 0:
                return move  # Return move directly without swapping coordinates
        except Exception as e:
            print(f"Error in Python alpha-beta implementation: {e}")
            import traceback
            traceback.print_exc()
    
    # Use C++ implementation if available
    if USE_CPP_IMPLEMENTATION:
        try:
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(state.board)
            cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
            
            # Find best move using alpha-beta pruning
            row, col = hex_cpp.find_best_move(cpp_board, depth, cpp_player)
            if 0 <= row < size and 0 <= col < size and state.board[row][col] == 0:
                return (row, col)  # Return coordinates without swapping
        except Exception as e:
            print(f"Error in C++ implementation: {e}")
    
    # Fallback to simple heuristic if both methods failed
    # Try to play near the center first, then try to connect to existing pieces
    center = size // 2
    
    # Sort empty cells by distance to center
    empty_cells.sort(key=lambda pos: abs(pos[0] - center) + abs(pos[1] - center))
    
    # Try to find a move that connects to an existing piece of the same color
    for row, col in empty_cells:
        # Check if this move is adjacent to any of our pieces
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and state.board[nr][nc] == player:
                return (row, col)
    
    # If no connecting move found, return the cell closest to center
    return empty_cells[0] if empty_cells else (-1, -1)

def check_win(board, player):
    if USE_CPP_IMPLEMENTATION:
        cpp_board = hex_cpp.HexBoard(len(board))
        cpp_board.set_board(board)
        cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
        return cpp_board.check_win(cpp_player)
    else:
        return has_winning_path(board, player)
