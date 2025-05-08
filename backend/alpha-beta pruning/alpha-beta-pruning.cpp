// File: alpha-beta-pruning.cpp
// Implementation of Hex game AI using alpha-beta pruning algorithm with optimizations
// including transposition table, move ordering, and virtual connection detection

#include <iostream>
#include <vector>
#include <algorithm>
#include <climits>
#include <unordered_map>
#include <random>
#include <chrono>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// Player enum represents the state of a cell on the board
enum Player { EMPTY = 0, PLAYER1 = 1, PLAYER2 = 2 };

// Hex grid neighbor directions (6 neighbors)
const int dx[] = {-1, -1, 0, 0, 1, 1};
const int dy[] = {0, 1, -1, 1, -1, 0};

// Hash function for the board state to use in transposition table
struct BoardHash {
    std::size_t operator()(const std::vector<std::vector<int>>& board) const {
        std::size_t seed = board.size();
        for (const auto& row : board) {
            for (int cell : row) {
                seed ^= cell + 0x9e3779b9 + (seed << 6) + (seed >> 2);
            }
        }
        return seed;
    }
};

// Transposition table entry
struct TTEntry {
    int depth;      // Depth of the search
    int value;      // Evaluation value
    int flag;       // Flag for the type of node (0=exact, 1=lower bound, 2=upper bound)
};

// Global transposition table to cache search results
std::unordered_map<std::vector<std::vector<int>>, TTEntry, BoardHash> transpositionTable;

class HexBoard {
private:
    int size;
    std::vector<std::vector<Player>> board;
    
    // Union-Find data structures for path detection
    std::vector<int> parent;
    std::vector<int> rank;
    
    // Cache for virtual connections
    mutable std::unordered_map<std::string, bool> vcCache;
    
    // Random number generator for move selection
    mutable std::mt19937 rng;
    
    // Union-Find helper methods
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }
    
    void unionSets(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        
        if (rootX == rootY) return;
        
        if (rank[rootX] < rank[rootY]) {
            parent[rootX] = rootY;
        }
        else if (rank[rootX] > rank[rootY]) {
            parent[rootY] = rootX;
        }
        else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
    }
    
    // Virtual connection detection
    bool hasVirtualConnection(int startRow, int startCol, int endRow, int endCol, Player player) const {
        std::string key = std::to_string(startRow) + "," + 
                          std::to_string(startCol) + "," + 
                          std::to_string(endRow) + "," + 
                          std::to_string(endCol) + "," + 
                          std::to_string(player);
        
        if (vcCache.find(key) != vcCache.end()) {
            return vcCache[key];
        }
        
        if (startRow == endRow && startCol == endCol && board[startRow][startCol] == player) {
            vcCache[key] = true;
            return true;
        }
        
        std::vector<std::vector<bool>> visited(size, std::vector<bool>(size, false));
        bool result = checkVCPath(startRow, startCol, endRow, endCol, player, visited);
        
        vcCache[key] = result;
        return result;
    }
    
    bool checkVCPath(int r, int c, int targetR, int targetC, Player player, 
                    std::vector<std::vector<bool>>& visited) const {
        if (r < 0 || r >= size || c < 0 || c >= size || visited[r][c]) {
            return false;
        }
        
        if (r == targetR && c == targetC) {
            return board[r][c] == player;
        }
        
        if (board[r][c] != player && board[r][c] != EMPTY) {
            return false;
        }
        
        visited[r][c] = true;
        
        for (int k = 0; k < 6; k++) {
            int nr = r + dx[k];
            int nc = c + dy[k];
            
            if (checkVCPath(nr, nc, targetR, targetC, player, visited)) {
                return true;
            }
        }
        
        return false;
    }
    
    // Check if a move is redundant (connecting already connected pieces)
    bool isRedundantMove(int row, int col, Player player) const {
        std::vector<std::pair<int, int>> adjacentPlayerCells;
        for (int k = 0; k < 6; k++) {
            int nr = row + dx[k];
            int nc = col + dy[k];
            
            if (nr >= 0 && nr < size && nc >= 0 && nc < size && board[nr][nc] == player) {
                adjacentPlayerCells.push_back({nr, nc});
            }
        }
        
        // If there are fewer than 2 adjacent player pieces, it's not redundant
        if (adjacentPlayerCells.size() < 2) {
            return false;
        }
        
        // Check if any pair of adjacent player cells are already connected
        for (size_t i = 0; i < adjacentPlayerCells.size(); i++) {
            for (size_t j = i + 1; j < adjacentPlayerCells.size(); j++) {
                int r1 = adjacentPlayerCells[i].first;
                int c1 = adjacentPlayerCells[i].second;
                int r2 = adjacentPlayerCells[j].first;
                int c2 = adjacentPlayerCells[j].second;
                
                if (hasVirtualConnection(r1, c1, r2, c2, player)) {
                    return true;
                }
            }
        }
        
        return false;
    }

