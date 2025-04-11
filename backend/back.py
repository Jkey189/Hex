import sys, copy, random, os
from collections import deque

# Add the correct path to search for the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# First, try to import the module using its file name directly
try:
    import alpha_beta_pruning as hex_cpp
    USE_CPP_IMPLEMENTATION = True
    print("Using C++ alpha-beta pruning implementation")
except ImportError:
    # If that fails, try to import using the original name
    try:
        import hex_cpp
        USE_CPP_IMPLEMENTATION = True
        print("Using C++ alpha-beta pruning implementation")
    except ImportError:
        # If both fail, use Python implementation
        USE_CPP_IMPLEMENTATION = False
        print("C++ implementation not found, using Python implementation")

# Define constants for the six directions on a hexagonal grid
DIRECTIONS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

class HexState:
    """
    Represents the state of a Hex game, including the board configuration and current player turn.
    
    Attributes:
        board (list): 2D grid representation where 0=empty, 1=blue player, 2=red player
        size (int): Dimension of the square board
        is_black_turn (bool): True if it's blue player's turn, False if red player's turn
    """
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
    
    def copy(self):
        """Creates a deep copy of the current game state"""
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

if not USE_CPP_IMPLEMENTATION:
    def evaluate(state):
        """
        Evaluates the current state of the game.
        Returns high positive score if current player is winning,
        high negative score if opponent is winning, 
        otherwise uses connectivity heuristic.
        """
        red_win = has_winning_path(state.board, 1)
        blue_win = has_winning_path(state.board, 2)
        
        if red_win: return 1000 if state.is_black_turn else -1000
        if blue_win: return -1000 if state.is_black_turn else 1000
        
        return connectivity_heuristic(state)
    
    def connectivity_heuristic(state):
        """
        Calculates a heuristic value based on the connected components
        of each player's pieces on the board.
        """
        red_score = count_connected_components(state.board, 1)
        blue_score = count_connected_components(state.board, 2)
        
        return red_score - blue_score if state.is_black_turn else blue_score - red_score
    
    def count_connected_components(board, player):
        """
        Counts the number of connected groups of pieces for the given player.
        Fewer, larger groups are generally better in Hex.
        """
        size = len(board)
        visited = set()
        component_count = 0
        
        for i in range(size):
            for j in range(size):
                if board[i][j] == player and (i, j) not in visited:
                    component_count += 1
                    bfs(board, i, j, player, visited)
        
        return component_count
    
    def bfs(board, row, col, player, visited):
        """
        Breadth-first search to find all connected pieces of the same player.
        Marks all connected pieces as visited.
        """
        size = len(board)
        queue = deque([(row, col)])
        visited.add((row, col))
        
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
    
    def has_winning_path(board, player):
        """
        Checks if the given player has a winning path on the board.
        A winning path connects one side of the board to the opposite side.
        Player 1 (Blue): Connect top to bottom
        Player 2 (Red): Connect left to right
        """
        size = len(board)
        visited = [[False for _ in range(size)] for _ in range(size)]
        
        if player == 1:  # Blue player - connect top to bottom
            # Start from top row cells that contain player's piece
            for col in range(size):
                if board[0][col] == player and not visited[0][col]:
                    # Use DFS to check if there's a path to bottom row
                    if dfs_path(board, 0, col, player, visited, 1):
                        return True
        else:  # Red player - connect left to right
            # Start from leftmost column cells that contain player's piece
            for row in range(size):
                if board[row][0] == player and not visited[row][0]:
                    # Use DFS to check if there's a path to rightmost column
                    if dfs_path(board, row, 0, player, visited, 2):
                        return True
        
        return False
    
    def dfs_path(board, row, col, player, visited, direction):
        """
        Depth-first search to determine if a winning path exists for the given player.
        direction=1: Check for path from top to bottom (Blue player)
        direction=2: Check for path from left to right (Red player)
        """
        size = len(board)
        
        # Check if we've reached the destination edge
        if direction == 1 and row == size - 1:  # Bottom row for Blue
            return board[row][col] == player
        elif direction == 2 and col == size - 1:  # Right column for Red
            return board[row][col] == player
            
        # Current cell must belong to the player
        if board[row][col] != player:
            return False
            
        visited[row][col] = True
        
        # Check all six adjacent cells in hexagonal grid
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if (0 <= nr < size and 0 <= nc < size and 
                not visited[nr][nc] and board[nr][nc] == player):
                if dfs_path(board, nr, nc, player, visited, direction):
                    return True
        
        return False
    
    def is_terminal(state):
        """
        Determines if the game has reached a terminal state (win for either player).
        """
        return has_winning_path(state.board, 1) or has_winning_path(state.board, 2)
    
    def generate_moves(state):
        """
        Generates all possible moves for the current player.
        Returns a list of new states and their corresponding move coordinates.
        """
        moves = []
        for i in range(state.size):
            for j in range(state.size):
                if state.board[i][j] == 0:
                    new_state = state.copy()
                    new_state.board[i][j] = 1 if state.is_black_turn else 2
                    new_state.is_black_turn = not state.is_black_turn
                    moves.append((new_state, i, j))
        return moves
    
    def alpha_beta_search(state, depth, alpha, beta, maximizing_player):
        """
        Performs alpha-beta pruning to find the best move for the current player.
        """
        player = 1 if maximizing_player else 2
        opponent = 2 if maximizing_player else 1
        
        if check_win(state.board, player): return (1000, None)
        if check_win(state.board, opponent): return (-1000, None)
        if depth == 0: return (evaluate_state(state, player), None)
        
        valid_moves = get_valid_moves(state)
        if not valid_moves: return (0, None)
        
        random.shuffle(valid_moves)
        best_move = None
        
        if maximizing_player:
            best_score = float('-inf')
            for move in valid_moves:
                row, col = move
                new_state = clone_state(state)
                new_state.board[row][col] = player
                new_state.player_turn = not state.player_turn
                
                score, _ = alpha_beta_search(new_state, depth - 1, alpha, beta, False)
                
                if score > best_score:
                    best_score = score
                    best_move = move
                    
                alpha = max(alpha, best_score)
                if beta <= alpha: break
            return (best_score, best_move)
        else:
            best_score = float('inf')
            for move in valid_moves:
                row, col = move
                new_state = clone_state(state)
                new_state.board[row][col] = player
                new_state.player_turn = not state.player_turn
                
                score, _ = alpha_beta_search(new_state, depth - 1, alpha, beta, True)
                
                if score < best_score:
                    best_score = score
                    best_move = move
                    
                beta = min(beta, best_score)
                if beta <= alpha: break
            return (best_score, best_move)

    def evaluate_state(state, player):
        """
        Evaluates the state of the board for the given player.
        Combines piece count, path distance, and center control into a weighted score.
        """
        opponent = 3 - player  # 2 if player is 1, 1 if player is 2
        board = state.board
        size = len(board)
        
        # Count pieces
        player_pieces = sum(row.count(player) for row in board)
        opponent_pieces = sum(row.count(opponent) for row in board)
        score = player_pieces - opponent_pieces
        
        # Path distance
        player_distance = shortest_path_distance(board, player)
        opponent_distance = shortest_path_distance(board, opponent)
        
        if player_distance == float('inf'):
            path_score = -50
        elif opponent_distance == float('inf'):
            path_score = 50
        else:
            path_score = opponent_distance - player_distance
        
        # Center control
        center = size // 2
        player_center_control = sum(1 for r in range(size) for c in range(size) 
                                   if board[r][c] == player and abs(r-center) + abs(c-center) <= center)
        opponent_center_control = sum(1 for r in range(size) for c in range(size) 
                                     if board[r][c] == opponent and abs(r-center) + abs(c-center) <= center)
        
        center_score = (player_center_control - opponent_center_control) * 2
        
        # Avoid redundant moves
        redundant_moves_penalty = 0
        for r in range(size):
            for c in range(size):
                if board[r][c] == 0 and is_redundant_move(board, r, c, player):
                    redundant_moves_penalty -= 5
        
        # Combine scores with weights
        return score * 10 + path_score * 30 + center_score * 20 + redundant_moves_penalty

    def is_redundant_move(board, row, col, player):
        """
        Checks if placing a piece at (row, col) would create a redundant connection
        (i.e., connecting pieces that are already connected through another path)
        """
        size = len(board)
        
        # Find adjacent player cells
        adjacent_player_cells = []
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player:
                adjacent_player_cells.append((nr, nc))
        
        # If there are fewer than 2 adjacent player pieces, it's not redundant
        if len(adjacent_player_cells) < 2:
            return False
        
        # Check if any pair of adjacent player cells are already connected
        for i in range(len(adjacent_player_cells)):
            for j in range(i + 1, len(adjacent_player_cells)):
                r1, c1 = adjacent_player_cells[i]
                r2, c2 = adjacent_player_cells[j]
                
                # Check if there's a path connecting these cells
                # Create a temporary board without the empty cell we're evaluating
                temp_board = [row[:] for row in board]
                if has_connection(temp_board, r1, c1, r2, c2, player):
                    return True
        
        return False
    
    def has_connection(board, start_row, start_col, end_row, end_col, player):
        """
        Checks if there's a path of the player's pieces from (start_row, start_col)
        to (end_row, end_col)
        """
        size = len(board)
        visited = [[False for _ in range(size)] for _ in range(size)]
        
        def dfs(r, c):
            if r == end_row and c == end_col:
                return True
                
            visited[r][c] = True
            
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if (0 <= nr < size and 0 <= nc < size and 
                    board[nr][nc] == player and not visited[nr][nc]):
                    if dfs(nr, nc):
                        return True
            
            return False
        
        return dfs(start_row, start_col)

    def shortest_path_distance(board, player):
        """
        Calculates the shortest path distance for the given player to connect their sides.
        """
        size = len(board)
        
        if player == 1:
            top_pieces = any(board[0][c] == player for c in range(size))
            bottom_pieces = any(board[size-1][c] == player for c in range(size))
            
            if not (top_pieces and bottom_pieces):
                min_distance = size
            else:
                empty_count = sum(1 for r in range(1, size-1) for c in range(size) if board[r][c] == 0)
                min_distance = empty_count // size
        else:
            left_pieces = any(board[r][0] == player for r in range(size))
            right_pieces = any(board[r][size-1] == player for r in range(size))
            
            if not (left_pieces and right_pieces):
                min_distance = size
            else:
                empty_count = sum(1 for r in range(size) for c in range(1, size-1) if board[r][c] == 0)
                min_distance = empty_count // size
        
        return min_distance if min_distance > 0 else 1

    def get_valid_moves(state):
        """
        Returns a list of all valid moves for the current player.
        """
        return [(row, col) for row in range(len(state.board)) 
                for col in range(len(state.board)) 
                if state.board[row][col] == 0]

    def clone_state(state):
        """
        Creates a deep copy of the given state.
        """
        new_state = HexState(len(state.board), state.player_turn)
        new_state.board = [row[:] for row in state.board]
        return new_state

    def find_best_move(state, depth=3):
        """
        Finds the best move for the current player using alpha-beta pruning.
        """
        player = 1 if state.is_black_turn else 2
        size = len(state.board)
        empty_count = sum(row.count(0) for row in state.board)
        
        # First move - play near center
        if empty_count == size * size:
            center = size // 2
            offset = random.choice([-1, 0, 1])
            return (center + offset, center)
        
        # Swap rule check
        if empty_count == size * size - 1 and player == 2:
            for r in range(size):
                for c in range(size):
                    if state.board[r][c] == 1:
                        center = size // 2
                        if abs(r - center) <= 1 and abs(c - center) <= 1:
                            return (c, r)
        
        # Use C++ implementation if available
        if USE_CPP_IMPLEMENTATION:
            cpp_board = hex_cpp.HexBoard(size)
            cpp_board.set_board(state.board)
            cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
            row, col = hex_cpp.find_best_move(cpp_board, depth, cpp_player)
            return (row, col)
        else:
            _, best_move = alpha_beta_search(state, depth, float('-inf'), float('inf'), state.is_black_turn)
            return best_move if best_move else (-1, -1)

def check_win(board, player):
    """
    Checks if the given player has won the game.
    """
    if USE_CPP_IMPLEMENTATION:
        cpp_board = hex_cpp.HexBoard(len(board))
        cpp_board.set_board(board)
        cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
        return cpp_board.check_win(cpp_player)
    else:
        return has_winning_path(board, player)
