from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    basic_salary: Mapped[float] = mapped_column(nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="employee")
    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance", back_populates="employee", cascade="all, delete-orphan"
    )
    salary_components: Mapped[list["SalaryComponent"]] = relationship(
        "SalaryComponent", back_populates="employee", cascade="all, delete-orphan"
    )
    payslips: Mapped[list["Payslip"]] = relationship(
        "Payslip", back_populates="employee", cascade="all, delete-orphan"
    )
