from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, UniqueConstraint
from app.models.base import Base


class ExpectedLineup(Base):
    __tablename__ = "expected_lineups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    is_probable = Column(Boolean, default=True)
    is_injured = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    source = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_lineup_player"),
    )
