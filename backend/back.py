import sys
import copy
import random
from collections import deque

try:
    import hex_cpp
    USE_CPP_IMPLEMENTATION = True
    print("Using C++ alpha-beta pruning implementation")
except ImportError:
    USE_CPP_IMPLEMENTATION = False
    print("C++ implementation not found, using Python implementation")

class HexState:
    def __init__(self, size, is_black_turn):
        self.board = [[0] * size for _ in range(size)]
        self.size = size
        self.is_black_turn = is_black_turn
    
    def copy(self):
        new_state = HexState(self.size, self.is_black_turn)
        new_state.board = [row[:] for row in self.board]
        return new_state

if not USE_CPP_IMPLEMENTATION:
    def evaluate(state):
        red_win = has_winning_path(state.board, 1)
        blue_win = has_winning_path(state.board, 2)
        
        if red_win:
            return 1000 if state.is_black_turn else -1000
        if blue_win:
            return -1000 if state.is_black_turn else 1000
        
        return connectivity_heuristic(state)
    
    def connectivity_heuristic(state):
        red_score = count_connected_components(state.board, 1)
        blue_score = count_connected_components(state.board, 2)
        
        return red_score - blue_score if state.is_black_turn else blue_score - red_score
    
    def count_connected_components(board, player):
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
        size = len(board)
        queue = deque([(row, col)])
        visited.add((row, col))
        
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
    
    def has_winning_path(board, player):
        size = len(board)
        visited = [[False for _ in range(size)] for _ in range(size)]
        
        if player == 1:
            for col in range(size):
                if (board[0][col] == player or (col == 0 or col == size-1)) and not visited[0][col]:
                    if dfs_path(board, 0, col, player, visited, 1):
                        return True
        else:
            for row in range(size):
                if (board[row][0] == player or (row == 0 or row == size-1)) and not visited[row][0]:
                    if dfs_path(board, row, 0, player, visited, 2):
                        return True
        
        return False
    
    def dfs_path(board, row, col, player, visited, direction):
        size = len(board)
        
        if direction == 1 and row == size - 1:
            return board[row][col] == player or col == 0 or col == size-1
        elif direction == 2 and col == size - 1:
            return board[row][col] == player or row == 0 or row == size-1
            
        if board[row][col] != player and not ((row == 0 or row == size-1) and (col == 0 or col == size-1)):
            return False
            
        visited[row][col] = True
        
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and not visited[nr][nc]:
                if board[nr][nc] == player or ((nr == 0 or nr == size-1) and (nc == 0 or nc == size-1)):
                    if dfs_path(board, nr, nc, player, visited, direction):
                        return True
        
        return False
    
    def is_terminal(state):
        return has_winning_path(state.board, 1) or has_winning_path(state.board, 2)
    
    def generate_moves(state):
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
        player = 1 if maximizing_player else 2
        opponent = 2 if maximizing_player else 1
        
        if check_win(state.board, player):
            return (1000, None)
        if check_win(state.board, opponent):
            return (-1000, None)
        if depth == 0:
            return (evaluate_state(state, player), None)
        
        valid_moves = get_valid_moves(state)
        if not valid_moves:
            return (0, None)
        
        import random
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
                if beta <= alpha:
                    break
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
                if beta <= alpha:
                    break
            return (best_score, best_move)

    def evaluate_state(state, player):
        opponent = 2 if player == 1 else 1
        board = state.board
        size = len(board)
        
        player_pieces = sum(row.count(player) for row in board)
        opponent_pieces = sum(row.count(opponent) for row in board)
        
        score = player_pieces - opponent_pieces
        
        player_distance = shortest_path_distance(board, player)
        opponent_distance = shortest_path_distance(board, opponent)
        
        if player_distance == float('inf'):
            path_score = -50
        elif opponent_distance == float('inf'):
            path_score = 50
        else:
            path_score = opponent_distance - player_distance
        
        center = size // 2
        player_center_control = sum(1 for r in range(size) for c in range(size) 
                                   if board[r][c] == player and abs(r-center) + abs(c-center) <= center)
        opponent_center_control = sum(1 for r in range(size) for c in range(size) 
                                     if board[r][c] == opponent and abs(r-center) + abs(c-center) <= center)
        
        center_score = (player_center_control - opponent_center_control) * 2
        
        final_score = score * 10 + path_score * 30 + center_score * 20
        
        return final_score

    def shortest_path_distance(board, player):
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
        valid_moves = []
        size = len(state.board)
        
        for row in range(size):
            for col in range(size):
                if state.board[row][col] == 0:
                    valid_moves.append((row, col))
                    
        return valid_moves

    def clone_state(state):
        new_state = HexState(len(state.board), state.player_turn)
        new_state.board = [row[:] for row in state.board]
        return new_state

    def find_best_move(state, depth=3):
        player = 1 if state.is_black_turn else 2
        
        size = len(state.board)
        empty_count = sum(row.count(0) for row in state.board)
        
        if empty_count == size * size:
            center = size // 2
            import random
            offset = random.choice([-1, 0, 1])
            return (center + offset, center)
        
        if empty_count == size * size - 1 and player == 2:
            for r in range(size):
                for c in range(size):
                    if state.board[r][c] == 1:
                        center = size // 2
                        if abs(r - center) <= 1 and abs(c - center) <= 1:
                            return (c, r)
        
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
    if USE_CPP_IMPLEMENTATION:
        cpp_board = hex_cpp.HexBoard(len(board))
        cpp_board.set_board(board)
        cpp_player = hex_cpp.Player.PLAYER1 if player == 1 else hex_cpp.Player.PLAYER2
        return cpp_board.check_win(cpp_player)
    else:
        return has_winning_path(board, player)
