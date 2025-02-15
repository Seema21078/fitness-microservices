from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.db_connection import get_db
from user_service.user_model import User
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError

app = FastAPI()
def reset_user_id_sequence(db: Session):
    db.execute( text("""
        SELECT setval('user_service.users_user_id_seq', 
        COALESCE((SELECT MAX(user_id) FROM user_service.users), 1), 
        true);"""))
    db.commit()
#Define a Pydantic schema for API requests, fastAPI will validate the incoming data
class UserCreate(BaseModel):
    name: str
    age: int
    gender: str
    weight: float
    email: EmailStr

#GET Endpoint - Fetch user by ID
@app.get("/users/{user_id}")
#Depends() -> injects a database session (db) into the get_user
def get_User(user_id: int , db: Session= Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code =404, detail="user not found")
    return{
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email
    }
    
#POST Endpoint - Create a New User
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    #if existing user, generate exception
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists, Please try with different email id")
    try:
        db_user = User(**user.model_dump())  # Convert Pydantic model to dict
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # Fetch generated user_id
        return {"message": "User created successfully", "user_id": db_user.user_id}
    
    #if primary_key already exists, reset the sequence
    except IntegrityError:
        db.rollback()
        reset_user_id_sequence(db)
        return {"error": "Duplicate user_id detected. Sequence has been reset. Try again."}
    