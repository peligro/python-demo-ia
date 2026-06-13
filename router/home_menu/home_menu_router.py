#router/home_menu/home_menu_router.py
from fastapi import APIRouter, Depends, status, Query, Path
from sqlmodel import Session
from database.database import get_session
from services.home_menu.home_menu_service import HomeMenuService
from schemas.home_menu import HomeMenuCreate, HomeMenuUpdate, HomeMenuPublic, HomeMenuRead, HomeMenuListResponse
from middleware.auth import get_current_user
from typing import Optional

router = APIRouter(prefix="/home-menu", tags=["Home Menu"])

def get_home_menu_service(session: Session = Depends(get_session)) -> HomeMenuService:
    return HomeMenuService(session)

def get_profile_id(current_user: dict = Depends(get_current_user)) -> int:
    """Extraer profile_id del usuario autenticado"""
    metadata = current_user.get("metadata")
    if not metadata or not metadata.profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"estado": "error", "mensaje": "Perfil no asignado"}
        )
    return metadata.profile_id

@router.post("", response_model=HomeMenuRead, status_code=status.HTTP_201_CREATED)
async def create_home_menu(
    menu_in: HomeMenuCreate,
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    return service.create(menu_in, profile_id)

@router.get("/all", response_model=list[HomeMenuPublic])
async def list_all_home_menus(
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    """Listar todos los home_menus permitidos (sin paginación)"""
    return service.get_all_flat(profile_id)

@router.get("", response_model=HomeMenuListResponse)
async def list_home_menus(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    """Listar con paginación, filtrado por permisos"""
    return service.get_paginated(page, limit, profile_id)

@router.get("/{menu_id}", response_model=HomeMenuRead)
async def get_home_menu(
    menu_id: int = Path(..., ge=1),
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    return service.get_by_id(menu_id, profile_id)

@router.put("/{menu_id}", response_model=HomeMenuRead)
async def update_home_menu(
    menu_id: int = Path(..., ge=1),
    menu_in: HomeMenuUpdate = None,
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    return service.update(menu_id, menu_in, profile_id)

@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_home_menu(
    menu_id: int = Path(..., ge=1),
    profile_id: int = Depends(get_profile_id),
    service: HomeMenuService = Depends(get_home_menu_service)
):
    service.delete(menu_id, profile_id)
    return None