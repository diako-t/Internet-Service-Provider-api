from fastapi import APIRouter, Depends, HTTPException, status, Response, Path, Query
from .. import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from typing import List
import logging

router = APIRouter(prefix="/services", tags=["service"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[schemas.ServiceResponse])
def get_services(limit: int=Query(10, gt=0), skip: int=Query(0, ge=0), search: str=Query("", max_length=200), db: Session = Depends(database.get_db)):
    services =db.query(models.Service).filter(models.Service.name.contains(search)).limit(limit).offset(skip).all()
    return services

@router.get("/{id}", response_model=schemas.ServiceResponse)
def get_service(id: int=Path(gt=0), db: Session = Depends(database.get_db)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"service {id} not found")
    return service

@router.post("/", response_model=schemas.ServiceResponse)
def create_service(data: schemas.ServiceCreate, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category = db.query(models.Category).filter(models.Category.id == data.category_id).first()
    if not category:
        logger.warning("Service creation failed: category_id=%s not found | admin_id=%s", data.category_id, current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    new_service = models.Service(**data.model_dump())
    try:
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        logger.info("Service created: service_id=%s | name=%s | admin_id=%s", new_service.id, new_service.name, current_admin.id)
        return new_service
    except Exception:
        db.rollback()
        logger.exception("Service creation failed: admin_id=%s", current_admin.id)
        raise

@router.put("/{id}", response_model=schemas.ServiceResponse)
def update_service(data: schemas.ServiceCreate, id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category = db.query(models.Category).filter(models.Category.id == data.category_id).first()
    if not category:
        logger.warning("Service update failed: category_id=%s not found | admin_id=%s", data.category_id, current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    service_query = db.query(models.Service).filter(models.Service.id == id)
    if not service_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="service not found")
    try:
        service_query.update(data.model_dump(), synchronize_session=False)
        db.commit()
        logger.info("Service updated: service_id=%s | admin_id=%s", id, current_admin.id)
        return service_query.first()
    except Exception:
        db.rollback()
        logger.exception("Service update failed: service_id=%s | admin_id=%s", id, current_admin.id)
        raise


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service_query = db.query(models.Service).filter(models.Service.id == id)
    service = service_query.first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="service not found")
    try:
        service_query.delete(synchronize_session=False)
        db.commit()
        logger.warning("Service deleted: service_id=%s | name=%s | admin_id=%s", id, service.name, current_admin.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        db.rollback()
        logger.exception("Service deletion failed: service_id=%s | admin_id=%s", id, current_admin.id)
        raise