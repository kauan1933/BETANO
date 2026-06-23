from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from app.models.base import Base
from sqlalchemy.sql import func


class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String(50), nullable=False)
    market = Column(String(100), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    selection = Column(String(200), nullable=False)
    odds_value = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
