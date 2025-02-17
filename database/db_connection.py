from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Load database URL from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create an asynchronous session maker
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# API for creating db session, can be used from other APIs
async def get_db():
    async with async_session() as db:
        yield db  # Session will be automatically closed after exiting the block
