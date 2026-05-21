import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth import bearer_scheme, current_user
from backend.database import authenticate_user, create_session, create_user, delete_session
from backend.models import User
from backend.schemas import AuthResponse, UserCreate, UserLogin, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


def auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        token=create_session(user.id),
        user=UserRead(id=user.id, name=user.name, email=user.email),
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate) -> AuthResponse:
    try:
        user = create_user(payload.name, payload.email, payload.password)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email",
        ) from exc
    return auth_response(user)


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: UserLogin) -> AuthResponse:
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return auth_response(user)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(current_user)) -> UserRead:
    return UserRead(id=user.id, name=user.name, email=user.email)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> None:
    if credentials is not None:
        delete_session(credentials.credentials)
