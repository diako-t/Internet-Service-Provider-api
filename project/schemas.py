from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, field_serializer
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal
import re

class UserCreate(BaseModel):
    first_name : str = Field(..., min_length=3, max_length=50)
    last_name : str = Field(..., min_length=3, max_length=50)
    phone_number : str 
    email : Optional[EmailStr] = None
    password : str = Field(..., min_length=8, max_length=64)

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if not value.isdigit():
            raise ValueError("phone number must contain only digits")
        if len(value) != 11:
            raise ValueError("phone number must be 11 digits")
        return value

    @field_validator("password")
    def validate_password(cls, value):
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")
        if not re.fullmatch(r"[A-Za-z0-9@_-]+", value):
            raise ValueError("password can only contain letters, numbers and @ _ -")
        return value

class UserResponse(BaseModel):
    id : int
    first_name : str
    last_name : str
    role : str

class AdminPosition(str, Enum):
    MANAGER = "manager"
    PRODUCT_MANAGER = "product_manager"
    SUPPORT_SPECIALIST = "support_specialist"

class AdminCreate(UserCreate):
    position : AdminPosition
    employee_code : str

class AdminResponse(BaseModel):
    id : int
    first_name: str
    last_name : str
    position : str
    employee_code : str

class Token(BaseModel):
    access_token : str
    refresh_token : str
    token_type : str

class RefreshToken(BaseModel):
    refresh_token : str

class CategoryCreate(BaseModel):
    name : str
    description : str = Field(default="", max_length=500)
    status : bool = True

class CategoryResponse(CategoryCreate):
    id : int

class ServiceCreate(BaseModel):
    category_id : int = Field(..., gt=0)
    name : str
    description : str = Field(default="", max_length=500)
    status : bool = True

class ServiceCategoryDetails(BaseModel):
    name: str

class ServiceResponse(BaseModel):
    id : int
    name : str
    description : Optional[str] = ""
    status : bool
    category : ServiceCategoryDetails

class PlanCreate(BaseModel):
    service_id : int = Field(..., gt=0)
    price : Decimal = Field(..., gt=0)
    duration_days : int = Field(..., gt=0)
    traffic : float | None = Field(default=None, gt=0)
    status : bool = True

class PlanServiceDetails(BaseModel):
    name : str

class PlanResponse(BaseModel):
    id : int
    price : Decimal
    duration_days : int
    traffic : float | None
    status : bool
    service : PlanServiceDetails

class OrderCreate(BaseModel):
    plan_id : int = Field(..., gt=0)
    quantity : int = Field(1, gt=0, le=10)

class OrderResponse(BaseModel):
    id : int
    total_amount : Decimal
    discount : Decimal
    status : str

class OrderItems(BaseModel):
    id : int
    plan_id : int
    service_name : str
    duration_days : int
    unit_price : Decimal
    quantity : int
    model_config = ConfigDict(from_attributes=True)

class OrderItemsResponse(BaseModel):
    id : int
    total_amount : Decimal
    discount : Decimal
    status : str
    items : List[OrderItems]
    model_config = ConfigDict(from_attributes=True)

class OrderItemUpdate(BaseModel):
    quantity : int = Field(..., gt=0, le=10)

class TransactionResponse(BaseModel):
    id : int
    order_id : int
    amount : Decimal
    gateway : str
    track_code : str | None
    status : str
    payment_time : datetime | None

class PaymentTest(BaseModel):
    success : bool

class SubscriptionsResponse(BaseModel):
    id : int
    service_name : str
    plan_id : int
    total_traffic : float | None
    start_date : datetime
    end_date : datetime
    status : str
    auto_renew : bool

    @field_serializer("start_date", "end_date")
    def serialize_dates(self, value : datetime):
        return value.strftime("%y-%m-%d %H:%M:%S")

class SubscriptionsResponseAdmin(SubscriptionsResponse):
    user_id : int

class SubscriptionUpdate(BaseModel):
    auto_renew : bool

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"