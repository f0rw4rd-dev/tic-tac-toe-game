from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Set
from player import Player


class Game(BaseModel):
    id: str
    board: List[List[str]] = [['', '', ''], ['', '', ''], ['', '', '']]
    players: Dict[str, Optional[Player]]
    sides: Dict[str, Optional[Player]] = {'X': None, 'O': None}
    turn: Player
    status: int = 0  # 0 - игра не началась, 1 - игра продолжается, 2 - игра окончена

    victories: Dict[str, int] = {'X': 0, 'O': 0}
    defeats: Dict[str, int] = {'X': 0, 'O': 0}
    draws: int = 0
