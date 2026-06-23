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


async def test_clock_in(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/attendance/clock-in",
        json={"employee_id": 1, "date": "2024-06-01", "clock_in_time": "09:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "present"


async def test_clock_out(client: AsyncClient):
    token = await _admin_token(client)
    await client.post(
        "/attendance/clock-in",
        json={"employee_id": 1, "date": "2024-06-01", "clock_in_time": "09:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    res = await client.post(
        "/attendance/clock-out",
        json={"employee_id": 1, "date": "2024-06-01", "clock_out_time": "18:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["clockOutTime"] == "18:00:00"


async def test_clock_in_duplicate(client: AsyncClient):
    token = await _admin_token(client)
    body = {"employee_id": 1, "date": "2024-06-01", "clock_in_time": "09:00:00"}
    await client.post("/attendance/clock-in", json=body, headers={"Authorization": f"Bearer {token}"})
    res = await client.post(
        "/attendance/clock-in", json=body, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 409


async def test_mark_leave(client: AsyncClient):
    token = await _admin_token(client)
    res = await client.post(
        "/attendance/leave",
        json={
            "employee_id": 1,
            "date": "2024-06-05",
            "leave_type": "sick",
            "notes": "Fever",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "leave"
    assert res.json()["leaveType"] == "sick"


async def test_query_attendance(client: AsyncClient):
    token = await _admin_token(client)
    await client.post(
        "/attendance/clock-in",
        json={"employee_id": 1, "date": "2024-06-01", "clock_in_time": "09:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/attendance/clock-in",
        json={"employee_id": 1, "date": "2024-06-02", "clock_in_time": "09:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.get(
        "/attendance?employee_id=1&date_from=2024-06-01&date_to=2024-06-30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total"] == 2


async def test_employee_self_clock_in(client: AsyncClient):
    emp_login = await client.post("/auth/login", json={"email": "emp@test.com", "password": "emp123"})
    emp_token = emp_login.json()["accessToken"]

    res = await client.post(
        "/attendance/clock-in",
        json={"employee_id": 1, "date": "2024-06-10", "clock_in_time": "09:00:00"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert res.status_code == 201
