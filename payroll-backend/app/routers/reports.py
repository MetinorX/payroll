import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import require_role
from app.models.employee import Employee
from app.models.payslip import Payslip, PayslipStatus
from app.models.user import User, UserRole

logger = logging.getLogger("payroll.reports")
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly")
async def monthly_report(
    month: int = Query(...),
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    base_conditions = [Payslip.month == month, Payslip.year == year,
                       Payslip.status.in_([PayslipStatus.finalized])]
    result = await db.execute(
        select(
            func.count(Payslip.id),
            func.coalesce(func.sum(Payslip.gross_pay), 0),
            func.coalesce(func.sum(Payslip.total_deductions), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
            func.count(Payslip.id).filter(Payslip.status == "finalized"),
        ).where(and_(*base_conditions))
    )
    row = result.one()
    return {
        "month": month,
        "year": year,
        "total_employees": row[0],
        "total_gross_pay": round(float(row[1]), 2),
        "total_deductions": round(float(row[2]), 2),
        "total_net_pay": round(float(row[3]), 2),
        "finalized_count": row[4],
    }


@router.get("/department")
async def department_report(
    month: int = Query(...),
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    result = await db.execute(
        select(
            Employee.department,
            func.count(Payslip.id),
            func.coalesce(func.sum(Payslip.gross_pay), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
        )
        .join(Payslip, Employee.id == Payslip.employee_id)
        .where(and_(
            Payslip.month == month,
            Payslip.year == year,
            Payslip.status.in_([PayslipStatus.finalized]),
        ))
        .group_by(Employee.department)
    )
    rows = result.all()
    return [
        {
            "department": row[0],
            "employee_count": row[1],
            "total_gross": round(float(row[2]), 2),
            "total_net": round(float(row[3]), 2),
        }
        for row in rows
    ]


@router.get("/ytd")
async def ytd_report(
    employee_id: int | None = Query(None),
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    conditions = [Payslip.year == year, Payslip.status.in_([PayslipStatus.finalized])]
    if employee_id:
        conditions.append(Payslip.employee_id == employee_id)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Payslip.gross_pay), 0),
            func.coalesce(func.sum(Payslip.total_deductions), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
            func.count(Payslip.id),
        ).where(and_(*conditions))
    )
    row = result.one()
    return {
        "year": year,
        "employee_id": employee_id,
        "total_gross_pay": round(float(row[0]), 2),
        "total_deductions": round(float(row[1]), 2),
        "total_net_pay": round(float(row[2]), 2),
        "payslip_count": row[3],
    }


@router.get("/export")
async def export_report(
    month: int = Query(...),
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    result = await db.execute(
        select(Payslip)
        .options(joinedload(Payslip.employee).joinedload(Employee.user))
        .where(and_(
            Payslip.month == month,
            Payslip.year == year,
            Payslip.status.in_([PayslipStatus.finalized]),
        ))
    )
    payslips = result.unique().scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee Code", "Name", "Department", "Designation",
        "Month", "Year", "Gross Pay", "Deductions", "Net Pay", "Status",
    ])

    for p in payslips:
        emp = p.employee
        name = f"{emp.first_name} {emp.last_name}"
        writer.writerow([
            emp.employee_code, name, emp.department, emp.designation,
            p.month, p.year, p.gross_pay, p.total_deductions, p.net_pay, p.status.value,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=payroll_{month}_{year}.csv"},
    )
