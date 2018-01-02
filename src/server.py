import logging
import Pyro4
import threading
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM, IPPROTO_IP, IP_MULTICAST_LOOP, IP_MULTICAST_TTL
from time import sleep

# ---------- Logging ----------
from games import Games
from players import Players

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()
# LOG.setLevel(logging.INFO)

# ---------- Constants ----------
__NAME = "CompetitiveSudoku"
__VER = "0.0.2"
__DESC = "Simple Competitive Sudoku Game"

_GAMES = Games()
_PLAYERS = Players()

def __info():
    return "%s v%s - %s" % (__NAME, __VER, __DESC)


def dummy_state():
    return [[[1, 2, 6, 9, 0, 0, 0, 3, 0], [0, 0, 8, 0, 0, 0, 1, 0, 4], [0, 0, 0, 3, 1, 0, 0, 0, 0],
             [2, 8, 0, 0, 7, 0, 0, 0, 0], [7, 6, 0, 0, 0, 0, 0, 1, 9], [0, 0, 0, 0, 2, 0, 0, 8, 6],
             [0, 0, 0, 0, 6, 1, 0, 0, 0], [6, 0, 2, 0, 0, 0, 9, 0, 0], [0, 3, 0, 0, 0, 4, 8, 6, 1]],
            [('rth', 0, '6fbea54a-dcf3-4949-bd61-668440fafabf')], 0]


@Pyro4.expose
class User(object):
    """
    User class, the main communication vector between the front-end and back-end
    """
    global _GAMES, _PLAYERS

    def __init__(self, name, competitive_sudoku):
        self.name = name
        self.sudoku = competitive_sudoku
        self.game = None
        self.id = str(_PLAYERS.reg_player(name))

    def get_games_list(self):
        """
        Get list of games on the server """
        return _GAMES.get_tuple()

    def create_game(self, max_players):
        """
        Create a new sudoku game and return the state """
        game_id = _GAMES.create_game(max_players)
        game = _GAMES.get_game(game_id)
        game.add_player(self.id)
        self.game = game
        return self.game.get_state(_PLAYERS)

    def join_game(self, game_id):
        """
        Join an existing sudoku game, returns the state """
        game = _GAMES.get_game(game_id)
        game.add_player(self.id)
        self.game = game
        return self.game.get_state(_PLAYERS)

    def make_guess(self, x_coord, y_coord, val):
        """
        Make a guess on the sudoku table """
        self.game.make_move(self.id, int(x_coord), int(y_coord), int(val))

        return self.game.get_state(_PLAYERS)

    def get_game_state(self):
        """
        Get the current playing field """

        return self.game.get_state(_PLAYERS)

    def quit_game(self):
        """
        Quit the current sudoku game the user is taking part in """
        self.game.remove_player(self.id)
        self.game = None

    def quit_server(self):
        """
        Quit the server completely """
        self.sudoku.remove_player(self.name)
        _PLAYERS.remove_player(self.id)


@Pyro4.expose
class CompetitiveSudoku(object):
    """
    Main server class, complete functions and necessity to be determined
    """

    def __init__(self):
        self.users = {}

    def register(self, name):
        if name in self.users:
            return None

        user = User(name, self)
        self.users[name] = user
        user_uri = daemon.register(user)

        return str(user_uri)

    def remove_player(self, name):
        self.users.pop(name, None)


def send_sudoku_uri_multicast(sudoku_uri, mc_addr, server_name, ttl=1):
    """
    Main method to send sudoku URI to the local multicast group
    :param sudoku_uri: Pyro URI to send out using multicast
    :param mc_addr: Multicast group address as tuple (mc_host, mc_port)
    :param ttl: Time to live
    """
    multicast_payload = "SERVERADDR;" + str(sudoku_uri) + ";" + str(server_name) + ";"

    try:
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(IPPROTO_IP, IP_MULTICAST_LOOP, 1)  # Enable loop-back multicast

        if s.getsockopt(IPPROTO_IP, IP_MULTICAST_TTL) != ttl:
            s.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)

        s.sendto(multicast_payload, mc_addr)
        s.close()

    except Exception as e:
        LOG.error("Cannot send multicast request: %s" % str(e))


def sudoku_uri_multicast(sudoku_uri, mc_addr, server_name):
    while 1:
        send_sudoku_uri_multicast(sudoku_uri, mc_addr, server_name)
        sleep(1)


if __name__ == "__main__":
    parser = ArgumentParser(description=__info(), version=__VER)

    parser.add_argument("-mc", "--multicast", help="Multicast group URI", default="239.1.1.1")
    parser.add_argument("-mcp", "--mcport", help="Multicast group port", default=7778)
    parser.add_argument("-host", "--host", help="Pyro host URI", default="127.0.0.1")
    parser.add_argument("-p", "--port", help="Pyro host port", default=7777)
    parser.add_argument("-n", "--name", help="Name of the game server", required=True)

    args = parser.parse_args()

    # Make a Pyro daemon
    daemon = Pyro4.Daemon(host=args.host, port=args.port)

    # Register the Sudoku game with Pyro
    sudoku = CompetitiveSudoku()
    uri = daemon.register(sudoku)

    LOG.info("The game URI is: " + str(uri))

    # Broadcast the URI of the Pyro server instance
    mc_host = args.multicast
    mc_port = args.mcport
    server_name = args.name

    mc_thread = threading.Thread(target=sudoku_uri_multicast, args=(uri, (mc_host, mc_port), server_name))
    mc_thread.setDaemon(True)
    mc_thread.start()

    daemon.requestLoop()
