from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    services = relationship("Service", back_populates="category")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    category = relationship("Category", back_populates="services")
    plans = relationship("ServicePlan", back_populates="service")


class ServicePlan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10,2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    service = relationship("Service", back_populates="plans")
    order_items = relationship("OrderItem", back_populates="plan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    signup_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    role = Column(String(20), default="customer", nullable=False)
    password = Column(Text, nullable=False)

    admin = relationship("Admin", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")

class Admin(Base):
    __tablename__ = "admins"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    position = Column(String(50), nullable=False)
    hire_date = Column(TIMESTAMP(timezone=True), nullable=True, server_default=text("now()"))
    employee_code = Column(String(20), unique=True, nullable=False)

    user = relationship("User", back_populates="admin")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"), nullable=False)
    discount = Column(Numeric(10,2), default=0)
    
    order_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    status = Column(String(50), nullable=False, default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)

    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id",ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    unit_price = Column(Numeric(10,2), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    plan = relationship("ServicePlan", back_populates="order_items")
    order = relationship("Order", back_populates="order_items")
    subscription = relationship("Subscription", back_populates="order_item", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id",ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    gateway = Column(String(50), nullable=False)
    track_code = Column(String(100), nullable=True, unique=True)
    status = Column(String(20), default="pending", nullable=False)
    payment_time = Column(TIMESTAMP(timezone=True), nullable=True)

    order = relationship("Order", back_populates="transactions")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, nullable=False)
    item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False, unique=True)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    auto_renew = Column(Boolean, default=False, nullable=False)

    order_item = relationship("OrderItem", back_populates="subscription")