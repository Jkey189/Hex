import sys, os
from collections import deque

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "alpha-beta pruning"))

# C++ acceleration module import
try:
    import hex_cpp
    USE_CPP_IMPLEMENTATION = True
except ImportError:
    try:
        from backend import alpha_beta_pruning
        USE_CPP_IMPLEMENTATION = True
    except ImportError:
        try:
            import alpha_beta_pruning as hex_cpp
            USE_CPP_IMPLEMENTATION = True
        except ImportError:
            USE_CPP_IMPLEMENTATION = False

# Hex grid neighbor directions (6 neighbors)
HEX_DIRECTIONS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

class HexState:
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
    
    def copy(self):
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

def check_win(board, player):
    """
    Checks if player has a winning path on the board using BFS.
    Player 1 (Blue): Connects top to bottom
    Player 2 (Red): Connects left to right
    """
    size = len(board)
    queue = deque()
    visited = set()
    
    # Set starting and target edges based on player
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
            
            # Check if position is valid and contains player's stone and hasn't been visited
            if (0 <= new_row < size and 0 <= new_col < size and 
                board[new_row][new_col] == player and 
                (new_row, new_col) not in visited):
                visited.add((new_row, new_col))
                queue.append((new_row, new_col))
    
    # No path found
    return False

def evaluate(board, is_black_turn):
    """Evaluates the board state for the current player."""
    player = 1 if is_black_turn else 2
    opponent = 3 - player
    
    # Win/loss detection
    if check_win(board, player):
        return 1000
    if check_win(board, opponent):
        return -1000
    
    # Heuristic evaluation
    size = len(board)
    player_score = opponent_score = 0
    
    for i in range(size):
        for j in range(size):
            if board[i][j] == player:
                player_score += 1
                # Bonus for edge pieces
                if (player == 1 and (i == 0 or i == size-1)) or (player == 2 and (j == 0 or j == size-1)):
                    player_score += 2
            elif board[i][j] == opponent:
                opponent_score += 1
                # Bonus for edge pieces
                if (opponent == 1 and (i == 0 or i == size-1)) or (opponent == 2 and (j == 0 or j == size-1)):
                    opponent_score += 2
    
    return player_score - opponent_score

def get_valid_moves(board):
    """Returns list of valid moves (empty cells)."""
    size = len(board)
    return [(i, j) for i in range(size) for j in range(size) if board[i][j] == 0]

def alpha_beta(board, depth, alpha, beta, is_maximizing_player, current_player):
    """Alpha-beta pruning algorithm for Hex."""
    size = len(board)
    opponent = 3 - current_player
    
    # Terminal conditions
    if depth == 0 or check_win(board, 1) or check_win(board, 2):
        return evaluate(board, current_player == 1), None
    
    # Get valid moves
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return evaluate(board, current_player == 1), None
    
    # Try center moves first (better performance)
    center = size // 2
    valid_moves.sort(key=lambda move: abs(move[0] - center) + abs(move[1] - center))
    
    if is_maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in valid_moves:
            r, c = move
            board[r][c] = current_player
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False, opponent)
            board[r][c] = 0  # Undo move
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in valid_moves:
            r, c = move
            board[r][c] = current_player
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True, opponent)
            board[r][c] = 0  # Undo move
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval, best_move

def find_best_move(state, depth=3):
    """Finds the best move for the current player."""
    player = 1 if state.is_black_turn else 2
    size = len(state.board)
    empty_count = sum(row.count(0) for row in state.board)
    
    # Handle empty board - play in center
    if empty_count == size * size:
        center = size // 2
        return (center, center)
    
    # Second move strategy
    if empty_count == size * size - 1 and player == 2:
        first_move = None
        for r in range(size):
            for c in range(size):
                if state.board[r][c] != 0:
                    first_move = (r, c)
                    break
            if first_move:
                break
        
        center = size // 2
        if first_move[0] == center and first_move[1] == center:
            return (center, center+1)  # Play adjacent if first move was center
        else:
            return (center, center)  # Otherwise play center
    
    # Use C++ implementation if available
    if USE_CPP_IMPLEMENTATION:
        try:
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(state.board)
            cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
            row, col = hex_cpp.find_best_move(cpp_board, depth, cpp_player)
            return (row, col)
        except Exception:
            pass  # Fall back to Python implementation
    
    # Python implementation
    empty_cells = get_valid_moves(state.board)
    if not empty_cells:
        return (-1, -1)
    
    try:
        adjusted_depth = min(depth, 4 if size <= 7 else 3 if size <= 9 else 2)
        board_copy = [row[:] for row in state.board]
        current_player = 1 if state.is_black_turn else 2
        _, move = alpha_beta(board_copy, adjusted_depth, float('-inf'), float('inf'),
                            state.is_black_turn, current_player)
        if move and 0 <= move[0] < size and 0 <= move[1] < size and state.board[move[0]][move[1]] == 0:
            return move
    except Exception:
        pass  # Fall back to heuristic
    
    # Fallback: play near existing pieces or center
    center = size // 2
    empty_cells.sort(key=lambda pos: abs(pos[0] - center) + abs(pos[1] - center))
    for row, col in empty_cells:
        for dr, dc in HEX_DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and state.board[nr][nc] == player:
                return (row, col)
    
    # Just play the first available move
    return empty_cells[0] if empty_cells else (-1, -1)
