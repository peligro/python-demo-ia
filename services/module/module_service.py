#services/module/module_service.py
from sqlmodel import Session, select, and_
from models.module import Module
from schemas.module import ModuleCreate, ModuleUpdate
from datetime import datetime, timezone
from fastapi import HTTPException, status


class ModuleService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, module_in: ModuleCreate) -> Module:
        # Validar unicidad de name y slug
        existing_name = self.session.exec(
            select(Module).where(Module.name == module_in.name)
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El módulo '{module_in.name}' ya existe"
            )
        
        existing_slug = self.session.exec(
            select(Module).where(Module.slug == module_in.slug)
        ).first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El slug '{module_in.slug}' ya está en uso"
            )
        
        db_module = Module.model_validate(module_in)
        db_module.created_at = datetime.now(timezone.utc)
        db_module.updated_at = datetime.now(timezone.utc)
        
        self.session.add(db_module)
        self.session.commit()
        self.session.refresh(db_module)
        return db_module

    def get_all(self) -> list[Module]:
        from sqlalchemy import desc
        statement = select(Module).order_by(desc(Module.id))
        return self.session.exec(statement).all()

    def get_by_id(self, module_id: int) -> Module:
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con ID {module_id} no encontrado"
            )
        return module

    def update(self, module_id: int, module_in: ModuleUpdate) -> Module:
        db_module = self.get_by_id(module_id)  # Reusa validación de existencia
        
        if module_in.name is not None and module_in.name != db_module.name:
            existing = self.session.exec(
                select(Module).where(
                    and_(Module.name == module_in.name, Module.id != module_id)
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El módulo '{module_in.name}' ya existe"
                )
            db_module.name = module_in.name
        
        if module_in.slug is not None and module_in.slug != db_module.slug:
            existing = self.session.exec(
                select(Module).where(
                    and_(Module.slug == module_in.slug, Module.id != module_id)
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El slug '{module_in.slug}' ya está en uso"
                )
            db_module.slug = module_in.slug
        
        db_module.updated_at = datetime.now(timezone.utc)
        self.session.add(db_module)
        self.session.commit()
        self.session.refresh(db_module)
        return db_module

    def delete(self, module_id: int) -> bool:
        db_module = self.get_by_id(module_id)
        self.session.delete(db_module)
        self.session.commit()
        return True