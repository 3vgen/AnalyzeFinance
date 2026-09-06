"""Роутер аутентификации и профиля (см. [[Пользователи и доступ]])."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.core.security import create_access_token
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.user import Token, UserCreate, UserLogin, UserRead
from testfinance.services.users import authenticate_user, create_user

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=Token, status_code=201)
async def register(
    payload: UserCreate, session: AsyncSession = Depends(get_session)
) -> Token:
    user = await create_user(session, payload)
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/auth/login", response_model=Token)
async def login(
    payload: UserLogin, session: AsyncSession = Depends(get_session)
) -> Token:
    user = await authenticate_user(session, payload.email, payload.password)
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/users/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
