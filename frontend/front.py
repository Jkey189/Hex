import sys, math, os, random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSpinBox, QFormLayout, QMessageBox, QComboBox)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont, QBrush
from PyQt5.QtCore import Qt, QPointF, QSize, QTimer

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
        self.paused = False # Add paused state

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
        if self.paused or self.game_over or self.board[row][col] != 0: return False # Check paused state
        
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
        if self.paused or self.move_count != 1 or self.is_black_turn: return False # Check paused state

        row, col = self.first_move # Get the original first move coordinates

        # Correct swap logic: Change the original piece to Red (2)
        self.board[row][col] = 2
        # Mirrored position logic removed

        # Update move notation to reflect the *original* position being taken by Red
        move_notation = f"{self.col_labels[col]}{self.row_labels[row]}"
        self.moves_history.append(f"Red: Swap ({move_notation})")

        # Print the swap move to console (using the original location)
        print(f"{move_notation} - red (swap)")

        self.move_count += 1
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board]) # Save state after swap
        self.current_view_index = -1 # Reset history view
        return True

    def check_winner(self):
        """
        Checks if either player has won by connecting their sides.
        Blue (Player 1) wins by connecting top and bottom.
        Red (Player 2) wins by connecting left and right.
        
        Returns:
            int or None: 1 for Blue win, 2 for Red win, None if no winner
        """
        # --- DEBUG PRINT --- Print board state before checking win
        print("--- Checking Winner ---")
        print(f"Current Player Check: {1 if self.is_black_turn else 2}") # Note: This might be confusing, check_winner checks *both*
        print("Board State Being Checked:")
        for r_idx, row in enumerate(self.board):
            print(f"  {r_idx}: {row}")
        # ---------------------

        if back.check_win(self.board, 1):
            print("DEBUG: back.check_win(board, 1) returned True") # Add debug print
            self.game_over, self.winner = True, 1
            return 1
        elif back.check_win(self.board, 2):
            print("DEBUG: back.check_win(board, 2) returned True") # Add debug print
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
        self.paused = False # Reset paused state

    def toggle_pause(self):
        """ Toggles the paused state of the game. """
        if not self.game_over: # Only allow pausing if game is not over
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
        if self.game.paused: # Prevent clicks if paused
            return

        # Allow clicks if game is not over, not viewing history, AND
        # (mode is PvA and it's Blue's turn) OR (mode is PvP and it's the current player's turn)
        allow_click = False
        if not self.game.game_over and not self.game.viewing_history:
            if self.main_window.game_mode == "PvA" and self.game.is_black_turn:
                allow_click = True
            elif self.main_window.game_mode == "PvP":
                allow_click = True # Both players click, make_move checks turn internally implicitly

        if not allow_click:
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
        
        # Check if a valid hex cell was clicked
        if closest_row >= 0 and closest_col >= 0:
            # --- PvP Swap Logic --- Check if Red player clicked on Blue's first move to swap
            is_pvp = self.main_window.game_mode == "PvP"
            is_second_move = self.game.move_count == 1
            is_red_turn = not self.game.is_black_turn
            clicked_first_move = (closest_row, closest_col) == self.game.first_move

            move_successful = False
            if is_pvp and is_second_move and is_red_turn and clicked_first_move:
                move_successful = self.game.swap_move()
            else:
                # --- Regular Move Logic ---
                move_successful = self.game.make_move(closest_row, closest_col)
            # -------------------------

            # User (Blue or Red in PvP) makes a move or swaps
            if move_successful:
                self.update()

                # Update navigation buttons state immediately
                if hasattr(self.main_window, "update_navigation_buttons"):
                    self.main_window.update_navigation_buttons()

                # Update turn label immediately after user move
                if hasattr(self.main_window, "update_turn_label"):
                    self.main_window.update_turn_label()

                # Check if user won
                winner = self.game.check_winner()
                if winner:
                    # Use the helper function to show the winner message
                    self._show_winner_message(winner)
                    if hasattr(self.main_window, "update_game_status"):
                        self.main_window.update_game_status()
                else:
                    # Only trigger AI if in PvA mode and it's now AI's (Red's) turn
                    if self.main_window.game_mode == "PvA" and not self.game.is_black_turn:
                        QTimer.singleShot(500, self.trigger_ai_move)
                    # In PvP mode, do nothing - wait for the next player's click.
                    # In AvA mode, clicks are disabled anyway.

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

    # Renamed from ai_move, now handles AI move for the CURRENT player
    def trigger_ai_move(self):
        if self.game.paused or self.game.game_over: # Prevent AI moves if paused or game over
            return

        ai_depth = self.main_window.current_ai_depth if hasattr(self.main_window, "current_ai_depth") else 3
        current_player = 1 if self.game.is_black_turn else 2

        # --- Swap Logic (Only relevant for Red on move 2) ---
        if self.game.move_count == 1 and current_player == 2: # Red's first potential move
            row, col = self.game.first_move
            center = self.game.size // 2
            # Basic swap logic: swap if Blue's first move is near center
            if abs(row - center) <= 1 and abs(col - center) <= 1:
                if self.game.swap_move():
                    self.update()
                    winner = self.game.check_winner()
                    if winner: self._show_winner_message(winner)
                    # Update turn label after potential swap
                    if hasattr(self.main_window, "update_turn_label"):
                        self.main_window.update_turn_label()

                    # If swap occurred in AvA mode, trigger next AI move (Blue)
                    if not self.game.game_over and self.main_window.game_mode == "AvA":
                        QTimer.singleShot(500, self.trigger_ai_move)
                    return # Swap was made, AI doesn't need to move this turn
        # --- End Swap Logic ---

        # Get the best move from the backend alpha-beta implementation
        current_state = self.game.to_python_state() # Get HexState object for the backend
        best_move = back.find_best_move(current_state, depth=ai_depth)

        if best_move != (-1, -1): # Check if a valid move was found
            if self.game.make_move(best_move[0], best_move[1]):
                self.update()

                # Update navigation buttons state immediately
                if hasattr(self.main_window, "update_navigation_buttons"):
                    self.main_window.update_navigation_buttons()

                # Update turn label after AI move
                if hasattr(self.main_window, "update_turn_label"):
                    self.main_window.update_turn_label()

                winner = self.game.check_winner()
                if winner:
                    self._show_winner_message(winner) # Use helper for message box
                    if hasattr(self.main_window, "update_game_status"):
                        self.main_window.update_game_status()
                elif self.main_window.game_mode == "AvA": # If game not over and in AvA mode, trigger next AI
                    QTimer.singleShot(500, self.trigger_ai_move)
            else:
                # Fallback if alpha-beta suggested an invalid move
                print(f"AI ({current_player}) suggested an invalid move: {best_move}")
                # Optionally, fall back to random move or stop in AvA?
                # For now, just print and stop the AvA chain if error occurs
        else:
             print(f"AI ({current_player}) could not find a valid move.") # Or game ended before AI move

    # Helper function to show winner message (generalized for modes)
    def _show_winner_message(self, winner):
        # Determine winner name based on mode
        if self.main_window.game_mode == "PvP":
            winner_name = "Blue (Player)" if winner == 1 else "Red (Player)"
        elif self.main_window.game_mode == "PvA":
            winner_name = "Blue (You)" if winner == 1 else "Red (AI)"
        else: # AvA
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
        self.ai_mode = True  # Keep true to block user clicks during Red's turn (used indirectly now)
        self.current_ai_depth = 3 # Default AI depth (Difficult)
        self.game_mode = "PvA" # Default game mode: Player vs AI
        
        # Increase minimum window size
        self.setMinimumSize(QSize(1200, 850))
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.board_widget = HexBoard(self.game, main_window=self)
        left_layout.addWidget(self.board_widget)
        left_layout.addStretch(1) # Keep stretch below board

        # Add stretch factor *before* controls to push them down
        left_layout.addStretch(1)

        controls_panel = QWidget()
        controls_layout = QFormLayout(controls_panel)
        
        self.turn_label = QLabel("")
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.turn_label)
        
        self.game_status = QLabel("")
        self.game_status.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.game_status)
        
        # Remove AI Difficulty from controls panel - will move to a horizontal layout later
        left_layout.addWidget(controls_panel)

        # --- Add Pause Button ---
        self.pause_button = QPushButton("Pause Game")
        self.pause_button.clicked.connect(self.toggle_pause)
        left_layout.addWidget(self.pause_button)
        # ------------------------

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        # Create a horizontal layout for game settings
        settings_layout = QHBoxLayout()
        settings_layout.setAlignment(Qt.AlignCenter)
        
        # --- Add AI Difficulty dropdown to settings layout ---
        difficulty_layout = QHBoxLayout()
        difficulty_label = QLabel("AI Difficulty:")
        difficulty_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Difficult"])
        # Map depth to initial text selection
        if self.current_ai_depth == 1:
            initial_difficulty_text = "Easy"
        elif self.current_ai_depth == 2:
            initial_difficulty_text = "Medium"
        else: # Default to Difficult for 3 or other values
            initial_difficulty_text = "Difficult"
            self.current_ai_depth = 3 # Ensure depth matches text
        self.difficulty_combo.setCurrentText(initial_difficulty_text)
        self.difficulty_combo.setMinimumWidth(100)
        self.difficulty_combo.currentIndexChanged.connect(self.update_ai_difficulty)
        difficulty_layout.addWidget(difficulty_label)
        difficulty_layout.addWidget(self.difficulty_combo)
        settings_layout.addLayout(difficulty_layout)
        # ------------------------------------------------------
        
        # Add Game Mode Selection
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
        
        rules_label = QLabel("Blue: Connect blue borders • Red: Connect red borders")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)

        # --- RE-ADD Navigation Buttons --- 
        navigation_layout = QHBoxLayout()
        self.prev_move_button = QPushButton("Previous Move")
        self.prev_move_button.clicked.connect(self.show_previous_move)
        self.next_move_button = QPushButton("Next Move")
        self.next_move_button.clicked.connect(self.show_next_move)
        navigation_layout.addWidget(self.prev_move_button)
        navigation_layout.addWidget(self.next_move_button)
        left_layout.addLayout(navigation_layout)
        # ---------------------------------

        self.view_label = QLabel("Current view: Latest move")
        self.view_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.view_label)

        main_layout.addWidget(left_panel)
        
        main_layout.setStretch(0, 1)

    def update_game_status(self):
        if self.game.game_over:
            self.game_status.setText("Game Over")
            self.game_status.setStyleSheet("font-weight: bold; color: lightgray;")
            self.pause_button.setEnabled(True) # Disable pause when game over
        elif self.game.paused:
            self.game_status.setText("")
            self.game_status.setStyleSheet("font-weight: bold; color: yellow;")
        else:
            self.game_status.setText("")
            self.game_status.setStyleSheet("")

    def reset_game(self):
        if self.game.paused: # Ensure game is resumed before reset
            self.toggle_pause()
        self.game.reset()
        self.board_widget.game = self.game
        self.board_widget.update()
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.game_status.setText("")
        self.difficulty_combo.setEnabled(True) # Re-enable combo on new game
        self.pause_button.setText("Pause Game") # Reset button text
        # Reset viewing history state
        self.game.current_view_index = -1
        self.game.viewing_history = False
        self.update_navigation_buttons()
        self.update_turn_label() # Update label for Blue's turn

        # If mode is AI vs AI, start the game loop
        if self.game_mode == "AvA":
            # Need a small delay to allow UI to settle before AI starts
            QTimer.singleShot(500, self.board_widget.trigger_ai_move)

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

    def update_turn_label(self):
        if self.game.paused:
            self.turn_label.setText("Game Paused")
            self.turn_label.setStyleSheet("font-weight: bold; color: yellow;")
            return

        if self.game.game_over:
            # Determine winner name based on mode
            if self.game_mode == "PvP":
                 winner_name = "Blue (Player)" if self.game.winner == 1 else "Red (Player)"
            elif self.game_mode == "PvA":
                 winner_name = "Blue (You)" if self.game.winner == 1 else "Red (AI)"
            else: # AvA mode
                 winner_name = "Blue (AI)" if self.game.winner == 1 else "Red (AI)"
            self.turn_label.setText(f"{winner_name} Wins!")
            # Use lighter shades for winner announcement
            winner_color = "lightblue" if self.game.winner == 1 else "lightcoral" # Lighter blue/red
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {winner_color}; font-size: 14px;")
        else:
            is_blue = self.game.is_black_turn
            # Determine player name based on mode and turn
            if self.game_mode == "PvP":
                player_name = "Blue's Turn" if is_blue else "Red's Turn"
            elif self.game_mode == "PvA":
                player_name = "Blue's Turn" if is_blue else "Red (AI Thinking...)"
            else: # AvA mode
                player_name = "Blue (AI Thinking...)" if is_blue else "Red (AI Thinking...)"
            self.turn_label.setText(player_name)
            # Use lighter shades for turn indicator
            turn_color = "lightblue" if is_blue else "lightcoral" # Lighter blue/red
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {turn_color};")

    # Slot to update AI difficulty when combo box changes
    def update_ai_difficulty(self, index):
        difficulty_text = self.difficulty_combo.itemText(index)
        # Map text to depth
        if difficulty_text == "Easy":
            new_depth = 1
        elif difficulty_text == "Medium":
            new_depth = 2
        else: # Difficult
            new_depth = 3

        # Check if game is in progress and value actually changed
        if self.game.move_count > 0 and new_depth != self.current_ai_depth:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Confirm Difficulty Change")
            msg_box.setText("Changing the AI difficulty will reset the current game.")
            msg_box.setInformativeText(f"Do you want to reset the game to '{difficulty_text}' difficulty?")
            reset_button = msg_box.addButton("Reset Game", QMessageBox.AcceptRole) # Yes
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)    # No
            msg_box.setDefaultButton(cancel_button)

            msg_box.exec_()

            if msg_box.clickedButton() == reset_button:
                # User confirmed reset
                self.current_ai_depth = new_depth
                self.reset_game() # reset_game handles UI state
            else:
                # User cancelled - revert combo box value visually
                # Determine current difficulty text based on self.current_ai_depth
                if self.current_ai_depth == 1:
                    current_difficulty_text = "Easy"
                elif self.current_ai_depth == 2:
                    current_difficulty_text = "Medium"
                else: # 3
                    current_difficulty_text = "Difficult"

                self.difficulty_combo.blockSignals(True)
                self.difficulty_combo.setCurrentText(current_difficulty_text)
                self.difficulty_combo.blockSignals(False)
        else:
             # Game not started or value is the same, just update internal depth
            self.current_ai_depth = new_depth
            # Ensure combo box reflects the value if game hasn't started
            if self.game.move_count == 0:
                # Determine current difficulty text based on self.current_ai_depth
                if self.current_ai_depth == 1:
                    current_difficulty_text = "Easy"
                elif self.current_ai_depth == 2:
                    current_difficulty_text = "Medium"
                else: # 3
                    current_difficulty_text = "Difficult"

                self.difficulty_combo.blockSignals(True)
                self.difficulty_combo.setCurrentText(current_difficulty_text)
                self.difficulty_combo.blockSignals(False)

    # Slot to change game mode when combo box changes
    def change_game_mode(self, index):
        new_mode_text = self.mode_combo.itemText(index)
        # Map text to mode identifier
        if new_mode_text == "Player vs Player":
            new_mode = "PvP"
        elif new_mode_text == "Player vs AI":
            new_mode = "PvA"
        else: # "AI vs AI"
            new_mode = "AvA"

        # Check if game is in progress and mode actually changed
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
                # User confirmed reset
                self.game_mode = new_mode
                self.reset_game()
            else:
                # User cancelled - revert combo box value visually
                # Determine current mode text based on self.game_mode
                if self.game_mode == "PvP":
                    current_mode_text = "Player vs Player"
                elif self.game_mode == "PvA":
                    current_mode_text = "Player vs AI"
                else: # AvA
                    current_mode_text = "AI vs AI"
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText(current_mode_text)
                self.mode_combo.blockSignals(False)
        else:
            # Game not started or mode is the same, just update
            self.game_mode = new_mode
            # If game hasn't started, ensure combo reflects the mode
            if self.game.move_count == 0:
                # Determine current mode text based on self.game_mode
                if self.game_mode == "PvP":
                    current_mode_text = "Player vs Player"
                elif self.game_mode == "PvA":
                    current_mode_text = "Player vs AI"
                else: # AvA
                    current_mode_text = "AI vs AI"
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText(current_mode_text)
                self.mode_combo.blockSignals(False)

    # --- Add Toggle Pause Method ---
    def toggle_pause(self):
        is_now_paused = self.game.toggle_pause()
        self.pause_button.setText("Resume Game" if is_now_paused else "Pause Game")
        self.update_turn_label()
        self.update_game_status()
        
        # If resuming in AI mode and it's AI's turn, trigger the move
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
