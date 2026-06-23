from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    position = Column(String(50), nullable=True)
    nationality = Column(String(100), nullable=True)
    photo_url = Column(String(500), nullable=True)
    external_id = Column(String(50), unique=True, nullable=True)
