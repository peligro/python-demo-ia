from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database.database import get_session
from services.item.item_service import ItemService
from schemas.item import ItemCreate, ItemUpdate, ItemPublic, ItemRead
from middleware.rbac import require_module, require_item
from common.constants import SETTINGS_ITEMS

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
    response_model=list[ItemPublic],
    dependencies=[Depends(require_module(SETTINGS_ITEMS))]
)
async def list_items(service: ItemService = Depends(get_item_service)):
    return service.get_all()

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