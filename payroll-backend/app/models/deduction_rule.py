import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RuleType(str, enum.Enum):
    pf = "pf"
    esi = "esi"
    professional_tax = "professional_tax"
    income_tax = "income_tax"


class DeductionRule(Base):
    __tablename__ = "deduction_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    employer_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
