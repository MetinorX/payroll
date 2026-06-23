import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PayslipStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"


class Payslip(Base):
    __tablename__ = "payslips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_pay: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_pay: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    working_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attended_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[PayslipStatus] = mapped_column(Enum(PayslipStatus), default=PayslipStatus.draft, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship("Employee", back_populates="payslips")
    line_items: Mapped[list["PayslipLineItem"]] = relationship(
        "PayslipLineItem", back_populates="payslip", cascade="all, delete-orphan"
    )
