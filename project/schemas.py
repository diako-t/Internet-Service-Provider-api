from pydantic import BaseModel, EmailStr
from typing import Optional

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
    status : Optional[bool] = True

class PlanServiceResponse(BaseModel):
    name : str

class PlanResponse(BaseModel):
    id : int
    price : float
    duration_days : int
    status : Optional[bool] = True
    service : PlanServiceResponse

