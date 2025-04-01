import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QListWidget, QSpinBox, QFormLayout)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QPointF, QSize
import os

# Backend import (you might need to adjust this based on your project structure)
import hex_ai_ai

class HexGame:
    def __init__(self, size):
        self.size = size
        self.board = [[0] * size for _ in range(size)]  # 0 - empty, 1 - black, 2 - white
        self.is_black_turn = True
        self.moves_history = []  # Track moves history
        # Define column and row labels
        self.col_labels = 'abcdefghijklmnopqrstuvwxyz'[:size]
        self.row_labels = list(range(1, size + 1))

    def to_python_state(self):
        # Create a Python HexState
        state = hex_ai_ai.HexState(self.size, self.is_black_turn)
        state.board = [row[:] for row in self.board]  # Create deep copy of board
        return state

    def make_move(self, row, col):
        if self.board[row][col] == 0:
            self.board[row][col] = 1 if self.is_black_turn else 2
            # Record the move with algebraic notation
            player = "Blue" if self.is_black_turn else "Red"  # Changed from Black/White to Blue/Red
            move = f"{player}: {self.col_labels[col]}{self.row_labels[row]}"
            self.moves_history.append(move)
            self.is_black_turn = not self.is_black_turn
            return True
        return False

    def check_winner(self):
        """
        Check if a player has won by creating a path connecting their respective sides.
        Blue (player 1) wins by connecting top and bottom blue borders.
        Red (player 2) wins by connecting left and right red borders.
        Returns:
        - 1 for Blue win
        - 2 for Red win
        - None if no winner yet
        """
        # Use the check_win function from hex_ai_ai
        if hex_ai_ai.check_win(self.board, 1):  # Check Blue (player 1)
            return 1
        elif hex_ai_ai.check_win(self.board, 2):  # Check Red (player 2)
            return 2
        return None

class HexBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.cell_size = 20  # Size of hexagon from center to vertex
        
        # Calculate board dimensions
        width = self.game.size * 2 * self.cell_size + (self.game.size - 1) * self.cell_size
        height = self.game.size * 2 * self.cell_size * math.sin(math.pi/3)
        
        # Add extra height to accommodate the top labels
        height += 40  # Extra space for labels at the top
        
        self.setMinimumSize(int(width), int(height))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get the center of the widget
        widget_center_x = self.width() / 2
        # Decrease the vertical offset to move the board up
        widget_center_y = self.height() / 2 + 12  # Reduced from 20 to 12 pixels
        
        # Calculate the width and height of a single hexagon
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        
        # Draw hexagons
        for row in range(self.game.size):
            for col in range(self.game.size):
                x = widget_center_x + (col - row) * (hex_width * 0.75)
                y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5)
                
                hexagon = self.create_hexagon(x, y)
                
                # Cell color - changed black to blue, white to red
                if self.game.board[row][col] == 1:
                    painter.setBrush(QColor("blue"))
                elif self.game.board[row][col] == 2:
                    painter.setBrush(QColor("red"))
                else:
                    painter.setBrush(QColor("lightgray"))

                painter.setPen(Qt.black)
                painter.drawPolygon(hexagon)
        
        # Draw precise zigzag border
        self.draw_precise_zigzag_border(painter, widget_center_x, widget_center_y)
        
        # Draw column and row labels
        self.draw_labels(painter, widget_center_x, widget_center_y, hex_width, hex_height)

