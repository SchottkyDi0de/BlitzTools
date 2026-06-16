from pydantic import BaseModel

class TankData(BaseModel):
    id: int
    en_name: str
    ru_name: str
    level: int
    category: str
    is_premium: bool
    is_collectible: bool
    is_secret: bool
