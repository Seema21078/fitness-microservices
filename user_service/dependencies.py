import logging
from logging_config import get_logger
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from logging_config import get_logger  #Import shared logger

logger = get_logger("user_service")  # Use shared logger
# Load secret key from environment or fallback
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = "HS256"
security = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token."""
    logger.info("Received token validation request.")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            logger.warning("Invalid token payload: %s", payload)
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info("Token is valid. User_payload: %s,User Email: %s, Role: %s",payload, user_id, role)
        return {"user_id": user_id, "role": role}  

    except JWTError as e:
        logger.error("JWT Error: %s", str(e))
        raise HTTPException(status_code=401, detail="Token is invalid or expired")