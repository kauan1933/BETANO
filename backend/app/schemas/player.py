from pydantic import BaseModel
from typing import Optional
from datetime import date


class PlayerBase(BaseModel):
    name: str
    team_id: int
    position: Optional[str] = None
    nationality: Optional[str] = None
    photo_url: Optional[str] = None


class PlayerResponse(PlayerBase):
    id: int
    external_id: Optional[str] = None

    class Config:
        from_attributes = True


class PlayerFormResponse(BaseModel):
    player_id: int
    games_analyzed: int
    avg_total_shots: float
    avg_shots_on_target: float
    avg_minutes_played: float
    consistency_score: float

    class Config:
        from_attributes = True


class PlayerWithFormResponse(PlayerResponse):
    form: Optional[PlayerFormResponse] = None


class TopShooterResponse(BaseModel):
    player_id: int
    player_name: str
    team_name: str
    league_name: str
    position: Optional[str] = None
    avg_total_shots: float
    avg_shots_on_target: float
    consistency_score: float
    prob_1_shot_ontarget: float
    prob_2_plus_shots_ontarget: float
    match_id: int
    match_time: Optional[str] = None


class TodayPlayerResponse(BaseModel):
    match_id: int
    match: str
    league: str
    match_date: date
    player: PlayerWithFormResponse
    prob_1_shot_ot: float
    prob_2_plus_shot_ot: float
    prob_x_total_shots: Optional[float] = None
    is_value_bet: bool = False
