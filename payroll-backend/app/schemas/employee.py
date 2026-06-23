from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel

from app.schemas.base import CamelModel


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    employee_code: str
    first_name: str
    last_name: str
    department: str
    designation: str
    date_of_joining: date
    basic_salary: float = 0.0


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    basic_salary: Optional[float] = None
    is_active: Optional[bool] = None


class EmployeeResponse(CamelModel):
    id: int
    user_id: int
    employee_code: str
    first_name: str
    last_name: str
    department: str
    designation: str
    date_of_joining: date
    basic_salary: float
    is_active: bool
    email: str
    role: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PaginatedEmployees(CamelModel):
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
