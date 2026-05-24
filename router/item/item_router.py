from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database.database import get_session
from services.item.item_service import ItemService
from schemas.item import ItemCreate, ItemUpdate, ItemPublic, ItemRead

router = APIRouter(prefix="/items", tags=["Item"])

def get_item_service(session: Session = Depends(get_session)) -> ItemService:
    return ItemService(session)

@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(item_in: ItemCreate, service: ItemService = Depends(get_item_service)):
    return service.create(item_in)

@router.get("", response_model=list[ItemPublic])
async def list_items(service: ItemService = Depends(get_item_service)):
    return service.get_all()

@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, service: ItemService = Depends(get_item_service)):
    return service.get_by_id(item_id)

@router.put("/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, item_in: ItemUpdate, service: ItemService = Depends(get_item_service)):
    return service.update(item_id, item_in)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, service: ItemService = Depends(get_item_service)):
    service.delete(item_id)
    return None