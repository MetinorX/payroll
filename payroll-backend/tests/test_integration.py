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
async def seed_full_data(db_session: AsyncSession):
    admin = User(email="admin@test.com", hashed_password=hash_password("admin123"), role=UserRole.admin)
    db_session.add(admin)
    await db_session.flush()

    emp_user = User(email="emp@test.com", hashed_password=hash_password("emp123"), role=UserRole.employee)
    db_session.add(emp_user)
    await db_session.flush()

    employee = Employee(
        user_id=emp_user.id, employee_code="EMP001", first_name="Integration", last_name="Test",
        department="QA", designation="Tester", date_of_joining=date_type(2024, 1, 1), basic_salary=50000,
    )
    db_session.add(employee)
    await db_session.flush()

    rules = [
        DeductionRule(name="PF", rule_type=RuleType.pf, rate=12.0, max_income=15000, employer_rate=12.0),
        DeductionRule(name="ESI", rule_type=RuleType.esi, rate=0.75, max_income=21000, employer_rate=3.25),
        DeductionRule(name="PT", rule_type=RuleType.professional_tax, rate=200.0, min_income=10000),
        DeductionRule(name="IT 0-2.5L", rule_type=RuleType.income_tax, rate=0.0, min_income=0, max_income=250000),
        DeductionRule(name="IT 2.5-5L", rule_type=RuleType.income_tax, rate=5.0, min_income=250000, max_income=500000),
        DeductionRule(name="IT 5-10L", rule_type=RuleType.income_tax, rate=20.0, min_income=500000, max_income=1000000),
        DeductionRule(name="IT 10L+", rule_type=RuleType.income_tax, rate=30.0, min_income=1000000),
    ]
    for r in rules:
        db_session.add(r)
    await db_session.flush()

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


async def test_full_integration_flow(client: AsyncClient):
    token = await _admin_token(client)

    # 1. List employees
    res = await client.get("/employees", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    # 2. Get salary config
    res = await client.get("/salary-config/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["totalMonthly"] == 50000

    # 3. Query attendance (no records exist yet)
    res = await client.get(
        "/attendance?employee_id=1&date_from=2024-06-01&date_to=2024-06-30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    # 5. Run payroll
    res = await client.post(
        "/payroll/run",
        json={"employee_id": 1, "month": 6, "year": 2024},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    payslip = res.json()
    assert payslip["grossPay"] == 50000
    assert payslip["netPay"] > 0
    assert len(payslip["lineItems"]) >= 4

    # 6. Finalize payslip
    payslip_id = payslip["id"]
    res = await client.post(
        f"/payroll/payslips/{payslip_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "finalized"

    # 7. Monthly report
    res = await client.get(
        "/reports/monthly?month=6&year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total_employees"] >= 1

    # 8. Department report
    res = await client.get(
        "/reports/department?month=6&year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 9. YTD report
    res = await client.get(
        "/reports/ytd?year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total_net_pay"] > 0

    # 10. CSV export
    res = await client.get(
        "/reports/export?month=6&year=2024",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]

    # 11. Employee self-access
    emp_login = await client.post("/auth/login", json={"email": "emp@test.com", "password": "emp123"})
    emp_token = emp_login.json()["accessToken"]

    res = await client.get("/payroll/payslips", headers={"Authorization": f"Bearer {emp_token}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1


async def test_reports_without_auth(client: AsyncClient):
    res = await client.get("/reports/monthly?month=6&year=2024")
    assert res.status_code == 403
