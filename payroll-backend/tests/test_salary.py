import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.user import User, UserRole
from datetime import date as date_type

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
    await db_session.commit()


async def _admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_set_salary_component(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/salary-config/1",
        json={
            "component_type": "basic",
            "amount": 25000,
            "effective_from": "2024-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["componentType"] == "basic"


async def test_get_salary_config(client: AsyncClient):
    token = await _admin_token(client)
    await client.post(
        "/salary-config/1",
        json={
            "component_type": "basic",
            "amount": 25000,
            "effective_from": "2024-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/salary-config/1",
        json={
            "component_type": "hra",
            "amount": 12500,
            "effective_from": "2024-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.get("/salary-config/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["components"]) == 2
    assert data["totalMonthly"] == 37500
