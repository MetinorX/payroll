import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LineType(str, enum.Enum):
    earning = "earning"
    deduction = "deduction"


class PayslipLineItem(Base):
    __tablename__ = "payslip_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payslip_id: Mapped[int] = mapped_column(Integer, ForeignKey("payslips.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    line_type: Mapped[LineType] = mapped_column(Enum(LineType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payslip: Mapped["Payslip"] = relationship("Payslip", back_populates="line_items")
