from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from app.schemas.base import CamelModel


class RunPayrollRequest(BaseModel):
    employee_id: int
    month: int
    year: int

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("year must be between 2000 and 2100")
        return v


class RunPayrollAllRequest(BaseModel):
    month: int
    year: int

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("year must be between 2000 and 2100")
        return v


class DeductionSummary(CamelModel):
    pf_employee: float
    pf_employer: float
    esi_employee: float
    esi_employer: float
    professional_tax: float
    income_tax: float
    total_employee_deductions: float


class PayslipResponse(CamelModel):
    id: int
    employee_id: int
    month: int
    year: int
    gross_pay: float
    total_deductions: float
    net_pay: float
    working_days: Optional[int] = None
    attended_days: Optional[int] = None
    status: str
    pdf_path: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PayslipLineItemResponse(CamelModel):
    id: int
    payslip_id: int
    description: str
    amount: float
    line_type: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PayslipDetailResponse(PayslipResponse):
    line_items: List[PayslipLineItemResponse] = []


class PayslipListResponse(CamelModel):
    items: List[PayslipResponse]
    total: int


class PayrollRunResult(CamelModel):
    employee_id: int
    employee_name: str
    employee_code: str
    gross_pay: float
    net_pay: float
    status: str
    message: str
