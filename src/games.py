import uuid
from game import Game


class Games:
    def __init__(self):
        self.games = {}

    def create_game(self, max_players):
        """
        Creates a new game and associates it with an id
        :param max_players: maximum number of players in the game
        :return: returns the id of the game
        """
        game_id = str(uuid.uuid4())
        new_game = Game(max_players)
        self.games[game_id] = new_game
        return game_id

    def get_game(self, game_id):
        """
        Returns a game instance for a given game id.
        """
        return self.games[game_id]

    def remove_empty(self):
        """
        Removes an empty games from the dictionary of games
        """
        for game_id, game in self.games.items():
            if len(game.scores) == 0:
                del self.games[game_id]

    def remove_player_from_game(self, game_id, player_id):
        """
        Removes a player from a game.
        :param game_id:  id of the game
        :param player_id:  id of the player
        :return:
        """
        game = self.games[game_id]
        game.remove_player(player_id)

    def get_tuple(self):
        '''
        Returns tuple representation of games,
        :return: (room_id, num_players, max_players)
        '''
        output = []
        self.remove_empty()
        # (room_id, num players, max players)
        for uid, game in self.games.items():
            if game.game_state != 2:
                elem = tuple((uid, len(game.scores), game.max_players))
                output.append(elem)
        return output

    def get_nr_games(self):
        """
        Returns the number of games
        """
        return len(self.games.keys())
