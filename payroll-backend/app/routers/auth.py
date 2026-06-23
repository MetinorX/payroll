import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_email,
    invalidate_all_user_tokens,
    is_jti_used,
    mark_jti_used,
    store_refresh_jti,
    verify_password,
)
from app.services.rate_limiter import rate_limit

logger = logging.getLogger("payroll.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(rate_limit(5, 60)),
):
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    token_data = {"sub": user.email, "role": user.role.value}
    refresh_token, jti = create_refresh_token(token_data)
    await store_refresh_jti(db, jti, user.email)
    logger.info("Login success", extra={"email": user.email, "ip": request.client.host if request.client else None})
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    jti = payload.get("jti")
    if not jti or await is_jti_used(db, jti):
        email = payload.get("sub")
        if email:
            await invalidate_all_user_tokens(db, email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token already used — all sessions invalidated",
        )

    await mark_jti_used(db, jti)

    email = payload.get("sub")
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": user.email, "role": user.role.value}
    new_refresh_token, new_jti = create_refresh_token(token_data)
    await store_refresh_jti(db, new_jti, user.email)
    logger.info("Token refresh", extra={"email": user.email})
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    employee_id = None
    if current_user.role == UserRole.employee:
        emp = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
        emp = emp.scalar_one_or_none()
        employee_id = emp.id if emp else None

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        employee_id=employee_id,
    )
