from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Path
from .. import schemas, database, models, oauth2
from typing import List
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/categories", tags=["categories"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[schemas.CategoryResponse])
def get_categories(limit: int=Query(10, gt=0), skip: int=Query(0, ge=0), search: str=Query("", max_length=200), db: Session = Depends(database.get_db)):
    categories = db.query(models.Category).filter(models.Category.name.contains(search)).limit(limit).offset(skip).all()
    return categories

@router.get("/{id}", response_model=schemas.CategoryResponse)
def get_category(id: int=Path(gt=0), db: Session = Depends(database.get_db)):
    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category {id} not found")
    return category

@router.post("/", response_model=schemas.CategoryResponse)
def create_category(data: schemas.CategoryCreate, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    new_category = models.Category(**data.model_dump())
    try:
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        logger.info("Category created: category_id=%s | name=%s | admin_id=%s", new_category.id, new_category.name, current_admin.id)
        return new_category
    except Exception:
        db.rollback()
        logger.exception("Category creation failed: admin_id=%s", current_admin.id)
        raise

@router.put("/{id}", response_model=schemas.CategoryResponse)
def update_category(data: schemas.CategoryCreate, id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category_query = db.query(models.Category).filter(models.Category.id == id)
    if not category_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")
    try:
        category_query.update(data.model_dump(), synchronize_session=False)
        db.commit()
        logger.info("Category updated: category_id=%s | admin_id=%s", id, current_admin.id)
        return category_query.first()
    except Exception:
        db.rollback()
        logger.exception("Category update failed: category_id=%s | admin_id=%s", id, current_admin.id)
        raise    

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: int=Path(gt=0), db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category_query = db.query(models.Category).filter(models.Category.id == id)
    category = category_query.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")
    name = category.name
    try:
        category_query.delete(synchronize_session=False)
        db.commit()
        logger.warning("Category deleted: category_id=%s | name=%s | admin_id=%s", id, name, current_admin.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        db.rollback()
        logger.exception("Category deletion failed: category_id=%s | admin_id=%s", id, current_admin.id)
        raise