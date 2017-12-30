from Tkinter import Tk
import tkMessageBox
from client_input import initiate_input, initiate_lobby, update_input, update_lobby, destroy_input_window, destroy_lobby_window
from client import *
import time
import threading
import SudokuGameGUI

# Setup logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

sudoku_refresh_thread = None
lobby_refresh_thread = None
input_refresh_thread = None

input_data = None
lobby_data = None

hard_exit = False


def refresh_input(root, input_window):
    global input_data
    global hard_exit

    servers = []
    try:
        # TODO: right proper req get servers be here
        # servers = req_get_games(server_uri)
        pass
    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))
        hard_exit = True
        return

    update_input(input_window, servers)
    input_data = input_window.server_uri, input_window.nickname

    if input_data[0] is not None and input_data[1] is not None:
        destroy_input_window(input_window)
        return False
    else:
        time.sleep(0.1)
        return True


def refresh_input_loopy(root, input_window):
    """
    This is the game lobby updater function.
    :param root:
    :param input_window:
    :return:
    """
    global hard_exit
    keep_refreshing = True

    while keep_refreshing:
        if hard_exit:
            input_window.destroy()
            break

        keep_refreshing = refresh_input(root, input_window)


def refresh_lobby(root, server_uri, room_window):
    """
    Polls the server for its game list and updates the visual list with the new data.
    :param root:
    :param server_uri:
    :param room_window:
    :return loop ending boolean:
    """
    global lobby_data
    global hard_exit

    games = []
    try:
        games = req_get_games(server_uri)
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


def refresh_lobby_loopy(root, server_uri, room_window, user_id):
    """
    This is the game lobby updater function.
    :param root:
    :param server_uri:
    :param room_window:
    :return:
    """
    global hard_exit
    keep_refreshing = True

    while keep_refreshing:
        if hard_exit:
            room_window.destroy()

            # Remove player from the list of players in the server
            try:
                req_remove_player_lobby(user_id, server_uri)
            except Exception as err:
                tkMessageBox.showwarning("Connection error", str(err))
                hard_exit = True

            break

        keep_refreshing = refresh_lobby(root, server_uri, room_window)


def refresh_game_state(sudoku_ui, game_state, user_id):
    """
    Calls the Sudoku UI game board visual state update.
    :param sudoku_ui:
    :param game_state:
    :return:
    """
    board, scores, game_progression = game_state
    keep_playing = True

    board_changed = sudoku_ui.update_board(root, board, scores, game_progression)

    if game_progression == 2:
        sudoku_ui.show_winner(scores[0], user_id)
        keep_playing = False

    return board_changed, keep_playing


def refresh_game(sudoku_ui, game_id, server_uri, user_id, board_changed=None):
    """
    Gets updated game state from server to refresh the visual game state if needed.
    :param sudoku_ui:
    :param game_id:
    :param server_uri:
    :param user_id:
    :param board_changed:
    :return loop ending boolean, board change for the next iteration:
    """
    global hard_exit

    try:
        if board_changed is not None:
            game_state = req_make_move(user_id, game_id, board_changed[0], board_changed[1], board_changed[2], server_uri)
        else:
            game_state = req_get_state(game_id, server_uri)

    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))
        hard_exit = True
        return False, False

    board_changed, keep_playing = refresh_game_state(sudoku_ui, game_state, user_id)

    time.sleep(0.2)
    return board_changed, keep_playing


def refresh_game_loopy(sudoku_ui, game_id, server_uri, user_id):
    """
    This is the main game updater function.
    :param sudoku_ui:
    :param game_id:
    :param server_uri:
    :param user_id:
    :return:
    """
    global hard_exit
    board_changed = None
    keep_playing = True

    while keep_playing:
        if hard_exit:
            sudoku_ui.destroy()
            hard_exit = False

            # Remove player from game
            try:
                req_remove_player(game_id, user_id, server_uri)
            except Exception as err:
                tkMessageBox.showwarning("Connection error", str(err))
            break

        board_changed, keep_playing = refresh_game(sudoku_ui, game_id, server_uri, user_id, board_changed)

    sudoku_ui.destroy()
    try:
        req_remove_player(game_id, user_id, server_uri)
    except Exception as err:
        tkMessageBox.showwarning("Connection error", str(err))


def main_input(root):
    """
    Keep refreshing input window until appropriate input is received and return it.
    :param root:
    :return server_uri, nickname:
    """
    global input_data
    global hard_exit
    input_window = initiate_input(root)

    input_refresh_thread = threading.Thread(target=refresh_input_loopy(root, input_window))
    input_refresh_thread.start()

    LOG.debug("Final input data is " + str(input_data))

    return input_data


def main_lobby(root, server_uri, user_id):
    """
    Runs the main game lobby thread.
    :param root:
    :param server_uri:
    :return:
    """
    global lobby_data

    room_window = initiate_lobby(root)

    lobby_refresh_thread = threading.Thread(target=refresh_lobby_loopy(root, server_uri, room_window, user_id))
    lobby_refresh_thread.start()

    LOG.debug("Final lobby data is " + str(lobby_data))

    return lobby_data


def main_sudoku(root, server_uri, lobby_data):
    """
    Runs the main sudoku game thread.
    :param root:
    :param lobby_data:
    :return:
    """
    action, value = lobby_data
    game_state = None

    if action == "create":
        LOG.debug("Creating new game by request of user")

        try:
            game_id, game_state = req_create_game(user_id, value, server_uri)
        except Exception as err:
            tkMessageBox.showwarning("Connection error", str(err))
            return

    elif action == "select":
        game_id = value

        try:
            game_state = req_join_game(user_id, game_id, server_uri)
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

    sudoku_refresh_thread = threading.Thread(target=refresh_game_loopy(sudoku_ui, game_id, server_uri, user_id))


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


if __name__ == "__main__":
    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_close)

    while 1:
        server_uri, user_id = main_input(root)

        if hard_exit:
            break

        # If received inputs are nones, it means we basically fuck off.
        if user_id is not None and server_uri is not None:
            active_client = True
        else:
            active_client = False

        # If the client is active, we will proceed.
        while active_client:
            # Connect client to lobby and show the game rooms.
            lobby_data = main_lobby(root, server_uri, user_id)

            # If we exited lobby permanently then break.
            if hard_exit:
                hard_exit = False
                break

            # If lobby returned odd stuff, then start it anew.
            if lobby_data is None:
                continue

            # If we got here, then we're ready to play.
            main_sudoku(root, server_uri, lobby_data)

    LOG.debug('kthxbye')
