from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
from player import Player


class Game(BaseModel):
    id: str
    board: List[List[str]] = [['', '', ''], ['', '', ''], ['', '', '']]
    players: List[Player] = []
    victories: Dict[str, int] = {'X': 0, 'O': 0}
    draws: int = 0
    last_move_time: Dict[str, datetime] = {'X': datetime.now(), 'O': datetime.now()}
    sides: Dict[str, Optional[Player]] = {'X': None, 'O': None}
    turn: Optional[Player] = None
    status: int = 0
