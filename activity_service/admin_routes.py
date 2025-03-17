from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connection import get_db
from .activity_model import Activity
from activity_service.dependencies import get_current_admin, validate_token, logger # Admin Authentication

router = APIRouter(prefix="/api/v1/admin/activity", tags=["Admin Activity"])

# Admin API - Fetch specific activity by ID (Debugging)
@router.get("/{activity_id}")
async def get_activity_by_id(activity_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    activity = await db.execute(select(Activity).filter(Activity.id == activity_id))
    result = activity.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Activity not found")
    return result

# Admin API - Fetch all user activities (Debugging)
@router.get("/all")
async def get_all_activities(db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    return await db.execute(select(Activity))

# Admin API - Fetch logs for debugging
@router.get("/logs")
async def get_activity_logs(date: str, admin=Depends(get_current_admin)):
    # Read logs from file system
    log_file = f"logs/activity_{date}.log"
    try:
        with open(log_file, "r") as f:
            return {"logs": f.readlines()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No logs found for this date")
