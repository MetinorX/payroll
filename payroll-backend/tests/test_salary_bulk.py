from datetime import date

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
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
    await db_session.commit()


async def _admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_bulk_salary_components(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/salary-config/1/bulk",
        json={
            "components": [
                {"component_type": "basic", "amount": 30000, "effective_from": "2024-06-01"},
                {"component_type": "hra", "amount": 15000, "effective_from": "2024-06-01"},
                {"component_type": "conveyance", "amount": 1600, "effective_from": "2024-06-01"},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["totalMonthly"] == 46600.0
    assert len(data["components"]) == 3


async def test_bulk_employee_not_found(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/salary-config/999/bulk",
        json={"components": [{"component_type": "basic", "amount": 30000, "effective_from": "2024-06-01"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
