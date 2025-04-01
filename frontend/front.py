import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QListWidget, QSpinBox, QFormLayout)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QPointF, QSize
import os

import hex_ai_ai

# Class representing the game state and logic
class HexGame:
    def __init__(self, size):
        self.size = size  # Size of the board (size x size)
        self.board = [[0] * size for _ in range(size)]  # Game board: 0=empty, 1=blue, 2=red
        self.is_black_turn = True  # True = Blue's turn, False = Red's turn
        self.moves_history = []  # List to store move history
        self.col_labels = 'abcdefghijklmnopqrstuvwxyz'[:size]  # Column labels (a, b, c...)
        self.row_labels = list(range(1, size + 1))  # Row labels (1, 2, 3...)
        self.first_move = None  # Store first move for swap rule
        self.move_count = 0  # Counter for tracking moves (for swap rule)
        self.game_over = False  # Flag to indicate if game has ended
        self.winner = None  # Store the winner (1 = Blue, 2 = Red)

    def to_python_state(self):
        # Convert game state to format used by AI
        state = hex_ai_ai.HexState(self.size, self.is_black_turn)
        state.board = [row[:] for row in self.board]  # Deep copy of board
        return state

    def make_move(self, row, col):
        # Don't allow moves if game is over
        if self.game_over:
            return False

        # Place a piece on the board and update game state
        if self.board[row][col] == 0:  # Cell must be empty
            self.board[row][col] = 1 if self.is_black_turn else 2  # Place blue or red
            player = "Blue" if self.is_black_turn else "Red"
            # Record move in algebraic notation
            move = f"{player}: {self.col_labels[col]}{self.row_labels[row]}"
            self.moves_history.append(move)
            
            # Update first move tracking for swap rule
            self.move_count += 1
            if self.move_count == 1:
                self.first_move = (row, col)
                
            self.is_black_turn = not self.is_black_turn  # Switch turns
            return True
        return False  # Move was invalid
        
    def swap_move(self):
        # Implement swap rule - second player can mirror first player's move
        if self.move_count == 1 and not self.is_black_turn:  # Only valid as second move
            # Mirror first move across diagonal
            row, col = self.first_move
            mirrored_row, mirrored_col = col, row
            
            # Place red piece at mirrored position
            self.board[mirrored_row][mirrored_col] = 2  # Red (second player)
            player = "Red"
            move = f"{player}: Swap ({self.col_labels[mirrored_col]}{self.row_labels[mirrored_row]})"
            self.moves_history.append(move)
            
            self.move_count += 1
            self.is_black_turn = not self.is_black_turn  # Switch turns
            return True
        return False  # Swap not allowed

    def check_winner(self):
        # Check if either player has won
        if hex_ai_ai.check_win(self.board, 1):
            self.game_over = True
            self.winner = 1  # Blue wins
            return 1
        elif hex_ai_ai.check_win(self.board, 2):
            self.game_over = True
            self.winner = 2  # Red wins 
            return 2
        return None

    def reset(self):
        # Reset the game state
        self.board = [[0] * self.size for _ in range(self.size)]
        self.is_black_turn = True
        self.moves_history = []
        self.first_move = None
        self.move_count = 0
        self.game_over = False
        self.winner = None

