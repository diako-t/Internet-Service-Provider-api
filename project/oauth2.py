from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from . import database, models, config
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import uuid

SECRET_KEY = config.setting.secret_key
ALGORITHM = config.setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.setting.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = config.setting.refresh_token_expire_days

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type" : "access"})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, db : Session, family_id : str | None = None):
    payload = data.copy()
    jti = str(uuid.uuid4())
    if family_id is None:
        family_id = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type" : "refresh", "jti" : jti, "family_id" : family_id})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = models.RefreshToken(jti = jti, family_id = family_id, user_id = payload["sub"], expires_at = expire)
    db.add(refresh_token)
    return encoded_jwt

def verify_access_token(token : str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        logger.warning("Access token rejected: invalid signature or expired")
        raise credentials_exception
    user_id = int(payload.get("sub"))
    token_type = payload.get("type")
    if user_id is None or token_type != "access":
        logger.warning("Access token rejected: wrong token type or missing required claims")
        raise credentials_exception
    return user_id

def verify_refresh_token(token : str, credentials_exception, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        logger.warning("Refresh token rejected: invalid signature or expired")
        raise credentials_exception
    token_type = payload.get("type")
    jti = payload.get("jti")
    if token_type != "refresh" or jti is None:
        logger.warning("Refresh token rejected: wrong token type or missing required claims") 
        raise credentials_exception
    refresh_token = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
    if not refresh_token:
        logger.warning("Refresh token rejected: not found in database | jti=%s", jti)
        raise credentials_exception
    if refresh_token.revoked_at is not None:
        db.query(models.RefreshToken).filter(models.RefreshToken.family_id == refresh_token.family_id, models.RefreshToken.revoked_at == None).update({"revoked_at":datetime.now(timezone.utc)})
        db.commit()
        logger.warning("Refresh token reuse detected, token family revoked | user_id=%s | family_id=%s", refresh_token.user_id, refresh_token.family_id)
        raise credentials_exception
    return refresh_token

def revoke_refresh_token_family(token : str, db : Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        logger.warning("Logout rejected: invalid or expired refresh token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    family_id = payload.get("family_id")
    if payload.get("type") != "refresh" or family_id is None:
        logger.warning("Logout rejected: token is not a refresh token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    db.query(models.RefreshToken).filter(models.RefreshToken.family_id == family_id, models.RefreshToken.revoked_at == None).update({"revoked_at":datetime.now(timezone.utc)})
    db.commit()
    logger.info("Refresh token family revoked on logout | user_id=%s | family_id=%s", payload.get("sub"), family_id)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials")
    user_id = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        logger.warning("Access token valid but user not found | user_id=%s", user_id)
        raise credentials_exception
    return user

def get_current_admin(current_user : models.User = Depends(get_current_user)):
    if current_user.role.lower() != "admin":
        logger.warning("Unauthorized admin access attempt | user_id=%s | role=%s", current_user.id, current_user.role)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return current_user