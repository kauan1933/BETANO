from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    logo_url = Column(String(500), nullable=True)
    external_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
