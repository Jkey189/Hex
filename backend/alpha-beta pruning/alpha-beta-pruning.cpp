#include <iostream>
#include <vector>
#include <algorithm>
#include <climits>
#include <unordered_set>
#include <unordered_map>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <functional>
#include <string>
#include <cmath>

namespace py = pybind11;

enum Player { EMPTY = 0, PLAYER1 = 1, PLAYER2 = 2 };

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

struct TTEntry {
    int depth;
    int value;
    int flag;
};

std::unordered_map<std::vector<std::vector<int>>, TTEntry, BoardHash> transpositionTable;

class HexBoard {
private:
    int size;
    std::vector<std::vector<Player>> board;
    
    std::vector<int> parent;
    std::vector<int> rank;
    
    int find(int x) {
        if (parent[x] != x){
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }
    
    void unionSets(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        
        if (rootX == rootY) return;
        
        if (rank[rootX] < rank[rootY]){
            parent[rootX] = rootY;
        }
        else if (rank[rootX] > rank[rootY]){
            parent[rootY] = rootX;
        }
        else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
    }
    
    bool hasWon(Player player) {
        if (player == EMPTY) return false;
        
        for (int i = 0; i < parent.size(); i++) {
            parent[i] = i;
            rank[i] = 0;
        }
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player) {
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
        
        if (player == PLAYER1) {
            for (int j = 0; j < size; j++) {
                if (board[0][j] != PLAYER1) {
                    continue;
                }
                
                for (int k = 0; k < size; k++) {
                    if (board[size-1][k] == PLAYER1 && 
                        find(0 * size + j) == find((size-1) * size + k)) {
                        return true;
                    }
                }
            }
        } else {
            for (int i = 0; i < size; i++) {
                if (board[i][0] != PLAYER2) {
                    continue;
                }
                
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

    mutable std::unordered_map<std::string, bool> vcCache;
    
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
        
        static const int dx[] = {-1, -1, 0, 0, 1, 1};
        static const int dy[] = {0, 1, -1, 1, -1, 0};
        
        for (int k = 0; k < 6; k++) {
            int nr = r + dx[k];
            int nc = c + dy[k];
            
            if (checkVCPath(nr, nc, targetR, targetC, player, visited)) {
                return true;
            }
        }
        
        return false;
    }

public:
    HexBoard(int s) : size(s) {
        board.resize(size, std::vector<Player>(size, EMPTY));
        parent.resize(size * size);
        rank.resize(size * size, 0);
        
        for (int i = 0; i < size * size; i++) {
            parent[i] = i;
        }
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
        
        HexBoard tempBoard = *this;
        tempBoard.makeMove(row, col, player);
        if (tempBoard.checkWin(player)) {
            return 10000;
        }
        
        int centerDist = std::abs(row - size/2) + std::abs(col - size/2);
        score += (size - centerDist);
        
        static const int dx[] = {-1, -1, 0, 0, 1, 1};
        static const int dy[] = {0, 1, -1, 1, -1, 0};
        
        int connectionsToSame = 0;
        
        for (int k = 0; k < 6; k++) {
            int nr = row + dx[k];
            int nc = col + dy[k];
            
            if (nr >= 0 && nr < size && nc >= 0 && nc < size) {
                if (board[nr][nc] == player) {
                    connectionsToSame += 3;
                    score += 3;
                } else if (board[nr][nc] == EMPTY) {
                    score += 1;
                }
            }
        }
        
        if (player == PLAYER1) {
            score += (size - std::abs(col - size/2));
        } else {
            score += (size - std::abs(row - size/2));
        }
        
        for (int k = 0; k < 6; k++) {
            int nr1 = row + dx[k];
            int nc1 = col + dy[k];
            
            if (nr1 >= 0 && nr1 < size && nc1 >= 0 && nc1 < size && board[nr1][nc1] == player) {
                for (int l = k+1; l < 6; l++) {
                    int nr2 = row + dx[l];
                    int nc2 = col + dy[l];
                    
                    if (nr2 >= 0 && nr2 < size && nc2 >= 0 && nc2 < size && 
                        board[nr2][nc2] == player) {
                        score += 5;
                    }
                }
            }
        }
        
        if (player == PLAYER1) {
            for (int j = 0; j < size; j++) {
                if (board[0][j] == player) {
                    for (int k = 0; k < size; k++) {
                        if (board[size-1][k] == player && 
                            hasVirtualConnection(0, j, size-1, k, player)) {
                            score += 4;
                        }
                    }
                }
            }
        } else {
            for (int i = 0; i < size; i++) {
                if (board[i][0] == player) {
                    for (int k = 0; k < size; k++) {
                        if (board[k][size-1] == player && 
                            hasVirtualConnection(i, 0, k, size-1, player)) {
                            score += 4;
                        }
                    }
                }
            }
        }
        
        return score;
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
        for (int player = PLAYER1; player <= PLAYER2; player++) {
            if (const_cast<HexBoard*>(this)->hasWon(static_cast<Player>(player))) {
                return true;
            }
        }
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == EMPTY) {
                    return false;
                }
            }
        }
        
        return true;
    }
    
