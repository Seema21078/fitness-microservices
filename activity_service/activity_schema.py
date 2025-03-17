from pydantic import BaseModel, conint, confloat
from datetime import date
from typing import Optional

class ActivityCreate(BaseModel):
    date: date
    steps: Optional[int] = None
    calories_burned: Optional[float] = None
    distance_km: Optional[float] = None
    active_minutes: Optional[int] = None
    workout_type: Optional[str] = None

    # Validation Constraints
    _validate_steps = conint(ge=0)  # Steps cannot be negative
    _validate_calories = confloat(ge=0)  # Calories cannot be negative
    _validate_distance = confloat(ge=0)  # Distance cannot be negative
    _validate_active_minutes = conint(ge=0)  # Active minutes cannot be negative

# Schema for response when retrieving activity data (used in GET /activity/{id})
class ActivityResponse(BaseModel):
    id: int
    user_id: int
    date: date
    steps: Optional[int]
    calories_burned: Optional[float]
    distance_km: Optional[float]
    active_minutes: Optional[int]
    workout_type: Optional[str]

    class Config:
        from_attributes = True  # Converts SQLAlchemy models to Pydantic objects

# Schema for summary responses (used in GET /activity/summary)
class ActivitySummary(BaseModel):
    user_id: int
    total_steps: int
    total_calories: float
    total_distance: float
    total_active_minutes: int
