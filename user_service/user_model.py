from sqlalchemy import Column, Integer, String, Float
from database.db_connection import Base

class User(Base):
    __tablename__ = "users"
    __table_args__= {"schema": "user_service"}
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable =False)
    gender = Column(String(20),nullable=False)
    weight = Column(Float,nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String, default="user")