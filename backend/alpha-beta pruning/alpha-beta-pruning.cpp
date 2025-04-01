#include <iostream>
#include <vector>
#include <algorithm>
#include <climits>
#include <unordered_set>

// Cell states: Empty (0), Player 1 (1), Player 2 (2)
enum Player { EMPTY = 0, PLAYER1 = 1, PLAYER2 = 2 };

class HexBoard {
private:
    int size;
    std::vector<std::vector<Player>> board;
    
    // Union-Find data structure for checking connections
    std::vector<int> parent;
    std::vector<int> rank;
    
    int find(int x) {
        if (parent[x] != x)
            parent[x] = find(parent[x]);
        return parent[x];
    }
    
    void unionSets(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        
        if (rootX == rootY) return;
        
        if (rank[rootX] < rank[rootY])
            parent[rootX] = rootY;
        else if (rank[rootX] > rank[rootY])
            parent[rootY] = rootX;
        else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
    }
    
    // Check if there's a path from top to bottom for Player 1
    // or from left to right for Player 2
    bool hasWon(Player player) {
        if (player == EMPTY) return false;
        
        // Reset the Union-Find data structure
        for (int i = 0; i < parent.size(); i++) {
            parent[i] = i;
            rank[i] = 0;
        }
        
        // Connect adjacent cells of the same color
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player) {
                    // Check six directions (hex grid)
                    static const int dx[] = {-1, -1, 0, 0, 1, 1};
                    static const int dy[] = {0, 1, -1, 1, -1, 0};
                    
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
        
        // Check for connection
        if (player == PLAYER1) {
            // Check if any top cell is connected to any bottom cell
            for (int j = 0; j < size; j++) {
                if (board[0][j] != PLAYER1) continue;
                
                for (int k = 0; k < size; k++) {
                    if (board[size-1][k] == PLAYER1 && 
                        find(0 * size + j) == find((size-1) * size + k)) {
                        return true;
                    }
                }
            }
        } else { // PLAYER2
            // Check if any left cell is connected to any right cell
            for (int i = 0; i < size; i++) {
                if (board[i][0] != PLAYER2) continue;
                
                for (int k = 0; k < size; k++) {
                    if (board[k][size-1] == PLAYER2 && 
                        find(i * size + 0) == find(k * size + (size-1))) {
                        return true;
                    }
                }
            }
        }
        
        return false;
    }

public:
    HexBoard(int s) : size(s) {
        board.resize(size, std::vector<Player>(size, EMPTY));
        parent.resize(size * size);
        rank.resize(size * size, 0);
        
        // Initialize parent array
        for (int i = 0; i < size * size; i++) {
            parent[i] = i;
        }
    }
    
    bool makeMove(int row, int col, Player player) {
        if (row < 0 || row >= size || col < 0 || col >= size || board[row][col] != EMPTY) {
            return false;
        }
        
        board[row][col] = player;
        return true;
    }
    
