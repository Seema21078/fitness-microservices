from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connection import get_db
from user_service.user_model import User
from pydantic import BaseModel, EmailStr, conint, confloat
from sqlalchemy.exc import IntegrityError
from functools import wraps
import logging
import os

#for logging
logger = logging.getLogger(__name__)
# Create the directory if it doesn't exist
log_dir = "C:/logs"
os.makedirs(log_dir, exist_ok=True)  # Creates directory if missing

logging.basicConfig(level=logging.INFO,
                    filename=os.path.join(log_dir, "app.log"),
                    filemode="a",         # Append mode
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

#Initialize Fast API app
app = FastAPI()

# was facing issue with user_id primary_key, check?
#def reset_user_id_sequence(db: Session):
#    db.execute( text("""
#   SELECT setval('user_service.users_user_id_seq', 
#   COALESCE((SELECT MAX(user_id) FROM user_service.users), 1), 
#   true);"""))
#    db.commit()

#Pydantic schema for API requests, fastAPI will validate the incoming data
class UserCreate(BaseModel):
    name: str
    age: conint (gt=0, le=120) # type: ignore
    gender: str
    weight: confloat (gt=0) # type: ignore
    email: EmailStr

#Pydantic schema for API response
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True
        
# Decorator for handling database errors
def handle_database_error(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Data consistency error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper
        
#GET Endpoint - Fetch user by ID
@app.get("/users/{user_id}", response_model=UserResponse)
@handle_database_error
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.user_id == user_id))
    user = result.scalars().first()  # Get the user from the result
    if not user:
        logger.warning(f"User not found with ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
    
#POST Endpoint - Create a New User
@app.post("/users", response_model=UserResponse)
@handle_database_error
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check for existing user by email
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        logger.warning(f"Duplicate email attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists, Please try with different email id"
        )
    
    try:
        db_user = User(**user.model_dump())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)  # Refresh to get the user_id
        logger.info(f"New user created: {db_user.user_id}")
        return db_user  # Return the actual user object
    
    except IntegrityError as e:
        await db.rollback()  # Correctly await rollback
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data input"
        )