public:
    HexBoard(int s) : size(s) {
        // Initialize the board
        board.resize(size, std::vector<Player>(size, EMPTY));
        
        // Initialize Union-Find data structures for size*size cells + 4 virtual nodes
        parent.resize(size * size + 4);
        rank.resize(size * size + 4, 0);
        
        for (int i = 0; i < size * size + 4; i++) {
            parent[i] = i;
        }
        
        // Initialize random number generator with time-based seed
        rng.seed(std::chrono::system_clock::now().time_since_epoch().count());
    }
    
    void setBoard(const std::vector<std::vector<int>>& pyBoard) {
        if (pyBoard.size() != size || pyBoard[0].size() != size) {
            throw std::invalid_argument("Board size mismatch");
        }
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                board[i][j] = static_cast<Player>(pyBoard[i][j]);
            }
        }
        
        vcCache.clear();
    }
    
    std::vector<std::vector<int>> getBoard() const {
        std::vector<std::vector<int>> result(size, std::vector<int>(size));
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                result[i][j] = static_cast<int>(board[i][j]);
            }
        }
        return result;
    }
    
    bool makeMove(int row, int col, Player player) {
        if (row < 0 || row >= size || col < 0 || col >= size || board[row][col] != EMPTY) {
            return false;
        }
        
        board[row][col] = player;
        vcCache.clear();
        return true;
    }
    
    void undoMove(int row, int col) {
        if (row >= 0 && row < size && col >= 0 && col < size) {
            board[row][col] = EMPTY;
            vcCache.clear();
        }
    }
    
    bool hasWon(Player player) {
        if (player == EMPTY) return false;
        
        // Initialize Union-Find data structures
        for (int i = 0; i < parent.size(); i++) {
            parent[i] = i;
            rank[i] = 0;
        }
        
        // Define 4 virtual nodes:
        int topVirtual = size * size;      // For Blue's top edge
        int bottomVirtual = size * size + 1; // For Blue's bottom edge
        int leftVirtual = size * size + 2;   // For Red's left edge
        int rightVirtual = size * size + 3;  // For Red's right edge
        
        // Connect all player's pieces
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player) {
                    // Connect to appropriate virtual nodes if on the edge
                    if (player == PLAYER1) {  // Blue player
                        if (i == 0) {  // Top row
                            unionSets(i * size + j, topVirtual);
                        }
                        if (i == size-1) {  // Bottom row
                            unionSets(i * size + j, bottomVirtual);
                        }
                    } else if (player == PLAYER2) {  // Red player
                        if (j == 0) {  // Leftmost column
                            unionSets(i * size + j, leftVirtual);
                        }
                        if (j == size-1) {  // Rightmost column
                            unionSets(i * size + j, rightVirtual);
                        }
                    }
                    
                    // Connect to adjacent cells of the same player
                    for (int k = 0; k < 6; k++) {
                        int ni = i + dx[k];
                        int nj = j + dy[k];
                        
                        if (ni >= 0 && ni < size && nj >= 0 && nj < size && 
                            board[ni][nj] == player) {
                            unionSets(i * size + j, ni * size + nj);
                        }
                    }
                }
            }
        }
        
        // Check if virtual nodes are connected
        if (player == PLAYER1) {
            return find(topVirtual) == find(bottomVirtual);
        } else if (player == PLAYER2) {
            return find(leftVirtual) == find(rightVirtual);
        }
        
        return false;
    }
    
    bool checkWin(Player player) const {
        return const_cast<HexBoard*>(this)->hasWon(player);
    }
    
    std::vector<std::pair<int, int>> getEmptyCells() const {
        std::vector<std::pair<int, int>> emptyCells;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == EMPTY) {
                    emptyCells.emplace_back(i, j);
                }
            }
        }
        return emptyCells;
    }
    
    std::vector<std::pair<int, int>> getOrderedMoves(Player player) const {
        std::vector<std::pair<std::pair<int, int>, int>> scoredMoves;
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == EMPTY) {
                    int score = calculateMoveScore(i, j, player);
                    scoredMoves.push_back({{i, j}, score});
                }
            }
        }
        
        // Sort by score in descending order
        std::sort(scoredMoves.begin(), scoredMoves.end(), 
                 [](const auto& a, const auto& b) { return a.second > b.second; });
                 
        std::vector<std::pair<int, int>> orderedMoves;
        for (const auto& scoredMove : scoredMoves) {
            orderedMoves.push_back(scoredMove.first);
        }
        
        return orderedMoves;
    }
    
    int calculateMoveScore(int row, int col, Player player) const {
        int score = 0;
        
        // Create a temporary board to test the move
        HexBoard tempBoard = *this;
        tempBoard.makeMove(row, col, player);
        
        // Check if this is a winning move
        if (tempBoard.checkWin(player)) {
            return 10000;  // Highest score for winning moves
        }
        
        // Check if this move would block opponent's win
        Player opponent = (player == PLAYER1) ? PLAYER2 : PLAYER1;
        bool isBlockingWin = false;
        
        for (const auto& cell : getEmptyCells()) {
            if (cell.first == row && cell.second == col) {
                continue;
            }
            
            tempBoard.undoMove(row, col);
            tempBoard.makeMove(cell.first, cell.second, opponent);
            
            if (tempBoard.checkWin(opponent)) {
                isBlockingWin = true;
            }
            
            tempBoard.undoMove(cell.first, cell.second);
            tempBoard.makeMove(row, col, player);
            
            if (isBlockingWin) {
                break;
            }
        }
        
        if (isBlockingWin) {
            return 9000;  // Very high score for blocking moves
        }
        
        // Check if the move would be redundant
        if (isRedundantMove(row, col, player)) {
            score -= 15;  // Penalize redundant moves
        }
        
        // Count adjacent pieces of the same color (connectivity focus)
        int adjacentPlayerPieces = 0;
        int secondOrderConnections = 0;  // Pieces that would be connected through this move
        
        for (int k = 0; k < 6; k++) {
            int nr = row + dx[k];
            int nc = col + dy[k];
            
            if (nr >= 0 && nr < size && nc >= 0 && nc < size) {
                if (board[nr][nc] == player) {
                    adjacentPlayerPieces++;
                    
                    // Check if this piece connects to other player pieces
                    for (int l = 0; l < 6; l++) {
                        if (k == l) continue; // Skip the original direction
                        
                        int nr2 = row + dx[l];
                        int nc2 = col + dy[l];
                        
                        if (nr2 >= 0 && nr2 < size && nc2 >= 0 && nc2 < size && 
                            board[nr2][nc2] == player) {
                            secondOrderConnections++;
                        }
                    }
                } 
                else if (board[nr][nc] == EMPTY) {
                    score += 1;  // Small bonus for potential future connections
                }
            }
        }
        
        // Strongly prioritize moves that connect existing pieces
        score += adjacentPlayerPieces * 20;
        
        // Extra bonus for moves that connect multiple groups
        score += secondOrderConnections * 5;
        
        // Direction-based strategic scoring
        if (player == PLAYER1) {  // Blue player wants to connect top-bottom
            // Prefer central columns for flexibility
            score += (size - std::abs(col - size/2)) * 2;
            
            // Bonus for pieces on the edges the player wants to connect
            if (row == 0 || row == size-1) {
                score += 15;  // Increased from 5 to emphasize edge connections
            }
            
            // Progressive bonus for advancing toward the opposite edge
            if (row > 0 && row < size-1) {
                score += row * 2;  // Increasing bonus as we move toward bottom
            }
        } 
        else {  // Red player wants to connect left-right
            // Prefer central rows for flexibility
            score += (size - std::abs(row - size/2)) * 2;
            
            // Bonus for pieces on the edges the player wants to connect
            if (col == 0 || col == size-1) {
                score += 15;  // Increased from 5 to emphasize edge connections
            }
            
            // Progressive bonus for advancing toward the opposite edge
            if (col > 0 && col < size-1) {
                score += col * 2;  // Increasing bonus as we move toward right
            }
        }
        
        return score;
    }
    
    int evaluate(Player maximizingPlayer) const {
        // Check for immediate win/loss
        if (checkWin(maximizingPlayer)) {
            return 1000;
        }
        
        Player opponent = (maximizingPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        if (checkWin(opponent)) {
            return -1000;
        }
        
        // Heuristic evaluation
        int playerScore = 0;
        int opponentScore = 0;
        
        // Count piece advantage and edge control
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == maximizingPlayer) {
                    playerScore += 1;
                    
                    // Bonus for edge pieces based on player's goal
                    if ((maximizingPlayer == PLAYER1 && (i == 0 || i == size-1)) ||
                        (maximizingPlayer == PLAYER2 && (j == 0 || j == size-1))) {
                        playerScore += 2;
                    }
                    
                    // Bonus for central positioning
                    int centerDist = std::abs(i - size/2) + std::abs(j - size/2);
                    playerScore += (size - centerDist) / 2;
                    
                    // Bonus for connections
                    for (int k = 0; k < 6; k++) {
                        int ni = i + dx[k];
                        int nj = j + dy[k];
                        
                        if (ni >= 0 && ni < size && nj >= 0 && nj < size && 
                            board[ni][nj] == maximizingPlayer) {
                            playerScore += 1;
                        }
                    }
                } 
                else if (board[i][j] == opponent) {
                    opponentScore += 1;
                    
                    // Bonus for edge pieces based on opponent's goal
                    if ((opponent == PLAYER1 && (i == 0 || i == size-1)) ||
                        (opponent == PLAYER2 && (j == 0 || j == size-1))) {
                        opponentScore += 2;
                    }
                    
                    // Bonus for central positioning
                    int centerDist = std::abs(i - size/2) + std::abs(j - size/2);
                    opponentScore += (size - centerDist) / 2;
                    
                    // Bonus for connections
                    for (int k = 0; k < 6; k++) {
                        int ni = i + dx[k];
                        int nj = j + dy[k];
                        
                        if (ni >= 0 && ni < size && nj >= 0 && nj < size && 
                            board[ni][nj] == opponent) {
                            opponentScore += 1;
                        }
                    }
                }
            }
        }
        
        return playerScore - opponentScore;
    }
    
    int getSize() const {
        return size;
    }
};

