import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ComponentType(str, enum.Enum):
    basic = "basic"
    hra = "hra"
    da = "da"
    conveyance = "conveyance"
    medical = "medical"
    special = "special"
    bonus = "bonus"


class SalaryComponent(Base):
    __tablename__ = "salary_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    component_type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_components")
