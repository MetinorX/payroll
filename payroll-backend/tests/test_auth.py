import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.auth import hash_password


@pytest_asyncio.fixture(autouse=True)
async def seed_users(db_session: AsyncSession):
    users = [
        User(
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
            is_active=True,
        ),
        User(
            email="hr@example.com",
            hashed_password=hash_password("hr123"),
            role=UserRole.hr,
            is_active=True,
        ),
        User(
            email="emp@example.com",
            hashed_password=hash_password("emp123"),
            role=UserRole.employee,
            is_active=True,
        ),
    ]
    for u in users:
        db_session.add(u)
    await db_session.commit()


async def test_login_success(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert res.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": "nonexist@test.com", "password": "test"})
    assert res.status_code == 401


async def test_refresh_token(client: AsyncClient):
    login_res = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    refresh_token = login_res.json()["refreshToken"]

    res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert "accessToken" in data
    assert "refreshToken" in data


async def test_me_endpoint(client: AsyncClient):
    login_res = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    access_token = login_res.json()["accessToken"]

    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"


async def test_me_unauthorized(client: AsyncClient):
    res = await client.get("/auth/me")
    assert res.status_code == 403


async def test_me_invalid_token(client: AsyncClient):
    res = await client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert res.status_code == 401


async def test_role_based_access(client: AsyncClient):
    login_res = await client.post("/auth/login", json={"email": "emp@example.com", "password": "emp123"})
    emp_token = login_res.json()["accessToken"]

    login_res = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    admin_token = login_res.json()["accessToken"]

    res_emp = await client.get("/auth/me", headers={"Authorization": f"Bearer {emp_token}"})
    assert res_emp.json()["role"] == "employee"

    res_admin = await client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.json()["role"] == "admin"
