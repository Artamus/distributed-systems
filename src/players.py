import uuid


class Players:

    def __init__(self):
        self.players = {}

    def reg_player(self, name):
        """
        Creates a new player and associates it's nickname to an id.
        """
        player_id = str(uuid.uuid4())
        self.players[player_id] = name
        return player_id

    def remove_player(self, player_id):
        """
        Removes a player from the dictionary of players
        """
        del self.players[player_id]

    def get_player_name(self, player_id):
        """
        Returns the player's name for the given player id.
        """
        return self.players[player_id]