int alphabeta(HexBoard& board, int depth, int alpha, int beta, bool maximizingPlayer, 
              Player currentPlayer, bool useCache = true) {
    // Check for terminal states
    if (board.checkWin(currentPlayer)) {
        return 1000;  // Win for current player
    }
    
    Player opponent = (currentPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
    if (board.checkWin(opponent)) {
        return -1000;  // Loss for current player
    }
    
    // Check transposition table if caching is enabled
    if (useCache) {
        std::vector<std::vector<int>> boardState = board.getBoard();
        
        auto it = transpositionTable.find(boardState);
        if (it != transpositionTable.end() && it->second.depth >= depth) {
            TTEntry entry = it->second;
            if (entry.flag == 0) {
                return entry.value;  // Exact value
            } else if (entry.flag == 1) {
                alpha = std::max(alpha, entry.value);  // Lower bound
            } else if (entry.flag == 2) {
                beta = std::min(beta, entry.value);  // Upper bound
            }
            
            if (alpha >= beta) {
                return entry.value;
            }
        }
    }
    
    // Reached the depth limit, evaluate the position
    if (depth == 0) {
        return board.evaluate(currentPlayer);
    }
    
    // Get possible moves ordered by heuristic evaluation
    std::vector<std::pair<int, int>> possibleMoves;
    
    if (maximizingPlayer) {
        possibleMoves = board.getOrderedMoves(currentPlayer);
    } else {
        possibleMoves = board.getOrderedMoves(opponent);
    }
    
    // No moves available
    if (possibleMoves.empty()) {
        return board.evaluate(currentPlayer);
    }
    
    int originalAlpha = alpha;
    int value;
    int flag = 0;
    
    if (maximizingPlayer) {
        value = INT_MIN;
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, currentPlayer);
            
            // Check for immediate win
            if (board.checkWin(currentPlayer)) {
                board.undoMove(move.first, move.second);
                return 1000;
            }
            
            int childValue = alphabeta(board, depth - 1, alpha, beta, false, currentPlayer, useCache);
            board.undoMove(move.first, move.second);
            
            value = std::max(value, childValue);
            alpha = std::max(alpha, value);
            
            if (alpha >= beta) {
                break;  // Beta cutoff
            }
        }
        
        // Set flag for transposition table entry
        if (value <= originalAlpha) {
            flag = 2;  // Upper bound
        } else if (value >= beta) {
            flag = 1;  // Lower bound
        } else {
            flag = 0;  // Exact value
        }
    } else {
        value = INT_MAX;
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, opponent);
            
            // Check for immediate loss
            if (board.checkWin(opponent)) {
                board.undoMove(move.first, move.second);
                return -1000;
            }
            
            int childValue = alphabeta(board, depth - 1, alpha, beta, true, currentPlayer, useCache);
            board.undoMove(move.first, move.second);
            
            value = std::min(value, childValue);
            beta = std::min(beta, value);
            
            if (beta <= alpha) {
                break;  // Alpha cutoff
            }
        }
        
        // Set flag for transposition table entry
        if (value <= originalAlpha) {
            flag = 2;  // Upper bound
        } else if (value >= beta) {
            flag = 1;  // Lower bound
        } else {
            flag = 0;  // Exact value
        }
    }
    
    // Store result in transposition table if caching is enabled
    if (useCache) {
        std::vector<std::vector<int>> boardState = board.getBoard();
        transpositionTable[boardState] = {depth, value, flag};
    }
    
    return value;
}

