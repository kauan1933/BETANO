from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Enum as SAEnum
from app.models.base import Base
from sqlalchemy.sql import func
import enum


class BetStatus(str, enum.Enum):
    ACTIVE = "active"
    HIT = "hit"
    MISSED = "missed"
    VOID = "void"


class ValueBet(Base):
    __tablename__ = "value_bets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    market = Column(String(100), nullable=False)
    calc_probability = Column(Float, nullable=False)
    market_odds = Column(Float, nullable=False)
    implied_probability = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False)
    confidence = Column(String(20), nullable=True)
    status = Column(SAEnum(BetStatus), default=BetStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
