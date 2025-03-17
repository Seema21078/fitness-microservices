from fastapi import FastAPI
from activity_service.user_routes import router as user_router
from activity_service.admin_routes import router as admin_router
from activity_service.dependencies import logger

app = FastAPI(title="Activity Service")

# Include separate routers
app.include_router(user_router)
app.include_router(admin_router)
logger.info("Activity Service Started.")