from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

#load database URL from .env
load_dotenv()
DATABASE_URL =os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
session =sessionmaker(autocommit=False, autoflush=False,bind=engine)

Base= declarative_base()

#API for creating db sesion, can be used from other APIs
def get_db():
    db= session()
    try:
        yield db
    finally:
        db.close()

