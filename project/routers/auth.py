from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from .. import schemas, database, models, utils, oauth2
from fastapi.security import OAuth2PasswordRequestForm
import logging
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=schemas.UserResponse)
def create_user(data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        logger.warning("Signup rejected: phone number already registered | phone=%s", data.phone_number[-4:])
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    data.password = utils.hash_password(data.password)
    new_user = models.User(**data.model_dump())
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("New user registered | user_id=%s | phone=%s", new_user.id, new_user.phone_number[-4:])
        return new_user
    except Exception:
        db.rollback()
        logger.exception("Signup failed unexpectedly | phone=%s", data.phone_number[-4:])
        raise

@router.post("/login", response_model=schemas.Token)
def login_user(response : Response, credentials : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.phone_number == credentials.username).first()
    if not user:
        logger.warning("Login rejected: phone number not registered | phone=%s", credentials.username[-4:])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not utils.verify_password(credentials.password, user.password):
        logger.warning("Login rejected: wrong password | user_id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    access_token = oauth2.create_access_token({"sub":str(user.id)})
    refresh_token = oauth2.create_refresh_token({"sub":str(user.id)}, db)
    db.commit()
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=oauth2.REFRESH_TOKEN_EXPIRE_DAYS * 86400, path="/auth")
    logger.info("User logged in | user_id=%s", user.id)
    return {"access_token" : access_token, "refresh_token": refresh_token, "token_type" : "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user : models.User = Depends(oauth2.get_current_user)):
    return current_user

@router.post("/admin", response_model=schemas.AdminResponse)
def create_admin(data: schemas.AdminCreate, db: Session = Depends(database.get_db), current_admin: models.User = Depends(oauth2.get_current_admin)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        logger.warning("Admin creation rejected: phone number already registered | phone=%s | created_by=%s", data.phone_number[-4:], current_admin.id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    existing_admin = db.query(models.Admin).filter(models.Admin.employee_code == data.employee_code).first()
    if existing_admin:
        logger.warning("Admin creation rejected: duplicate employee code | employee_code=%s | created_by=%s", data.employee_code, current_admin.id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="employee code already exists")
    data.password = utils.hash_password(data.password)
    new_user = models.User(first_name=data.first_name, last_name=data.last_name, phone_number=data.phone_number, email=data.email, password=data.password, role="admin")
    try:
        db.add(new_user)
        db.flush()
        new_admin = models.Admin(user_id=new_user.id, position=data.position, employee_code=data.employee_code)
        db.add(new_admin)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_admin)
        logger.info("New admin created | admin_id=%s | employee_code=%s | created_by=%s", new_admin.user_id, new_admin.employee_code, current_admin.id)
        return {"id": new_user.id, "first_name": new_user.first_name, "last_name": new_user.last_name, "position": new_admin.position, "employee_code": new_admin.employee_code}
    except Exception:
        db.rollback()
        logger.exception("Admin creation failed unexpectedly | created_by=%s", current_admin.id)
        raise

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(response : Response, refresh_token: str | None = Cookie(default=None), db : Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
    if refresh_token is None:
        logger.warning("Token refresh rejected: refresh token cookie missing")
        raise credentials_exception
    old_refresh_token = oauth2.verify_refresh_token(refresh_token, credentials_exception, db)
    old_refresh_token.revoked_at = datetime.now(timezone.utc)
    new_access_token = oauth2.create_access_token({"sub":str(old_refresh_token.user_id)})
    new_refresh_token = oauth2.create_refresh_token({"sub":str(old_refresh_token.user_id)}, db, family_id=old_refresh_token.family_id)
    db.commit()
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=False, samesite="lax", max_age=oauth2.REFRESH_TOKEN_EXPIRE_DAYS * 86400, path="/auth")
    logger.info("Token refreshed | user_id=%s | family_id=%s", old_refresh_token.user_id, old_refresh_token.family_id)
    return {"access_token" : new_access_token, "refresh_token": refresh_token, "token_type":"bearer"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response : Response, refresh_token : str | None = Cookie(default=None), db : Session = Depends(database.get_db)):
    if refresh_token is not None:
        oauth2.revoke_refresh_token_family(refresh_token, db)
    else:
        logger.info("Logout attempt without refresh token cookie")
    response.delete_cookie(key="refresh_token", path="/auth")