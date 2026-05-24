from sqlmodel import Session, select, func, and_
from models.app_menu import AppMenu
from models.profile_module import ProfileModule
from schemas.app_menu import AppMenuCreate, AppMenuUpdate
from datetime import datetime, timezone
from fastapi import HTTPException, status
from typing import Optional

class AppMenuService:
    def __init__(self, session: Session):
        self.session = session

    def _get_allowed_module_ids(self, profile_id: int) -> set[int]:
        """Obtener IDs de módulos permitidos para un perfil"""
        profile_modules = self.session.exec(
            select(ProfileModule).where(ProfileModule.profile_id == profile_id)
        ).all()
        return {pm.module_id for pm in profile_modules if pm.module_id}

    def create(self, menu_in: AppMenuCreate, profile_id: int) -> AppMenu:
        # Validar que el perfil tiene permiso para el módulo (si se especifica)
        if menu_in.module_id:
            allowed_modules = self._get_allowed_module_ids(profile_id)
            if menu_in.module_id not in allowed_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"estado": "error", "mensaje": "No tienes permiso para este módulo"}
                )
        
        db_menu = AppMenu.model_validate(menu_in)
        db_menu.created_at = datetime.now(timezone.utc)
        db_menu.updated_at = datetime.now(timezone.utc)
        
        self.session.add(db_menu)
        self.session.commit()
        self.session.refresh(db_menu)
        return db_menu

    def get_all_flat(self, profile_id: int) -> list[AppMenu]:
        """Listar todos los menús permitidos (sin paginación, plano)"""
        allowed_modules = self._get_allowed_module_ids(profile_id)
        
        stmt = select(AppMenu).order_by(AppMenu.order, AppMenu.label)
        if allowed_modules:
            stmt = stmt.where(
                and_(AppMenu.module_id.isnot(None), AppMenu.module_id.in_(allowed_modules))
            )
        else:
            # Si no tiene módulos permitidos, solo mostrar menús sin módulo (globales)
            stmt = stmt.where(AppMenu.module_id.is_(None))
        
        return self.session.exec(stmt).all()

    def get_paginated(self, page: int, limit: int, profile_id: int) -> dict:
        """Listar con paginación, filtrado por permisos"""
        offset = (page - 1) * limit
        allowed_modules = self._get_allowed_module_ids(profile_id)
        
        # Query base con filtros de permisos
        base_stmt = select(AppMenu)
        if allowed_modules:
            base_stmt = base_stmt.where(
                and_(AppMenu.module_id.isnot(None), AppMenu.module_id.in_(allowed_modules))
            )
        else:
            base_stmt = base_stmt.where(AppMenu.module_id.is_(None))
        
        # Total
        total = self.session.exec(select(func.count()).select_from(base_stmt.subquery())).one()
        
        # Datos paginados
        stmt = base_stmt.order_by(AppMenu.order, AppMenu.label).offset(offset).limit(limit)
        menus = self.session.exec(stmt).all()
        
        return {"total": total, "page": page, "limit": limit, "data": menus}

    def get_by_id(self, menu_id: int, profile_id: int) -> AppMenu:
        menu = self.session.get(AppMenu, menu_id)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"estado": "error", "mensaje": "Menú no encontrado"}
            )
        
        # Validar permiso si tiene módulo asociado
        if menu.module_id:
            allowed_modules = self._get_allowed_module_ids(profile_id)
            if menu.module_id not in allowed_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"estado": "error", "mensaje": "No tienes permiso para ver este menú"}
                )
        
        return menu

    def update(self, menu_id: int, menu_in: AppMenuUpdate, profile_id: int) -> AppMenu:
        db_menu = self.get_by_id(menu_id, profile_id)  # Reusa validación de permisos
        
        if menu_in.module_id is not None and menu_in.module_id != db_menu.module_id:
            allowed_modules = self._get_allowed_module_ids(profile_id)
            if menu_in.module_id and menu_in.module_id not in allowed_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"estado": "error", "mensaje": "No tienes permiso para este módulo"}
                )
        
        update_data = menu_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_menu, field, value)
        
        db_menu.updated_at = datetime.now(timezone.utc)
        self.session.add(db_menu)
        self.session.commit()
        self.session.refresh(db_menu)
        return db_menu

    def delete(self, menu_id: int, profile_id: int) -> bool:
        db_menu = self.get_by_id(menu_id, profile_id)  # Reusa validación de permisos
        self.session.delete(db_menu)
        self.session.commit()
        return True
