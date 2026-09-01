from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from .. import models, database, oauth2, schemas
from typing import List, Optional
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/transactions", tags=["payment"])

@router.get("/admin", response_model=List[schemas.TransactionResponse])
def get_tranaction_by_admin(user_id : Optional[int] = None, limit : int = 10, offset : int = 0, db : Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    query = db.query(models.Transaction)
    if user_id is not None:
        query = query.join(models.Order).filter(models.Order.user_id == user_id)
    transactions = query.limit(limit).offset(offset).all()
    return transactions

@router.get("/", response_model=List[schemas.TransactionResponse])
def get_transactions(db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    transactions = db.query(models.Transaction).join(models.Order).filter(models.Order.user_id == current_user.id).all()
    return transactions

@router.get("/{transaction_id}" ,response_model=schemas.TransactionResponse)
def get_tranaction(transaction_id : int, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    transaction = db.query(models.Transaction).join(models.Order).filter(models.Order.user_id == current_user.id, models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction not found")
    return transaction

@router.post("/{transaction_id}/pay", response_model=schemas.TransactionResponse)
def test_payment(transaction_id : int, data : schemas.PaymentTest, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    transaction = db.query(models.Transaction).join(models.Order).filter(models.Order.user_id == current_user.id, models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction not found")
    if transaction.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="transaction has already been processed")
    order = transaction.order
    if data.success:
        transaction.status = "success"
        transaction.track_code=f"TEST-{uuid.uuid4().hex[:10].upper()}"
        transaction.payment_time = datetime.now(timezone.utc)
        order.status = "paid"
        items = order.order_items
    else:
        transaction.status = "failed"
        transaction.payment_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(transaction)
    return transaction