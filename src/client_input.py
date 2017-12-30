# encoding: utf-8
from Tkinter import Frame, Button, BOTH, Entry, Label, OptionMenu, StringVar, CENTER
from ttk import Treeview
from client import *
import tkMessageBox
import logging

# Setup logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Input sizes
INPUT_WIDTH = 400
INPUT_HEIGHT = 400

# Lobby sizes
LOBBY_WIDTH = 400
LOBBY_HEIGHT = 400


class ConnectionUI(Frame):
    """
    Initial name and port dialogue UI.
    In case of incorrect inputs, the user is notified via error messages and is allowed to continue
    providing inputs.
    """
    server_uri = None
    nickname = None

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.row, self.col = -1, -1
        self.__initUI()

    def __initUI(self):
        """
        Initialize UI with two entry fields and a connection button."""

        self.parent.title('Connect to a Sudoku server')
        self.pack(fill=BOTH, expand=1)

        Label(self, text='Enter Nickname').grid(row=0, column=0, padx=(15, 0))
        Label(self, text='Nickname presets').grid(row=1, column=0, padx=(15, 0))

        self.entry_nickname = Entry(self)
        self.entry_nickname.grid(row=0, column=1, padx=(0, 15))

        var = StringVar(self)
        var.set('')

        self.entry_nickname_options = OptionMenu(self, var, 'Peeter', 'Jürka', 'Antskan', 'Jüri', 'Toss', command=self.__select_preset)
        self.entry_nickname_options.grid(row=1, column=1, padx=(0, 15))

        self.server_list = Treeview(self, columns=('server', 'games'))
        self.server_list['show'] = 'headings'
        self.server_list.heading('server', text='Server name')
        self.server_list.column('server', width=250, anchor=CENTER)
        self.server_list.heading('games', text='Gilgames')
        self.server_list.column('games', width=100, anchor=CENTER)
        self.server_list.grid(row=2, column=0, columnspan=2, rowspan=2, padx=20, pady=(10, 0))

        self.connect_lobby = Button(self, text='Join server', command=self.__connect_server)
        self.connect_lobby.grid(row=3, column=1, pady=(0, 10))

    def __connect_server(self):
        """
        Input name has no space and less or equal to 8 characters.
        Input port consists of an integer between 1001 and 65535.
        """
        name_ok = False
        server_ok = False
        LOG.debug('Server connect button has been pressed.')

        # Nickname entry validation
        nickname = self.entry_nickname.get()
        if 8 >= len(nickname) > 0:
            if ' ' not in nickname:
                name_ok = True
                LOG.debug('Player created: ' + nickname)
            else:
                tkMessageBox.showwarning("Name error", "Player name cannot contain space.")
        elif len(nickname) <= 0:
            tkMessageBox.showwarning("Name error", "Player name cannot be empty.")
        elif len(nickname) > 8:
            tkMessageBox.showwarning("Name error", "Player name has to be less than 9 characters long.")

        # Server list selection validation
        current_item = self.server_list.focus()
        selected_server = None

        if current_item is not None and current_item.strip() != '':
            # Select game column value from item values dictionary.
            selected_server = self.server_list.item(current_item)['values'][0]
            LOG.debug('Player wishes to join server ' + str(selected_server))

            if selected_server is not None:
                server_ok = True
        else:
            tkMessageBox.showwarning("Connection error", "Please fuck off and select a server to join.")

        if name_ok and server_ok:
            self.nickname = nickname
            self.server_uri = selected_server

    def __select_preset(self, value):
        """
        Selects one of the preset names as the nickname """
        self.entry_nickname.delete(0, 'end')
        self.entry_nickname.insert('end', value)

    def populate_server_list(self, games):
        """
        Method to re-populate the server list every poll.
        Additionally retains the focused line during polling.
        :param games:
        """
        previous_selection = self.server_list.selection()
        prev_item = None
        if len(previous_selection) > 0:
            prev_item = self.server_list.item(previous_selection[0])

        self.server_list.delete(*self.server_list.get_children())
        for game in games:
            self.server_list.insert('', 'end', values=(str(game[0]), str(game[1]) + '/' + str(game[2])))

        if prev_item is not None:
            for item in self.server_list.get_children():
                if self.server_list.item(item) == prev_item:
                    self.server_list.selection_set(item)
                    self.server_list.focus(item)


