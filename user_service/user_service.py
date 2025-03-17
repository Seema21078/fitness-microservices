from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status,Request,APIRouter
from requests import Session
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connection import get_db
from user_service.user_model import User
from pydantic import BaseModel, EmailStr, conint, confloat
from sqlalchemy.exc import IntegrityError
from functools import wraps
import logging
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from user_service.dependencies import validate_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from logging_config import get_logger

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = "HS256"
security = HTTPBearer()
logger = get_logger("user_service")  #Initialize logger properly
logger.info("User Service Started.")

# JWT Configurations
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#Initialize Fast API app
app = FastAPI(title="User Service")

#Pydantic schema for API requests, fastAPI will validate the incoming data
class UserCreate(BaseModel):
    name: str
    age: conint (gt=0, le=120) # type: ignore
    gender: str
    weight: confloat (gt=0) # type: ignore
    email: EmailStr
    password: str

#Pydantic schema for API response
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True
        
class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserLogin(BaseModel):  
    email: EmailStr
    password: str
            
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

# Validate option
@app.get("/validate_token",tags=["Auth"])
async def validate_token_api(user: dict = Depends(validate_token)):
    """Expose validate_token as an API for other microservices."""
    logger.info("validate_token called successfully for user: %s", user["user_id"])
    return user

# Register User API 
@app.post("/register", response_model=UserResponse, tags=["Auth"])
@handle_database_error
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Attempted to register with existing email: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash the password and create a new user
        hashed_password = get_password_hash(user.password)
        db_user = User(**user.model_dump(exclude={"password"}), password_hash=hashed_password)

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user  # Successfully created user

    except IntegrityError as e:
        await db.rollback()  # Ensure rollback on error
        logger.error(f"Database integrity error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    except Exception as e:
        await db.rollback()
        logger.critical(f"Unexpected error during user registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
#Login User API, creates access token
@app.post("/login", response_model=Token, tags=["Auth"])
@handle_database_error
async def login_for_access_token(user: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        user_record = result.scalar_one_or_none()

        if not user_record or not verify_password(user.password, user_record.password_hash):
            logger.warning(f"Failed login attempt for email: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        access_token = create_access_token(data={"sub": user.email,"role": user_record.role },
                                           expires_delta=access_token_expires)
        logger.info(f"User {user.email} logged in successfully.")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Unexpected error during login for email {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
        
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
@app.post("/users", response_model=UserResponse, tags=["User"])
@handle_database_error
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user in the database."""
    logger.info(f"Received request to create user: {user.email}")

    # Check if a user with the same email already exists
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(f"Duplicate email attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists, Please try with a different email id"
        )
    
    try:
        # Create new user
        # Hash the password and create a new user
        hashed_password = get_password_hash(user.password)
        db_user = User(**user.model_dump(exclude={"password"}), password_hash=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)  # Refresh to get the user_id
        
        logger.info(f"New user created successfully: User ID {db_user.user_id}, Email: {user.email}")
        return db_user  # Return the actual user object

    except IntegrityError as e:
        await db.rollback()  # Correctly await rollback
        logger.error(f"Database integrity error while creating user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data input"
        )
    
    except Exception as e:
        await db.rollback()
        logger.critical(f"Unexpected error during user creation for {user.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
