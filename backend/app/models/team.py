from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(10), nullable=True)
    logo_url = Column(String(500), nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    external_id = Column(String(50), unique=True, nullable=True)
