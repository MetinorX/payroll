import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.employee import Employee
from app.models.payslip import Payslip, PayslipStatus
from app.models.user import User, UserRole
from app.schemas.base import CamelModel

logger = logging.getLogger("payroll.dashboard")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStats(CamelModel):
    total_employees: int
    active_employees: int
    total_payslips_this_month: int
    finalized_payslips_this_month: int
    monthly_gross_pay: float
    monthly_net_pay: float
    monthly_total_deductions: float


class ChartDataPoint(CamelModel):
    month: int
    year: int
    total_gross: float
    total_net: float
    total_deductions: float


class PayrollChartResponse(CamelModel):
    data: list[ChartDataPoint]


async def _get_employee_id(db: AsyncSession, user: User) -> int | None:
    if user.role != UserRole.employee:
        return None
    result = await db.execute(select(Employee.id).where(Employee.user_id == user.id))
    return result.scalar_one_or_none()


async def _payslip_conditions(month: int, year: int, employee_id: int | None) -> list:
    conditions = [Payslip.month == month, Payslip.year == year]
    if employee_id is not None:
        conditions.append(Payslip.employee_id == employee_id)
    return conditions


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    month: int = Query(...),
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_emp = 0
    active_emp = 0
    if current_user.role != UserRole.employee:
        total_emp = (await db.execute(select(func.count(Employee.id)))).scalar() or 0
        active_emp = (await db.execute(
            select(func.count(Employee.id)).where(Employee.is_active.is_(True))
        )).scalar() or 0

    emp_id = await _get_employee_id(db, current_user)
    conditions = await _payslip_conditions(month, year, emp_id)

    monthly_counts = await db.execute(
        select(
            func.count(Payslip.id),
            func.count(Payslip.id).filter(Payslip.status == PayslipStatus.finalized),
            func.coalesce(func.sum(Payslip.gross_pay), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
            func.coalesce(func.sum(Payslip.total_deductions), 0),
        ).where(and_(*conditions))
    )
    row = monthly_counts.one()

    return DashboardStats(
        total_employees=total_emp,
        active_employees=active_emp,
        total_payslips_this_month=row[0],
        finalized_payslips_this_month=row[1],
        monthly_gross_pay=round(float(row[2]), 2),
        monthly_net_pay=round(float(row[3]), 2),
        monthly_total_deductions=round(float(row[4]), 2),
    )


@router.get("/payroll-chart", response_model=PayrollChartResponse)
async def payroll_chart(
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conditions = [Payslip.year == year]
    emp_id = await _get_employee_id(db, current_user)
    if emp_id is not None:
        conditions.append(Payslip.employee_id == emp_id)

    result = await db.execute(
        select(
            Payslip.month,
            Payslip.year,
            func.coalesce(func.sum(Payslip.gross_pay), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
            func.coalesce(func.sum(Payslip.total_deductions), 0),
        )
        .where(and_(*conditions))
        .group_by(Payslip.year, Payslip.month)
        .order_by(Payslip.month)
    )
    rows = result.all()

    return PayrollChartResponse(data=[
        ChartDataPoint(
            month=row[0],
            year=row[1],
            total_gross=round(float(row[2]), 2),
            total_net=round(float(row[3]), 2),
            total_deductions=round(float(row[4]), 2),
        )
        for row in rows
    ])
