from sqlalchemy import Column, Integer, Float, DateTime
from app.models.base import Base
from sqlalchemy.sql import func


class PlayerForm(Base):
    __tablename__ = "player_form"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, nullable=False, index=True)
    games_analyzed = Column(Integer, default=0)
    avg_total_shots = Column(Float, default=0.0)
    avg_shots_on_target = Column(Float, default=0.0)
    avg_minutes_played = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, server_default=func.now())