std::pair<int, int> findBestMove(HexBoard& board, int maxDepth, Player player) {
    // Clear transposition table for a fresh search
    transpositionTable.clear();
    
    std::pair<int, int> bestMove = {-1, -1};
    int size = board.getSize();
    
    // Check for empty board - play in center
    bool emptyBoard = true;
    for (const auto& move : board.getEmptyCells()) {
        if (board.getBoard()[move.first][move.second] != EMPTY) {
            emptyBoard = false;
            break;
        }
    }
    
    if (emptyBoard) {
        int center = size / 2;
        return {center, center};
    }
    
    // First, check for immediate winning moves
    std::vector<std::pair<int, int>> possibleMoves = board.getOrderedMoves(player);
    for (const auto& move : possibleMoves) {
        board.makeMove(move.first, move.second, player);
        if (board.checkWin(player)) {
            board.undoMove(move.first, move.second);
            return move;
        }
        board.undoMove(move.first, move.second);
    }
    
    // Next, check for immediate blocking moves
    Player opponent = (player == PLAYER1) ? PLAYER2 : PLAYER1;
    for (const auto& move : possibleMoves) {
        board.makeMove(move.first, move.second, opponent);
        if (board.checkWin(opponent)) {
            board.undoMove(move.first, move.second);
            return move;
        }
        board.undoMove(move.first, move.second);
    }
    
    // Use iterative deepening to find the best move
    for (int currentDepth = 1; currentDepth <= maxDepth; currentDepth++) {
        int bestValue = INT_MIN;
        std::pair<int, int> tempBestMove = {-1, -1};
        
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, player);
            
            // Early exit for winning moves
            if (board.checkWin(player)) {
                board.undoMove(move.first, move.second);
                return move;
            }
            
            int moveValue = alphabeta(board, currentDepth - 1, INT_MIN, INT_MAX, false, player, true);
            board.undoMove(move.first, move.second);
            
            if (moveValue > bestValue) {
                bestValue = moveValue;
                tempBestMove = move;
            }
        }
        
        if (tempBestMove.first != -1) {
            bestMove = tempBestMove;
        }
        
        // Exit early if we found a winning move sequence
        if (bestValue >= 900) {
            break;
        }
    }
    
    // If no good move found (shouldn't happen), select a random valid move
    if (bestMove.first == -1 && !possibleMoves.empty()) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<size_t> dist(0, possibleMoves.size() - 1);
        bestMove = possibleMoves[dist(gen)];
    }
    
    return bestMove;
}