    bool checkWin(Player player) const {
        return const_cast<HexBoard*>(this)->hasWon(player);
    }
    
    int evaluate(Player maximizingPlayer) const {
        if (const_cast<HexBoard*>(this)->hasWon(maximizingPlayer)) {
            return 1000;
        }
        
        Player opponent = (maximizingPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        if (const_cast<HexBoard*>(this)->hasWon(opponent)) {
            return -1000;
        }
        
        return advancedEvaluatePosition(maximizingPlayer);
    }
    
    int advancedEvaluatePosition(Player player) const {
        if (player == EMPTY) return 0;
        
        Player opponent = (player == PLAYER1) ? PLAYER2 : PLAYER1;
        int score = 0;
        
        int playerPieces = 0;
        int opponentPieces = 0;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player) playerPieces++;
                else if (board[i][j] == opponent) opponentPieces++;
            }
        }
        
        std::vector<std::vector<bool>> visited(size, std::vector<bool>(size, false));
        int connectivity = calculateConnectivity(player, visited);
        
        int edgeControl = calculateEdgeControl(player);
        
        int pathLength = calculateShortestPath(player);
        int opponentPathLength = calculateShortestPath(opponent);
        
        score = 10 * connectivity + 
                5 * edgeControl + 
                15 * (opponentPathLength - pathLength) +
                1 * playerPieces;
                
        return score;
    }
    
    int calculateConnectivity(Player player, std::vector<std::vector<bool>>& visited) const {
        int connectivity = 0;
        
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (board[i][j] == player && !visited[i][j]) {
                    int groupSize = dfs(i, j, player, visited);
                    connectivity += groupSize * groupSize;
                }
            }
        }
        
        return connectivity;
    }
    
    int calculateEdgeControl(Player player) const {
        int control = 0;
        
        if (player == PLAYER1) {
            for (int j = 0; j < size; j++) {
                if (board[0][j] == player) control += 3;
                if (board[size-1][j] == player) control += 3;
            }
        } else {
            for (int i = 0; i < size; i++) {
                if (board[i][0] == player) control += 3;
                if (board[i][size-1] == player) control += 3;
            }
        }
        
        return control;
    }
    
    int calculateShortestPath(Player player) const {
        std::vector<std::vector<int>> distance(size, std::vector<int>(size, INT_MAX));
        std::vector<std::pair<int, int>> queue;
        
        if (player == PLAYER1) {
            for (int j = 0; j < size; j++) {
                if (board[0][j] == player || board[0][j] == EMPTY) {
                    distance[0][j] = (board[0][j] == player) ? 0 : 1;
                    queue.push_back({0, j});
                }
            }
        } else {
            for (int i = 0; i < size; i++) {
                if (board[i][0] == player || board[i][0] == EMPTY) {
                    distance[i][0] = (board[i][0] == player) ? 0 : 1;
                    queue.push_back({i, 0});
                }
            }
        }
        
        for (size_t idx = 0; idx < queue.size(); idx++) {
            int r = queue[idx].first;
            int c = queue[idx].second;
            
            static const int dx[] = {-1, -1, 0, 0, 1, 1};
            static const int dy[] = {0, 1, -1, 1, -1, 0};
            
            for (int k = 0; k < 6; k++) {
                int nr = r + dx[k];
                int nc = c + dy[k];
                
                if (nr >= 0 && nr < size && nc >= 0 && nc < size) {
                    int newDist = distance[r][c] + ((board[nr][nc] == player) ? 0 : 1);
                    
                    if (newDist < distance[nr][nc]) {
                        distance[nr][nc] = newDist;
                        queue.push_back({nr, nc});
                    }
                }
            }
        }
        
        int minDist = INT_MAX;
        
        if (player == PLAYER1) {
            for (int j = 0; j < size; j++) {
                minDist = std::min(minDist, distance[size-1][j]);
            }
        } else {
            for (int i = 0; i < size; i++) {
                minDist = std::min(minDist, distance[i][size-1]);
            }
        }
        
        return minDist;
    }
    
    int dfs(int i, int j, Player player, std::vector<std::vector<bool>>& visited) const {
        if (i < 0 || i >= size || j < 0 || j >= size || 
            visited[i][j] || board[i][j] != player) {
            return 0;
        }
        
        visited[i][j] = true;
        int count = 1;
        
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

int alphabeta(HexBoard& board, int depth, int alpha, int beta, bool maximizingPlayer, 
              Player currentPlayer, bool useCache = true) {
    
    if (useCache) {
        std::vector<std::vector<int>> boardState = board.getBoard();
        
        auto it = transpositionTable.find(boardState);
        if (it != transpositionTable.end() && it->second.depth >= depth) {
            TTEntry entry = it->second;
            if (entry.flag == 0) {
                return entry.value;
            } else if (entry.flag == 1) {
                alpha = std::max(alpha, entry.value);
            } else if (entry.flag == 2) {
                beta = std::min(beta, entry.value);
            }
            
            if (alpha >= beta) {
                return entry.value;
            }
        }
    }
    
    if (depth == 0 || board.isGameOver()) {
        return board.evaluate(currentPlayer);
    }
    
    std::vector<std::pair<int, int>> possibleMoves;
    
    if (maximizingPlayer) {
        possibleMoves = board.getOrderedMoves(currentPlayer);
    } else {
        Player opponent = (currentPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        possibleMoves = board.getOrderedMoves(opponent);
    }
    
    int originalAlpha = alpha;
    int value;
    int flag = 0;
    
    if (maximizingPlayer) {
        value = INT_MIN;
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, currentPlayer);
            int childValue = alphabeta(board, depth - 1, alpha, beta, false, currentPlayer, useCache);
            board.undoMove(move.first, move.second);
            
            value = std::max(value, childValue);
            alpha = std::max(alpha, value);
            
            if (alpha >= beta) {
                break;
            }
        }
        
        if (value <= originalAlpha) {
            flag = 2;
        } else if (value >= beta) {
            flag = 1;
        } else {
            flag = 0;
        }
    } else {
        value = INT_MAX;
        Player opponent = (currentPlayer == PLAYER1) ? PLAYER2 : PLAYER1;
        
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, opponent);
            int childValue = alphabeta(board, depth - 1, alpha, beta, true, currentPlayer, useCache);
            board.undoMove(move.first, move.second);
            
            value = std::min(value, childValue);
            beta = std::min(beta, value);
            
            if (beta <= alpha) {
                break;
            }
        }
        
        if (value <= originalAlpha) {
            flag = 2;
        } else if (value >= beta) {
            flag = 1;
        } else {
            flag = 0;
        }
    }
    
    if (useCache) {
        std::vector<std::vector<int>> boardState = board.getBoard();
        transpositionTable[boardState] = {depth, value, flag};
    }
    
    return value;
}

