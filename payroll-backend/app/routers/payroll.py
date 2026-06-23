import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.employee import Employee
from app.models.payslip import Payslip, PayslipStatus
from app.models.payslip_line_item import PayslipLineItem, LineType
from app.models.user import User, UserRole
from app.schemas.payroll import (
    PayslipDetailResponse,
    PayslipLineItemResponse,
    PayslipListResponse,
    PayslipResponse,
    PayrollRunResult,
    RunPayrollAllRequest,
    RunPayrollRequest,
)
from app.services.pdf_generator import generate_payslip_pdf
from app.services.tax_calculator import compute_payroll

logger = logging.getLogger("payroll.payroll")
router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.post("/run", response_model=PayslipDetailResponse, status_code=status.HTTP_201_CREATED)
async def run_payroll(
    body: RunPayrollRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    emp = await db.get(Employee, body.employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    existing = await db.execute(
        select(Payslip).where(
            Payslip.employee_id == body.employee_id,
            Payslip.month == body.month,
            Payslip.year == body.year,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payslip already exists for this period",
        )

    result = await compute_payroll(db, body.employee_id, body.month, body.year)

    payslip = Payslip(
        employee_id=body.employee_id,
        month=body.month,
        year=body.year,
        gross_pay=result.gross_pay,
        total_deductions=result.deductions.total_employee_deductions,
        net_pay=result.net_pay,
        working_days=result.working_days,
        attended_days=result.attended_days,
        status=PayslipStatus.draft,
    )
    db.add(payslip)
    await db.flush()

    earnings = [
        ("Basic", result.basic),
        ("HRA", result.hra),
        ("DA", result.da),
        ("Conveyance", result.conveyance),
        ("Medical", result.medical),
        ("Special", result.special),
        ("Bonus", result.bonus),
    ]
    for desc, amount in earnings:
        if amount > 0:
            db.add(
                PayslipLineItem(
                    payslip_id=payslip.id,
                    description=desc,
                    amount=amount,
                    line_type=LineType.earning,
                )
            )

    deductions = [
        ("PF (Employee)", result.deductions.pf_employee),
        ("ESI (Employee)", result.deductions.esi_employee),
        ("Professional Tax", result.deductions.professional_tax),
        ("Income Tax", result.deductions.income_tax),
    ]
    for desc, amount in deductions:
        if amount > 0:
            db.add(
                PayslipLineItem(
                    payslip_id=payslip.id,
                    description=desc,
                    amount=amount,
                    line_type=LineType.deduction,
                )
            )

    employee_name = f"{emp.first_name} {emp.last_name}"
    pdf_path = generate_payslip_pdf(
        employee_name=employee_name,
        employee_code=emp.employee_code,
        department=emp.department,
        designation=emp.designation,
        month=body.month,
        year=body.year,
        result=result,
    )
    payslip.pdf_path = pdf_path

    await db.commit()
    await db.refresh(payslip)
    logger.info("Payslip generated", extra={"employee_id": body.employee_id, "month": body.month, "year": body.year})
    return await _get_payslip_detail(db, payslip.id)


@router.post("/run-all", response_model=list[PayrollRunResult], status_code=status.HTTP_201_CREATED)
async def run_payroll_all(
    body: RunPayrollAllRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    employees = await db.execute(select(Employee).where(Employee.is_active.is_(True)))
    employees = employees.scalars().all()

    results = []
    for emp in employees:
        existing = await db.execute(
            select(Payslip).where(
                Payslip.employee_id == emp.id,
                Payslip.month == body.month,
                Payslip.year == body.year,
            )
        )
        if existing.scalar_one_or_none():
            results.append(PayrollRunResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                employee_code=emp.employee_code,
                gross_pay=0,
                net_pay=0,
                status="skipped",
                message="Payslip already exists for this period",
            ))
            continue

        try:
            result = await compute_payroll(db, emp.id, body.month, body.year)

            payslip = Payslip(
                employee_id=emp.id,
                month=body.month,
                year=body.year,
                gross_pay=result.gross_pay,
                total_deductions=result.deductions.total_employee_deductions,
                net_pay=result.net_pay,
                working_days=result.working_days,
                attended_days=result.attended_days,
                status=PayslipStatus.draft,
            )
            db.add(payslip)
            await db.flush()

            earnings = [
                ("Basic", result.basic), ("HRA", result.hra), ("DA", result.da),
                ("Conveyance", result.conveyance), ("Medical", result.medical),
                ("Special", result.special), ("Bonus", result.bonus),
            ]
            for desc, amount in earnings:
                if amount > 0:
                    db.add(PayslipLineItem(
                        payslip_id=payslip.id, description=desc,
                        amount=amount, line_type=LineType.earning,
                    ))

            deduction_items = [
                ("PF (Employee)", result.deductions.pf_employee),
                ("ESI (Employee)", result.deductions.esi_employee),
                ("Professional Tax", result.deductions.professional_tax),
                ("Income Tax", result.deductions.income_tax),
            ]
            for desc, amount in deduction_items:
                if amount > 0:
                    db.add(PayslipLineItem(
                        payslip_id=payslip.id, description=desc,
                        amount=amount, line_type=LineType.deduction,
                    ))

            pdf_path = generate_payslip_pdf(
                employee_name=f"{emp.first_name} {emp.last_name}",
                employee_code=emp.employee_code,
                department=emp.department,
                designation=emp.designation,
                month=body.month,
                year=body.year,
                result=result,
            )
            payslip.pdf_path = pdf_path

            results.append(PayrollRunResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                employee_code=emp.employee_code,
                gross_pay=result.gross_pay,
                net_pay=result.net_pay,
                status="created",
                message="Payslip generated successfully",
            ))
        except Exception as e:
            await db.rollback()
            results.append(PayrollRunResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                employee_code=emp.employee_code,
                gross_pay=0,
                net_pay=0,
                status="error",
                message=str(e),
            ))

    await db.commit()
    logger.info("Bulk payroll run complete", extra={"month": body.month, "year": body.year, "total": len(results)})
    return results


@router.post("/payslips/{payslip_id}/finalize", response_model=PayslipResponse)
async def finalize_payslip(
    payslip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    payslip = await db.get(Payslip, payslip_id)
    if not payslip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")

    if payslip.status == PayslipStatus.finalized:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payslip is already finalized")

    payslip.status = PayslipStatus.finalized
    await db.commit()
    await db.refresh(payslip)
    logger.info("Payslip finalized", extra={"payslip_id": payslip_id})
    return payslip


@router.get("/payslips", response_model=PayslipListResponse)
async def list_payslips(
    employee_id: int | None = Query(None),
    month: int | None = Query(None),
    year: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
        emp = emp.scalar_one_or_none()
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
        employee_id = emp.id

    conditions = []
    if employee_id:
        conditions.append(Payslip.employee_id == employee_id)
    if month:
        conditions.append(Payslip.month == month)
    if year:
        conditions.append(Payslip.year == year)

    query = select(Payslip).where(and_(true(), *conditions)).order_by(Payslip.year.desc(), Payslip.month.desc())
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    payslips = result.scalars().all()

    return PayslipListResponse(
        items=[PayslipResponse.model_validate(p) for p in payslips],
        total=total,
    )


@router.get("/payslips/{payslip_id}", response_model=PayslipDetailResponse)
async def get_payslip(
    payslip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
        emp = emp.scalar_one_or_none()
        if emp:
            payslip = await db.get(Payslip, payslip_id)
            if payslip and payslip.employee_id != emp.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await _get_payslip_detail(db, payslip_id)


@router.get("/download/{payslip_id}")
async def download_payslip(
    payslip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
        emp = emp.scalar_one_or_none()
        if emp:
            payslip = await db.get(Payslip, payslip_id)
            if payslip and payslip.employee_id != emp.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    payslip = await db.get(Payslip, payslip_id)
    if not payslip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")
    if not payslip.pdf_path or not os.path.exists(payslip.pdf_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not generated yet")

    return FileResponse(
        payslip.pdf_path,
        media_type="application/pdf",
        filename=f"payslip_{payslip_id}.pdf",
    )


async def _get_payslip_detail(db: AsyncSession, payslip_id: int) -> PayslipDetailResponse:
    result = await db.execute(
        select(Payslip).options(joinedload(Payslip.line_items)).where(Payslip.id == payslip_id)
    )
    payslip = result.unique().scalar_one_or_none()
    if not payslip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")

    return PayslipDetailResponse(
        id=payslip.id,
        employee_id=payslip.employee_id,
        month=payslip.month,
        year=payslip.year,
        gross_pay=payslip.gross_pay,
        total_deductions=payslip.total_deductions,
        net_pay=payslip.net_pay,
        working_days=payslip.working_days,
        attended_days=payslip.attended_days,
        status=payslip.status.value,
        pdf_path=payslip.pdf_path,
        created_at=payslip.created_at,
        line_items=[
            PayslipLineItemResponse(
                id=li.id,
                payslip_id=li.payslip_id,
                description=li.description,
                amount=li.amount,
                line_type=li.line_type.value,
            )
            for li in payslip.line_items
        ],
    )
