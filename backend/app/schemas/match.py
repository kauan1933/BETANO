from pydantic import BaseModel
from typing import Optional
from datetime import date


class MatchResponse(BaseModel):
    id: int
    league_name: str
    home_team: str
    away_team: str
    match_date: date
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    class Config:
        from_attributes = True


class LineupPlayer(BaseModel):
    player_id: int
    player_name: str
    position: Optional[str] = None
    is_probable: bool
    is_injured: bool
    is_suspended: bool


class MatchDetailResponse(MatchResponse):
    home_lineup: list[LineupPlayer] = []
    away_lineup: list[LineupPlayer] = []
