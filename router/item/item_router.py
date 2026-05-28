from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session, select, func
from sqlalchemy import desc
from database.database import get_session
from services.item.item_service import ItemService
from schemas.item import ItemCreate, ItemUpdate, ItemPublic, ItemRead, ItemListResponse
from middleware.rbac import require_module, require_item
from common.constants import SETTINGS_ITEMS
from models.item import Item
from typing import Optional

router = APIRouter(prefix="/items", tags=["Item"])

def get_item_service(session: Session = Depends(get_session)) -> ItemService:
    return ItemService(session)

@router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_item(SETTINGS_ITEMS, "create_item"))]
)
async def create_item(item_in: ItemCreate, service: ItemService = Depends(get_item_service)):
    return service.create(item_in)

@router.get(
    "",
    response_model=ItemListResponse,
    dependencies=[Depends(require_module(SETTINGS_ITEMS))]
)
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    service: ItemService = Depends(get_item_service)
):
    """Listar ítems con paginación y búsqueda"""
    offset = (page - 1) * limit
    
    # Query base
    stmt = select(Item)
    count_stmt = select(func.count(Item.id))
    
    # Filtro de búsqueda
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(Item.name.ilike(search_pattern) | Item.code.ilike(search_pattern))
        count_stmt = count_stmt.where(Item.name.ilike(search_pattern) | Item.code.ilike(search_pattern))
    
    # Total de registros
    total = service.session.exec(count_stmt).one()
    
    # Datos paginados
    stmt = stmt.order_by(desc(Item.id)).offset(offset).limit(limit)
    items = service.session.exec(stmt).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": items
    }

@router.get(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_item(SETTINGS_ITEMS, "view_item"))]
)
async def get_item(item_id: int, service: ItemService = Depends(get_item_service)):
    return service.get_by_id(item_id)

@router.put(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_item(SETTINGS_ITEMS, "edit_item"))]
)
async def update_item(item_id: int, item_in: ItemUpdate, service: ItemService = Depends(get_item_service)):
    return service.update(item_id, item_in)

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_item(SETTINGS_ITEMS, "delete_item"))]
)
async def delete_item(item_id: int, service: ItemService = Depends(get_item_service)):
    service.delete(item_id)
    return None