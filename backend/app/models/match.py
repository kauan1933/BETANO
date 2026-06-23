from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum as SAEnum
from app.models.base import Base
import enum


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    match_date = Column(Date, nullable=False, index=True)
    status = Column(SAEnum(MatchStatus), default=MatchStatus.SCHEDULED)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    external_id = Column(String(50), unique=True, nullable=True)