################################################################################################################################################
    def draw_precise_zigzag_border(self, painter, widget_center_x, widget_center_y):
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        size = self.game.size
        
        # Offset factor to draw lines on the outer side
        offset_factor = 1  # 0% outside of the hexagon edge
        
        # Blue borders (top and bottom)
        painter.setPen(QPen(QColor("blue"), 2))
        
        # Top blue border
        for col in range(size):
            row = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            # Calculate outer points for top edge (vertices 0 to 1)
            v0 = vertices[4]
            v1 = vertices[5]
            v2 = vertices[0]
            v3 = vertices[5]
            
            # Create points with offset to draw outside the hexagon
            outer_v0x = x + (v0.x() - x) * offset_factor
            outer_v0y = y + (v0.y() - y) * offset_factor
            outer_v1x = x + (v1.x() - x) * offset_factor
            outer_v1y = y + (v1.y() - y) * offset_factor
            outer_v2x = x + (v2.x() - x) * offset_factor
            outer_v2y = y + (v2.y() - y) * offset_factor
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            
            # Draw along the top edge of the hexagon (vertices 0 to 1)
            painter.drawLine(
                int(outer_v0x), int(outer_v0y),
                int(outer_v1x), int(outer_v1y)
            )
            painter.drawLine(
                int(outer_v2x), int(outer_v2y),
                int(outer_v3x), int(outer_v3y)
            )
        
        # Bottom blue border
        for col in range(size):
            flag = True if col == size - 1 else False
            
            row = size - 1
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            # Calculate outer points for bottom edge (vertices 3 to 4)
            v3 = vertices[1]
            v4 = vertices[2]
            v5 = vertices[2]
            v6 = vertices[3]
            
            # Create points with offset to draw outside the hexagon
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            outer_v4x = x + (v4.x() - x) * offset_factor
            outer_v4y = y + (v4.y() - y) * offset_factor
            outer_v5x = x + (v5.x() - x) * offset_factor
            outer_v5y = y + (v5.y() - y) * offset_factor
            outer_v6x = x + (v6.x() - x) * offset_factor
            outer_v6y = y + (v6.y() - y) * offset_factor
            
            # Draw along the bottom edge of the hexagon (vertices 3 to 4)
            if not flag:
                painter.drawLine(
                    int(outer_v3x), int(outer_v3y),
                    int(outer_v4x), int(outer_v4y)
                )
            painter.drawLine(
                int(outer_v5x), int(outer_v5y),
                int(outer_v6x), int(outer_v6y)
            )
        
        # Red borders (left and right)
        painter.setPen(QPen(QColor("red"), 2))
        
        # Left red border
        for row in range(size):
            flag = True if row == 0 else False
            
            col = 0
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            # Calculate outer points for left edge (vertices 5 to 0)
            v6 = vertices[3]
            v7 = vertices[4]
            v8 = vertices[4]
            v9 = vertices[5]
            
            # Create points with offset to draw outside the hexagon
            outer_v6x = x + (v6.x() - x) * offset_factor
            outer_v6y = y + (v6.y() - y) * offset_factor
            outer_v7x = x + (v7.x() - x) * offset_factor
            outer_v7y = y + (v7.y() - y) * offset_factor
            outer_v8x = x + (v8.x() - x) * offset_factor
            outer_v8y = y + (v8.y() - y) * offset_factor
            outer_v9x = x + (v9.x() - x) * offset_factor
            outer_v9y = y + (v9.y() - y) * offset_factor
            
            # Draw along the left edge of the hexagon (vertices 5 to 0)
            painter.drawLine(
                int(outer_v6x), int(outer_v6y),
                int(outer_v7x), int(outer_v7y)
            )
            if not flag:
                painter.drawLine(
                    int(outer_v8x), int(outer_v8y),
                    int(outer_v9x), int(outer_v9y)
                )
        
        # Right red border
        for row in range(size):
            col = size - 1
            x = widget_center_x + (col - row) * (hex_width * 0.75)
            y = widget_center_y + (col + row - size + 1) * (hex_height * 0.5)
            vertices = self.get_hex_vertices(x, y)
            
            # Calculate outer points for right edge (vertices 2 to 3)
            v2 = vertices[0]
            v3 = vertices[1]
            v4 = vertices[1]
            v5 = vertices[2]
            
            # Create points with offset to draw outside the hexagon
            outer_v2x = x + (v2.x() - x) * offset_factor
            outer_v2y = y + (v2.y() - y) * offset_factor
            outer_v3x = x + (v3.x() - x) * offset_factor
            outer_v3y = y + (v3.y() - y) * offset_factor
            outer_v4x = x + (v4.x() - x) * offset_factor
            outer_v4y = y + (v4.y() - y) * offset_factor
            outer_v5x = x + (v5.x() - x) * offset_factor
            outer_v5y = y + (v5.y() - y) * offset_factor
            
            # Draw along the right edge of the hexagon (vertices 2 to 3)
            painter.drawLine(
                int(outer_v2x), int(outer_v2y),
                int(outer_v3x), int(outer_v3y)
            )
            painter.drawLine(
                int(outer_v4x), int(outer_v4y),
                int(outer_v5x), int(outer_v5y)
            )
            
        # Add labels for players
        self.draw_player_labels(painter, widget_center_x, widget_center_y, hex_width, hex_height, size)
