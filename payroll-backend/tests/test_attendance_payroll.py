from datetime import date, time

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.deduction_rule import DeductionRule, RuleType
from app.models.employee import Employee
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

    emp_user = User(
        email="emp@test.com",
        hashed_password=hash_password("emp123"),
        role=UserRole.employee,
        is_active=True,
    )
    db_session.add(emp_user)
    await db_session.flush()

    employee = Employee(
        user_id=emp_user.id,
        employee_code="EMP001",
        first_name="Test",
        last_name="User",
        department="Engineering",
        designation="Developer",
        date_of_joining=date(2024, 1, 1),
        basic_salary=50000,
    )
    db_session.add(employee)
    await db_session.flush()

    rules = [
        DeductionRule(name="PF", rule_type=RuleType.pf, rate=12.0, max_income=15000, employer_rate=12.0, is_active=True),
        DeductionRule(name="Professional Tax", rule_type=RuleType.professional_tax, rate=200.0, min_income=10000, is_active=True),
        DeductionRule(name="Income Tax 0-2.5L", rule_type=RuleType.income_tax, rate=0.0, min_income=0, max_income=250000, is_active=True),
        DeductionRule(name="Income Tax 2.5L-5L", rule_type=RuleType.income_tax, rate=5.0, min_income=250000, max_income=500000, is_active=True),
        DeductionRule(name="Income Tax 5L-10L", rule_type=RuleType.income_tax, rate=20.0, min_income=500000, max_income=1000000, is_active=True),
        DeductionRule(name="Income Tax 10L+", rule_type=RuleType.income_tax, rate=30.0, min_income=1000000, is_active=True),
    ]
    for r in rules:
        db_session.add(r)

    components = [
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.basic, amount=50000, effective_from=date(2024, 1, 1)),
    ]
    for c in components:
        db_session.add(c)

    await db_session.commit()


async def _admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_payroll_working_days_computed(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["workingDays"] is not None
    assert data["attendedDays"] is not None
    assert data["workingDays"] >= 20
    assert data["grossPay"] == 50000.0


async def test_payroll_prorated_with_attendance(client: AsyncClient, db_session: AsyncSession):
    attendance = Attendance(
        employee_id=1, date=date(2024, 6, 1),
        clock_in_time=time(9, 0), status=AttendanceStatus.present,
    )
    db_session.add(attendance)
    await db_session.commit()

    token = await _admin_token(client)
    res = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["attendedDays"] == 1
    assert data["workingDays"] >= 20
    prorated = 50000 * (1 / data["workingDays"])
    assert data["grossPay"] == round(prorated, 2)
