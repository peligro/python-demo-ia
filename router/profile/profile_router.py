from fastapi import APIRouter, Depends, status, Path, Body
from sqlmodel import Session
from database.database import get_session
from services.profile.profile_service import ProfileService
from schemas.profile import ProfileCreate, ProfileUpdate, ProfilePublic, ProfileRead
from schemas.module import ModuleRead
from schemas.item import ItemPublic, ItemRead


router = APIRouter(prefix="/profiles", tags=["Profile"])

def get_profile_service(session: Session = Depends(get_session)) -> ProfileService:
    return ProfileService(session)

@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_in: ProfileCreate,
    service: ProfileService = Depends(get_profile_service)
):
    return service.create(profile_in)

@router.get("", response_model=list[ProfilePublic])
async def list_profiles(
    service: ProfileService = Depends(get_profile_service)
):
    return service.get_all()

@router.get("/{profile_id}", response_model=ProfilePublic)
async def get_profile(
    profile_id: int,
    service: ProfileService = Depends(get_profile_service)
):
    return service.get_by_id(profile_id)

@router.put("/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: int,
    profile_in: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service)
):
    return service.update(profile_id, profile_in)

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    service: ProfileService = Depends(get_profile_service)
):
    service.delete(profile_id)
    return None

@router.get("/{profile_id}/modules", response_model=list[ModuleRead])
async def get_profile_modules(
    profile_id: int = Path(..., ge=1),
    service: ProfileService = Depends(get_profile_service)
):
    return service.get_modules_by_profile(profile_id)

@router.post("/{profile_id}/modules", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def assign_module_to_profile(
    profile_id: int = Path(..., ge=1),
    module_id: int = Body(..., ge=1, embed=True),
    service: ProfileService = Depends(get_profile_service)
):
    return service.assign_module_to_profile(profile_id, module_id).module

@router.delete("/{profile_id}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_module_from_profile(
    profile_id: int = Path(..., ge=1),
    module_id: int = Path(..., ge=1),
    service: ProfileService = Depends(get_profile_service)
):
    service.remove_module_from_profile(profile_id, module_id)
    return None


@router.get("/{profile_id}/modules/{module_id}/items", response_model=list[ItemPublic])
async def get_profile_module_items(
    profile_id: int = Path(..., ge=1),
    module_id: int = Path(..., ge=1),
    service: ProfileService = Depends(get_profile_service)
):
    # Primero obtenemos el profile_module_id
    pm = self.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    return service.get_items_by_profile_module(pm.id)

# Asignar item
@router.post("/{profile_id}/modules/{module_id}/items", response_model=ItemRead, status_code=201)
async def assign_item_to_profile_module(
    profile_id: int = Path(..., ge=1),
    module_id: int = Path(..., ge=1),
    item_id: int = Body(..., ge=1, embed=True),
    service: ProfileService = Depends(get_profile_service)
):
    pm = self.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    return service.assign_item_to_profile_module(pm.id, item_id).item

# Eliminar asignación
@router.delete("/{profile_id}/modules/{module_id}/items/{item_id}", status_code=204)
async def remove_item_from_profile_module(
    profile_id: int = Path(..., ge=1),
    module_id: int = Path(..., ge=1),
    item_id: int = Path(..., ge=1),
    service: ProfileService = Depends(get_profile_service)
):
    pm = self.session.exec(
        select(ProfileModule).where(
            and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
        )
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
    service.remove_item_from_profile_module(pm.id, item_id)
    return None