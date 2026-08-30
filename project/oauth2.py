from datetime import datetime, timedelta
from jose import JWTError, jwt
from . import database, models, config
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

SECRET_KEY = config.setting.secret_key
ALGORITHM = config.setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.setting.access_token_expire_minutes

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token : str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id = payload.get("id")
    except JWTError:
        raise credentials_exception
    return id

def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login")), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials")
    id = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise credentials_exception
    return user

def get_current_admin(current_user : models.User = Depends(get_current_user)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return current_user