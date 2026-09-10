from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List, Optional
import logging

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.OrderResponse)
def create_cart(data : schemas.OrderBase, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    plan = db.query(models.ServicePlan).filter(data.plan_id == models.ServicePlan.id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    if not plan.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plan is not active")
    if data.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quantity must be at least 1")
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "pending").first()
    if not order:
        order = models.Order(user_id=current_user.id, total_amount=0)
        db.add(order)
        db.flush()
    order_item = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id, models.OrderItem.plan_id == plan.id).first()
    if order_item:
        order_item.quantity += data.quantity
    else:
        order_item = models.OrderItem(order_id=order.id, plan_id=plan.id, unit_price=plan.price, quantity=data.quantity)
        db.add(order_item)
    try:
        db.flush()
        total_price = sum(item.unit_price * item.quantity for item in order.order_items)
        order.total_amount = total_price - order.discount
        db.commit()
        db.refresh(order)
        logger.info("item added to cart: order_id=%s | plan_id=%s | item_id=%s | user_id=%s", order.id, plan.id, order_item.id, current_user.id)
        return order
    except Exception:
        db.rollback()
        logger.exception("adding item failed: plan_id=%s | user_id=%s", plan.id, current_user.id)
        raise

@router.get("/cart", response_model=schemas.OrderItemResponse)
def get_cart(db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "pending").first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cart is empty")
    items = []
    for item in order.order_items:
        items.append({"id":item.id, "plan_id":item.plan_id, "service_name":item.plan.service.name, "duration_days":item.plan.duration_days, "traffic":item.plan.traffic, "unit_price":item.unit_price, "quantity":item.quantity})
    return {"id":order.id, "total_amount":order.total_amount, "discount":order.discount, "status":order.status, "items":items}

@router.put("/items/{item_id}", response_model=schemas.OrderResponse)
def update_items(item_id : int, data : schemas.OrderItemUpdate, db :Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    if data.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quantity must be at least 1")
    order_item = db.query(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id, models.OrderItem.id == item_id, models.Order.status == "pending").first()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order item not found")
    try:
        order_item.quantity = data.quantity
        db.flush()
        order = order_item.order
        total_price = sum(item.unit_price * item.quantity for item in order.order_items)
        order.total_amount = total_price - order.discount    
        db.commit()
        db.refresh(order)
        logger.info("Order item updated: item_id=%s | new_quantity=%s | user_id=%s", item_id, data.quantity, current_user.id)
        return order
    except Exception:
        db.rollback()
        logger.exception("Order item update failed: item_id=%s | user_id=%s", item_id, current_user.id)
        raise

@router.delete("/items/{item_id}", response_model=schemas.OrderResponse)
def delete_items(item_id : int, db :Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    order_item = db.query(models.OrderItem).join(models.Order).filter(models.Order.user_id == current_user.id, models.OrderItem.id == item_id, models.Order.status == "pending").first()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order item not found")
    order = order_item.order
    try:
        db.delete(order_item)
        db.flush()
        total_price = sum(item.unit_price * item.quantity for item in order.order_items)
        order.total_amount = total_price - order.discount   
        db.commit()
        db.refresh(order)
        logger.info("Order item deleted: item_id=%s | order_id=%s | user_id=%s", item_id, order.id, current_user.id)
        return order
    except Exception:
        db.rollback()
        logger.exception("Order item deletion failed: item_id=%s | user_id=%s", item_id, current_user.id)
        raise

@router.delete("/cart", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(db :Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "pending").first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cart is empty")
    order_id = order.id
    try:
        db.delete(order)
        db.commit()
        logger.warning("Cart deleted: order_id=%s | user_id=%s", order_id, current_user.id)
    except Exception:
        db.rollback()
        logger.exception("Cart deletion failed: order_id=%s | user_id=%s", order_id, current_user.id)
        raise


@router.get("/admin", response_model=List[schemas.OrderItemResponse])
def get_orders_by_admin(user_id : Optional[int] = None, limit : int = 10, offset : int = 0, db: Session = Depends(database.get_db), current_admin : models.User = Depends(oauth2.get_current_admin)):
    query = db.query(models.Order)
    if user_id is not None:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user does not exist")
        query = query.filter(models.Order.user_id == user_id)
    orders = query.limit(limit).offset(offset).all()
    result = []
    for order in orders:
        items = []
        for item in order.order_items:
            items.append({"id":item.id, "plan_id":item.plan_id, "service_name":item.plan.service.name, "duration_days":item.plan.duration_days, "traffic":item.plan.traffic, "unit_price":item.unit_price, "quantity":item.quantity})
        result.append({"id":order.id, "total_amount":order.total_amount, "discount":order.discount, "status":order.status, "items":items})
    return result

@router.get("/", response_model=List[schemas.OrderItemResponse])
def get_orders(db :Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
    result = []
    for order in orders:
        items = []
        for item in order.order_items:
            items.append({"id":item.id, "plan_id":item.plan_id, "service_name":item.plan.service.name, "duration_days":item.plan.duration_days, "traffic":item.plan.traffic, "unit_price":item.unit_price, "quantity":item.quantity})
        result.append({"id":order.id, "total_amount":order.total_amount, "discount":order.discount, "status":order.status, "items":items})
    return result

@router.get("/{order_id}", response_model=schemas.OrderItemResponse)
def get_order(order_id : int, db :Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    items = []
    for item in order.order_items:
        items.append({"id":item.id, "plan_id":item.plan_id, "service_name":item.plan.service.name, "duration_days":item.plan.duration_days, "traffic":item.plan.traffic, "unit_price":item.unit_price, "quantity":item.quantity})
    return {"id":order.id, "total_amount":order.total_amount, "discount":order.discount, "status":order.status, "items":items}

@router.post("/{order_id}/checkout", response_model=schemas.TransactionResponse)
def checkout(order_id : int, db : Session = Depends(database.get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.id == order_id, models.Order.status == "pending").first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    if not order.order_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cart is empty")
    if order.total_amount <= 0:
        logger.warning( "Checkout failed: invalid payment amount | order_id=%s | user_id=%s", order_id, current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid payment")
    transaction = db.query(models.Transaction).filter(models.Transaction.order_id == order_id, models.Transaction.status == "pending").first()
    if transaction:
        return transaction
    try:
        transaction = models.Transaction(order_id=order.id, amount=order.total_amount, gateway="test", status="pending")
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        logger.info("Checkout initiated: transaction_id=%s | order_id=%s | amount=%s | user_id=%s", transaction.id, order_id, transaction.amount, current_user.id)
        return transaction
    except Exception:
        db.rollback()
        logger.exception("Checkout failed: order_id=%s | user_id=%s", order_id, current_user.id)
        raise