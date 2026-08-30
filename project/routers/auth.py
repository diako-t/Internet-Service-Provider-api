from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, database, models, utils, oauth2
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=schemas.UserResponse)
def create_user(data: schemas.UserBase, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    data.password = utils.hash_password(data.password)
    new_user = models.User(**data.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login_user(credentials : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.phone_number == credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    access_token = oauth2.create_access_token({"id":user.id, "phone":user.phone_number})
    return {"access_token" : access_token, "token_type" : "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user : models.User = Depends(oauth2.get_current_user)):
    return current_user

@router.post("/admin", response_model=schemas.AdminResponse)
def create_admin(data: schemas.AdminBase, db: Session = Depends(database.get_db), current_admin: models.User = Depends(oauth2.get_current_admin)):
    existing_user = db.query(models.User).filter(models.User.phone_number == data.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone number already registered")
    existing_admin = db.query(models.Admin).filter(models.Admin.employee_code == data.employee_code).first()
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="employee code already exists")
    data.password = utils.hash_password(data.password)
    new_user = models.User(first_name=data.first_name, last_name=data.last_name, phone_number=data.phone_number, email=data.email, password=data.password, role="admin")
    db.add(new_user)
    db.flush()
    new_admin = models.Admin(user_id=new_user.id, position=data.position, employee_code=data.employee_code)
    db.add(new_admin)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_admin)
    return {"id": new_user.id, "first_name": new_user.first_name, "last_name": new_user.last_name, "position": new_admin.position, "employee_code": new_admin.employee_code}