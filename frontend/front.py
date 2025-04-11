import sys, math, os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSpinBox, QFormLayout, QMessageBox)
from PyQt5.QtGui import QPainter, QPolygonF, QColor, QPen, QFont, QBrush
from PyQt5.QtCore import Qt, QPointF, QSize

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import back

class HexGame:
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
        state = back.HexState(self.size, self.is_black_turn)
        state.board = [row[:] for row in self.board]
        return state

    def make_move(self, row, col):
        if self.game_over or self.board[row][col] != 0: return False
        
        self.board[row][col] = 1 if self.is_black_turn else 2
        player_color = "Blue" if self.is_black_turn else "Red"
        move_notation = f"{self.col_labels[col]}{self.row_labels[row]}"
        self.moves_history.append(f"{player_color}: {move_notation}")
        
        self.move_count += 1
        if self.move_count == 1: self.first_move = (row, col)
            
        self.is_black_turn = not self.is_black_turn
        self.board_states.append([row[:] for row in self.board])
        self.current_view_index = -1
        return True

    def check_winner(self):
        if back.check_win(self.board, 1):
            self.game_over, self.winner = True, 1
            return 1
        elif back.check_win(self.board, 2):
            self.game_over, self.winner = True, 2
            return 2
        return None

    def reset(self):
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
        
        def draw_border_line(v1, v2, color):
            painter.setPen(QPen(QColor(color), 2))
            painter.drawLine(int(v1[0]), int(v1[1]), int(v2[0]), int(v2[1]))
        
        painter.setPen(QPen(QColor("blue"), 2))
        for col in range(size):
            x, y = self.get_hex_position(0, col, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            draw_border_line([vertices[4].x(), vertices[4].y()], [vertices[5].x(), vertices[5].y()], "blue")
            draw_border_line([vertices[0].x(), vertices[0].y()], [vertices[5].x(), vertices[5].y()], "blue")
            
            x, y = self.get_hex_position(size-1, col, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            if col < size - 1:
                draw_border_line([vertices[1].x(), vertices[1].y()], [vertices[2].x(), vertices[2].y()], "blue")
            draw_border_line([vertices[2].x(), vertices[2].y()], [vertices[3].x(), vertices[3].y()], "blue")
            
        painter.setPen(QPen(QColor("red"), 2))
        for row in range(size):
            x, y = self.get_hex_position(row, 0, cx, cy, hex_width, hex_height)
            vertices = self.get_hex_vertices(x, y)
            draw_border_line([vertices[3].x(), vertices[3].y()], [vertices[4].x(), vertices[4].y()], "red")
            if row > 0:
                draw_border_line([vertices[4].x(), vertices[4].y()], [vertices[5].x(), vertices[5].y()], "red")
            
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
        
        # Only allow human moves when it's blue's turn (is_black_turn is True)
        if not self.game.is_black_turn:
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
            
            parent = self.parent()
            if hasattr(parent, "update_moves_list"):
                parent.update_moves_list()
            
            winner = self.game.check_winner()
            if winner:
                winner_name = "Blue (You)" if winner == 1 else "Red (AI)"
                msg = QMessageBox()
                msg.setWindowTitle("Game Over")
                msg.setText(f"{winner_name} has won the game by connecting their borders!")
                msg.setInformativeText("Click 'New Game' to play again.")
                msg.setIcon(QMessageBox.Information)
                msg.exec_()
                
                if hasattr(parent, "update_game_status"):
                    parent.update_game_status()
            
            # Automatically make AI move after player's move
            if not self.game.game_over:
                import time
                time.sleep(0.3)  # Short delay for better UX
                self.ai_move()

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
        
        # AI only plays as red (when is_black_turn is False)
        if self.game.is_black_turn:
            return
        
        parent = self.parent()
        ai_depth = parent.get_ai_depth() if hasattr(parent, "get_ai_depth") else 3
        
        state = self.game.to_python_state()
        best_move = back.find_best_move(state, depth=ai_depth)
        
        # Validate the move before applying it
        if (best_move[0] >= 0 and best_move[0] < self.game.size and 
            best_move[1] >= 0 and best_move[1] < self.game.size and 
            self.game.board[best_move[0]][best_move[1]] == 0):
            
            # Make the move without swapping coordinates
            if self.game.make_move(best_move[0], best_move[1]):
                self.update()
                
                if hasattr(parent, "update_moves_list"):
                    parent.update_moves_list()
                
                winner = self.game.check_winner()
                if winner:
                    winner_name = "Blue (You)" if winner == 1 else "Red (AI)"
                    msg = QMessageBox()
                    msg.setWindowTitle("Game Over")
                    msg.setText(f"{winner_name} has won the game by connecting their borders!")
                    msg.setInformativeText("Click 'New Game' to play again.")
                    msg.setIcon(QMessageBox.Information)
                    msg.exec_()
                    
                    if hasattr(parent, "update_game_status"):
                        parent.update_game_status()
        else:
            # Emergency fallback - find any valid move
            for r in range(self.game.size):
                for c in range(self.game.size):
                    if self.game.board[r][c] == 0:
                        if self.game.make_move(r, c):
                            print(f"Warning: Using emergency fallback move ({r},{c})")
                            self.update()
                            if hasattr(parent, "update_moves_list"):
                                parent.update_moves_list()
                            return

class HexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.game = HexGame(11)
        self.ai_mode = True  # Always set to AI mode
        self.current_ai_depth = 3
        
        self.setMinimumSize(QSize(1050, 700))
        self.setup_ui()

    def setup_ui(self):
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
        
        self.turn_label = QLabel("")
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.turn_label)
        
        self.game_status = QLabel("")
        self.game_status.setAlignment(Qt.AlignCenter)
        controls_layout.addRow(self.game_status)
        
        self.difficulty_layout = QHBoxLayout()
        self.difficulty_label = QLabel("AI Difficulty:")
        self.difficulty_spinner = QSpinBox()
        self.difficulty_spinner.setRange(1, 4)
        self.difficulty_spinner.setValue(3)
        self.difficulty_spinner.valueChanged.connect(self.on_difficulty_changed)
        self.difficulty_layout.addWidget(self.difficulty_label)
        self.difficulty_layout.addWidget(self.difficulty_spinner)
        controls_layout.addRow(self.difficulty_layout)
        
        self.difficulty_label.setVisible(True)
        self.difficulty_spinner.setVisible(True)
        
        left_layout.addWidget(controls_panel)

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        left_layout.addWidget(reset_button)
        
        self.mode_label = QLabel("Play vs AI Mode")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.mode_label)
        
        rules_label = QLabel("Blue: Connect blue borders • Red: Connect red borders")
        rules_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(rules_label)
        
        main_layout.addWidget(left_panel)
        
        main_layout.setStretch(0, 1)

    def update_game_status(self):
        if self.game.game_over:
            winner_color = "blue" if self.game.winner == 1 else "red"
            self.game_status.setText("Game Over")
            self.game_status.setStyleSheet(f"font-weight: bold; color: {winner_color};")
        else:
            self.game_status.setText("")

    def update_moves_list(self):
        self.update_turn_label()
        
        if self.ai_mode and not self.game.game_over and not self.game.is_black_turn:
            import time
            time.sleep(0.1)
            self.board_widget.ai_move()

    def reset_game(self):
        self.game.reset()
        self.board_widget.game = self.game
        self.board_widget.update()
        self.turn_label.setStyleSheet("font-weight: bold; color: white;")
        self.game_status.setText("")
        
        self.difficulty_spinner.setEnabled(True)
        if not self.game.is_black_turn:
            self.board_widget.ai_move()

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
        if self.game.game_over:
            winner_name = "Blue (You)" if self.game.winner == 1 else "Red (AI)"
            self.turn_label.setText(f"{winner_name} Wins!")
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {"blue" if self.game.winner == 1 else "red"}; font-size: 14px;")
        else:
            is_blue = self.game.is_black_turn
            player_name = "Blue (Your Turn)" if is_blue else "Red (AI Thinking...)"
            self.turn_label.setText(player_name)
            self.turn_label.setStyleSheet(f"font-weight: bold; color: {"blue" if is_blue else "red"};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HexWindow()
    window.show()
    sys.exit(app.exec_())
