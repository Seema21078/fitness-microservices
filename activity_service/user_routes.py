import os
from functools import wraps
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .activity_model import Activity
from .activity_schema import ActivityCreate, ActivityResponse, ActivitySummary
from activity_service.dependencies import validate_token, logger  # Import centralized authentication & logger
from database.db_connection import get_db
from user_service.user_model import User
from datetime import date, timedelta
from typing import List, Optional

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
@router.get("/{id:int}", response_model=ActivityResponse)
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

# Update Activity API
@router.put("/{id}", response_model=ActivityResponse)
async def update_activity(
    id: int,
    activity_update: ActivityCreate,
    current_user: dict = Depends(validate_token),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"User {current_user['user_id']} attempting to update activity {id}")

    # Fetch activity from database
    result = await db.execute(select(Activity).where(Activity.id == id))
    activity = result.scalar_one_or_none()

    # If activity does not exist, return 404
    if not activity:
        logger.warning(f"Activity {id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")
    
    #Find user_id from current user email id
    stmt = select(User.user_id).where(User.email == current_user["user_id"] )
    result = await db.execute(stmt)
    user_id1 = result.scalar_one_or_none()
    
    # Ensure the logged-in user owns this activity
    if activity.user_id != user_id1:
        logger.warning(f"Unauthorized update attempt by user {current_user['user_id']} for activity {id}")
        raise HTTPException(status_code=403, detail="Access Denied")

    # Update only the provided fields
    update_data = activity_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(activity, key, value)

    # Save changes to database
    await db.commit()
    await db.refresh(activity)

    logger.info(f"Activity {id} updated successfully for user {current_user['user_id']}")
    return activity

# Delete Activity API
@router.delete("/{id}")
async def delete_activity(
    id: int,
    current_user: dict = Depends(validate_token),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Fetching activity {id} for user {current_user['user_id']}")
    activity = await db.execute(select(Activity).where(Activity.id == id))
    activity = activity.scalar_one_or_none()
    
    # If activity does not exist, return 404
    if not activity:
        logger.warning(f"Activity {id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Find user_id from current user email id
    stmt = select(User.user_id).where(User.email == current_user["user_id"] )
    result = await db.execute(stmt)
    user_id1 = result.scalar_one_or_none()
    
    # Ensure the logged-in user owns this activity
    if activity.user_id != user_id1:
        logger.warning(f"Unauthorized update attempt by user {current_user['user_id']} for activity {id}")
        raise HTTPException(status_code=403, detail="Access Denied")
    
    await db.delete(activity)
    await db.commit()
    return {"message":" Activity deleted successfully"} 

# Summary endpoint API
@router.get("/summary", response_model=ActivitySummary, tags=["User Activity"])
async def get_activity_summary(
    period: str = "week",
    current_user: dict = Depends(validate_token),
    db: AsyncSession = Depends(get_db)
):
    logger.info("Token validated successfully.")
    logger.info("Activity summary")
    today = date.today()
    # Determine start_date based on the requested period
    if period == "week":
        # Calculate Monday of the current week
        start_date = today - timedelta(days=today.weekday())
    elif period == "month":
        # Set start_date to the first day of the current month
        start_date = today.replace(day=1)
    else:
        raise HTTPException(status_code=400, detail="Invalid period. Use 'week' or 'month'.")

    # Retrieve the internal user_id from the user_service using the email from the token
    stmt = select(User.user_id).where(User.email == current_user["user_id"])
    result = await db.execute(stmt)
    user_id = result.scalar_one_or_none()
    
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Start_day {start_date} , End_day {today}")
    # Aggregate activity data for the authenticated user within the date range
    stmt = select(
        func.coalesce(func.sum(Activity.steps), 0).label("total_steps"),
        func.coalesce(func.sum(Activity.calories_burned), 0).label("total_calories"),
        func.coalesce(func.sum(Activity.distance_km), 0).label("total_distance"),
        func.coalesce(func.sum(Activity.active_minutes), 0).label("total_active_minutes")
    ).where(
        Activity.user_id == user_id,
        Activity.date.between(start_date, today)
    )
    
    result = await db.execute(stmt)
    summary = result.first()
    logger.info(f"Summary - {summary}")
    
    if summary is None:
        raise HTTPException(status_code=404, detail="No activity data found for the period.")
    
    # Convert the result to a dict, add the user_id, and include period start/end dates
    summary_data = summary._asdict()  # Use _asdict() if using SQLAlchemy Row object
    summary_data["user_id"] = user_id
    summary_data["period_start"] = start_date
    summary_data["period_end"] = today
    logger.info(f"Activity summary computed for user {user_id}: {summary_data}")
    return summary_data

@router.get("/", response_model=List[ActivityResponse])
async def list_activities(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    workout_type: Optional[str] = None,
    current_user: dict = Depends(validate_token),
    db: AsyncSession = Depends(get_db)
):
    # Log at the very beginning so we know this endpoint was hit.
    logger.info("Entered list_activities endpoint with query parameters: start_date=%s, end_date=%s, workout_type=%s",
                start_date, end_date, workout_type)
    
    # Retrieve internal user_id using the email from the token
    stmt = select(User.user_id).where(User.email == current_user["user_id"])
    result = await db.execute(stmt)
    user_id = result.scalar_one_or_none()
    if not user_id:
        logger.error("User not found for email: %s", current_user["user_id"])
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build the query starting with filtering by user_id
    query = select(Activity).where(Activity.user_id == user_id)
    
    # Apply date filtering if provided
    if start_date and end_date:
        query = query.where(Activity.date.between(start_date, end_date))
    elif start_date:
        query = query.where(Activity.date >= start_date)
    elif end_date:
        query = query.where(Activity.date <= end_date)
    
    # Apply filtering for workout type if provided
    if workout_type:
        # Using ilike for case-insensitive matching
        query = query.where(Activity.workout_type.ilike(f"%{workout_type}%"))
    
    # Log the final query for debugging purposes (optional)
    logger.info("Final query: %s", query)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    logger.info("Found %d activities for user %s", len(activities), user_id)
    return activities