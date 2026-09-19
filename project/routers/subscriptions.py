from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from sqlalchemy.orm import Session
from .. import models, database, oauth2, schemas
from typing import Optional, List
import logging

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
logger = logging.getLogger(__name__)

@router.get("/admin", response_model=List[schemas.SubscriptionsResponseAdmin])
def get_subscriptions_by_admin(user_id: int=Query(None, gt=0), active : Optional[schemas.SubscriptionStatus] = None, limit: int=Query(10, gt=0), offset: int=Query(0, ge=0), db : Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    query = db.query(models.Subscription).join(models.OrderItem).join(models.Order)
    if user_id is not None:
        query = query.filter(models.Order.user_id == user_id)
    if active is not None:
        query = query.filter(models.Subscription.status == active)
    subscriptions = query.limit(limit).offset(offset).all()
    result = []
    for sub in subscriptions:
        item = sub.order_item
        result.append({"id":sub.id, "service_name":item.plan.service.name, "plan_id":item.plan_id, "total_traffic":sub.total_traffic, "start_date":sub.start_date, "end_date":sub.end_date, "status":sub.status, "auto_renew":sub.auto_renew, "user_id":item.order.user_id})
    return result

@router.get("/", response_model=List[schemas.SubscriptionsResponse])
def get_subscriptions(active : Optional[schemas.SubscriptionStatus] = None, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    subscriptions = db.query(models.Subscription).join(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id)
    if active is not None:
        subscriptions = subscriptions.filter(models.Subscription.status == active)
    subscriptions = subscriptions.all()
    result = []
    for sub in subscriptions:
        item = sub.order_item
        result.append({"id":sub.id, "service_name":item.plan.service.name, "plan_id":item.plan_id, "total_traffic":sub.total_traffic, "start_date":sub.start_date, "end_date":sub.end_date, "status":sub.status, "auto_renew":sub.auto_renew})
    return result

@router.get("/{subscription_id}", response_model=schemas.SubscriptionsResponse)
def get_subscription(subscription_id : int=Path(gt=0), db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    subscription = db.query(models.Subscription).join(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id, models.Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    item = subscription.order_item
    return {"id":subscription.id, "service_name":item.plan.service.name, "plan_id":item.plan_id, "total_traffic":subscription.total_traffic, "start_date":subscription.start_date, "end_date":subscription.end_date, "status":subscription.status, "auto_renew":subscription.auto_renew}

@router.patch("/{subscription_id}", response_model=schemas.SubscriptionsResponse)
def subscription_update(data : schemas.SubscriptionUpdate, subscription_id : int=Path(gt=0), db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    subscription = db.query(models.Subscription).join(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id, models.Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    if subscription.status.lower() != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subscription is not active")
    try:
        subscription.auto_renew = data.auto_renew
        db.commit()
        db.refresh(subscription)
        logger.info("Subscription updated: subscription_id=%s | auto_renew=%s | user_id=%s", subscription.id, subscription.auto_renew, current_user.id)
        item = subscription.order_item
        return {"id":subscription.id, "service_name":item.plan.service.name, "plan_id":item.plan_id, "total_traffic":subscription.total_traffic, "start_date":subscription.start_date, "end_date":subscription.end_date, "status":subscription.status, "auto_renew":subscription.auto_renew}
    except Exception:
        db.rollback()
        logger.exception("Subscription update failed: subscription_id=%s | user_id=%s", subscription.id, current_user.id)
        raise

@router.patch("/{subscription_id}/cancel", response_model=schemas.SubscriptionsResponse)
def subscription_delete(subscription_id : int=Path(gt=0), db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    subscription = db.query(models.Subscription).join(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id, models.Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    if subscription.status.lower() != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subscription is not active")
    try:
        subscription.status = "cancelled"
        subscription.auto_renew = False
        db.commit()
        db.refresh(subscription)
        logger.warning("Subscription cancelled: subscription_id=%s | user_id=%s", subscription.id, current_user.id)
        item = subscription.order_item
        return {"id":subscription.id, "service_name":item.plan.service.name, "plan_id":item.plan_id, "total_traffic":subscription.total_traffic, "start_date":subscription.start_date, "end_date":subscription.end_date, "status":subscription.status, "auto_renew":subscription.auto_renew}
    except Exception:
        db.rollback()
        logger.exception("Subscription cancellation failed: subscription_id=%s | user_id=%s", subscription.id, current_user.id)
        raise