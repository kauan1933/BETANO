from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from app.models.base import Base


class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    minutes_played = Column(Integer, default=0)
    total_shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("player_id", "match_id", name="uq_player_match"),
    )
