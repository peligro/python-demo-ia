from sqlmodel import Session, select, and_
from models.item import Item
from schemas.item import ItemCreate, ItemUpdate
from datetime import datetime, timezone
from fastapi import HTTPException, status

class ItemService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, item_in: ItemCreate) -> Item:
        existing = self.session.exec(select(Item).where(Item.code == item_in.code)).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El código '{item_in.code}' ya está en uso")
        
        db_item = Item.model_validate(item_in)
        db_item.created_at = datetime.now(timezone.utc)
        db_item.updated_at = datetime.now(timezone.utc)
        
        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item

    def get_all(self) -> list[Item]:
        from sqlalchemy import desc
        statement = select(Item).order_by(desc(Item.id))
        return self.session.exec(statement).all()

    def get_by_id(self, item_id: int) -> Item:
        item = self.session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ítem con ID {item_id} no encontrado")
        return item

    def update(self, item_id: int, item_in: ItemUpdate) -> Item:
        db_item = self.get_by_id(item_id)
        
        if item_in.code is not None and item_in.code != db_item.code:
            existing = self.session.exec(select(Item).where(and_(Item.code == item_in.code, Item.id != item_id))).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El código '{item_in.code}' ya está en uso")
            db_item.code = item_in.code
            
        if item_in.name is not None:
            db_item.name = item_in.name
            
        db_item.updated_at = datetime.now(timezone.utc)
        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item

    def delete(self, item_id: int) -> bool:
        db_item = self.get_by_id(item_id)
        self.session.delete(db_item)
        self.session.commit()
        return True