# Widget to display and interact with the game board
class HexBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.cell_size = 20
        
        width = self.game.size * 2 * self.cell_size + (self.game.size - 1) * self.cell_size
        height = self.game.size * 2 * self.cell_size * math.sin(math.pi/3)
        
        height += 40
        
        self.setMinimumSize(int(width), int(height))
    
    def paintEvent(self, event):
        # Draw the game board and pieces
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2 + 12
        
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        
        for row in range(self.game.size):
            for col in range(self.game.size):
                x = widget_center_x + (col - row) * (hex_width * 0.75)
                y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5)
                
                hexagon = self.create_hexagon(x, y)
                
                if self.game.board[row][col] == 1:
                    painter.setBrush(QColor("blue"))
                elif self.game.board[row][col] == 2:
                    painter.setBrush(QColor("red"))
                else:
                    painter.setBrush(QColor("lightgray"))

                painter.setPen(Qt.black)
                painter.drawPolygon(hexagon)
        
        self.draw_precise_zigzag_border(painter, widget_center_x, widget_center_y)
        self.draw_labels(painter, widget_center_x, widget_center_y, hex_width, hex_height)

    def draw_precise_zigzag_border(self, painter, widget_center_x, widget_center_y):
        # Draw zigzag borders for the game board
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        size = self.game.size
        
        offset_factor = 1
        
        painter.setPen(QPen(QColor("blue"), 2))
        
        for col in range(size):
            row = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            v0 = vertices[4]
            v1 = vertices[5]
            v2 = vertices[0]
            v3 = vertices[5]
            
            outer_v0x = x + (v0.x() - x) * offset_factor
            outer_v0y = y + (v0.y() - y) * offset_factor
            outer_v1x = x + (v1.x() - x) * offset_factor
            outer_v1y = y + (v1.y() - y) * offset_factor
            outer_v2x = x + (v2.x() - x) * offset_factor
            outer_v2y = y + (v2.y() - y) * offset_factor
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            
            painter.drawLine(
                int(outer_v0x), int(outer_v0y),
                int(outer_v1x), int(outer_v1y)
            )
            painter.drawLine(
                int(outer_v2x), int(outer_v2y),
                int(outer_v3x), int(outer_v3y)
            )
        
        for col in range(size):
            flag = True if col == size - 1 else False
            
            row = size - 1
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            v3 = vertices[1]
            v4 = vertices[2]
            v5 = vertices[2]
            v6 = vertices[3]
            
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            outer_v4x = x + (v4.x() - x) * offset_factor
            outer_v4y = y + (v4.y() - y) * offset_factor
            outer_v5x = x + (v5.x() - x) * offset_factor
            outer_v5y = y + (v5.y() - y) * offset_factor
            outer_v6x = x + (v6.x() - x) * offset_factor
            outer_v6y = y + (v6.y() - y) * offset_factor
            
            if not flag:
                painter.drawLine(
                    int(outer_v3x), int(outer_v3y),
                    int(outer_v4x), int(outer_v4y)
                )
            painter.drawLine(
                int(outer_v5x), int(outer_v5y),
                int(outer_v6x), int(outer_v6y)
            )
        
        painter.setPen(QPen(QColor("red"), 2))
        
        for row in range(size):
            flag = True if row == 0 else False
            
            col = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            v6 = vertices[3]
            v7 = vertices[4]
            v8 = vertices[4]
            v9 = vertices[5]
            
            outer_v6x = x + (v6.x() - x) * offset_factor
            outer_v6y = y + (v6.y() - y) * offset_factor
            outer_v7x = x + (v7.x() - x) * offset_factor
            outer_v7y = y + (v7.y() - y) * offset_factor
            outer_v8x = x + (v8.x() - x) * offset_factor
            outer_v8y = y + (v8.y() - y) * offset_factor
            outer_v9x = x + (v9.x() - x) * offset_factor
            outer_v9y = y + (v9.y() - y) * offset_factor
            
            painter.drawLine(
                int(outer_v6x), int(outer_v6y),
                int(outer_v7x), int(outer_v7y)
            )
            if not flag:
                painter.drawLine(
                    int(outer_v8x), int(outer_v8y),
                    int(outer_v9x), int(outer_v9y)
                )
        
        for row in range(size):
            col = size - 1
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            v2 = vertices[0]
            v3 = vertices[1]
            v4 = vertices[1]
            v5 = vertices[2]
            
            outer_v2x = x + (v2.x() - x) * offset_factor
            outer_v2y = y + (v2.y() - y) * offset_factor
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            outer_v4x = x + (v4.x() - x) * offset_factor
            outer_v4y = y + (v4.y() - y) * offset_factor
            outer_v5x = x + (v5.x() - x) * offset_factor
            outer_v5y = y + (v5.y() - y) * offset_factor
            
            painter.drawLine(
                int(outer_v2x), int(outer_v2y),
                int(outer_v3x), int(outer_v3y)
            )
            painter.drawLine(
                int(outer_v4x), int(outer_v4y),
                int(outer_v5x), int(outer_v5y)
            )
            
        self.draw_player_labels(painter, widget_center_x, widget_center_y, hex_width, hex_height, size)
    
    def draw_player_labels(self, painter, widget_center_x, widget_center_y, hex_width, hex_height, size):
        # Draw player labels on the board
        x = widget_center_x + (0) * (hex_width * 0.75)
        y = widget_center_y + (0 - size + 1) * (hex_height * 0.5)
        top_left = self.get_hex_vertices(x, y)[0]
        
        x = widget_center_x + ((size-1) - 0) * (hex_width * 0.75)
        y = widget_center_y + ((size-1) + 0 - size + 1) * (hex_height * 0.5)
        top_right = self.get_hex_vertices(x, y)[1]
        
        x = widget_center_x + ((size-1) - (size-1)) * (hex_width * 0.75)
        y = widget_center_y + ((size-1) + (size-1) - size + 1) * (hex_height * 0.5)
        bottom_right = self.get_hex_vertices(x, y)[3]
        
        x = widget_center_x + (0 - (size-1)) * (hex_width * 0.75)
        y = widget_center_y + (0 + (size-1) - size + 1) * (hex_height * 0.5)
        bottom_left = self.get_hex_vertices(x, y)[4]

    def create_hexagon(self, x, y):
        # Create a hexagon shape at given coordinates
        hexagon = QPolygonF()
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(angle_rad)
            hexagon.append(QPointF(px, py))
        return hexagon

    def get_hex_vertices(self, x, y):
        # Get vertices of a hexagon at given coordinates
        vertices = []
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(math.pi/3 * i)
            vertices.append(QPointF(px, py))
        return vertices

    def mousePressEvent(self, event):
        # Don't process clicks if game is over
        if self.game.game_over:
            return

        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2 + 12
        
        x, y = event.x(), event.y()  # Get mouse coordinates
        
        # Find which hexagon was clicked
        closest_row, closest_col = -1, -1
        min_distance = float('inf')
        
        # Check all cells to find closest
        for row in range(self.game.size):
            for col in range(self.game.size):
                hex_width = 2 * self.cell_size
                hex_height = 2 * self.cell_size * math.sin(math.pi/3)
                
                # Calculate center of this hex cell
                hex_x = widget_center_x + (col - row) * (hex_width * 0.75)
                hex_y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5)
                
                # Calculate distance from click to hex center
                distance = (x - hex_x) ** 2 + (y - hex_y) ** 2
                
                # Update closest if this is closer and within threshold
                if distance < min_distance and distance < (self.cell_size ** 2 * 1.5):
                    min_distance = distance
                    closest_row, closest_col = row, col
        
        # If we found a valid hex to click
        if closest_row >= 0 and closest_col >= 0:
            if self.game.make_move(closest_row, closest_col):
                self.update()  # Redraw the board
                
                # Update UI elements in parent window
                if hasattr(self.parent(), "update_moves_list"):
                    self.parent().update_moves_list()
                
                if hasattr(self.parent(), "update_swap_button"):
                    self.parent().update_swap_button()
                
                # Check for winner
                winner = self.game.check_winner()
                if winner:
                    winner_name = 'Blue' if winner == 1 else 'Red'
                    from PyQt5.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setWindowTitle("Game Over")
                    msg.setText(f"{winner_name} has won the game by connecting their borders!")
                    msg.setInformativeText("Click 'New Game' to play again.")
                    msg.setIcon(QMessageBox.Information)
                    msg.exec_()
                    
                    # Update game status in parent window
                    if hasattr(self.parent(), "update_game_status"):
                        self.parent().update_game_status()

    def draw_labels(self, painter, widget_center_x, widget_center_y, hex_width, hex_height):
        # Draw column and row labels on the board
        bold_font = QFont('Arial', 10)
        bold_font.setBold(True)
        painter.setFont(bold_font)
        
        painter.setPen(QPen(Qt.white))
        
        for col in range(self.game.size):
            row = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75) + 22
            y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5) - 8
            
            painter.drawText(int(x), int(y), self.game.col_labels[col])
        
        for row in range(self.game.size):
            col = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75) - 28
            y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5) - 8
            
            painter.drawText(int(x), int(y), str(self.game.row_labels[row]))

