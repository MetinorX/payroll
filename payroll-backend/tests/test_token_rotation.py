import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.auth import hash_password


@pytest_asyncio.fixture(autouse=True)
async def seed_users(db_session: AsyncSession):
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()


async def test_refresh_token_rotation(client: AsyncClient):
    login = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    assert login.status_code == 200
    refresh_token = login.json()["refreshToken"]

    first = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert first.status_code == 200

    second = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert second.status_code == 401


async def test_refresh_all_invalidated_on_reuse(client: AsyncClient):
    login = await client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    refresh_token1 = login.json()["refreshToken"]

    r1 = await client.post("/auth/refresh", json={"refresh_token": refresh_token1})
    assert r1.status_code == 200
    refresh_token2 = r1.json()["refreshToken"]

    r2 = await client.post("/auth/refresh", json={"refresh_token": refresh_token1})
    assert r2.status_code == 401

    r3 = await client.post("/auth/refresh", json={"refresh_token": refresh_token2})
    assert r3.status_code == 401


async def test_invalid_refresh_token(client: AsyncClient):
    res = await client.post("/auth/refresh", json={"refresh_token": "definitely-invalid"})
    assert res.status_code == 401
