import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceList,
    AttendanceResponse,
    ClockInRequest,
    ClockOutRequest,
    LeaveRequest,
)

logger = logging.getLogger("payroll.attendance")
router = APIRouter(prefix="/attendance", tags=["Attendance"])


async def _get_employee(db: AsyncSession, user: User) -> Employee:
    result = await db.execute(select(Employee).where(Employee.user_id == user.id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return emp


@router.post("/clock-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def clock_in(
    body: ClockInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await _get_employee(db, current_user)
        if emp.id != body.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    existing = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == body.employee_id,
            Attendance.date == body.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already clocked in for this date")

    record = Attendance(
        employee_id=body.employee_id,
        date=body.date,
        clock_in_time=body.clock_in_time,
        status=AttendanceStatus.present,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    body: ClockOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await _get_employee(db, current_user)
        if emp.id != body.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == body.employee_id,
            Attendance.date == body.date,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No clock-in record found")

    record.clock_out_time = body.clock_out_time
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/leave", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def mark_leave(
    body: LeaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    existing = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == body.employee_id,
            Attendance.date == body.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Record already exists for this date")

    record = Attendance(
        employee_id=body.employee_id,
        date=body.date,
        status=AttendanceStatus.leave,
        leave_type=body.leave_type,
        notes=body.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=AttendanceList)
async def list_attendance(
    employee_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await _get_employee(db, current_user)
        employee_id = emp.id

    conditions = []
    if employee_id:
        conditions.append(Attendance.employee_id == employee_id)
    if date_from:
        conditions.append(Attendance.date >= date_from)
    if date_to:
        conditions.append(Attendance.date <= date_to)

    query = select(Attendance).where(and_(*conditions)).order_by(Attendance.date.desc())
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    return AttendanceList(
        items=[AttendanceResponse.model_validate(r) for r in records],
        total=total,
    )
