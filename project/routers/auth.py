from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, database, models, utils, oauth2
from fastapi.security import OAuth2PasswordRequestForm
import logging

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=schemas.UserResponse)
def create_user(data: schemas.UserBase, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        logger.warning("Signup attempt with already registered phone_number=%s", data.phone_number)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    data.password = utils.hash_password(data.password)
    new_user = models.User(**data.model_dump())
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("New user registered: user_id=%s | phone=%s", new_user.id, new_user.phone_number)
        return new_user
    except Exception:
        db.rollback()
        logger.exception("New user registration failed: phone=%s", data.phone_number)
        raise

@router.post("/login", response_model=schemas.Token)
def login_user(credentials : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.phone_number == credentials.username).first()
    if not user:
        logger.warning("Login attempt with unregistered phone_number=%s", credentials.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not utils.verify_password(credentials.password, user.password):
        logger.warning("Failed login attempt (wrong password): user_id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    access_token = oauth2.create_access_token({"id":user.id, "phone":user.phone_number})
    logger.info("User logged in: user_id=%s", user.id)
    return {"access_token" : access_token, "token_type" : "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user : models.User = Depends(oauth2.get_current_user)):
    return current_user

@router.post("/admin", response_model=schemas.AdminResponse)
def create_admin(data: schemas.AdminBase, db: Session = Depends(database.get_db), current_admin: models.User = Depends(oauth2.get_current_admin)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        logger.warning("Admin creation attempt with already registered phone_number=%s", data.phone_number)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    existing_admin = db.query(models.Admin).filter(models.Admin.employee_code == data.employee_code).first()
    if existing_admin:
        logger.warning("Admin creation attempt with duplicate employee_code=%s", data.employee_code)
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
        logger.info("New admin created: admin_id=%s | employee_code=%s | created_by=%s", new_admin.user_id, new_admin.employee_code, current_admin.id)
        return {"id": new_user.id, "first_name": new_user.first_name, "last_name": new_user.last_name, "position": new_admin.position, "employee_code": new_admin.employee_code}
    except Exception:
        db.rollback()
        logger.exception("New admin creation failed: created_by=%s", current_admin.id)