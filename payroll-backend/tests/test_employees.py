import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.auth import hash_password


@pytest_asyncio.fixture(autouse=True)
async def seed_admin(db_session: AsyncSession):
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()


async def _login(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["accessToken"]


async def test_create_employee(client: AsyncClient):
    token = await _login(client)
    res = await client.post(
        "/employees",
        json={
            "email": "emp@test.com",
            "password": "emp123",
            "employee_code": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Engineering",
            "designation": "Developer",
            "date_of_joining": "2024-01-15",
            "basic_salary": 50000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "emp@test.com"
    assert data["employeeCode"] == "EMP001"
    assert data["department"] == "Engineering"


async def test_create_duplicate_email(client: AsyncClient):
    token = await _login(client)
    body = {
        "email": "dup@test.com",
        "password": "emp123",
        "employee_code": "EMP002",
        "first_name": "Jane",
        "last_name": "Doe",
        "department": "HR",
        "designation": "Manager",
        "date_of_joining": "2024-01-15",
        "basic_salary": 60000,
    }
    res1 = await client.post("/employees", json=body, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 201

    res2 = await client.post("/employees", json=body, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 409


async def test_list_employees(client: AsyncClient):
    token = await _login(client)

    # Create 2 employees
    for i in range(2):
        await client.post(
            "/employees",
            json={
                "email": f"emp{i}@test.com",
                "password": "emp123",
                "employee_code": f"EMP00{i}",
                "first_name": f"First{i}",
                "last_name": f"Last{i}",
                "department": "Engineering",
                "designation": "Developer",
                "date_of_joining": "2024-01-15",
                "basic_salary": 50000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    res = await client.get("/employees", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


async def test_get_employee(client: AsyncClient):
    token = await _login(client)
    create_res = await client.post(
        "/employees",
        json={
            "email": "get@test.com",
            "password": "emp123",
            "employee_code": "EMP010",
            "first_name": "Get",
            "last_name": "Test",
            "department": "Sales",
            "designation": "Executive",
            "date_of_joining": "2024-01-15",
            "basic_salary": 40000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    emp_id = create_res.json()["id"]

    res = await client.get(f"/employees/{emp_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["firstName"] == "Get"


async def test_update_employee(client: AsyncClient):
    token = await _login(client)
    create_res = await client.post(
        "/employees",
        json={
            "email": "update@test.com",
            "password": "emp123",
            "employee_code": "EMP020",
            "first_name": "Old",
            "last_name": "Name",
            "department": "IT",
            "designation": "Junior",
            "date_of_joining": "2024-01-15",
            "basic_salary": 30000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    emp_id = create_res.json()["id"]

    res = await client.put(
        f"/employees/{emp_id}",
        json={"first_name": "New", "basic_salary": 45000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["firstName"] == "New"
    assert res.json()["basicSalary"] == 45000


async def test_delete_employee(client: AsyncClient):
    token = await _login(client)
    create_res = await client.post(
        "/employees",
        json={
            "email": "delete@test.com",
            "password": "emp123",
            "employee_code": "EMP030",
            "first_name": "Delete",
            "last_name": "Me",
            "department": "Ops",
            "designation": "Coordinator",
            "date_of_joining": "2024-01-15",
            "basic_salary": 35000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    emp_id = create_res.json()["id"]

    res = await client.delete(f"/employees/{emp_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 204

    res = await client.get(f"/employees/{emp_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404


async def test_employee_self_access(client: AsyncClient):
    admin_token = await _login(client)

    # Create employee
    create_res = await client.post(
        "/employees",
        json={
            "email": "self@test.com",
            "password": "self123",
            "employee_code": "EMP040",
            "first_name": "Self",
            "last_name": "Access",
            "department": "Engineering",
            "designation": "Dev",
            "date_of_joining": "2024-01-15",
            "basic_salary": 50000,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    emp_id = create_res.json()["id"]

    # Login as employee
    emp_login = await client.post("/auth/login", json={"email": "self@test.com", "password": "self123"})
    emp_token = emp_login.json()["accessToken"]

    # Employee can access own record
    res = await client.get(f"/employees/{emp_id}", headers={"Authorization": f"Bearer {emp_token}"})
    assert res.status_code == 200

    # Employee cannot list all employees
    res = await client.get("/employees", headers={"Authorization": f"Bearer {emp_token}"})
    assert res.status_code == 403