    void undoMove(int row, int col) {
        if (row >= 0 && row < size && col >= 0 && col < size) {
            board[row][col] = EMPTY;
        }
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
    
    bool isGameOver() const {
        // Check if either player has won
        for (int player = PLAYER1; player <= PLAYER2; player++) {
            if (const_cast<HexBoard*>(this)->hasWon(static_cast<Player>(player))) {
                return true;
            }
        }
        
        // Check if board is full
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == EMPTY) {
                    return false;
                }
            }
        }
        
        return true;
    }
    
    int evaluate(Player maximizingPlayer) const {
        // Check if game is won
        if (const_cast<HexBoard*>(this)->hasWon(maximizingPlayer)) {
            return 1000;
        }
        
        Player opponent = (maximizingPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        if (const_cast<HexBoard*>(this)->hasWon(opponent)) {
            return -1000;
        }
        
        // If no winner yet, use heuristic evaluation
        return evaluatePosition(maximizingPlayer) - evaluatePosition(opponent);
    }
    
    // Simple heuristic: count number of connected groups and their sizes
    int evaluatePosition(Player player) const {
        if (player == EMPTY) return 0;
        
        std::vector<std::vector<bool>> visited(size, std::vector<bool>(size, false));
        int score = 0;
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player && !visited[i][j]) {
                    int groupSize = dfs(i, j, player, visited);
                    score += groupSize * groupSize; // Square the size to favor larger groups
                }
            }
        }
        
        return score;
    }
    
    int dfs(int i, int j, Player player, std::vector<std::vector<bool>>& visited) const {
        if (i < 0 || i >= size || j < 0 || j >= size || 
            visited[i][j] || board[i][j] != player) {
            return 0;
        }
        
        visited[i][j] = true;
        int count = 1;
        
        // Check six directions (hex grid)
        static const int dx[] = {-1, -1, 0, 0, 1, 1};
        static const int dy[] = {0, 1, -1, 1, -1, 0};
        
        for (int k = 0; k < 6; k++) {
            int ni = i + dx[k];
            int nj = j + dy[k];
            count += dfs(ni, nj, player, visited);
        }
        
        return count;
    }
    
    void print() const {
        for (int i = 0; i < size; i++) {
            // Print leading spaces for this row
            for (int s = 0; s < i; s++) {
                std::cout << " ";
            }
            
            for (int j = 0; j < size; j++) {
                char symbol;
                switch (board[i][j]) {
                    case EMPTY: symbol = '.'; break;
                    case PLAYER1: symbol = 'X'; break;
                    case PLAYER2: symbol = 'O'; break;
                }
                std::cout << symbol;
                if (j < size - 1) std::cout << " ";
            }
            std::cout << std::endl;
        }
    }
    
    int getSize() const {
        return size;
    }
};

// Alpha-Beta pruning algorithm for Hex
int alphabeta(HexBoard& board, int depth, int alpha, int beta, bool maximizingPlayer, Player currentPlayer) {
    // Terminal node or depth limit reached
    if (depth == 0 || board.isGameOver()) {
        return board.evaluate(currentPlayer);
    }
    
    std::vector<std::pair<int, int>> possibleMoves = board.getEmptyCells();
    
    if (maximizingPlayer) {
        int value = INT_MIN;
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, currentPlayer);
            value = std::max(value, alphabeta(board, depth - 1, alpha, beta, false, currentPlayer));
            board.undoMove(move.first, move.second);
            
            alpha = std::max(alpha, value);
            if (beta <= alpha) {
                break; // Beta cutoff
            }
        }
        return value;
    } else {
        int value = INT_MAX;
        Player opponent = (currentPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, opponent);
            value = std::min(value, alphabeta(board, depth - 1, alpha, beta, true, currentPlayer));
            board.undoMove(move.first, move.second);
            
            beta = std::min(beta, value);
            if (beta <= alpha) {
                break; // Alpha cutoff
            }
        }
        return value;
    }
}

std::pair<int, int> findBestMove(HexBoard& board, int depth, Player player) {
    int bestValue = INT_MIN;
    std::pair<int, int> bestMove = {-1, -1};
    
    std::vector<std::pair<int, int>> possibleMoves = board.getEmptyCells();
    
    for (const auto& move : possibleMoves) {
        board.makeMove(move.first, move.second, player);
        int moveValue = alphabeta(board, depth - 1, INT_MIN, INT_MAX, false, player);
        board.undoMove(move.first, move.second);
        
        if (moveValue > bestValue) {
            bestValue = moveValue;
            bestMove = move;
        }
    }
    
    return bestMove;
}

int main() {
    int boardSize = 5; // Use a smaller board for faster computation
    int searchDepth = 3;
    
    HexBoard hexBoard(boardSize);
    
    // Example: Make a few moves
    hexBoard.makeMove(0, 0, PLAYER1);
    hexBoard.makeMove(1, 1, PLAYER2);
    
    std::cout << "Current board state:" << std::endl;
    hexBoard.print();
    
    // Find best move for Player 1
    auto bestMove = findBestMove(hexBoard, searchDepth, PLAYER1);
    
    std::cout << "Best move for Player 1: (" << bestMove.first << ", " << bestMove.second << ")" << std::endl;
    
    // Make the move
    hexBoard.makeMove(bestMove.first, bestMove.second, PLAYER1);
    
    std::cout << "Board after move:" << std::endl;
    hexBoard.print();
    
    return 0;
}
