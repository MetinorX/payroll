import enum
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, Integer, String, ForeignKey, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    leave = "leave"
    half_day = "half_day"


class LeaveType(str, enum.Enum):
    sick = "sick"
    casual = "casual"
    earned = "earned"
    unpaid = "unpaid"


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    clock_in_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    clock_out_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), default=AttendanceStatus.present, nullable=False
    )
    leave_type: Mapped[LeaveType | None] = mapped_column(Enum(LeaveType), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendance_records")
