import logging
import threading
import time
import tkMessageBox
from Tkinter import Tk
from socket import socket, AF_INET, SOCK_DGRAM, inet_aton, IPPROTO_IP, IP_ADD_MEMBERSHIP, SOL_SOCKET, SO_REUSEADDR, \
    SHUT_RDWR, timeout, SHUT_WR

import Pyro4

import SudokuGameGUI
from client_input import initiate_input, initiate_lobby, update_input, update_lobby, destroy_input_window, \
    destroy_lobby_window, initiate_mc_window, destroy_mc_window

# Setup logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)

sudoku_refresh_thread = None
lobby_refresh_thread = None
input_refresh_thread = None

input_data = None
lobby_data = None

hard_exit = False

__SERVERS = {}


def refresh_input(input_window):
    """
    Polls for game servers and handles server connection data.
    :param input_window:
    :return loop ending boolean:
    """
    global input_data
    global hard_exit

    update_input(input_window, __SERVERS)
    input_data = input_window.server_uri, input_window.nickname

    if input_data[0] is not None and input_data[1] is not None:
        destroy_input_window(input_window)
        return False
    else:
        time.sleep(0.1)
        return True


def refresh_input_loopy(input_window):
    """
    This is the game initial connection window updater function.
    :param input_window:
    :return:
    """
    global hard_exit
    keep_refreshing = True

    while keep_refreshing:
        if hard_exit:
            input_window.destroy()
            break

        keep_refreshing = refresh_input(input_window)


def refresh_lobby(room_window, user):
    """
    Polls the server for its game list and updates the visual list with the new data.
    :param room_window:
    :param user:
    :return loop ending boolean:
    """
    global lobby_data
    global hard_exit

    games = []
    try:
        games = user.get_games_list()
    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))
        hard_exit = True
        return

    update_lobby(room_window, games)

    lobby_data = room_window.action

    if lobby_data is not None:
        destroy_lobby_window(room_window)
        return False
    else:
        time.sleep(0.1)
        return True


def refresh_lobby_loopy(room_window, user):
    """
    This is the game lobby updater function.
    :param room_window:
    :param user:
    :return:
    """
    global hard_exit
    keep_refreshing = True

    while keep_refreshing:
        if hard_exit:
            room_window.destroy()

            # Remove player from the list of players in the server
            try:
                user.quit_server()
            except Exception as err:
                tkMessageBox.showwarning("Connection error", str(err))
                hard_exit = True

            break

        keep_refreshing = refresh_lobby(room_window, user)


def refresh_game_state(sudoku_ui, game_state, user_id):
    """
    Calls the Sudoku UI game board visual state update.
    :param sudoku_ui:
    :param game_state:
    :param user_id:
    :return:
    """
    board, scores, game_progression = game_state
    keep_playing = True

    board_changed = sudoku_ui.update_board(root, board, scores, game_progression)

    if game_progression == 2:
        sudoku_ui.show_winner(scores[0], user_id)
        keep_playing = False

    return board_changed, keep_playing


def refresh_game(sudoku_ui, user, board_changed=None):
    """
    Gets updated game state from server to refresh the visual game state if needed.
    :param sudoku_ui:
    :param user:
    :param board_changed:
    :return loop ending boolean, board change for the next iteration:
    """
    global hard_exit

    try:
        if board_changed is not None:
            game_state = user.make_guess(board_changed[0], board_changed[1], board_changed[2])
        else:
            game_state = user.get_game_state()

    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))
        hard_exit = True
        return False, False

    board_changed, keep_playing = refresh_game_state(sudoku_ui, game_state, user_id)

    time.sleep(0.2)
    return board_changed, keep_playing


def refresh_game_loopy(sudoku_ui, user):
    """
    This is the main game updater function.
    :param sudoku_ui:
    :param user:
    :return:
    """
    global hard_exit
    board_changed = None
    keep_playing = True

    while keep_playing:
        if hard_exit:
            sudoku_ui.destroy()
            hard_exit = False
            break

        board_changed, keep_playing = refresh_game(sudoku_ui, user, board_changed)

    sudoku_ui.destroy()
    try:
        user.quit_game()
    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))


def main_mc_input(root):
    """
    Keep refreshing MC input window until appropriate input is received and return it.
    :param root:
    :return host, port:
    """
    global hard_exit
    mc_window = initiate_mc_window(root)

    while True:
        if hard_exit:
            destroy_mc_window(mc_window)
            return None, None

        root.update()

        if mc_window.mc_host is not None and mc_window.mc_port is not None:
            destroy_mc_window(mc_window)
            return mc_window.mc_host, mc_window.mc_port