PYBIND11_MODULE(hex_cpp, m) {
    m.doc() = "C++ implementation of Hex game with alpha-beta pruning AI";
    
    py::enum_<Player>(m, "Player")
        .value("EMPTY", Player::EMPTY)
        .value("PLAYER1", Player::PLAYER1)
        .value("PLAYER2", Player::PLAYER2)
        .export_values();
    
    py::class_<HexBoard>(m, "HexBoard")
        .def(py::init<int>())
        .def("set_board", &HexBoard::setBoard)
        .def("get_board", &HexBoard::getBoard)
        .def("make_move", &HexBoard::makeMove)
        .def("undo_move", &HexBoard::undoMove)
        .def("get_empty_cells", &HexBoard::getEmptyCells)
        .def("check_win", &HexBoard::checkWin)
        .def("get_size", &HexBoard::getSize);
    
    m.def("find_best_move", &findBestMove, 
          py::arg("board"), py::arg("depth") = 3, py::arg("player") = Player::PLAYER1,
          "Find the best move using alpha-beta pruning with iterative deepening");
    
    m.def("alphabeta", &alphabeta,
          py::arg("board"), py::arg("depth"), py::arg("alpha"), py::arg("beta"),
          py::arg("maximizingPlayer"), py::arg("currentPlayer"), py::arg("useCache") = true,
          "Alpha-beta pruning algorithm with transposition table");
}
