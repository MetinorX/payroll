from datetime import date as date_type

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
        user_id=emp_user.id,
        employee_code="EMP001",
        first_name="Test",
        last_name="User",
        department="Engineering",
        designation="Developer",
        date_of_joining=date_type(2024, 1, 1),
        basic_salary=50000,
    )
    db_session.add(employee)
    await db_session.flush()

    # Seed deduction rules
    rules = [
        DeductionRule(name="PF", rule_type=RuleType.pf, rate=12.0, max_income=15000, employer_rate=12.0, is_active=True),
        DeductionRule(name="ESI", rule_type=RuleType.esi, rate=0.75, max_income=21000, employer_rate=3.25, is_active=True),
        DeductionRule(name="Professional Tax", rule_type=RuleType.professional_tax, rate=200.0, min_income=10000, is_active=True),
        DeductionRule(name="Income Tax 0-2.5L", rule_type=RuleType.income_tax, rate=0.0, min_income=0, max_income=250000, is_active=True),
        DeductionRule(name="Income Tax 2.5L-5L", rule_type=RuleType.income_tax, rate=5.0, min_income=250000, max_income=500000, is_active=True),
        DeductionRule(name="Income Tax 5L-10L", rule_type=RuleType.income_tax, rate=20.0, min_income=500000, max_income=1000000, is_active=True),
        DeductionRule(name="Income Tax 10L+", rule_type=RuleType.income_tax, rate=30.0, min_income=1000000, is_active=True),
    ]
    for r in rules:
        db_session.add(r)
    await db_session.flush()

    # Seed salary components
    components = [
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.basic, amount=25000, effective_from=date_type(2024, 1, 1)),
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.hra, amount=12500, effective_from=date_type(2024, 1, 1)),
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.conveyance, amount=1600, effective_from=date_type(2024, 1, 1)),
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.medical, amount=1250, effective_from=date_type(2024, 1, 1)),
        SalaryComponent(employee_id=employee.id, component_type=ComponentType.special, amount=9650, effective_from=date_type(2024, 1, 1)),
    ]
    for c in components:
        db_session.add(c)
    await db_session.commit()


async def _admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_run_payroll(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["grossPay"] == 50000.0  # 25000 + 12500 + 1600 + 1250 + 9650
    assert data["netPay"] > 0
    assert data["totalDeductions"] > 0
    assert len(data["lineItems"]) > 0
    assert data["status"] == "draft"


async def test_duplicate_payroll(client: AsyncClient):
    token = await _admin_token(client)
    await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    res = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409


async def test_finalize_payslip(client: AsyncClient):
    token = await _admin_token(client)
    run = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    payslip_id = run.json()["id"]

    res = await client.post(
        f"/payroll/payslips/{payslip_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "finalized"


async def test_list_payslips(client: AsyncClient):
    token = await _admin_token(client)
    await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.get("/payroll/payslips", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1


async def test_employee_own_payslip(client: AsyncClient):
    admin_token = await _admin_token(client)
    run = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    payslip_id = run.json()["id"]

    emp_login = await client.post("/auth/login", json={"email": "emp@test.com", "password": "emp123"})
    emp_token = emp_login.json()["accessToken"]

    res = await client.get(
        f"/payroll/payslips/{payslip_id}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert res.status_code == 200
    assert res.json()["employeeId"] == 1
