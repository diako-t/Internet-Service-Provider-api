from fastapi import APIRouter, Depends, HTTPException, status, Response, Path, Query
from .. import schemas, database, models, oauth2
from typing import List
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/plans", tags=["service_plans"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[schemas.PlanResponse])
def get_plans(limit: int=Query(10, gt=0), skip: int=Query(0, ge=0), db: Session = Depends(database.get_db)):
    plans = db.query(models.ServicePlan).limit(limit).offset(skip).all()
    return plans

@router.get("/{id}", response_model=schemas.PlanResponse)
def get_plan(id: int=Path(gt=0), db: Session = Depends(database.get_db)):
    plan = db.query(models.ServicePlan).filter(models.ServicePlan.id == id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    return plan

@router.post("/", response_model=schemas.PlanResponse)
def create_plan(data: schemas.PlanCreate, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == data.service_id).first()
    if not service:
        logger.info("Plan creation failed: service_id=%s not found | admin_id=%s", data.service_id, current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    new_plan = models.ServicePlan(**data.model_dump())
    try:
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        logger.info("Plan created | plan_id=%s | service_name=%s | admin_id=%s", new_plan.id, service.name, current_admin.id)
        return new_plan
    except Exception:
        db.rollback()
        logger.exception("Plan creation failed | admin_id=%s", current_admin.id)
        raise

@router.put("/{id}", response_model=schemas.PlanResponse)
def update_plan(data: schemas.PlanCreate, id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == data.service_id).first()
    if not service:
        logger.info("Plan update failed: service_id=%s not found | admin_id=%s", data.service_id, current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    plan_query = db.query(models.ServicePlan).filter(models.ServicePlan.id == id)
    plan = plan_query.first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    try:
        plan_query.update(data.model_dump(), synchronize_session=False)
        db.commit()
        logger.info("Plan updated | plan_id=%s | admin_id=%s", plan.id, current_admin.id)
        return plan_query.first()
    except Exception:
        db.rollback()
        logger.exception("Plan update failed | plan_id=%s | admin_id=%s", id, current_admin.id)
        raise

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    plan_query = db.query(models.ServicePlan).filter(models.ServicePlan.id == id)
    plan = plan_query.first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    try:
        plan_query.delete(synchronize_session=False)
        db.commit()
        logger.warning("Plan deleted | plan_id=%s | service_id=%s | admin_id=%s", id, plan.service.name, current_admin.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        db.rollback()
        logger.exception("Plan deletion failed | plan_id=%s | admin_id=%s", id, current_admin.id)
        raise