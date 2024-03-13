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
    player = Player(username=username) if username not in players else players[username]
    game_id = str(uuid.uuid4())
    side = random.choice(['X', 'O'])
    game = Game(id=game_id, players=[player], sides={side: player}, turn=player, player_status={username: 0})
    players[player.username] = player
    games[game_id] = game

    return {'game_id': game_id, 'side': side}


@app.post('/games/join')
def join_game(game_id: str, username: str):
    player = Player(username=username) if username not in players else players[username]
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    if len(game.players) >= 2:
        raise HTTPException(status_code=400, detail='К игре уже подключено 2 человека')

    side = 'X' if game.sides['X'] is None else 'O'
    game.sides[side] = player
    game.players.append(player)
    players[player.username] = player

    return {'side': side}


@app.post('/games/move')
def make_move(game_id: str, username: str, x: int, y: int):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    if game.status > 0:
        raise HTTPException(status_code=400, detail='Игра окончена')

    player = next((p for p in game.players if p.username == username), None)

    if not player:
        raise HTTPException(status_code=400, detail='Игрок не присоединен к данной игре')

    if len(game.players) < 2:
        raise HTTPException(status_code=400, detail='Ожидание второго игрока')

    if game.board[x][y] != '':
        raise HTTPException(status_code=400, detail='Данная клетка уже занята')

    if game.turn != player:
        raise HTTPException(status_code=400, detail='Сейчас ход другого игрока')

    game.board[x][y] = 'X' if player == game.sides['X'] else 'O'
    game.turn = game.sides['O'] if player == game.sides['X'] else game.sides['X']

    winner = check_winner(game.board)

    if winner:
        player.victories += 1
        game.victories[game.board[x][y]] += 1
        game.status = 2

        for p in game.players:
            p.status = -1
    elif all([cell != '' for row in game.board for cell in row]):
        game.draws += 1
        game.status = 1

        for p in game.players:
            p.status = -1
    else:
        game.status = 0

    game.last_move_time[username] = datetime.now()

    return {'status': game.status}


@app.get('/games/{game_id}/{username}/board')
def get_board(game_id: str, username: str):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail='Игра не найдена')

    board = {}
    for i in range(3):
        for j in range(3):
            board[f'{3 * i + j}'] = game.board[i][j]

    board.update({
        'turn': 'X' if game.sides['X'] == game.turn else 'O',
        'side': 'X' if game.sides['X'] == next((p for p in game.players if p.username == username), None) else 'O',
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

    player = next((p for p in game.players if p.username == username), None)

    if not player:
        raise HTTPException(status_code=400, detail='Игрок не присоединен к данной игре')

    # if game.status == 0:
    #     raise HTTPException(status_code=400, detail='Игра еще не окончена')

    for p in game.players:
        if p.username == username:
            if p.status == 0:
                raise HTTPException(status_code=400, detail='Игра еще не окончена')
            else:
                p.status = 0

    game.board = [['', '', ''], ['', '', ''], ['', '', '']]
    game.last_move_time = {'X': datetime.now(), 'O': datetime.now()}
    game.sides = {'X': None, 'O': None}
    game.turn = player
    game.status = 0

    side = random.choice(['X', 'O'])
    opposite_side = 'O' if side == 'X' else 'X'

    opposite_player = next((p for p in game.players if p.username != username), None)

    game.sides[side] = player
    game.sides[opposite_side] = opposite_player

    return {'side': side}

# @app.on_event('startup')
# @repeat_every(seconds=30)
# def cleanup_inactive_games():
#     now = datetime.now()
#     for game_id, game in list(games.items()):
#         if now - game.last_move_time > timedelta(seconds=30):
#             del games[game_id]
