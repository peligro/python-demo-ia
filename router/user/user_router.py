from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session
from database.database import get_session
from services.user.user_service import UserService
from schemas.user import (
    UserCreate, UserUpdate, UserPublic, UserRead,
    UserListResponseWithMetadata, UserPublicWithMetadata
)
from typing import Optional

router = APIRouter(prefix="/users", tags=["User"])


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return service.create(user_in)


@router.get("", response_model=UserListResponseWithMetadata)
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Registros por página (máx 100)"),
    name: Optional[str] = Query(None, min_length=2, description="Búsqueda parcial por nombre"),
    email: Optional[str] = Query(None, description="Búsqueda por correo"),
    state_id: Optional[int] = Query(None, ge=1, description="Filtrar por estado (user_metadata)"),
    profile_id: Optional[int] = Query(None, ge=1, description="Filtrar por perfil (user_metadata)"),
    service: UserService = Depends(get_user_service)
):
    return service.get_paginated_with_metadata(page, limit, name, email, state_id, profile_id)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return service.get_by_id(user_id)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    return service.update(user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    service.delete(user_id)
    return None