#!/usr/bin/env python3
import sys, math, os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFormLayout, QMessageBox, QComboBox)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QPointF, QSize, QTimer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import back

class HexGame:
    """
    Main game logic class for Hex.
    """
    def __init__(self, size):
        self.size = size
        self.board = [[0] * size for _ in range(size)]
        self.is_black_turn = True  # Blue is first player
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
        self.paused = False

    def to_python_state(self):
        """Converts current game state to HexState object for AI"""
        state = back.HexState(self.size, self.is_black_turn)
        state.board = [row[:] for row in self.board]
        return state

    def make_move(self, row, col):
        """Makes a move at the specified position"""
        if self.paused or self.game_over or self.board[row][col] != 0:
            return False
        
        self.board[row][col] = 1 if self.is_black_turn else 2
        player_color = "Blue" if self.is_black_turn else "Red"
        move_notation = f"{self.col_labels[col]}{self.row_labels[row]}"
        self.moves_history.append(f"{player_color}: {move_notation}")
        
        self.move_count += 1
        if self.move_count == 1:
            self.first_move = (row, col)
            
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board])
        self.current_view_index = -1
        return True
        
    def swap_move(self):
        """Implements the pie rule (swap)"""
        if self.paused or self.move_count != 1 or self.is_black_turn:
            return False

        row, col = self.first_move
        # Change original piece to Red (2)
        self.board[row][col] = 2
        
        move_notation = f"{self.col_labels[col]}{self.row_labels[row]}"
        self.moves_history.append(f"Red: Swap ({move_notation})")
        
        self.move_count += 1
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board])
        self.current_view_index = -1
        return True

    def check_winner(self):
        """Checks if either player has won"""
        if back.check_win(self.board, 1):
            self.game_over, self.winner = True, 1
            return 1
        elif back.check_win(self.board, 2):
            self.game_over, self.winner = True, 2
            return 2
        return None

    def reset(self):
        """Resets the game to initial state"""
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
        self.paused = False

    def toggle_pause(self):
        """Toggles pause state"""
        if not self.game_over:
            self.paused = not self.paused
            return self.paused
        return False

class HexBoard(QWidget):
    def __init__(self, game, main_window, parent=None):
        super().__init__(parent)
        self.game = game
        self.main_window = main_window
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
        if self.game.paused:
            return

        # Handle clicks based on game mode
        allow_click = False
        if not self.game.game_over and not self.game.viewing_history:
            if self.main_window.game_mode == "PvA" and self.game.is_black_turn:
                allow_click = True
            elif self.main_window.game_mode == "PvP":
                allow_click = True

        if not allow_click:
            return

        # Find which hex was clicked
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
        
        # Process the move if a hex was clicked
        if closest_row >= 0 and closest_col >= 0:
            # Handle swap rule in PvP mode
            is_pvp = self.main_window.game_mode == "PvP"
            is_second_move = self.game.move_count == 1
            is_red_turn = not self.game.is_black_turn
            clicked_first_move = (closest_row, closest_col) == self.game.first_move

            move_successful = False
            if is_pvp and is_second_move and is_red_turn and clicked_first_move:
                move_successful = self.game.swap_move()
            else:
                move_successful = self.game.make_move(closest_row, closest_col)

            if move_successful:
                self.update()
                self.main_window.update_navigation_buttons()
                self.main_window.update_turn_label()

                # Check for win condition
                winner = self.game.check_winner()
                if winner:
                    self._show_winner_message(winner)
                    self.main_window.update_game_status()
                # Trigger AI move if needed
                elif self.main_window.game_mode == "PvA" and not self.game.is_black_turn:
                    QTimer.singleShot(500, self.trigger_ai_move)

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

    def trigger_ai_move(self):
        """Handles AI moves"""
        if self.game.paused or self.game.game_over:
            return

        ai_depth = self.main_window.current_ai_depth
        current_player = 1 if self.game.is_black_turn else 2

        # Handle swap rule for AI (Red's second move)
        if self.game.move_count == 1 and current_player == 2:
            row, col = self.game.first_move
            center = self.game.size // 2
            # Swap if first move was advantageous (near center)
            if abs(row - center) <= 1 and abs(col - center) <= 1:
                if self.game.swap_move():
                    self.update()
                    winner = self.game.check_winner()
                    if winner:
                        self._show_winner_message(winner)
                    self.main_window.update_turn_label()

                    # If swap in AvA mode, trigger next AI move
                    if not self.game.game_over and self.main_window.game_mode == "AvA":
                        QTimer.singleShot(200, self.trigger_ai_move)
                    return

        # Get best move from AI
        current_state = self.game.to_python_state()
        best_move = back.find_best_move(current_state, depth=ai_depth)

        if best_move != (-1, -1):
            if self.game.make_move(best_move[0], best_move[1]):
                self.update()
                self.main_window.update_navigation_buttons()
                self.main_window.update_turn_label()

                winner = self.game.check_winner()
                if winner:
                    self._show_winner_message(winner)
                    self.main_window.update_game_status()
                elif self.main_window.game_mode == "AvA":
                    QTimer.singleShot(500, self.trigger_ai_move)

    def _show_winner_message(self, winner):
        """Shows winner message dialog"""
        if self.main_window.game_mode == "PvP":
            winner_name = "Blue (Player)" if winner == 1 else "Red (Player)"
        elif self.main_window.game_mode == "PvA":
            winner_name = "Blue (You)" if winner == 1 else "Red (AI)"
        else:  # AvA
            winner_name = "Blue (AI)" if winner == 1 else "Red (AI)"

        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"{winner_name} has won the game by connecting their borders!")
        msg.setInformativeText("Click 'New Game' to play again.")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

class HexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.game = HexGame(11)
        self.current_ai_depth = 3  # Default AI depth (Difficult)
        self.game_mode = "PvA"     # Default game mode: Player vs AI
        
        self.setMinimumSize(QSize(1200, 850))
        self.setup_ui()

    def setup_ui(self):
        """Creates and arranges all UI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel containing board and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Board widget
        self.board_widget = HexBoard(self.game, main_window=self)
        left_layout.addWidget(self.board_widget)
        left_layout.addStretch(1)

        # Game status area
        controls_panel = QWidget()
        controls_layout = QFormLayout(controls_panel)
        
        self.turn_label = QLabel("")
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.turn_label)
        
        self.game_status = QLabel("")
        self.game_status.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.game_status)
        
        left_layout.addWidget(controls_panel)

        # Game control buttons
        self.pause_button = QPushButton("Pause Game")
        self.pause_button.clicked.connect(self.toggle_pause)
        left_layout.addWidget(self.pause_button)

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        # Game settings layout
        settings_layout = QHBoxLayout()
        settings_layout.setAlignment(Qt.AlignCenter)
        
        # AI Difficulty settings
        difficulty_layout = QHBoxLayout()
        difficulty_label = QLabel("AI Difficulty:")
        difficulty_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Difficult"])
        
        # Set initial difficulty text
        if self.current_ai_depth == 1:
            initial_difficulty_text = "Easy"
        elif self.current_ai_depth == 2:
            initial_difficulty_text = "Medium"
        else:
            initial_difficulty_text = "Difficult"
        
        self.difficulty_combo.setCurrentText(initial_difficulty_text)
        self.difficulty_combo.setMinimumWidth(100)
        self.difficulty_combo.currentIndexChanged.connect(self.update_ai_difficulty)
        difficulty_layout.addWidget(difficulty_label)
        difficulty_layout.addWidget(self.difficulty_combo)
        settings_layout.addLayout(difficulty_layout)
        
        # Game Mode selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Game Mode:")
        mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Player vs Player", "Player vs AI", "AI vs AI"])
        self.mode_combo.setCurrentText("Player vs AI" if self.game_mode == "PvA" else "AI vs AI")
        self.mode_combo.currentIndexChanged.connect(self.change_game_mode)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)
        
        left_layout.addLayout(settings_layout)
        
        # Game rules label
        rules_label = QLabel("Blue: Connect blue borders • Red: Connect red borders")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)

        # Move navigation buttons
        navigation_layout = QHBoxLayout()
        self.prev_move_button = QPushButton("Previous Move")
        self.prev_move_button.clicked.connect(self.show_previous_move)
        self.next_move_button = QPushButton("Next Move")
        self.next_move_button.clicked.connect(self.show_next_move)
        navigation_layout.addWidget(self.prev_move_button)
        navigation_layout.addWidget(self.next_move_button)
        left_layout.addLayout(navigation_layout)

        self.view_label = QLabel("Current view: Latest move")
        self.view_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.view_label)

        main_layout.addWidget(left_panel)
        main_layout.setStretch(0, 1)
        
        # Initialize UI state
        self.update_turn_label()
        self.update_navigation_buttons()

    def update_game_status(self):
        """Updates game status display"""
        if self.game.game_over:
            self.game_status.setText("Game Over")
            self.game_status.setStyleSheet("font-weight: bold; color: lightgray;")
            self.pause_button.setEnabled(False)
        elif self.game.paused:
            self.game_status.setText("Paused")
            self.game_status.setStyleSheet("font-weight: bold; color: yellow;")
        else:
            self.game_status.setText("")
            self.game_status.setStyleSheet("")
            self.pause_button.setEnabled(True)

    def reset_game(self):
        """Resets the game and UI"""
        if self.game.paused:
            self.toggle_pause()
        self.game.reset()
        self.board_widget.update()
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.game_status.setText("")
        self.difficulty_combo.setEnabled(True)
        self.pause_button.setText("Pause Game")
        self.pause_button.setEnabled(True)
        self.update_navigation_buttons()
        self.update_turn_label()

        # Start AI vs AI game if in that mode
        if self.game_mode == "AvA":
            QTimer.singleShot(500, self.board_widget.trigger_ai_move)

    def show_previous_move(self):
        """Shows the previous move in history"""
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
            
    def show_next_move(self):
        """Shows the next move in history"""
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

    def update_navigation_buttons(self):
        """Updates the state of move navigation buttons"""
        if not self.game.board_states:
            self.prev_move_button.setEnabled(False)
            self.next_move_button.setEnabled(False)
            self.view_label.setText("Current view: No moves yet")
            return
            
        if self.game.current_view_index == -1:
            self.prev_move_button.setEnabled(True)
            self.next_move_button.setEnabled(False)
            self.view_label.setText("Current view: Latest move")
        else:
            self.prev_move_button.setEnabled(self.game.current_view_index > 0)
            self.next_move_button.setEnabled(self.game.current_view_index < len(self.game.board_states) - 1)
            self.view_label.setText(f"Current view: Move #{self.game.current_view_index + 1}")

    def update_turn_label(self):
        """Updates the turn indicator label"""
        if self.game.paused:
            self.turn_label.setText("Game Paused")
            self.turn_label.setStyleSheet("font-weight: bold; color: yellow;")
            return

        if self.game.game_over:
            # Show winner
            if self.game_mode == "PvP":
                winner_name = "Blue (Player)" if self.game.winner == 1 else "Red (Player)"
            elif self.game_mode == "PvA":
                winner_name = "Blue (You)" if self.game.winner == 1 else "Red (AI)"
            else:  # AvA mode
                winner_name = "Blue (AI)" if self.game.winner == 1 else "Red (AI)"
                
            self.turn_label.setText(f"{winner_name} Wins!")
            winner_color = "lightblue" if self.game.winner == 1 else "lightcoral"
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {winner_color}; font-size: 14px;")
        else:
            # Show current turn
            is_blue = self.game.is_black_turn
            if self.game_mode == "PvP":
                player_name = "Blue's Turn" if is_blue else "Red's Turn"
            elif self.game_mode == "PvA":
                player_name = "Blue's Turn" if is_blue else "Red (AI Thinking...)"
            else:  # AvA mode
                player_name = "Blue (AI Thinking...)" if is_blue else "Red (AI Thinking...)"
                
            self.turn_label.setText(player_name)
            turn_color = "lightblue" if is_blue else "lightcoral"
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {turn_color};")
            
        self.update_game_status()

    def update_ai_difficulty(self, index):
        """Updates the AI difficulty level"""
        difficulty_text = self.difficulty_combo.itemText(index)
        if difficulty_text == "Easy":
            new_depth = 1
        elif difficulty_text == "Medium":
            new_depth = 2
        else:  # Difficult
            new_depth = 3

        # Confirm reset if game in progress
        if self.game.move_count > 0 and new_depth != self.current_ai_depth:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Confirm Difficulty Change")
            msg_box.setText("Changing the AI difficulty will reset the current game.")
            msg_box.setInformativeText(f"Do you want to reset the game to '{difficulty_text}' difficulty?")
            reset_button = msg_box.addButton("Reset Game", QMessageBox.AcceptRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_button)

            msg_box.exec_()

            if msg_box.clickedButton() == reset_button:
                self.current_ai_depth = new_depth
                self.reset_game()
            else:
                # Revert combo box if canceled
                self._update_difficulty_combo_value()
        else:
            # Just update if game not started
            self.current_ai_depth = new_depth
            if self.game.move_count == 0:
                self._update_difficulty_combo_value()
                
    def _update_difficulty_combo_value(self):
        """Updates difficulty combo value without triggering signals"""
        if self.current_ai_depth == 1:
            current_difficulty_text = "Easy"
        elif self.current_ai_depth == 2:
            current_difficulty_text = "Medium"
        else:  # 3
            current_difficulty_text = "Difficult"
            
        self.difficulty_combo.blockSignals(True)
        self.difficulty_combo.setCurrentText(current_difficulty_text)
        self.difficulty_combo.blockSignals(False)

    def change_game_mode(self, index):
        """Changes the game mode"""
        new_mode_text = self.mode_combo.itemText(index)
        if new_mode_text == "Player vs Player":
            new_mode = "PvP"
        elif new_mode_text == "Player vs AI":
            new_mode = "PvA"
        else:  # "AI vs AI"
            new_mode = "AvA"

        # Confirm reset if game in progress
        if self.game.move_count > 0 and new_mode != self.game_mode:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Confirm Mode Change")
            msg_box.setText("Changing the game mode will reset the current game.")
            msg_box.setInformativeText(f"Do you want to reset the game to '{new_mode_text}' mode?")
            reset_button = msg_box.addButton("Reset Game", QMessageBox.AcceptRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_button)

            msg_box.exec_()

            if msg_box.clickedButton() == reset_button:
                self.game_mode = new_mode
                self.reset_game()
            else:
                # Revert combo box if canceled
                self._update_mode_combo_value()
        else:
            # Just update if game not started
            self.game_mode = new_mode
            if self.game.move_count == 0:
                self._update_mode_combo_value()
                
    def _update_mode_combo_value(self):
        """Updates mode combo value without triggering signals"""
        if self.game_mode == "PvP":
            current_mode_text = "Player vs Player"
        elif self.game_mode == "PvA":
            current_mode_text = "Player vs AI"
        else:  # AvA
            current_mode_text = "AI vs AI"
            
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText(current_mode_text)
        self.mode_combo.blockSignals(False)

    def toggle_pause(self):
        """Toggles the game pause state"""
        is_now_paused = self.game.toggle_pause()
        self.pause_button.setText("Resume Game" if is_now_paused else "Pause Game")
        self.update_turn_label()
        
        # Resume AI turns if needed
        if not is_now_paused and not self.game.game_over:
            if self.game_mode == "AvA":
                QTimer.singleShot(500, self.board_widget.trigger_ai_move)
            elif self.game_mode == "PvA" and not self.game.is_black_turn:
                QTimer.singleShot(500, self.board_widget.trigger_ai_move)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HexWindow()
    window.show()
    sys.exit(app.exec_())
