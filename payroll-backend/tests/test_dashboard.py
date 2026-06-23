from datetime import date

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deduction_rule import DeductionRule, RuleType
from app.models.employee import Employee
from app.models.payslip import Payslip, PayslipStatus
from app.models.salary_component import ComponentType, SalaryComponent
from app.models.user import User, UserRole
from app.services.auth import hash_password


@pytest_asyncio.fixture(autouse=True)
async def seed_data(db_session: AsyncSession):
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    emp_user = User(
        email="emp@test.com",
        hashed_password=hash_password("emp123"),
        role=UserRole.employee,
        is_active=True,
    )
    db_session.add(emp_user)
    await db_session.flush()

    employee = Employee(
        user_id=emp_user.id, employee_code="EMP001",
        first_name="Test", last_name="User",
        department="Engineering", designation="Developer",
        date_of_joining=date(2024, 1, 1), basic_salary=50000,
    )
    db_session.add(employee)
    await db_session.flush()

    for r in [
        DeductionRule(name="PF", rule_type=RuleType.pf, rate=12.0, max_income=15000, employer_rate=12.0, is_active=True),
        DeductionRule(name="Professional Tax", rule_type=RuleType.professional_tax, rate=200.0, min_income=10000, is_active=True),
    ]:
        db_session.add(r)

    for c in [
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.basic, amount=50000, effective_from=date(2024, 1, 1)),
    ]:
        db_session.add(c)

    payslip = Payslip(
        employee_id=employee.id, month=6, year=2024,
        gross_pay=50000, total_deductions=5000, net_pay=45000,
        status=PayslipStatus.finalized,
    )
    db_session.add(payslip)
    await db_session.commit()


async def _admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_dashboard_stats(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.get(
        "/dashboard/stats?month=6&year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["totalEmployees"] == 1
    assert data["activeEmployees"] == 1
    assert data["totalPayslipsThisMonth"] == 1
    assert data["finalizedPayslipsThisMonth"] == 1
    assert data["monthlyGrossPay"] == 50000.0


async def test_dashboard_payroll_chart(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.get(
        "/dashboard/payroll-chart?year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["month"] == 6
    assert data["data"][0]["totalGross"] == 50000.0


async def test_employee_cannot_access_dashboard(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": "emp@test.com", "password": "emp123"})
    token = res.json()["accessToken"]
    res = await client.get(
        "/dashboard/stats?month=6&year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
