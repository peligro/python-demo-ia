from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database.database import get_session
from services.module.module_service import ModuleService
from schemas.module import ModuleCreate, ModuleUpdate, ModulePublic, ModuleRead
from middleware.rbac import require_module, require_item
from common.constants import SETTINGS_MODULES

router = APIRouter(prefix="/modules", tags=["Module"])


def get_module_service(session: Session = Depends(get_session)) -> ModuleService:
    return ModuleService(session)


@router.post(
    "",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_item(SETTINGS_MODULES, "create_module"))]
)
async def create_module(
    module_in: ModuleCreate,
    service: ModuleService = Depends(get_module_service)
):
    return service.create(module_in)


@router.get(
    "",
    response_model=list[ModulePublic],
    dependencies=[Depends(require_module(SETTINGS_MODULES))]
)
async def list_modules(
    service: ModuleService = Depends(get_module_service)
):
    return service.get_all()


@router.get(
    "/{module_id}",
    response_model=ModuleRead,
    dependencies=[Depends(require_item(SETTINGS_MODULES, "view_module"))]
)
async def get_module(
    module_id: int,
    service: ModuleService = Depends(get_module_service)
):
    return service.get_by_id(module_id)


@router.put(
    "/{module_id}",
    response_model=ModuleRead,
    dependencies=[Depends(require_item(SETTINGS_MODULES, "edit_module"))]
)
async def update_module(
    module_id: int,
    module_in: ModuleUpdate,
    service: ModuleService = Depends(get_module_service)
):
    return service.update(module_id, module_in)


@router.delete(
    "/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_item(SETTINGS_MODULES, "delete_module"))]
)
async def delete_module(
    module_id: int,
    service: ModuleService = Depends(get_module_service)
):
    service.delete(module_id)
    return None