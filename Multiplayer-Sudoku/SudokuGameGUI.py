from Tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM

MARGIN = 20  # Pixels around the board
SIDE = 50  # Width of every board cell.
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # Width and height of the whole board


class SudokuUI(Frame):
    """
    Sudoku grid UI class."""

    def __init__(self, parent, board):
        self.game = board
        Frame.__init__(self, parent)
        self.parent = parent

        self.row, self.col = -1, -1
        self.new_entry = None
        self.previous_guess = None

        self.game_state = 0

        self.__initUI()

    def __initUI(self):
        """
        Initialize sudoku playing field grid and bind clicking and entry handlers."""

        self.parent.title("Sudoku")
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self,
                             width=WIDTH,
                             height=HEIGHT)
        self.canvas.pack(fill=BOTH, side=TOP)

        self.__draw_grid()
        self.__draw_puzzle()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __draw_grid(self):
        """
        Draw Sudoku 3x3 x 3x3 grid."""

        for i in xrange(10):
            color = "blue" if i % 3 == 0 else "gray"

            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = HEIGHT - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = WIDTH - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def __draw_puzzle(self):
        """
        Draw Sudoku solution numbers."""

        self.canvas.delete("numbers")
        for i in xrange(9):
            for j in xrange(9):
                answer = self.game.board[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers"
                    )

    def __cell_clicked(self, event):
        """
        Handle a single cell click and highlight the clicked cell.
        :param event:
        """
        x, y = event.x, event.y
        if MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN:
            self.canvas.focus_set()

            # get row and col numbers from x,y coordinates
            row, col = (y - MARGIN) / SIDE, (x - MARGIN) / SIDE

            # if cell was selected already - deselect it
            if (row, col) == (self.row, self.col):
                self.row, self.col = -1, -1
            elif self.game.board[row][col] == 0:
                self.row, self.col = row, col

        self.__draw_cursor()

    def __draw_cursor(self):
        """
        Draw the red outline for the selected square."""

        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="red", tags="cursor"
            )

    def __key_pressed(self, event):
        """
        Handle solution number entry."""

        if self.row >= 0 and self.col >= 0 and event.char in "123456789":
            self.new_entry = (self.row, self.col, int(event.char))
            self.col, self.row = -1, -1
            self.__draw_puzzle()
            self.__draw_cursor()

    def update_board(self, root, board, new_game_state):
        """
        Update board during the gameplay. If all players are not connected, solution entry is not permitted.
        In case of a wrong answer the selected square is flashed red for a fraction of a second to notify
        the player about his life decisions.

        :param root:
        :param board:
        :param new_game_state:
        :return entered value:
        """
        return_val = None

        # Check for game state, if it is "0", just return, else continue the game
        if self.game_state == 0:
            root.update()

            if new_game_state != 0:
                self.game_state = new_game_state
            return return_val

        # If previous guess was not correct flash it red
        if self.previous_guess is not None and board[self.previous_guess[0]][self.previous_guess[1]] != \
                self.previous_guess[2]:
            row, col, _ = self.previous_guess
            x0 = MARGIN + col * SIDE + 1
            y0 = MARGIN + row * SIDE + 1
            x1 = MARGIN + (col + 1) * SIDE - 1
            y1 = MARGIN + (row + 1) * SIDE - 1
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="red", tags="fail")
        else:
            self.canvas.delete("fail")

        # Initiate return value to none, update the board and draw it
        self.game.update_board(board)
        self.__draw_puzzle()
        root.update()

        # If user has entered anything in between, write it into the return value and previous guess and return
        if self.new_entry is not None:
            return_val = self.new_entry
            self.previous_guess = self.new_entry
            self.new_entry = None
        else:
            self.previous_guess = None

        return return_val


class SudokuBoard(object):
    """
    Sudoku Board representation"""

    def __init__(self, board):
        self.board = self.__create_board(board)

    def __create_board(self, input_board):
        if len(input_board) != 9:
            raise SudokuError("There must be 9 rows to the board")

        for row in input_board:
            if len(row) != 9:
                raise SudokuError("There must be 9 columns to a row")

            for digit in row:
                if type(digit) != int and 0 <= digit < 10:
                    raise SudokuError("Only numbers between 0-9 are permitted on the sudoku field")

        return input_board

    def update_board(self, input_board):
        if len(input_board) != 9:
            raise SudokuError("There must be 9 rows to the board")

        for row in input_board:
            if len(row) != 9:
                raise SudokuError("There must be 9 columns to a row")

            for digit in row:
                if type(digit) != int and 0 <= digit < 10:
                    raise SudokuError("Only numbers between 0-9 are permitted on the sudoku field")

        self.board = input_board


class SudokuError(Exception):
    """
    An application specific error.
    """
    pass
