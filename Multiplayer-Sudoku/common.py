# Requests --------------------------------------------------------------------
# User enters nick name, app checks if it is valid and not taken
__REQ_REG_USER = '1'
# Connect to server with port number
__REQ_CONNECT_SERVER_PORT = '2'
# Return existing sessions of games (id, number of players, max players)
__REQ_GET_GAMES = '3'
# Set max players num, returns session id, adds client to game
__REQ_CREATE_GAME = '4'
# Send Player id, game room id to add player request
__REQ_ADD_PLAYER_TO_GAMEROOM = '5'

# Send req with game_id, (x,y) coord and val, returns board and current scores together, if game is over then return boolean True
__REQ_MAKE_MOVE = '6'
# Initalize board, add players, make session (GAME)
__REQ_INIT_GAME = '7'

__CTR_MSGS = {__REQ_REG_USER: 'Register user with nickname',
              __REQ_CONNECT_SERVER_PORT: 'Connect game server port',
              __REQ_GET_GAMES: 'Get all game sessions (game rooms)',
              __REQ_CREATE_GAME: 'Create new game room',
              __REQ_ADD_PLAYER_TO_GAMEROOM: 'Add player to game room',
              __REQ_MAKE_MOVE: 'Player make move',
              __REQ_INIT_GAME: 'Return current game state with board and scores'
              }
# Responses--------------------------------------------------------------------
__RSP_OK = '0'
# Responses for connecting server with port number
__RSP_CONNECTION_REFUSED = '1'
__RSP_SERVER_NOT_FOUND = '2'
# For all else problems beside server not found etc.
__RSP_CONNECTION_ERROR = '3'
# User tries to join game room which is full
__RSP_GAME_FULL_ERROR = '4'

__ERR_MSGS = {__RSP_OK: 'No Error',
              __RSP_CONNECTION_REFUSED: 'Connection refused',
              __RSP_SERVER_NOT_FOUND: 'Server not found',
              __RSP_CONNECTION_ERROR: 'Connection error',
              __RSP_GAME_FULL_ERROR: 'Game room is full'
              }
# Field separator for sending multiple values ---------------------------------
__MSG_FIELD_SEP = ':'
__MSG_END = '__END'
