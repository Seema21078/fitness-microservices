from sqlalchemy import Column, Integer, Float, String, Date
from database.db_connection import Base

class Activity(Base):
    __tablename__ = "activity_data"
    __table_args__ = {"schema": "activity_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  
    date = Column(Date, nullable=False)
    steps = Column(Integer, nullable=True)
    calories_burned = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    active_minutes = Column(Integer, nullable=True)
    workout_type = Column(String(50), nullable=True)
