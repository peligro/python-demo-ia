from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session
from database.database import get_session
from services.user.user_service import UserService
from schemas.user import (
    UserCreate, UserUpdate, UserPublic, UserRead,
    UserListResponseWithMetadata, UserPublicWithMetadata
)
from middleware.rbac import require_module, require_item, require_any_special_code
from common.constants import SETTINGS_USERS, VIEW_ALL_REGISTER
from typing import Optional

router = APIRouter(prefix="/users", tags=["User"])

def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)

@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_item(SETTINGS_USERS, "create_user"))]
)
async def create_user(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create(user_in)

@router.get(
    "",
    response_model=UserListResponseWithMetadata,
    dependencies=[Depends(require_any_special_code(VIEW_ALL_REGISTER))]  # Solo admin total
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None, min_length=2),
    email: Optional[str] = Query(None),
    state_id: Optional[int] = Query(None, ge=1),
    profile_id: Optional[int] = Query(None, ge=1),
    service: UserService = Depends(get_user_service)
):
    return service.get_paginated_with_metadata(page, limit, name, email, state_id, profile_id)

@router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_item(SETTINGS_USERS, "view_user"))]
)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get_by_id(user_id)

@router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_item(SETTINGS_USERS, "edit_user"))]
)
async def update_user(user_id: int, user_in: UserUpdate, service: UserService = Depends(get_user_service)):
    return service.update(user_id, user_in)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_item(SETTINGS_USERS, "delete_user"))]
)
async def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    service.delete(user_id)
    return None