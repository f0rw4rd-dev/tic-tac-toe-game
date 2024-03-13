from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Set


class Player(BaseModel):
    username: str
    status: int = 0  # 0 - игрок не в игре, 1 - игрок в игре, -1 - игрок перезагружается
    last_request_time: datetime = datetime.now()
    last_move_time: datetime = datetime.now()
    game_id: Optional[str] = None

    victories: int = 0
    defeats: int = 0
    draws: int = 0
