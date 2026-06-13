#services/profile_service/profile_service.py
from sqlmodel import Session, select, and_, func
from sqlalchemy import desc
from models.profile import Profile
from models.profile_module import ProfileModule
from models.profile_module_item import ProfileModuleItem
from models.module import Module
from models.item import Item
from schemas.profile import ProfileCreate, ProfileUpdate
from datetime import datetime, timezone
from fastapi import HTTPException, status
from typing import Optional, List


class ProfileService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, profile_in: ProfileCreate) -> Profile:
        existing = self.session.exec(
            select(Profile).where(Profile.name == profile_in.name)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El perfil '{profile_in.name}' ya existe"
            )
        
        db_profile = Profile.model_validate(profile_in)
        db_profile.created_at = datetime.now(timezone.utc)
        db_profile.updated_at = datetime.now(timezone.utc)
        
        self.session.add(db_profile)
        self.session.commit()
        self.session.refresh(db_profile)
        return db_profile

    # ✅ Para el select de usuarios (sin paginación)
    def get_all(self) -> List[Profile]:
        statement = select(Profile).order_by(desc(Profile.id))
        return self.session.exec(statement).all()

    # ✅ Para el mantenedor (con paginación y búsqueda)
    def get_paginated(
        self, 
        page: int = 1, 
        limit: int = 20, 
        search: Optional[str] = None
    ) -> dict:
        offset = (page - 1) * limit
        
        # Query base
        stmt = select(Profile)
        count_stmt = select(func.count(Profile.id))
        
        # Filtro de búsqueda
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(Profile.name.ilike(search_pattern) | Profile.description.ilike(search_pattern))
            count_stmt = count_stmt.where(Profile.name.ilike(search_pattern) | Profile.description.ilike(search_pattern))
        
        # Total de registros
        total = self.session.exec(count_stmt).one()
        
        # Datos paginados
        stmt = stmt.order_by(desc(Profile.id)).offset(offset).limit(limit)
        profiles = self.session.exec(stmt).all()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": profiles
        }

    def get_by_id(self, profile_id: int) -> Profile:
        profile = self.session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Perfil con ID {profile_id} no encontrado"
            )
        return profile

    def update(self, profile_id: int, profile_in: ProfileUpdate) -> Profile:
        db_profile = self.get_by_id(profile_id)
        
        if profile_in.name is not None and profile_in.name != db_profile.name:
            existing = self.session.exec(
                select(Profile).where(
                    and_(Profile.name == profile_in.name, Profile.id != profile_id)
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El perfil '{profile_in.name}' ya existe"
                )
            db_profile.name = profile_in.name
        
        if profile_in.description is not None:
            db_profile.description = profile_in.description
        
        db_profile.updated_at = datetime.now(timezone.utc)
        self.session.add(db_profile)
        self.session.commit()
        self.session.refresh(db_profile)
        return db_profile

    def delete(self, profile_id: int) -> bool:
        db_profile = self.get_by_id(profile_id)
        self.session.delete(db_profile)
        self.session.commit()
        return True

    # ✅ Métodos para ProfileModule (DENTRO de la clase)
    def get_modules_by_profile(self, profile_id: int) -> List[Module]:
        profile = self.session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
        
        statement = (
            select(Module)
            .join(ProfileModule, Module.id == ProfileModule.module_id)
            .where(ProfileModule.profile_id == profile_id)
        )
        return self.session.exec(statement).all()

    def assign_module_to_profile(self, profile_id: int, module_id: int) -> ProfileModule:
        if not self.session.get(Profile, profile_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
        if not self.session.get(Module, module_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")

        existing = self.session.exec(
            select(ProfileModule).where(
                and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
            )
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El módulo ya está asignado")

        pm = ProfileModule(profile_id=profile_id, module_id=module_id)
        self.session.add(pm)
        self.session.commit()
        self.session.refresh(pm)
        return pm

    def remove_module_from_profile(self, profile_id: int, module_id: int) -> bool:
        pm = self.session.exec(
            select(ProfileModule).where(
                and_(ProfileModule.profile_id == profile_id, ProfileModule.module_id == module_id)
            )
        ).first()
        if not pm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
        
        self.session.delete(pm)
        self.session.commit()
        return True

    def get_items_by_profile_module(self, profile_module_id: int) -> List[Item]:
        """Listar items asignados a un profile_module específico"""
        pm = self.session.get(ProfileModule, profile_module_id)
        if not pm:
            raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
        
        statement = (
            select(Item)
            .join(ProfileModuleItem, Item.id == ProfileModuleItem.item_id)
            .where(ProfileModuleItem.profile_module_id == profile_module_id)
        )
        return self.session.exec(statement).all()

    def assign_item_to_profile_module(self, profile_module_id: int, item_id: int) -> ProfileModuleItem:
        """Asignar un item a un profile_module"""
        if not self.session.get(ProfileModule, profile_module_id):
            raise HTTPException(status_code=404, detail="ProfileModule no encontrado")
        if not self.session.get(Item, item_id):
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        existing = self.session.exec(
            select(ProfileModuleItem).where(
                and_(
                    ProfileModuleItem.profile_module_id == profile_module_id,
                    ProfileModuleItem.item_id == item_id
                )
            )
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="El item ya está asignado")
        
        pmi = ProfileModuleItem(profile_module_id=profile_module_id, item_id=item_id)
        self.session.add(pmi)
        self.session.commit()
        self.session.refresh(pmi)
        return pmi

    def remove_item_from_profile_module(self, profile_module_id: int, item_id: int) -> bool:
        """Eliminar asignación item → profile_module"""
        pmi = self.session.exec(
            select(ProfileModuleItem).where(
                and_(
                    ProfileModuleItem.profile_module_id == profile_module_id,
                    ProfileModuleItem.item_id == item_id
                )
            )
        ).first()
        if not pmi:
            raise HTTPException(status_code=404, detail="Asignación no encontrada")
        
        self.session.delete(pmi)
        self.session.commit()
        return True