def main_input(root):
    """
    Keep refreshing input window until appropriate input is received and return it.
    :param root:
    :return server_uri, nickname:
    """
    global input_data
    global hard_exit

    LOG.debug("About to initiate input")
    input_window = initiate_input(root)

    LOG.debug("Initiated input window")

    input_refresh_thread = threading.Thread(target=refresh_input_loopy(input_window))
    input_refresh_thread.start()

    LOG.debug("Final input data is " + str(input_data))

    return input_data


def main_lobby(root, user):
    """
    Runs the main game lobby thread.
    :param root:
    :param user:
    :return:
    """
    global lobby_data

    room_window = initiate_lobby(root)

    lobby_refresh_thread = threading.Thread(target=refresh_lobby_loopy(room_window, user))
    lobby_refresh_thread.start()

    LOG.debug("Final lobby data is " + str(lobby_data))

    return lobby_data


def main_sudoku(root, lobby_data, user):
    """
    Runs the main sudoku game thread.
    :param root:
    :param lobby_data:
    :param user:
    :return:
    """
    action, value = lobby_data
    game_state = None

    if action == "create":
        LOG.debug("Creating new game by request of user")

        try:
            game_state = user.create_game(value)
        except Exception as err:
            tkMessageBox.showwarning("Connection error", str(err))
            return

    elif action == "select":
        game_id = value

        try:
            game_state = user.join_game(game_id)
        except Exception as err:
            tkMessageBox.showwarning("Connection error", str(err))
            return

    if not game_state:
        tkMessageBox.showwarning("Game error", "The selected room is full.")
        return

    LOG.debug("The game state is " + str(game_state))

    # First unpack game state into board, scores, game progression indicator
    board, scores, game_progression = game_state[0], game_state[1], game_state[2]

    LOG.debug("Scores are " + str(scores))
    LOG.debug("Game state is " + str(game_progression))

    game = SudokuGameGUI.SudokuBoard(board)
    sudoku_ui = SudokuGameGUI.SudokuUI(root, game)
    root.geometry("%dx%d" % (SudokuGameGUI.TOTAL_WIDTH, SudokuGameGUI.HEIGHT))

    sudoku_refresh_thread = threading.Thread(target=refresh_game_loopy(sudoku_ui, user))


def on_close():
    """
    Handling window close as a prompt.
    If user is okay with leaving, a global variable is set to exit and will be read in appropriate context
    to close the current window.
    :return:
    """
    global hard_exit
    if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
        hard_exit = True


class MulticastDiscoveryThread(threading.Thread):
    def __init__(self, servers):
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)

        self.sock = socket(AF_INET, SOCK_DGRAM)

        try:
            membership = inet_aton(mc_host) + inet_aton("0.0.0.0")

            self.sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, membership)
            self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

            self.sock.bind(("0.0.0.0", mc_port))

            self.sock.settimeout(1)

            LOG.debug("Socket bound")
            self.servers = servers
        except:
            self.sock.close()
            exit()

    def run(self):
        while not self._stopevent.isSet():
            try:
                message, address = self.sock.recvfrom(255)
            except timeout:
                LOG.debug("No data in multicast")
                message, address = None, None

            if message:
                header, content = message.split(";", 1)

                LOG.debug("Header: " + str(header))
                LOG.debug("Content: " + str(content))

                addr, content = content.split(";", 1)
                name, content = content.split(";", 1)
                nr_of_players = content.split(";", 1)[0]
                if addr not in self.servers:
                    self.servers[addr] = (nr_of_players, name)

        #self.sock.shutdown(SHUT_WR)
        self.sock.close()

    def join(self, timeout=None):
        self._stopevent.set()
        threading.Thread.join(self, timeout)


if __name__ == "__main__":
    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_close)

    mc_host, mc_port = main_mc_input(root)

    while 1:
        multicast_thread = MulticastDiscoveryThread(__SERVERS)
        multicast_thread.start()

        server_uri, user_id = main_input(root)

        multicast_thread.join()

        LOG.debug(server_uri)
        LOG.debug(user_id)

        if hard_exit:
            break

        # Register username
        me = None
        try:
            sudoku = Pyro4.Proxy(server_uri)

            my_uri = sudoku.register(user_id)

            if my_uri:
                me = Pyro4.Proxy(my_uri)

        except Exception as err:
            tkMessageBox.showwarning("Connection error at registration", str(err))
            exit(1)

        # If received inputs are nones, it means we basically fuck off.
        if me is not None:
            active_client = True
        else:
            active_client = False
            tkMessageBox.showwarning("Name error", "This nickname is not available")

        # If the client is active, we will proceed.
        while active_client:

            # Connect client to lobby and show the game rooms.
            lobby_data = main_lobby(root, me)

            # If we exited lobby permanently then break.
            if hard_exit:
                hard_exit = False
                break

            # If lobby returned odd stuff, then start it anew.
            if lobby_data is None:
                continue

            # If we got here, then we're ready to play.
            main_sudoku(root, lobby_data, me)

    LOG.debug('kthxbye')
