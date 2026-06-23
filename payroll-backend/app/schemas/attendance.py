from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.attendance import AttendanceStatus, LeaveType
from app.schemas.base import CamelModel


class ClockInRequest(BaseModel):
    employee_id: int
    date: date
    clock_in_time: time


class ClockOutRequest(BaseModel):
    employee_id: int
    date: date
    clock_out_time: time


class LeaveRequest(BaseModel):
    employee_id: int
    date: date
    leave_type: LeaveType
    notes: Optional[str] = None


class AttendanceResponse(CamelModel):
    id: int
    employee_id: int
    date: date
    clock_in_time: Optional[time] = None
    clock_out_time: Optional[time] = None
    status: AttendanceStatus
    leave_type: Optional[LeaveType] = None
    notes: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class AttendanceQueryParams(BaseModel):
    employee_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class AttendanceList(CamelModel):
    items: List[AttendanceResponse]
    total: int
