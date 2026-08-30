from fastapi import APIRouter, Depends, HTTPException, status, Response
from .. import schemas, database, models, oauth2
from typing import List
from sqlalchemy.orm import Session

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=List[schemas.CategoryResponse])
def get_categories(limit: int=10, skip: int=0, search: str="", db: Session = Depends(database.get_db)):
    categories = db.query(models.Category).filter(models.Category.name.contains(search)).limit(limit).offset(skip).all()
    return categories

@router.get("/{id}", response_model=schemas.CategoryResponse)
def get_category(id: int, db: Session = Depends(database.get_db)):
    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category {id} not found")
    return category

@router.post("/", response_model=schemas.CategoryResponse)
def create_category(data: schemas.CategoryBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    new_category = models.Category(**data.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put("/{id}", response_model=schemas.CategoryResponse)
def update_category(id: int, data: schemas.CategoryBase, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category_query = db.query(models.Category).filter(models.Category.id == id)
    if not category_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")
    category_query.update(data.model_dump(), synchronize_session=False)
    db.commit()
    return category_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: int, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    category_query = db.query(models.Category).filter(models.Category.id == id)
    if not category_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")
    category_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)