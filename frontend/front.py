import sys, math, os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QListWidget, QSpinBox, QFormLayout, QMessageBox)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont, QBrush
from PyQt5.QtCore import Qt, QPointF, QSize

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import back

class HexGame:
    """
    Main game logic class for Hex.
    
    Responsible for:
    - Maintaining the game state (board, current player, game status)
    - Making/undoing moves and tracking move history
    - Handling the swap rule (pie rule)
    - Checking for win conditions
    
    Attributes:
        size (int): Board size (creates a size × size grid)
        board (list): 2D grid where 0=empty, 1=blue player(Player1), 2=red player(Player2)
        is_black_turn (bool): True if it's blue player's turn, False for red player
        moves_history (list): List of string representations of moves
        col_labels/row_labels (list): Labels for board coordinates
        board_states (list): History of all board states for move replay
    """
    def __init__(self, size):
        self.size = size
        self.board = [[0] * size for _ in range(size)]
        self.is_black_turn = True
        self.moves_history = []
        self.col_labels = "abcdefghijklmnopqrstuvwxyz"[:size]
        self.row_labels = list(range(1, size + 1))
        self.first_move = None
        self.move_count = 0
        self.game_over = False
        self.winner = None
        self.board_states = []
        self.current_view_index = -1
        self.viewing_history = False

    def to_python_state(self):
        """
        Converts the current game state to a HexState object for AI processing
        """
        state = back.HexState(self.size, self.is_black_turn)
        state.board = [row[:] for row in self.board]
        return state

    def make_move(self, row, col):
        """
        Attempts to make a move at the specified position.
        
        Args:
            row (int): Row index
            col (int): Column index
            
        Returns:
            bool: True if move was successful, False if invalid
        
        Side effects:
            - Updates the board state
            - Adds move to history
            - Switches current player
            - Records board state for replay
        """
        if self.game_over or self.board[row][col] != 0: return False
        
        self.board[row][col] = 1 if self.is_black_turn else 2
        player_color = "Blue" if self.is_black_turn else "Red"
        move_notation = f"{self.col_labels[col]}{self.row_labels[row]}"
        self.moves_history.append(f"{player_color}: {move_notation}")
        
        # Print the move to console
        lowercase_color = player_color.lower()
        print(f"{move_notation} - {lowercase_color}")
        
        self.move_count += 1
        if self.move_count == 1: self.first_move = (row, col)
            
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board])
        self.current_view_index = -1
        return True
        
    def swap_move(self):
        """
        Implements the "pie rule" (swap rule) in Hex.
        After the first move, the second player can choose to swap positions,
        taking the first player's position and color.
        
        Returns:
            bool: True if the swap was successful, False otherwise
        """
        if self.move_count != 1 or self.is_black_turn: return False
        
        row, col = self.first_move
        mirrored_row, mirrored_col = col, row
        
        self.board[mirrored_row][mirrored_col] = 2
        move_notation = f"{self.col_labels[mirrored_col]}{self.row_labels[mirrored_row]}"
        self.moves_history.append(f"Red: Swap ({move_notation})")
        
        # Print the swap move to console
        print(f"{move_notation} - red (swap)")
        
        self.move_count += 1
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board])
        self.current_view_index = -1
        return True

    def check_winner(self):
        """
        Checks if either player has won by connecting their sides.
        Blue (Player 1) wins by connecting top and bottom.
        Red (Player 2) wins by connecting left and right.
        
        Returns:
            int or None: 1 for Blue win, 2 for Red win, None if no winner
        """
        if back.check_win(self.board, 1):
            self.game_over, self.winner = True, 1
            return 1
        elif back.check_win(self.board, 2):
            self.game_over, self.winner = True, 2
            return 2
        return None

    def reset(self):
        """
        Resets the game to its initial state
        """
        self.board = [[0] * self.size for _ in range(self.size)]
        self.is_black_turn = True
        self.moves_history = []
        self.first_move = None
        self.move_count = 0
        self.game_over = False
        self.winner = None
        self.board_states = []
        self.current_view_index = -1
        self.viewing_history = False

class HexBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.cell_size = 20
        
        width = self.game.size * 2 * self.cell_size + (self.game.size - 1) * self.cell_size
        height = self.game.size * 2 * self.cell_size * math.sin(math.pi/3) + 40
        
        self.setMinimumSize(int(width), int(height))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2 + 12
        
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        
        # Draw board hexagons
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
        
        self.draw_borders(painter, widget_center_x, widget_center_y, hex_width, hex_height)
        self.draw_labels(painter, widget_center_x, widget_center_y, hex_width, hex_height)

    def draw_borders(self, painter, cx, cy, hex_width, hex_height):
        size = self.game.size
        
        # Helper function to draw border line
        def draw_border_line(v1, v2, color):
            painter.setPen(QPen(QColor(color), 2))
            painter.drawLine(int(v1[0]), int(v1[1]), int(v2[0]), int(v2[1]))
        
        # Draw blue borders (top and bottom)
        painter.setPen(QPen(QColor("blue"), 2))
        for col in range(size):
            # Top border
            x, y = self.get_hex_position(0, col, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            draw_border_line([vertices[4].x(), vertices[4].y()], [vertices[5].x(), vertices[5].y()], "blue")
            draw_border_line([vertices[0].x(), vertices[0].y()], [vertices[5].x(), vertices[5].y()], "blue")
            
            # Bottom border
            x, y = self.get_hex_position(size-1, col, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            if col < size - 1:
                draw_border_line([vertices[1].x(), vertices[1].y()], [vertices[2].x(), vertices[2].y()], "blue")
            draw_border_line([vertices[2].x(), vertices[2].y()], [vertices[3].x(), vertices[3].y()], "blue")
            
        # Draw red borders (left and right)
        painter.setPen(QPen(QColor("red"), 2))
        for row in range(size):
            # Left border
            x, y = self.get_hex_position(row, 0, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            draw_border_line([vertices[3].x(), vertices[3].y()], [vertices[4].x(), vertices[4].y()], "red")
            if row > 0:
                draw_border_line([vertices[4].x(), vertices[4].y()], [vertices[5].x(), vertices[5].y()], "red")
            
            # Right border
            x, y = self.get_hex_position(row, size-1, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            draw_border_line([vertices[0].x(), vertices[0].y()], [vertices[1].x(), vertices[1].y()], "red")
            draw_border_line([vertices[1].x(), vertices[1].y()], [vertices[2].x(), vertices[2].y()], "red")

    def get_hex_position(self, row, col, cx, cy, hex_width, hex_height):
        x = cx + (col - row) * (hex_width * 0.75)
        y = cy + (col + row - self.game.size + 1) * (hex_height * 0.5)
        return x, y

    def create_hexagon(self, x, y):
        hexagon = QPolygonF()
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(angle_rad)
            hexagon.append(QPointF(px, py))
        return hexagon

    def get_hex_vertices(self, x, y):
        vertices = []
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = x + self.cell_size * math.cos(angle_rad)
            py = y + self.cell_size * math.sin(angle_rad)
            vertices.append(QPointF(px, py))
        return vertices

    def mousePressEvent(self, event):
        if self.game.game_over or self.game.viewing_history:
            return
        
        parent = self.parent()    
        if hasattr(parent, "ai_mode") and parent.ai_mode and not self.game.is_black_turn:
            return

        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2 + 12
        
        x, y = event.x(), event.y()
        closest_row, closest_col = -1, -1
        min_distance = float("inf")
        
        hex_width = 2 * self.cell_size
        hex_height = 2 * self.cell_size * math.sin(math.pi/3)
        
        for row in range(self.game.size):
            for col in range(self.game.size):
                hex_x, hex_y = self.get_hex_position(row, col, widget_center_x, widget_center_y, 
                                                   hex_width, hex_height)
                distance = (x - hex_x) ** 2 + (y - hex_y) ** 2
                
                if distance < min_distance and distance < (self.cell_size ** 2 * 1.5):
                    min_distance = distance
                    closest_row, closest_col = row, col
        
        if closest_row >= 0 and closest_col >= 0 and self.game.make_move(closest_row, closest_col):
            self.update()
            
            if hasattr(parent, "update_moves_list"):
                parent.update_moves_list()
            
            if hasattr(parent, "update_swap_button"):
                parent.update_swap_button()
            
            winner = self.game.check_winner()
            if winner:
                winner_name = "Blue" if winner == 1 else "Red"
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game by connecting their borders!")
                msg.setInformativeText("Click 'New Game' to play again.")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()
                
                if hasattr(parent, "update_game_status"):
                    parent.update_game_status()

    def draw_labels(self, painter, widget_center_x, widget_center_y, hex_width, hex_height):
        bold_font = QFont("Arial", 10)
        bold_font.setBold(True)
        painter.setFont(bold_font)
        painter.setPen(QPen(Qt.white))
        
        for col in range(self.game.size):
            x = widget_center_x + (col - 0) * (hex_width * 0.75) + 22
            y = widget_center_y + (col + 0 - self.game.size + 1) * (hex_height * 0.5) - 8
            painter.drawText(int(x), int(y), self.game.col_labels[col])
        
        for row in range(self.game.size):
            x = widget_center_x + (0 - row) * (hex_width * 0.75) - 28
            y = widget_center_y + (0 + row - self.game.size + 1) * (hex_height * 0.5) - 8
            painter.drawText(int(x), int(y), str(self.game.row_labels[row]))

    def ai_move(self):
        if self.game.game_over:
            return
        
        parent = self.parent()
        ai_depth = parent.get_ai_depth() if hasattr(parent, "get_ai_depth") else 3
            
        # Check if should swap
        if self.game.move_count == 1 and not self.game.is_black_turn:
            row, col = self.game.first_move
            center = self.game.size // 2
            if abs(row - center) <= 1 and abs(col - center) <= 1 and self.game.swap_move():
                self.update()
                if hasattr(parent, "update_moves_list"):
                    parent.update_moves_list()
                if hasattr(parent, "update_swap_button"):
                    parent.update_swap_button()
                return
        
        # Find best move
        state = self.game.to_python_state()
        best_move = back.find_best_move(state, depth=ai_depth)
        
        if best_move[0] >= 0 and best_move[1] >= 0 and self.game.make_move(best_move[0], best_move[1]):
            self.update()
            
            if hasattr(parent, "update_moves_list"):
                parent.update_moves_list()
            if hasattr(parent, "update_swap_button"):
                parent.update_swap_button()
            
            winner = self.game.check_winner()
            if winner:
                winner_name = "Blue" if winner == 1 else "Red"
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game by connecting their borders!")
                msg.setInformativeText("Click 'New Game' to play again.")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()
                
                if hasattr(parent, "update_game_status"):
                    parent.update_game_status()

class HexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.game = HexGame(11)
        self.ai_mode = False
        self.current_ai_depth = 3
        
        self.setMinimumSize(QSize(1050, 700))
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.board_widget = HexBoard(self.game)
        left_layout.addWidget(self.board_widget)
        left_layout.addStretch(1)

        # Controls panel
        controls_panel = QWidget()
        controls_layout = QFormLayout(controls_panel)
        
        self.turn_label = QLabel("HEX")
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.turn_label)
        
        self.game_status = QLabel("")
        self.game_status.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.game_status)
        
        self.mode_button = QPushButton("Play vs AI")
        self.mode_button.clicked.connect(self.toggle_game_mode)
        controls_layout.addRow(self.mode_button)
        
        # Difficulty controls
        self.difficulty_layout = QHBoxLayout()
        self.difficulty_label = QLabel("AI Difficulty:")
        self.difficulty_spinner = QSpinBox()
        self.difficulty_spinner.setRange(1, 4)
        self.difficulty_spinner.setValue(3)
        self.difficulty_spinner.valueChanged.connect(self.on_difficulty_changed)
        self.difficulty_layout.addWidget(self.difficulty_label)
        self.difficulty_layout.addWidget(self.difficulty_spinner)
        controls_layout.addRow(self.difficulty_layout)
        
        self.difficulty_label.setVisible(False)
        self.difficulty_spinner.setVisible(False)
        
        self.swap_button = QPushButton("Swap First Move")
        self.swap_button.clicked.connect(self.swap_player_move)
        self.swap_button.setVisible(False)
        self.swap_button.setToolTip("Mirror opponent's first move across the diagonal")
        controls_layout.addRow(self.swap_button)
        
        left_layout.addWidget(controls_panel)

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        self.mode_label = QLabel("Two Player Mode")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.mode_label)
        
        rules_label = QLabel("Blue: Connect blue borders • Red: Connect red borders")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)
        
        main_layout.addWidget(left_panel)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        steps_label = QLabel("Moves History:")
        right_layout.addWidget(steps_label)
        
        self.steps_list = QListWidget()
        right_layout.addWidget(self.steps_list)
        
        nav_buttons_layout = QHBoxLayout()
        
        self.prev_move_button = QPushButton("Previous Move")
        self.prev_move_button.clicked.connect(self.show_previous_move)
        nav_buttons_layout.addWidget(self.prev_move_button)
        
        self.next_move_button = QPushButton("Next Move")
        self.next_move_button.clicked.connect(self.show_next_move)
        nav_buttons_layout.addWidget(self.next_move_button)
        
        right_layout.addLayout(nav_buttons_layout)
        
        self.view_label = QLabel("Current view: Latest move")
        self.view_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.view_label)
        
        main_layout.addWidget(right_panel)
        
        main_layout.setStretch(0, 7)
        main_layout.setStretch(1, 3)

    def swap_player_move(self):
        if self.game.game_over:
            return
            
        if self.game.swap_move():
            self.board_widget.update()
            self.update_moves_list()
            self.update_swap_button()
            
            winner = self.game.check_winner()
            if winner:
                winner_name = "Blue" if winner == 1 else "Red"
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game by connecting their borders!")
                msg.setInformativeText("Click 'New Game' to play again.")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()
                
                self.update_game_status()
    
    def update_swap_button(self):
        can_swap = self.game.move_count == 1 and not self.game.is_black_turn and not self.ai_mode
        self.swap_button.setVisible(can_swap)
        self.update_turn_label()
    
    def update_turn_label(self):
        if self.game.game_over:
            winner_name = "Blue" if self.game.winner == 1 else "Red"
            self.turn_label.setText(f"{winner_name} Wins!")
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {"blue" if self.game.winner == 1 else "red"}; font-size: 14px;")
        else:
            is_blue = self.game.is_black_turn
            self.turn_label.setText("Blue's Turn" if is_blue else "Red's Turn")
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {"blue" if is_blue else "red"};")

    def update_game_status(self):
        """
        Updates the status label to indicate game state
        - Shows "Game Over" with the winner's color when the game ends
        - Clears the status when the game is still in progress
        """
        if self.game.game_over:
            winner_color = "blue" if self.game.winner == 1 else "red"
            self.game_status.setText("Game Over")
            self.game_status.setStyleSheet(f"font-weight: bold; color: {winner_color};")
        else:
            self.game_status.setText("")

    def update_moves_list(self):
        """
        Updates the moves history list in the UI
        - Clears the current list and adds all moves with appropriate colors
        - Scrolls to the bottom to show the most recent move
        - Updates the turn indicator label
        - Triggers AI move if playing against AI and it's AI's turn
        """
        self.steps_list.clear()
        
        from PyQt5.QtGui import QColor
        
        # Add each move to the history list with appropriate color
        for move_idx, move in enumerate(self.game.moves_history):
            item = QListWidgetItem()
            color = "blue" if "Blue" in move else "red"
            item.setForeground(QColor(color))
            item.setText(f"#{move_idx + 1} {move}")
            self.steps_list.addItem(item)
            
        # Scroll to the latest move
        self.steps_list.scrollToBottom()
        self.update_turn_label()
        
        # Trigger AI move if it's AI's turn
        if self.ai_mode and not self.game.game_over and not self.game.is_black_turn:
            self.board_widget.ai_move()

    def reset_game(self):
        self.game.reset()
        self.board_widget.game = self.game
        self.board_widget.update()
        self.steps_list.clear()
        self.update_swap_button()
        self.turn_label.setText("HEX")
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.game_status.setText("")
        
        if self.ai_mode:
            self.difficulty_spinner.setEnabled(True)
            if not self.game.is_black_turn:
                self.board_widget.ai_move()

    def toggle_game_mode(self):
        self.ai_mode = not self.ai_mode
        
        if self.ai_mode:
            self.mode_button.setText("Play 1 vs 1")
            self.mode_label.setText("Play vs AI Mode")
            self.difficulty_label.setVisible(True)
            self.difficulty_spinner.setVisible(True)
        else:
            self.mode_button.setText("Play vs AI")
            self.mode_label.setText("Two Player Mode")
            self.difficulty_label.setVisible(False)
            self.difficulty_spinner.setVisible(False)
        
        self.reset_game()
    
    def get_ai_depth(self):
        return self.current_ai_depth

    def on_difficulty_changed(self, new_value):
        if len(self.game.moves_history) > 0:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Change Difficulty")
            msg_box.setText(f"Changing AI difficulty requires starting a new game.")
            msg_box.setInformativeText(f"Do you want to start a new game with difficulty level {new_value}?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec_() == QMessageBox.Yes:
                self.current_ai_depth = new_value
                self.reset_game()
            else:
                self.difficulty_spinner.blockSignals(True)
                self.difficulty_spinner.setValue(self.current_ai_depth)
                self.difficulty_spinner.blockSignals(False)
        else:
            self.current_ai_depth = new_value

    def show_previous_move(self):
        if not self.game.board_states:
            return
            
        if self.game.current_view_index == -1:
            self.game.current_view_index = len(self.game.board_states) - 1
            
        if self.game.current_view_index > 0:
            self.game.current_view_index -= 1
            self.game.board = [row[:] for row in self.game.board_states[self.game.current_view_index]]
            self.board_widget.update()
            self.game.viewing_history = True
            self.update_navigation_buttons()
            self.steps_list.setCurrentRow(self.game.current_view_index)
            
    def show_next_move(self):
        if not self.game.board_states:
            return
            
        if self.game.current_view_index < len(self.game.board_states) - 1:
            self.game.current_view_index += 1
            self.game.board = [row[:] for row in self.game.board_states[self.game.current_view_index]]
            self.board_widget.update()
            
            if self.game.current_view_index == len(self.game.board_states) - 1:
                self.game.viewing_history = False
                self.game.current_view_index = -1
            
            self.update_navigation_buttons()
            self.steps_list.setCurrentRow(self.game.current_view_index)

    def update_navigation_buttons(self):
        if not self.game.board_states:
            self.prev_move_button.setEnabled(False)
            self.next_move_button.setEnabled(False)
            self.view_label.setText("Current view: No moves yet")
            return
            
        if self.game.current_view_index == -1:
            self.prev_move_button.setEnabled(len(self.game.board_states) > 0)
            self.next_move_button.setEnabled(False)
            self.view_label.setText("Current view: Latest move")
        else:
            self.prev_move_button.setEnabled(self.game.current_view_index > 0)
            self.next_move_button.setEnabled(self.game.current_view_index < len(self.game.board_states) - 1)
            self.view_label.setText(f"Current view: Move #{self.game.current_view_index + 1}")
            self.steps_list.setCurrentRow(self.game.current_view_index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HexWindow()
    window.show()
    sys.exit(app.exec_())
