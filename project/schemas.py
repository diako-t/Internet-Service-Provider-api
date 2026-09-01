from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    first_name : str
    last_name : str
    phone_number : str
    email : Optional[EmailStr] = None
    password : str

class UserResponse(BaseModel):
    id : int
    first_name : str
    last_name : str
    role : str

class AdminBase(UserBase):
    position : str
    employee_code : str

class AdminResponse(BaseModel):
    id : int
    first_name: str
    last_name : str
    position : str
    employee_code : str

class Token(BaseModel):
    access_token : str
    token_type : str

class CategoryBase(BaseModel):
    name : str
    description : Optional[str] = ""   
    status : Optional[bool] = True

class CategoryResponse(CategoryBase):
    id : int

class ServiceBase(BaseModel):
    category_id : int
    name : str
    description : Optional[str] = ""
    status : Optional[bool] = True

class ServiceCategoryResponse(BaseModel):
    name: str

class ServiceResponse(BaseModel):
    id : int
    name : str
    description : Optional[str] = ""
    status : Optional[bool] = True
    category : ServiceCategoryResponse

class PlanBase(BaseModel):
    service_id : int
    price : float
    duration_days : int
    traffic : float | None
    status : Optional[bool] = True

class PlanServiceResponse(BaseModel):
    name : str

class PlanResponse(BaseModel):
    id : int
    price : float
    duration_days : int
    traffic : float | None
    status : Optional[bool] = True
    service : PlanServiceResponse

class OrderBase(BaseModel):
    plan_id : int
    quantity : int = 1
class OrderResponse(BaseModel):
    id : int
    total_amount : float
    discount : float
    status : str

class OrderItems(BaseModel):
    id : int
    plan_id : int
    service_name : str
    duration_days : int
    unit_price : float
    quantity : int
    model_config = ConfigDict(from_attributes=True)

class OrderItemResponse(BaseModel):
    id : int
    total_amount : float
    discount : float
    status : str
    items : List[OrderItems]
    model_config = ConfigDict(from_attributes=True)

class OrderItemUpdate(BaseModel):
    quantity : int

class TransactionResponse(BaseModel):
    id : int
    order_id : int
    amount : float
    gateway : str
    track_code : str | None
    status : str

class PaymentTest(BaseModel):
    success : bool

class TransactionResponse(BaseModel):
    id : int
    amount : float
    gateway : str
    track_code : str | None
    status : str
    payment_time : datetime | None

class SubscriptionsResponse(BaseModel):
    id : int
    service_name : str
    plan_id : int
    total_traffic : float | None
    start_date : datetime
    end_date : datetime
    status : str
    auto_renew : bool

class SubscriptionsResponseAdmin(SubscriptionsResponse):
    user_id : int

class SubscriptionUpdate(BaseModel):
    auto_renew : bool