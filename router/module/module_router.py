from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session, select, func
from sqlalchemy import desc
from database.database import get_session
from services.module.module_service import ModuleService
from schemas.module import ModuleCreate, ModuleUpdate, ModulePublic, ModuleRead, ModuleListResponse
from middleware.rbac import require_module, require_item
from common.constants import SETTINGS_MODULES
from models.module import Module
from typing import Optional

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
    response_model=ModuleListResponse,  # ← Cambiado a ModuleListResponse
    dependencies=[Depends(require_module(SETTINGS_MODULES))]
)
async def list_modules(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    service: ModuleService = Depends(get_module_service)
):
    """Listar módulos con paginación y búsqueda"""
    offset = (page - 1) * limit
    
    # Query base
    stmt = select(Module)
    count_stmt = select(func.count(Module.id))
    
    # Filtro de búsqueda
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(Module.name.ilike(search_pattern) | Module.slug.ilike(search_pattern))
        count_stmt = count_stmt.where(Module.name.ilike(search_pattern) | Module.slug.ilike(search_pattern))
    
    # Total de registros
    total = service.session.exec(count_stmt).one()
    
    # Datos paginados
    stmt = stmt.order_by(desc(Module.id)).offset(offset).limit(limit)
    modules = service.session.exec(stmt).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": modules
    }

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