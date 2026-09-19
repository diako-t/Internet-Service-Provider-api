from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from . import database, models, config
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

SECRET_KEY = config.setting.secret_key
ALGORITHM = config.setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.setting.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = config.setting.refresh_token_expire_days

logger = logging.getLogger(__name__)

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type" : "access"})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type" : "refresh"})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token : str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        token_type = payload.get("type")
        if user_id is None or token_type != "access":
            logger.warning("Invalid access token")
            raise credentials_exception
    except JWTError:
        logger.warning("Invalid or expired access token received")
        raise credentials_exception
    return user_id

def verify_refresh_token(token : str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            logger.warning("Invalid refresh token") 
            raise credentials_exception
    except JWTError:
        logger.warning("Invalid or expired refresh token received")
        raise credentials_exception
    return user_id

def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login")), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials")
    id = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        logger.warning("Token was valid but no user found with id=%s", id)
        raise credentials_exception
    return user

def get_current_admin(current_user : models.User = Depends(get_current_user)):
    if current_user.role.lower() != "admin":
        logger.warning("Unauthorized admin access attempt: user_id=%s | role=%s", current_user.id, current_user.role)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return current_user