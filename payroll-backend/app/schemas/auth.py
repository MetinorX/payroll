from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.schemas.base import CamelModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(CamelModel):
    id: int
    email: str
    role: str
    is_active: bool
    employee_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
