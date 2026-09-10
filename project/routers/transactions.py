from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from .. import models, database, oauth2, schemas
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import logging

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)

@router.get("/admin", response_model=List[schemas.TransactionResponse])
def get_transaction_by_admin(user_id : Optional[int] = None, limit : int = 10, offset : int = 0, db : Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
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
def get_transaction(transaction_id : int, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
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
    try:
        if data.success:
            transaction.status = "success"
            transaction.track_code=f"TEST-{uuid.uuid4().hex[:10].upper()}"
            transaction.payment_time = datetime.now(timezone.utc)
            order.status = "paid"
            now = datetime.now(timezone.utc)
            for item in order.order_items:
                duration = item.plan.duration_days * item.quantity
                traffic = item.plan.traffic * item.quantity if item.plan.traffic is not None else None
                sub = models.Subscription(item_id=item.id, start_date=now, end_date=now+timedelta(days=duration), total_traffic=traffic, status="active", auto_renew=False)
                db.add(sub)
            order.status = "completed"
            db.commit()
            logger.info("Payment successful: transaction_id=%s | user_id=%s | track_code=%s", transaction.id, current_user.id, transaction.track_code)
        else:
            transaction.status = "failed"
            transaction.payment_time = datetime.now(timezone.utc)
            db.commit()
            logger.info("Payment failed: transaction_id=%s | order_id=%s | user_id=%s", transaction.id, order.id, current_user.id)
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()  
        logger.exception("Payment processing failed: transaction_id=%s | user_id=%s", transaction.id, current_user.id)
        raise