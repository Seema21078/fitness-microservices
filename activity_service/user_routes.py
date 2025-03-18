import os
from functools import wraps
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .activity_model import Activity
from .activity_schema import ActivityCreate, ActivityResponse
from activity_service.dependencies import validate_token, logger  # Import centralized authentication & logger
from database.db_connection import get_db
from user_service.user_model import User

router = APIRouter(prefix="/activity", tags=["User Activity"])
# Decorator for handling database errors
def handle_database_error(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database IntegrityError: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Data consistency error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected Database Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected Error: {str(e)}"
            )
    return wrapper

# Log Activity (User Logs Daily Steps, Calories, etc.)
@router.post("/", response_model=ActivityResponse)
@handle_database_error
async def log_activity(
    activity_data: ActivityCreate,
    current_user: dict = Depends(validate_token),  # Extract `user_email` from token
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"User {current_user['user_id']} logging activity: {activity_data}")

    # Fetch `user_id` using SQLAlchemy ORM (instead of raw SQL)
    stmt = select(User.user_id).where(User.email == current_user["user_id"])
    result = await db.execute(stmt)
    user_id1 = result.scalar_one_or_none()

    if not user_id1:
        logger.warning(f"User email {current_user['user_id']} not found in user_service.users")
        raise HTTPException(status_code=404, detail="User not found")

    # Store the retrieved `user_id` in activity_data
    new_activity = Activity(**activity_data.model_dump(), user_id=user_id1)
    
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)

    logger.info(f"Activity logged successfully with ID: {new_activity.id}")
    return new_activity

# Get Activity by ID (For Debugging)
@router.get("/{id}", response_model=ActivityResponse)
@handle_database_error
async def get_activity(
    id: int,
    current_user: dict = Depends(validate_token),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Fetching activity {id} for user {current_user['user_id']}")
    
    # Fetch `user_id` using SQLAlchemy ORM (instead of raw SQL)
    stmt = select(User.user_id).where(User.email == current_user["user_id"])
    result = await db.execute(stmt)
    user_id1 = result.scalar_one_or_none()
    
    if not user_id1:
        logger.warning(f"User email {current_user['user_id']} not found in user_service.users")
        raise HTTPException(status_code=404, detail="User not found")

    # if user is valid, filter activity details 
    result = await db.execute(select(Activity).filter(Activity.id == id))
    activity = result.scalar_one_or_none()
    
    if not activity:
        logger.warning(f"Activity id is invalid {id}")
        raise HTTPException(status_code=403, detail="Invalid Activity")
    
    if activity.user_id != user_id1:
        logger.warning(f"Unauthorized access attempt by user {current_user['user_id']} for activity {id}")
        raise HTTPException(status_code=403, detail="Access Denied")
    
    logger.info(f"Activity {id} fetched successfully")
    return activity