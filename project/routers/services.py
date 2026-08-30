from fastapi import APIRouter, Depends, HTTPException, status, Response
from .. import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/services", tags=["service"])

@router.get("/", response_model=List[schemas.ServiceResponse])
def get_services(limit: int=10, skip: int=0, search: str="", db: Session = Depends(database.get_db)):
    services =db.query(models.Service).filter(models.Service.name.contains(search)).limit(limit).offset(skip).all()
    return services

@router.get("/{id}", response_model=schemas.ServiceResponse)
def get_service(id: int, db: Session = Depends(database.get_db)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"service {id} not found")
    return service

@router.post("/", response_model=schemas.ServiceResponse)
def create_service(data: schemas.ServiceBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category = db.query(models.Category).filter(models.Category.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    new_service = models.Service(**data.model_dump())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

@router.put("/{id}", response_model=schemas.ServiceResponse)
def update_service(id :int, data: schemas.ServiceBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category = db.query(models.Category).filter(models.Category.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    service_query = db.query(models.Service).filter(models.Service.id == id)
    if not service_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="service not found")
    service_query.update(data.model_dump(), synchronize_session=False)
    db.commit()
    return service_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(id: int, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service_query = db.query(models.Service).filter(models.Service.id == id)
    if not service_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="service not found")
    service_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)