import sys
import copy
import random
from collections import deque

# Try to import the C++ module, fall back to Python implementation if not available
try:
    import hex_cpp
    USE_CPP_IMPLEMENTATION = True
    print("Using C++ alpha-beta pruning implementation")
except ImportError:
    USE_CPP_IMPLEMENTATION = False
    print("C++ implementation not found, using Python implementation")

# Class representing the game state for AI calculations
class HexState:
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]  # Game board: 0=empty, 1=blue, 2=red
        self.size = size  # Board size
        self.is_black_turn = is_black_turn  # Current player's turn
    
    def copy(self):
        # Create a deep copy of the state
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

# If using the Python implementation, define these functions
if not USE_CPP_IMPLEMENTATION:
    def evaluate(state):
        # Evaluate the current game state from current player's perspective
        # Higher values favor the current player
        
        # Check for win conditions first
        red_win = has_winning_path(state.board, 1)  # 1 = blue
        blue_win = has_winning_path(state.board, 2)  # 2 = red
        
        if red_win:
            return 1000 if state.is_black_turn else -1000  # Max/min scores for win/loss
        if blue_win:
            return -1000 if state.is_black_turn else 1000
        
        # If no winner yet, use sophisticated connectivity heuristic
        return connectivity_heuristic(state)
    
    def connectivity_heuristic(state):
        # Evaluate position based on how well-connected pieces are
        red_score = count_connected_components(state.board, 1)  # Blue
        blue_score = count_connected_components(state.board, 2)  # Red
        
        # Return score relative to current player
        return red_score - blue_score if state.is_black_turn else blue_score - red_score
    
    def count_connected_components(board, player):
        # Count and score connected groups of pieces
        size = len(board)
        visited = set()
        component_count = 0
        
        # Find all connected components
        for i in range(size):
            for j in range(size):
                if board[i][j] == player and (i, j) not in visited:
                    component_count += 1
                    bfs(board, i, j, player, visited)  # Mark all connected pieces
        
        return component_count
    
    def bfs(board, row, col, player, visited):
        # Breadth-first search to find all connected pieces
        size = len(board)
        queue = deque([(row, col)])
        visited.add((row, col))
        
        # 6 directions for hex grid neighbors
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        while queue:
            r, c = queue.popleft()
            # Check all 6 neighbors
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
    
    def has_winning_path(board, player):
        # Check if player has a winning path connecting their edges
        size = len(board)
        visited = [[False for _ in range(size)] for _ in range(size)]
        
        if player == 1:  # Blue: check top to bottom connection
            # Start from each top cell with player's piece
            for col in range(size):
                # Consider corners as part of both sides
                if (board[0][col] == player or (col == 0 or col == size-1)) and not visited[0][col]:
                    if dfs_path(board, 0, col, player, visited, 1):
                        return True  # Found a path to bottom
        else:  # Red: check left to right connection
            # Start from each left cell with player's piece
            for row in range(size):
                # Consider corners as part of both sides
                if (board[row][0] == player or (row == 0 or row == size-1)) and not visited[row][0]:
                    if dfs_path(board, row, 0, player, visited, 2):
                        return True  # Found a path to right edge
        
        return False  # No winning path found
    
    def dfs_path(board, row, col, player, visited, direction):
        size = len(board)
        
        # Check if we reached opposite edge
        if direction == 1 and row == size - 1:  # Blue reaches bottom
            # Consider corner cells as belonging to both players
            return board[row][col] == player or col == 0 or col == size-1
        elif direction == 2 and col == size - 1:  # Red reaches right
            # Consider corner cells as belonging to both players
            return board[row][col] == player or row == 0 or row == size-1
            
        # Don't explore further if cell is not owned by player and not a corner
        if board[row][col] != player and not ((row == 0 or row == size-1) and (col == 0 or col == size-1)):
            return False
            
        visited[row][col] = True
        
        # Try all 6 directions (hex grid)
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and not visited[nr][nc]:
                # For non-corner cells, we need a player's piece
                # For corner cells, we can pass through regardless
                if board[nr][nc] == player or ((nr == 0 or nr == size-1) and (nc == 0 or nc == size-1)):
                    if dfs_path(board, nr, nc, player, visited, direction):
                        return True
        
        return False  # No path found from this cell
    
    def is_terminal(state):
        # Check if game is over (someone won)
        return has_winning_path(state.board, 1) or has_winning_path(state.board, 2)
    
    def generate_moves(state):
        # Generate all possible moves from current state
        moves = []
        for i in range(state.size):
            for j in range(state.size):
                if state.board[i][j] == 0:  # Empty cell
                    # Create new state with this move
                    new_state = state.copy()
                    new_state.board[i][j] = 1 if state.is_black_turn else 2
                    new_state.is_black_turn = not state.is_black_turn  # Switch turns
                    moves.append((new_state, i, j))  # Store state and move coordinates
        return moves
    
    def alpha_beta(state, depth, alpha, beta, is_maximizing_player):
        # Alpha-beta minimax search for best move
        # Recursively evaluates positions by simulating optimal play
        
        # Base case: leaf node (terminal state or max depth reached)
        if depth == 0 or is_terminal(state):
            return evaluate(state)
        
        if is_maximizing_player:
            # Maximizing player tries to get highest value
            max_eval = float('-inf')
            possible_moves = generate_moves(state)
            
            for move_state, _, _ in possible_moves:
                # Recursive evaluation of move
                eval_score = alpha_beta(move_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                # Prune if we can't improve further on this path
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval
        else:
            # Minimizing player tries to get lowest value
            min_eval = float('inf')
            possible_moves = generate_moves(state)
            
            for move_state, _, _ in possible_moves:
                # Recursive evaluation of move
                eval_score = alpha_beta(move_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                # Prune if we can't improve further on this path
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval

def find_best_move(state, depth=3):
    """Find the best move using alpha-beta pruning"""
    if USE_CPP_IMPLEMENTATION:
        # Convert Python board to C++ board
        cpp_board = hex_cpp.HexBoard(state.size)
        cpp_board.set_board(state.board)
        
        # Use C++ to find best move
        player = hex_cpp.Player.PLAYER1 if state.is_black_turn else hex_cpp.Player.PLAYER2
        row, col = hex_cpp.find_best_move(cpp_board, depth, player)
        return (row, col)
    else:
        # Use Python implementation
        best_move = (-1, -1)
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        possible_moves = generate_moves(state)
        
        # No moves available
        if not possible_moves:
            return (-1, -1)
        
        # Shuffle moves to add variety
        random.shuffle(possible_moves)
        
        # Evaluate each possible move
        for move_state, row, col in possible_moves:
            move_value = alpha_beta(move_state, depth - 1, alpha, beta, False)
            
            if move_value > best_value:
                best_value = move_value
                best_move = (row, col)
            
            alpha = max(alpha, best_value)
        
        return best_move

def check_win(board, player):
    """Check if player has won by connecting their sides"""
    if USE_CPP_IMPLEMENTATION:
        cpp_board = hex_cpp.HexBoard(len(board))
        cpp_board.set_board(board)
        cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
        return cpp_board.check_win(cpp_player)
    else:
        return has_winning_path(board, player)
