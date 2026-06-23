from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ValueBetResponse(BaseModel):
    id: int
    match: str
    player_name: str
    team_name: str
    league_name: str
    market: str
    calc_probability: float
    market_odds: float
    implied_probability: float
    expected_value: float
    confidence: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
