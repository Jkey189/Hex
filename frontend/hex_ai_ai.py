import sys
import copy
import random  # Added for random move selection
from collections import deque

class HexState:
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
    
    def copy(self):
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

def evaluate(state):
    """
    Evaluate the state of the game from the perspective of the current player.
    For Hex, we need a more sophisticated evaluation than just counting pieces.
    """
    # Check if the game is won by either player
    red_win = has_winning_path(state.board, 1)  # 1 = red
    blue_win = has_winning_path(state.board, 2)  # 2 = blue
    
    if red_win:
        return 1000 if state.is_black_turn else -1000
    if blue_win:
        return -1000 if state.is_black_turn else 1000
    
    # If no winner, evaluate based on connectivity metrics
    return connectivity_heuristic(state)

def connectivity_heuristic(state):
    """
    A heuristic that evaluates how well-connected each player's pieces are
    toward their respective goals.
    """
    red_score = count_connected_components(state.board, 1)
    blue_score = count_connected_components(state.board, 2)
    
    # Return score from perspective of current player
    return red_score - blue_score if state.is_black_turn else blue_score - red_score

def count_connected_components(board, player):
    """Count the number of connected components for a player"""
    size = len(board)
    visited = set()
    component_count = 0
    
    for i in range(size):
        for j in range(size):
            if board[i][j] == player and (i, j) not in visited:
                # Found a new component
                component_count += 1
                # Mark all connected pieces as visited
                bfs(board, i, j, player, visited)
    
    return component_count

def bfs(board, row, col, player, visited):
    """Breadth-first search to mark all connected pieces"""
    size = len(board)
    queue = deque([(row, col)])
    visited.add((row, col))
    
    # Hex has 6 adjacent hexagons
    directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and (nr, nc) not in visited:
                queue.append((nr, nc))
                visited.add((nr, nc))

def has_winning_path(board, player):
    """
    Check if player has a winning path
    For Red (player 1): path from top to bottom
    For Blue (player 2): path from left to right
    
    This determines if a player has won the game by connecting opposite sides.
    """
    size = len(board)
    visited = [[False for _ in range(size)] for _ in range(size)]
    
    if player == 1:  # Red - check top to bottom
        # Check each position in the top row
        for col in range(size):
            if board[0][col] == player and not visited[0][col]:
                if dfs_path(board, 0, col, player, visited, 1):
                    return True
    else:  # Blue - check left to right
        # Check each position in the leftmost column
        for row in range(size):
            if board[row][0] == player and not visited[row][0]:
                if dfs_path(board, row, 0, player, visited, 2):
                    return True
    
    return False

def dfs_path(board, row, col, player, visited, direction):
    """
    DFS to find a path for the player
    direction: 1 - top to bottom, 2 - left to right
    """
    size = len(board)
    
    # Base case: reached the opposite edge
    if (direction == 1 and row == size - 1) or (direction == 2 and col == size - 1):
        return True
        
    visited[row][col] = True
    
    # Hex has 6 adjacent hexagons
    directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and not visited[nr][nc]:
            if dfs_path(board, nr, nc, player, visited, direction):
                return True
    
    return False

def is_terminal(state):
    """
    Check if the game has ended by determining if either player has won.
    When a player connects their opposite sides, the game ends.
    """
    return has_winning_path(state.board, 1) or has_winning_path(state.board, 2)

def generate_moves(state):
    """Generate all possible moves from current state"""
    moves = []
    for i in range(state.size):
        for j in range(state.size):
            if state.board[i][j] == 0:  # empty cell
                new_state = state.copy()
                new_state.board[i][j] = 1 if state.is_black_turn else 2
                new_state.is_black_turn = not state.is_black_turn
                moves.append((new_state, i, j))  # Store the move coordinates with the state
    return moves

def alpha_beta(state, depth, alpha, beta, is_maximizing_player):
    """
    Alpha-beta pruning algorithm for minimax search.
    
    Parameters:
    - state: Current game state
    - depth: How many moves ahead to look
    - alpha: Best already explored option for maximizer
    - beta: Best already explored option for minimizer
    - is_maximizing_player: Whether current player is maximizer
    
    This is a recursive algorithm that prunes branches of the search tree
    that cannot possibly affect the final decision.
    """
    if depth == 0 or is_terminal(state):
        return evaluate(state)
    
    if is_maximizing_player:
        max_eval = float('-inf')
        possible_moves = generate_moves(state)
        
        for move_state, _, _ in possible_moves:
            eval_score = alpha_beta(move_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break  # Beta pruning - opponent won't allow this path
        
        return max_eval
    else:
        min_eval = float('inf')
        possible_moves = generate_moves(state)
        
        for move_state, _, _ in possible_moves:
            eval_score = alpha_beta(move_state, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break  # Alpha pruning - we already have a better path
        
        return min_eval

def find_best_move(state, depth=3):
    """
    Find the best move using alpha-beta pruning.
    
    Parameters:
    - state: Current game state
    - depth: How many moves ahead to look
    
    Returns:
    - (row, col): Coordinates of the best move
    """
    best_move = (-1, -1)
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    possible_moves = generate_moves(state)
    
    # If no moves are possible
    if not possible_moves:
        return (-1, -1)
    
    # Shuffle moves for variety when multiple moves have the same value
    import random
    random.shuffle(possible_moves)
    
    for move_state, row, col in possible_moves:
        # For each possible move, evaluate using alpha-beta
        move_value = alpha_beta(move_state, depth - 1, alpha, beta, False)
        
        if move_value > best_value:
            best_value = move_value
            best_move = (row, col)
        
        # Update alpha
        alpha = max(alpha, best_value)
    
    return best_move

def check_win(board, player):
    """
    Check if the specified player has won by connecting opposite sides.
    
    For Blue (player 1): win by connecting top to bottom blue borders
    For Red (player 2): win by connecting left to right red borders
    
    When this returns True, the game should stop.
    """
    size = len(board)
    visited = [[False for _ in range(size)] for _ in range(size)]
    
    if player == 1:  # Blue - check top to bottom
        # Check each position in the top row
        for col in range(size):
            if board[0][col] == player and not visited[0][col]:
                if dfs_path(board, 0, col, player, visited, 1):
                    return True
    else:  # Red - check left to right
        # Check each position in the leftmost column
        for row in range(size):
            if board[row][0] == player and not visited[row][0]:
                if dfs_path(board, row, 0, player, visited, 2):
                    return True
    
    return False
