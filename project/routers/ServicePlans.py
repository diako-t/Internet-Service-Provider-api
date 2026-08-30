from fastapi import APIRouter, Depends, HTTPException, status, Response
from .. import schemas, database, models, oauth2
from typing import List
from sqlalchemy.orm import Session

router = APIRouter(prefix="/plans", tags=["service_plans"])

@router.get("/", response_model=List[schemas.PlanResponse])
def get_plans(limit: int=10, skip: int=0, db: Session = Depends(database.get_db)):
    plans = db.query(models.ServicePlan).limit(limit).offset(skip).all()
    return plans

@router.get("/{id}", response_model=schemas.PlanResponse)
def get_plan(id: int, db: Session = Depends(database.get_db)):
    plan = db.query(models.ServicePlan).filter(models.ServicePlan.id == id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    return plan

@router.post("/", response_model=schemas.PlanResponse)
def create_plan(data: schemas.PlanBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == data.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    new_plan = models.ServicePlan(**data.model_dump())
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.put("/{id}", response_model=schemas.PlanResponse)
def update_plan(id :int, data: schemas.PlanBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == data.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    plan_query = db.query(models.ServicePlan).filter(models.ServicePlan.id == id)
    if not plan_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    plan_query.update(data.model_dump(), synchronize_session=False)
    db.commit()
    return plan_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(id: int, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    plan_query = db.query(models.ServicePlan).filter(models.ServicePlan.id == id)
    if not plan_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    plan_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)