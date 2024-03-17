from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from player import Player
from game import Game
from datetime import datetime, timedelta

import uuid
import random

app = FastAPI()

games = {}
players = {}

last_game_id = 0


def check_winner(board):
    winning_positions = [
        [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)], [(2, 0), (1, 1), (0, 2)]
    ]

    for positions in winning_positions:
        result = [board[x][y] for x, y in positions]
        if result == ['X', 'X', 'X']:
            return 'X'
        elif result == ['O', 'O', 'O']:
            return 'O'
    return None


@app.post('/games/create')
def create_game(username: str):
    global last_game_id
    game_id = str(last_game_id)
    last_game_id += 1

    if username in players:
        player = players[username]

        if player.status != 0:
            raise HTTPException(status_code=400, detail='Игрок уже в игре')
        else:
            player.status = 1
            player.game_id = game_id
    else:
        player = Player(username=username, game_id=game_id, status=1)
        players[username] = player

    players[username].last_request_time = datetime.now()

    side = random.choice(['X', 'O'])
    games[game_id] = Game(id=game_id, sides={side: player}, turn=player, players={username: player})

    return {'game_id': game_id, 'side': side}


@app.post('/games/join')
def join_game(game_id: str, username: str):
    game_id = str(game_id)
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    if len(game.players) == 2:
        raise HTTPException(status_code=400, detail='К игре уже подключено 2 человека')

    if username in game.players:
        raise HTTPException(status_code=400, detail='Игрок уже присоединен к данной игре')

    if username in players:
        player = players[username]

        if player.status != 0:
            raise HTTPException(status_code=400, detail='Игрок уже в игре')
        else:
            player.status = 1
            player.game_id = game_id
    else:
        player = Player(username=username, game_id=game_id, status=1)
        players[username] = player

    players[username].last_request_time = datetime.now()

    side = 'X' if game.sides.get('X') is None else 'O'

    game.sides[side] = player
    game.players[username] = player
    game.status = 1

    for p_username, p_player in game.players.items():
        p_player.last_move_time = datetime.now()

    return {'side': side}


@app.post('/games/move')
def make_move(game_id: str, username: str, x: int, y: int):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    if game.status == 0:
        raise HTTPException(status_code=400, detail='Игра еще не началась')

    player = game.players.get(username)

    if not player:
        raise HTTPException(status_code=400, detail='Игрок не присоединен к данной игре')

    players[username].last_request_time = datetime.now()
    players[username].last_move_time = datetime.now()

    if len(game.players) < 2:
        raise HTTPException(status_code=400, detail='Ожидание второго игрока')

    if game.board[x][y] != '':
        raise HTTPException(status_code=400, detail='Данная клетка уже занята')

    if game.turn != player:
        raise HTTPException(status_code=400, detail='Сейчас ход другого игрока')

    if game.status == 2:
        raise HTTPException(status_code=400, detail='Игра уже окончена')

    game.board[x][y] = 'X' if player == game.sides.get('X') else 'O'
    game.turn = game.sides['O'] if player == game.sides.get('X') else game.sides.get('X')

    winner = check_winner(game.board)

    if winner:  # Победа
        player.victories += 1
        game.status = 2
        game.victories[game.board[x][y]] += 1

        for p_username, p_player in game.players.items():
            p_player.status = -1

    elif all([cell != '' for row in game.board for cell in row]):  # Ничья
        game.status = 2
        game.draws += 1

        for p_username, p_player in game.players.items():
            p_player.status = -1
    else:
        game.status = 1

        for p_username, p_player in game.players.items():
            p_player.status = 1

    return {'status': game.status}


@app.get('/games/{game_id}/{username}/board')
def get_board(game_id: str, username: str):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    player = game.players.get(username)

    if not player:
        raise HTTPException(status_code=400, detail='Игрок не присоединен к данной игре')

    players[username].last_request_time = datetime.now()

    board = {}
    for i in range(3):
        for j in range(3):
            board[f'{3 * i + j}'] = game.board[i][j]

    board.update({
        'turn': 'X' if game.sides.get('X') == game.turn else 'O',
        'side': 'X' if game.sides.get('X') is not None and game.sides.get('X').username == username else 'O',
        'victories.X': game.victories['X'],
        'victories.O': game.victories['O'],
        'draws': game.draws,
        'num_players': len(game.players)
    })

    return board


@app.post('/games/restart')
def restart_game(game_id: str, username: str):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    player = game.players.get(username)

    if not player:
        raise HTTPException(status_code=400, detail='Игрок не присоединен к данной игре')

    players[username].last_request_time = datetime.now()

    if game.status != 2:
        raise HTTPException(status_code=400, detail='Игра еще не окончена')

    k_restart = 0
    for p_username, p_player in game.players.items():
        if p_player.status == -1:
            k_restart += 1

        if p_username == username:
            if p_player.status != -1:
                raise HTTPException(status_code=400, detail='Игрок уже перезагружен')
            else:
                p_player.status = 1

    game.board = [['', '', ''], ['', '', ''], ['', '', '']]

    if k_restart == 2:
        game.sides = {'X': None, 'O': None}
        game.turn = player

        side = random.choice(['X', 'O'])
        game.sides[side] = player
    elif k_restart == 1:
        side = 'X' if game.sides.get('X') is None else 'O'
        game.status = 1
    else:
        raise HTTPException(status_code=400, detail='Игра не требует перезапуска')

    game.sides[side] = player

    return {'side': side}


@app.get('/cleanup')
def cleanup():
    now = datetime.now()
    for username, player in players.items():
        if (now - player.last_request_time > timedelta(seconds=30)
                or now - player.last_move_time > timedelta(seconds=30) and player.status == 1 and player.game_id is not None and games.get(player.game_id) is not None and games[player.game_id].status == 1):
            temp_game_id = player.game_id

            if temp_game_id is not None and temp_game_id in games:
                for p_username, p_player in games[temp_game_id].players.items():
                    p_player.status = 0
                    p_player.game_id = None

                del games[temp_game_id]
