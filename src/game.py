
def read_solution():
    """
    Reads the Sudoku starting board and solution from a file
    """
    f = open("solutions.txt", "r")
    solution = [[None]*9 for x in range(0,9)]
    for i in range(9):
        row = f.readline().strip()
        split_row = row.split(" ")
        for j in range(9):
            solution[i][j] = int (split_row[j])
                     
    f.readline()
    
    board = [[None]*9 for x in range(0,9)]
    for i in range(9):
        row = f.readline().strip()
        split_row = row.split(" ")
        for j in range(9):
            board[i][j] = int (split_row[j])
    f.close()

    return solution, board


class Game:

    def __init__(self, max_players):
        """
        Creates a new game
        :param max_players: number of players that can play the game at once
        :return:
        """
        self.solution, self.board = read_solution()
        self.scores = {}
        self.max_players = int(max_players)
        self.game_state = 0

    def make_move(self, user_id, x, y, value):
        """
        Processes a player's move
        :param user_id: player's id
        :param x: row number
        :param y: column number
        :param value: the digit that the player entered
        :return:
        """
        if self.valid_move(x, y, value):
            if self.board[x][y] != value:  # If the move has already been made, ignore it
                self.board[x][y] = value
                self.scores[user_id] += 1
                self.check_game_won()
            return True
        self.scores[user_id] -= 1
        return False
            
    def valid_move(self, x, y, value):
        """
        Checks if the move is valid
        :param x: row number
        :param y: column number
        :param value: the digit that the player entered
        :return:
        """
        if self.solution[x][y] == value:
            return True
        return False
            
    def check_game_won(self):
        """
        Checks if the game is over
        :return: Returns True, if the game is over and False if it's not
        """
        game_won = True
        for i in range(9):
            for j in range(9):
                if self.board[i][j] != self.solution[i][j]:
                    game_won = False
        if game_won:
            self.game_state = 2

    def add_player(self, player_id):
        """
        Adds a new player to the game, if possible
        :param player_id:
        :return:
        """
        if len(self.scores) < self.max_players:
            self.scores[player_id] = 0
            if len(self.scores) == self.max_players:
                self.game_state = 1
            return True
        return False

    def get_num_players(self):
        """
        Returns the number of players in the game
        """
        return len(self.scores)

    def remove_player(self, player_id):
        """
        Removes the given player from the game
        """
        self.scores.pop(player_id, None)
        # Check if only one player remains - if so, end the game
        if self.get_num_players() == 1 and self.game_state == 1:
            self.game_state = 2

    def get_state(self, players):
        """
        Returns the current state of the game
        """
        names_scores = []
        for uid, score in self.scores.items():
            name = players.get_player_name(uid)
            names_scores.append((name, score, uid))
        names_scores = sorted(names_scores, key=lambda x: x[1], reverse=True)
        return [self.board, names_scores, self.game_state]