# Main application window
class HexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.game = HexGame(11)
        
        self.setMinimumSize(QSize(1050, 600))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.board_widget = HexBoard(self.game)
        left_layout.addWidget(self.board_widget)
        
        left_layout.addStretch(1)

        controls_panel = QWidget()
        controls_layout = QFormLayout(controls_panel)
        
        self.turn_label = QLabel("Blue's Turn")
        self.turn_label.setStyleSheet("font-weight: bold; color: blue;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.turn_label)
        
        # Add game status label
        self.game_status = QLabel("")
        self.game_status.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.game_status)
        
        self.swap_button = QPushButton("Swap First Move")
        self.swap_button.clicked.connect(self.swap_player_move)
        self.swap_button.setVisible(False)
        self.swap_button.setToolTip("Mirror opponent's first move across the diagonal")
        controls_layout.addRow(self.swap_button)
        
        left_layout.addWidget(controls_panel)

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        mode_label = QLabel("Two Player Mode")
        mode_label.setAlignment(Qt.AlignCenter)
        mode_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(mode_label)
        
        rules_label = QLabel("Blue: Connect blue boarders • Red: Connect red boarders")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)
        
        main_layout.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        steps_label = QLabel("Moves History:")
        right_layout.addWidget(steps_label)
        
        self.steps_list = QListWidget()
        right_layout.addWidget(self.steps_list)
        
        main_layout.addWidget(right_panel)
        
        main_layout.setStretch(0, 7)
        main_layout.setStretch(1, 3)

    def swap_player_move(self):
        # Don't allow swap if game is over
        if self.game.game_over:
            return
            
        # Handle swap button click
        if self.game.swap_move():
            self.board_widget.update()  # Redraw the board
            self.update_moves_list()  # Update move history
            self.update_swap_button()  # Update button visibility
            
            # Check for winner after swap
            winner = self.game.check_winner()
            if winner:
                winner_name = 'Blue' if winner == 1 else 'Red'
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game!")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()

    def update_swap_button(self):
        # Show swap button only when it can be used (after first move, on red's turn)
        can_swap = self.game.move_count == 1 and not self.game.is_black_turn
        self.swap_button.setVisible(can_swap)
        self.update_turn_label()
    
    def update_turn_label(self):
        # Update the label showing whose turn it is or game status
        if self.game.game_over:
            winner_name = 'Blue' if self.game.winner == 1 else 'Red'
            self.turn_label.setText(f"{winner_name} Wins!")
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {'blue' if self.game.winner == 1 else 'red'}; font-size: 14px;")
        else:
            if self.game.is_black_turn:
                self.turn_label.setText("Blue's Turn")
                self.turn_label.setStyleSheet("font-weight: bold; color: blue;")
            else:
                self.turn_label.setText("Red's Turn")
                self.turn_label.setStyleSheet("font-weight: bold; color: red;")

    def update_game_status(self):
        # Update game status message
        if self.game.game_over:
            winner_color = 'blue' if self.game.winner == 1 else 'red'
            self.game_status.setText("Game Over")
            self.game_status.setStyleSheet(f"font-weight: bold; color: {winner_color};")
        else:
            self.game_status.setText("")

    def update_moves_list(self):
        # Update the move history list in the UI
        self.steps_list.clear()
        for move in self.game.moves_history:
            self.steps_list.addItem(move)
        self.steps_list.scrollToBottom()  # Auto-scroll to latest move
        self.update_turn_label()

    def reset_game(self):
        # Start a new game
        self.game = HexGame(11)  # 11x11 board
        self.board_widget.game = self.game
        self.board_widget.update()  # Redraw board
        self.steps_list.clear()  # Clear move history
        self.update_swap_button()  # Reset swap button
        self.turn_label.setText("Blue's Turn")  # Reset turn indicator
        self.turn_label.setStyleSheet("font-weight: bold; color: blue;")
        self.game_status.setText("")  # Reset game status

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HexWindow()
    window.show()
    sys.exit(app.exec_())
