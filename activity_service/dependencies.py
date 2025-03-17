import os
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from logging_config import get_logger

logger = get_logger("activity_service")

# Load `USER_SERVICE_URL` from environment or use default
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://127.0.0.1:8002/validate_token")
security = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validate JWT token by calling `user_service/validate_token` API."""
    token = credentials.credentials  # Extract token from Authorization header
    
    logger.info(" Validating token with user_service...")
    logger.info(" printing token- %s",token)
    logger.info(f"Sent request to: {USER_SERVICE_URL}")

    try:
        # Send request to user_service for validation
        response = requests.get(
            USER_SERVICE_URL,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info("Token validated successfully. Response: %s", response.json())
        if response.status_code == 200:
            logger.info("Token validated successfully. Response: %s", response.json())
            return response.json()  # Returns {"user_id": "...", "role": "..."}
        else:
            logger.error("Token validation failed. Response: %s", response.json())
            raise HTTPException(status_code=401, detail="Invalid or expired token")


    except requests.exceptions.RequestException as e:
        logger.error("Error contacting user_service: %s", str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    user_data = validate_token(credentials)  # Use the existing function

    if user_data.get("role") != "admin":
        logger.warning(f"Unauthorized access attempt by user {user_data.get('user_id')}")
        raise HTTPException(status_code=403, detail="Admin access required")

    return user_data  # Returns admin user details