std::pair<int, int> findBestMove(HexBoard& board, int maxDepth, Player player) {
    transpositionTable.clear();
    
    std::pair<int, int> bestMove = {-1, -1};
    
    std::vector<std::pair<int, int>> possibleMoves = board.getOrderedMoves(player);
    for (const auto& move : possibleMoves) {
        board.makeMove(move.first, move.second, player);
        if (board.checkWin(player)) {
            board.undoMove(move.first, move.second);
            return move;
        }
        board.undoMove(move.first, move.second);
    }
    
    for (int currentDepth = 1; currentDepth <= maxDepth; currentDepth++) {
        int bestValue = INT_MIN;
        std::pair<int, int> tempBestMove = {-1, -1};
        
        for (const auto& move : possibleMoves) {
            board.makeMove(move.first, move.second, player);
            int moveValue = alphabeta(board, currentDepth - 1, INT_MIN, INT_MAX, false, player);
            board.undoMove(move.first, move.second);
            
            if (moveValue > bestValue) {
                bestValue = moveValue;
                tempBestMove = move;
            }
        }
        
        if (tempBestMove.first != -1) {
            bestMove = tempBestMove;
        }
        
        if (bestValue >= 900) {
            break;
        }
    }
    
    return bestMove;
}

PYBIND11_MODULE(hex_cpp, m) {
    m.doc() = "C++ implementation of Hex game with alpha-beta pruning";
    
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
        .def("get_ordered_moves", &HexBoard::getOrderedMoves)
        .def("is_game_over", &HexBoard::isGameOver)
        .def("check_win", &HexBoard::checkWin)
        .def("evaluate", &HexBoard::evaluate)
        .def("print", &HexBoard::print)
        .def("get_size", &HexBoard::getSize);
    
    m.def("find_best_move", &findBestMove, 
          py::arg("board"), py::arg("depth") = 3, py::arg("player") = Player::PLAYER1,
          "Find the best move using enhanced alpha-beta pruning with iterative deepening");
    
    m.def("alphabeta", &alphabeta,
          py::arg("board"), py::arg("depth"), py::arg("alpha"), py::arg("beta"),
          py::arg("maximizingPlayer"), py::arg("currentPlayer"), py::arg("useCache") = true,
          "Alpha-beta pruning algorithm with transposition table");
}
