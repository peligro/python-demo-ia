from fastapi import APIRouter, Depends, status, Query, Path, Body, HTTPException
from sqlmodel import Session, select, and_
from database.database import get_session
from services.profile.profile_service import ProfileService
from schemas.profile import ProfileCreate, ProfileUpdate, ProfilePublic, ProfileRead, ProfileListResponse, ProfileModulesResponse
from schemas.module import ModuleRead, ModulePublic
from schemas.item import ItemPublic, ItemRead
from middleware.rbac import require_module, require_item
from common.constants import SETTINGS_PROFILES
from models.profile_module import ProfileModule
from typing import Optional

router = APIRouter(prefix="/profiles", tags=["Profile"])

def get_profile_service(session: Session = Depends(get_session)) -> ProfileService:
    return ProfileService(session)

# =============================================================================
# ✅ PRIMERO: Rutas estáticas (sin parámetros)
# =============================================================================

@router.post(
    "",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "create_profile"))]
)
async def create_profile(profile_in: ProfileCreate, service: ProfileService = Depends(get_profile_service)):
    return service.create(profile_in)

@router.get(
    "/all",
    response_model=list[ProfilePublic],
    dependencies=[Depends(require_module(SETTINGS_PROFILES))]
)
async def list_all_profiles(service: ProfileService = Depends(get_profile_service)):
    """Listar todos los perfiles (para select de usuarios)"""
    return service.get_all()

# =============================================================================
# ✅ SEGUNDO: Rutas con parámetros pero más específicas (/modules)
# =============================================================================

@router.get(
    "/{profile_id}/modules",
    response_model=ProfileModulesResponse,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "view_profile_modules"))]
)
async def get_profile_modules(
    profile_id: int = Path(..., ge=1), 
    service: ProfileService = Depends(get_profile_service)
):
    """Obtener módulos asignados a un perfil con metadata completa"""
    profile = service.get_by_id(profile_id)
    modules = service.get_modules_by_profile(profile_id)
    module_ids = [m.id for m in modules]
    
    return {
        "profile_id": profile.id,
        "profile_name": profile.name,
        "modules": modules,
        "module_ids": module_ids
    }

@router.post(
    "/{profile_id}/modules",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "assign_profile_module"))]
)
async def assign_module_to_profile(
    profile_id: int = Path(..., ge=1), 
    module_id: int = Body(..., ge=1, embed=True), 
    service: ProfileService = Depends(get_profile_service)
):
    return service.assign_module_to_profile(profile_id, module_id).module

@router.delete(
    "/{profile_id}/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "remove_profile_module"))]
)
async def remove_module_from_profile(
    profile_id: int = Path(..., ge=1), 
    module_id: int = Path(..., ge=1), 
    service: ProfileService = Depends(get_profile_service)
):
    service.remove_module_from_profile(profile_id, module_id)
    return None

@router.get(
    "/{profile_id}/modules/{module_id}/items",
    response_model=list[ItemPublic],
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "view_profile_module_items"))]
)
async def get_profile_module_items(
    profile_id: int = Path(..., ge=1), 
    module_id: int = Path(..., ge=1), 
    service: ProfileService = Depends(get_profile_service)
):
    pm = service.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    return service.get_items_by_profile_module(pm.id)

@router.post(
    "/{profile_id}/modules/{module_id}/items",
    response_model=ItemRead,
    status_code=201,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "assign_profile_module_item"))]
)
async def assign_item_to_profile_module(
    profile_id: int = Path(..., ge=1), 
    module_id: int = Path(..., ge=1), 
    item_id: int = Body(..., ge=1, embed=True), 
    service: ProfileService = Depends(get_profile_service)
):
    pm = service.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    return service.assign_item_to_profile_module(pm.id, item_id).item

@router.delete(
    "/{profile_id}/modules/{module_id}/items/{item_id}",
    status_code=204,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "remove_profile_module_item"))]
)
async def remove_item_from_profile_module(
    profile_id: int = Path(..., ge=1), 
    module_id: int = Path(..., ge=1), 
    item_id: int = Path(..., ge=1), 
    service: ProfileService = Depends(get_profile_service)
):
    pm = service.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    service.remove_item_from_profile_module(pm.id, item_id)
    return None


# =============================================================================
# ✅ NUEVO: Sincronización masiva de módulos
# =============================================================================

@router.put(
    "/{profile_id}/modules",
    response_model=ProfileModulesResponse,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "assign_profile_module"))]
)
async def sync_profile_modules(
    profile_id: int = Path(..., ge=1),
    request: ProfileModulesResponse = Body(...),  # ← Espera { modules: [1,2,3] }
    service: ProfileService = Depends(get_profile_service)
):
    """Sincronizar todos los módulos de un perfil (reemplaza los existentes)"""
    # 1. Obtener módulos actuales
    current_modules = service.get_modules_by_profile(profile_id)
    current_ids = {m.id for m in current_modules}
    
    # 2. Módulos a agregar (nuevos)
    new_ids = set(request.module_ids)  # ← Usar module_ids del request
    to_add = new_ids - current_ids
    
    # 3. Módulos a quitar (ya no seleccionados)
    to_remove = current_ids - new_ids
    
    # 4. Agregar nuevos
    for module_id in to_add:
        service.assign_module_to_profile(profile_id, module_id)
    
    # 5. Quitar los que no están
    for module_id in to_remove:
        service.remove_module_from_profile(profile_id, module_id)
    
    # 6. Retornar respuesta actualizada
    modules = service.get_modules_by_profile(profile_id)
    module_ids = [m.id for m in modules]
    profile = service.get_by_id(profile_id)
    
    return {
        "profile_id": profile.id,
        "profile_name": profile.name,
        "modules": modules,
        "module_ids": module_ids
    }


# =============================================================================
# ✅ TERCERO: Rutas CRUD básicas (más genéricas)
# =============================================================================

@router.get(
    "",
    response_model=ProfileListResponse,
    dependencies=[Depends(require_module(SETTINGS_PROFILES))]
)
async def list_profiles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    service: ProfileService = Depends(get_profile_service)
):
    """Listar perfiles con paginación y búsqueda (para mantenedor)"""
    return service.get_paginated(page, limit, search)

@router.get(
    "/{profile_id}",
    response_model=ProfilePublic,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "view_profile"))]
)
async def get_profile(profile_id: int, service: ProfileService = Depends(get_profile_service)):
    return service.get_by_id(profile_id)

@router.put(
    "/{profile_id}",
    response_model=ProfileRead,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "edit_profile"))]
)
async def update_profile(profile_id: int, profile_in: ProfileUpdate, service: ProfileService = Depends(get_profile_service)):
    return service.update(profile_id, profile_in)

@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_item(SETTINGS_PROFILES, "delete_profile"))]
)
async def delete_profile(profile_id: int, service: ProfileService = Depends(get_profile_service)):
    service.delete(profile_id)
    return None