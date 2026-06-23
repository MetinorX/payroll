import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.payslip import Payslip
from app.models.payslip_line_item import PayslipLineItem
from app.models.salary_component import SalaryComponent
from app.models.user import User, UserRole
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    PaginatedEmployees,
)
from app.services.auth import hash_password

logger = logging.getLogger("payroll.employees")
router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=PaginatedEmployees)
async def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: str | None = Query(None),
    designation: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    query = select(Employee).options(joinedload(Employee.user))

    if department:
        query = query.where(Employee.department.ilike(f"%{department}%"))
    if designation:
        query = query.where(Employee.designation.ilike(f"%{designation}%"))
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    if search:
        query = query.where(
            or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.last_name.ilike(f"%{search}%"),
                Employee.employee_code.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    employees = result.unique().scalars().all()

    return PaginatedEmployees(
        items=[_employee_to_response(e) for e in employees],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.employee:
        emp = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
        emp = emp.scalar_one_or_none()
        if not emp or emp.id != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(Employee).options(joinedload(Employee.user)).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.unique().scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return _employee_to_response(employee)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    existing_user = await db.execute(select(User).where(User.email == body.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_code = await db.execute(
        select(Employee).where(Employee.employee_code == body.employee_code)
    )
    if existing_code.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Employee code already exists"
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=UserRole.employee,
    )
    db.add(user)
    await db.flush()

    employee = Employee(
        user_id=user.id,
        employee_code=body.employee_code,
        first_name=body.first_name,
        last_name=body.last_name,
        department=body.department,
        designation=body.designation,
        date_of_joining=body.date_of_joining,
        basic_salary=body.basic_salary,
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    result = await db.execute(
        select(Employee).options(joinedload(Employee.user)).where(Employee.id == employee.id)
    )
    logger.info("Employee created", extra={"employee_id": employee.id, "code": employee.employee_code})
    return _employee_to_response(result.unique().scalar_one())


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    result = await db.execute(
        select(Employee).options(joinedload(Employee.user)).where(Employee.id == employee_id)
    )
    employee = result.unique().scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    logger.info("Employee updated", extra={"employee_id": employee.id})
    return _employee_to_response(employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(
        select(Employee)
        .options(
            joinedload(Employee.user),
            joinedload(Employee.salary_components),
            joinedload(Employee.attendance_records),
            joinedload(Employee.payslips).joinedload(Payslip.line_items),
        )
        .where(Employee.id == employee_id)
    )
    employee = result.unique().scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    await db.delete(employee)
    await db.commit()
    logger.info("Employee deleted", extra={"employee_id": employee_id})


def _employee_to_response(emp: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=emp.id,
        user_id=emp.user_id,
        employee_code=emp.employee_code,
        first_name=emp.first_name,
        last_name=emp.last_name,
        department=emp.department,
        designation=emp.designation,
        date_of_joining=emp.date_of_joining,
        basic_salary=emp.basic_salary,
        is_active=emp.is_active,
        email=emp.user.email,
        role=emp.user.role.value,
    )