class LobbyUI(Frame):
    """
    Sudoku multiplayer lobby UI class.
    In case of incorrect inputs error messages are shown.
    """
    action = None

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.row, self.col = -1, -1
        self.__initUI()

    def __initUI(self):
        """
        Initialize UI with a list and required entry fields and submit buttons."""

        self.parent.title('Multiplayer Game')
        self.pack(fill=BOTH, expand=1)

        self.lobby_list = Treeview(self, columns=('room', 'players'))
        self.lobby_list['show'] = 'headings'
        self.lobby_list.heading('room', text='Room ID')
        self.lobby_list.column('room', width=250, anchor=CENTER)
        self.lobby_list.heading('players', text='Players')
        self.lobby_list.column('players', width=100, anchor=CENTER)
        self.lobby_list.grid(row=1, column=0, columnspan=2, rowspan=2, padx=20, pady=(10, 0))

        self.connect_lobby = Button(self, text='Joining Sudoku\n Solving Session', command=self.__connect_lobby)
        self.connect_lobby.grid(row=3, column=1, pady=(0, 10))

        Label(self, text='Creating new Sudoku\n solving session:').grid(row=4, column=0)

        self.max_players = Entry(self)
        self.max_players.grid(row=4, column=1)

        self.create_game = Button(self, text='Join new game', command=self.__create_game)
        self.create_game.grid(row=5, column=1)

    def __connect_lobby(self):
        """
        Handle lobby connection button."""
        LOG.debug('Lobby connect button has been pressed.')
        current_item = self.lobby_list.focus()
        selected_id = None

        if current_item is not None and current_item.strip() != '':
            # Select game column value from item values dictionary.
            selected_id = self.lobby_list.item(current_item)['values'][0]
            LOG.debug('Player wishes to join game ' + str(selected_id))

            if selected_id is not None:
                self.action = ('select', selected_id)
        else:
            tkMessageBox.showwarning("Connection error", "Please select a game from the lobby to join.")

    def __create_game(self):
        """
        Create game with some number of max players."""
        max_ok = False

        try:
            max_count = int(self.max_players.get())
        except (ValueError, TypeError):
            max_count = -1
            tkMessageBox.showwarning("Input error", "Max player count has to be an integer.")

        if isinstance(max_count, int):
            if max_count >= 2:
                max_ok = True
                LOG.debug('Ok max player count.')
            else:
                tkMessageBox.showwarning("Input error", "Max player count has to be larger than 2.")
                LOG.error('Bad max count.')

        if max_ok:
            self.action = ('create', max_count)

    def populate_lobby_list(self, servers):
        """
        Method to re-populate the lobby list every poll.
        Additionally retains the focused line during polling.
        :param games:
        """
        previous_selection = self.lobby_list.selection()
        prev_item = None
        if len(previous_selection) > 0:
            prev_item = self.lobby_list.item(previous_selection[0])

        self.lobby_list.delete(*self.lobby_list.get_children())
        for server in servers:
            self.lobby_list.insert('', 'end', values=(str(server[0]), str(server[1]) + '/' + str(server[2])))

        if prev_item is not None:
            for item in self.lobby_list.get_children():
                if self.lobby_list.item(item) == prev_item:
                    self.lobby_list.selection_set(item)
                    self.lobby_list.focus(item)


def initiate_input(root):
    """
    Create input UI and attach it to root.

    :param root:
    :return client window:
    """
    input_window = ConnectionUI(root)
    root.geometry('%dx%d' % (INPUT_WIDTH, INPUT_HEIGHT))

    return input_window


def update_input(input_window, servers):
    """
    Update server list view from games list data.
    :param input_window:
    :param servers:
    """

    input_window.populate_server_list(servers)
    input_window.update()


def destroy_input_window(input_window):
    """
    Close lobby UI portion of root.
    :param input_window:
    """
    LOG.debug('Lobby is destroyed.')
    input_window.destroy()


def initiate_lobby(root):
    """
    Create lobby UI and attach it to root.
    :param root:
    :return lobby window:
    """
    room_window = LobbyUI(root)
    root.geometry('%dx%d' % (LOBBY_WIDTH, LOBBY_HEIGHT))
    LOG.debug('Kick up the 4d3d3d3.')
    return room_window


def update_lobby(lobby_window, games):
    """
    Update lobby list view from games list data.
    :param lobby_window:
    :param games:
    """

    lobby_window.populate_lobby_list(games)
    lobby_window.update()


def destroy_lobby_window(lobby_window):
    """
    Close lobby UI portion of root.
    :param lobby_window:
    """
    LOG.debug('Lobby is destroyed.')
    lobby_window.destroy()
