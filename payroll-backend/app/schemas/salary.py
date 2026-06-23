from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.salary_component import ComponentType
from app.schemas.base import CamelModel


class SalaryComponentCreate(BaseModel):
    component_type: ComponentType
    amount: float
    effective_from: date
    effective_to: Optional[date] = None


class SalaryBulkCreate(BaseModel):
    components: List[SalaryComponentCreate]


class SalaryComponentResponse(CamelModel):
    id: int
    employee_id: int
    component_type: ComponentType
    amount: float
    effective_from: date
    effective_to: Optional[date] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class SalaryConfigResponse(CamelModel):
    employee_id: int
    components: List[SalaryComponentResponse]
    total_monthly: float
