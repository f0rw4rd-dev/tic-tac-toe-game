from pydantic import BaseModel


class Player(BaseModel):
    username: str
    victories: int = 0
    defeats: int = 0
    draws: int = 0