################################################################################################################################################
    
    def draw_player_labels(self, painter, widget_center_x, widget_center_y, hex_width, hex_height, size):
        # Get corner coordinates for labels
        
        # Top-left corner
        x = widget_center_x + (0) * (hex_width * 0.75)
        y = widget_center_y + (0 - size + 1) * (hex_height * 0.5)
        top_left = self.get_hex_vertices(x, y)[0]
        
        # Top-right corner
        x = widget_center_x + ((size-1) - 0) * (hex_width * 0.75)
        y = widget_center_y + ((size-1) + 0 - size + 1) * (hex_height * 0.5)
        top_right = self.get_hex_vertices(x, y)[1]
        
        # Bottom-right corner
        x = widget_center_x + ((size-1) - (size-1)) * (hex_width * 0.75)
        y = widget_center_y + ((size-1) + (size-1) - size + 1) * (hex_height * 0.5)
        bottom_right = self.get_hex_vertices(x, y)[3]
        
        # Bottom-left corner
        x = widget_center_x + (0 - (size-1)) * (hex_width * 0.75)
        y = widget_center_y + (0 + (size-1) - size + 1) * (hex_height * 0.5)
        bottom_left = self.get_hex_vertices(x, y)[4]
        
        # The text labels "Red" and "Blue" have been removed
        # The colored borders still indicate which sides players need to connect

    def create_hexagon(self, x, y):
        """Create a regular hexagon centered at (x, y) with flat top edge"""
        hexagon = QPolygonF()
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(angle_rad)
            hexagon.append(QPointF(px, py))
        return hexagon

    def get_hex_vertices(self, x, y):
        """Return the 6 vertices of a hexagon centered at (x,y)"""
        vertices = []
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(angle_rad)
            vertices.append(QPointF(px, py))
        return vertices

    def mousePressEvent(self, event):
        # Get the center of the widget
        widget_center_x = self.width() / 2
        # Use the same adjusted vertical offset for click detection
        widget_center_y = self.height() / 2 + 12  # Reduced from 20 to 12 pixels
        
        x, y = event.x(), event.y()
        
        # Find the closest hexagon to the click
        closest_row, closest_col = -1, -1
        min_distance = float('inf')
        
        for row in range(self.game.size):
            for col in range(self.game.size):
                # Calculate hexagon center using the same transformation without gaps
                hex_width = 2 * self.cell_size
                hex_height = 2 * self.cell_size * math.sin(math.pi/3)
                
                hex_x = widget_center_x + (col - row) * (hex_width * 0.75)
                hex_y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5)
                
                # Calculate distance from click to hexagon center
                distance = (x - hex_x) ** 2 + (y - hex_y) ** 2
                
                if distance < min_distance and distance < (self.cell_size ** 2 * 1.5):  # Increased catch area
                    min_distance = distance
                    closest_row, closest_col = row, col
        
        # If we found a valid hexagon to click
        if closest_row >= 0 and closest_col >= 0:
            if self.game.make_move(closest_row, closest_col):
                self.update()  # redraw after player step
                # Update moves list - notify parent
                if hasattr(self.parent(), "update_moves_list"):
                    self.parent().update_moves_list()
                
                winner = self.game.check_winner()
                if winner:
                    winner_name = 'Blue' if winner == 1 else 'Red'
                    print(f"Winner: {winner_name}")
                    # Show a message dialog with the winner
                    from PyQt5.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setWindowTitle("Game Over")
                    msg.setText(f"{winner_name} has won the game!")
                    msg.setIcon(QMessageBox.Information)
                    msg.exec_()
                elif not self.game.is_black_turn:  # AI step
                    self.ai_move()

    def ai_move(self):
        # Use Python implementation
        state = self.game.to_python_state()
        # Get the current depth setting from the parent window
        ai_depth = 3  # Default depth
        if hasattr(self.parent(), "get_ai_depth"):
            ai_depth = self.parent().get_ai_depth()
        
        best_move = hex_ai_ai.find_best_move(state, depth=ai_depth)
        if best_move[0] != -1 and best_move[1] != -1:
            self.game.make_move(best_move[0], best_move[1])
            self.update()  # redraw after AI step
            # Update moves list - notify parent
            if hasattr(self.parent(), "update_moves_list"):
                self.parent().update_moves_list()
            
            winner = self.game.check_winner()
            if winner:
                winner_name = 'Blue' if winner == 1 else 'Red'
                print(f"Winner: {winner_name}")
                # Show a message dialog with the winner
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game!")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()

    def draw_labels(self, painter, widget_center_x, widget_center_y, hex_width, hex_height):
        """Draw column and row labels around the board"""
        # Create a bold font
        bold_font = QFont('Arial', 10)
        bold_font.setBold(True)
        painter.setFont(bold_font)
        
        # Set white color for all labels
        painter.setPen(QPen(Qt.white))
        
        # Draw column labels (letters) on the upper-right edges of hexagons
        for col in range(self.game.size):
            # Calculate position for column label - move to upper-right edge
            row = 0
            # Adjust x position to be further to the right
            x = widget_center_x + (col - row) * (hex_width * 0.75) + 22
            # Adjust y position to match the upper-right edge
            y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5) - 8
            
            # Draw the letter
            painter.drawText(int(x), int(y), self.game.col_labels[col])
        
        # Draw row labels (numbers) - more to the left and a little lower
        for row in range(self.game.size):
            # Calculate position for row label
            col = 0
            # Move further left
            x = widget_center_x + (col - row) * (hex_width * 0.75) - 28
            # Move slightly down
            y = widget_center_y + (col + row - self.game.size + 1) * (hex_height * 0.5) - 8
            
            # Draw the number
            painter.drawText(int(x), int(y), str(self.game.row_labels[row]))

class HexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.game = HexGame(11)  # Standard size board
        
        # Set a larger minimum size for the window
        self.setMinimumSize(QSize(1050, 600))

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Changed to horizontal layout

        # Left side - Board and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Board
        self.board_widget = HexBoard(self.game)
        left_layout.addWidget(self.board_widget)
        
        # Add stretch to push the button down
        left_layout.addStretch(1)

        # Controls section
        controls_panel = QWidget()
        controls_layout = QFormLayout(controls_panel)
        
        # AI Depth control
        self.depth_spinner = QSpinBox()
        self.depth_spinner.setMinimum(1)
        self.depth_spinner.setMaximum(5)  # Limit to reasonable depths
        self.depth_spinner.setValue(3)  # Default depth
        self.depth_spinner.setToolTip("Higher values make the AI stronger but slower")
        controls_layout.addRow("AI Difficulty:", self.depth_spinner)
        
        left_layout.addWidget(controls_panel)

        # Reset game button
        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        # Game rules explanation - removed color names
        rules_label = QLabel("Connect top to bottom • Connect left to right")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)
        
        main_layout.addWidget(left_panel)

        # Right side - Steps list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        steps_label = QLabel("Moves History:")
        right_layout.addWidget(steps_label)
        
        self.steps_list = QListWidget()
        right_layout.addWidget(self.steps_list)
        
        main_layout.addWidget(right_panel)
        
        # Set ratio between panels (game board gets more space)
        main_layout.setStretch(0, 7)  # Left panel - game board
        main_layout.setStretch(1, 3)  # Right panel - steps list

    def get_ai_depth(self):
        """Get the current AI search depth setting"""
        return self.depth_spinner.value()

    def update_moves_list(self):
        """Update the moves history list display"""
        self.steps_list.clear()
        for move in self.game.moves_history:
            self.steps_list.addItem(move)
        # Auto-scroll to the latest move
        self.steps_list.scrollToBottom()

    def reset_game(self):
        self.game = HexGame(11)  # Keep using 11x11 for reset
        self.board_widget.game = self.game
        self.board_widget.update()
        # Clear moves list
        self.steps_list.clear()

# Start game
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HexWindow()
    window.show()
    sys.exit(app.exec_())
