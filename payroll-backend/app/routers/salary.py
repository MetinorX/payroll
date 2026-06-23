import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.employee import Employee
from app.models.salary_component import SalaryComponent
from app.models.user import User, UserRole
from app.schemas.salary import (
    SalaryBulkCreate,
    SalaryComponentCreate,
    SalaryComponentResponse,
    SalaryConfigResponse,
)

logger = logging.getLogger("payroll.salary")
router = APIRouter(prefix="/salary-config", tags=["Salary Configuration"])


@router.get("/{employee_id}", response_model=SalaryConfigResponse)
async def get_salary_config(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    result = await db.execute(
        select(SalaryComponent).where(
            SalaryComponent.employee_id == employee_id,
            SalaryComponent.effective_to.is_(None),
        )
    )
    components = result.scalars().all()

    total = sum(c.amount for c in components)
    return SalaryConfigResponse(
        employee_id=employee_id,
        components=[SalaryComponentResponse.model_validate(c) for c in components],
        total_monthly=total,
    )


@router.post("/{employee_id}", response_model=SalaryComponentResponse, status_code=status.HTTP_201_CREATED)
async def set_salary_component(
    employee_id: int,
    body: SalaryComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    component = SalaryComponent(
        employee_id=employee_id,
        component_type=body.component_type,
        amount=body.amount,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
    )
    db.add(component)
    await db.commit()
    await db.refresh(component)
    logger.info("Salary component created", extra={"employee_id": employee_id, "type": body.component_type.value})
    return SalaryComponentResponse.model_validate(component)


@router.post("/{employee_id}/bulk", response_model=SalaryConfigResponse, status_code=status.HTTP_201_CREATED)
async def set_salary_components_bulk(
    employee_id: int,
    body: SalaryBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.hr)),
):
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    created = []
    for comp in body.components:
        component = SalaryComponent(
            employee_id=employee_id,
            component_type=comp.component_type,
            amount=comp.amount,
            effective_from=comp.effective_from,
            effective_to=comp.effective_to,
        )
        db.add(component)
        created.append(component)

    await db.commit()
    for c in created:
        await db.refresh(c)

    result = await db.execute(
        select(SalaryComponent).where(
            SalaryComponent.employee_id == employee_id,
            SalaryComponent.effective_to.is_(None),
        )
    )
    all_components = result.scalars().all()
    total = sum(c.amount for c in all_components)

    logger.info("Salary components created in bulk", extra={"employee_id": employee_id, "count": len(created)})
    return SalaryConfigResponse(
        employee_id=employee_id,
        components=[SalaryComponentResponse.model_validate(c) for c in all_components],
        total_monthly=total,
    )
