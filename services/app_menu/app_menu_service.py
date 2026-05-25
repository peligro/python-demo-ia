from sqlmodel import Session, select, func, and_, or_
from sqlalchemy.orm import selectinload
from models.app_menu import AppMenu
from models.module import Module
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

    def _build_app_menu_response(self, menu: AppMenu) -> dict:
        """Construir respuesta con module_slug y parent si existen"""
        data = {
            "id": menu.id,
            "label": menu.label,
            "title": menu.title,
            "icon": menu.icon,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "module_id": menu.module_id,
            "module_slug": None,
            "parent": None,
        }
        
        # Agregar module_slug si existe
        if menu.module and menu.module.slug:
            data["module_slug"] = menu.module.slug
        
        # Agregar información del padre si existe
        if menu.parent_id:
            parent_menu = self.session.get(AppMenu, menu.parent_id)
            if parent_menu:
                data["parent"] = {
                    "id": parent_menu.id,
                    "label": parent_menu.label
                }
        
        return data

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

    def get_all_flat(self, profile_id: int) -> list[dict]:
        """Listar todos los menús permitidos (sin paginación)"""
        allowed_modules = self._get_allowed_module_ids(profile_id)
        
        stmt = select(AppMenu).outerjoin(Module).order_by(AppMenu.order, AppMenu.label)
        if allowed_modules:
            stmt = stmt.where(
                and_(AppMenu.module_id.isnot(None), AppMenu.module_id.in_(allowed_modules))
            )
        else:
            stmt = stmt.where(AppMenu.module_id.is_(None))
        
        menus = self.session.exec(stmt).all()
        return [self._build_app_menu_response(m) for m in menus]

    def get_paginated(self, page: int, limit: int, profile_id: int, search: Optional[str] = None) -> dict:
        """Listar con paginación, filtrado por permisos y búsqueda opcional"""
        from sqlalchemy import and_
        
        offset = (page - 1) * limit
        allowed_modules = self._get_allowed_module_ids(profile_id)
        
        # Query base con filtros de permisos
        base_stmt = select(AppMenu).outerjoin(Module)
        
        # Filtro de módulos permitidos
        if allowed_modules:
            base_stmt = base_stmt.where(
                and_(AppMenu.module_id.isnot(None), AppMenu.module_id.in_(allowed_modules))
            )
        else:
            base_stmt = base_stmt.where(AppMenu.module_id.is_(None))
        
        # ✅ Filtro de búsqueda (label o title)
        if search:
            search_pattern = f"%{search}%"
            base_stmt = base_stmt.where(
                or_(
                    AppMenu.label.ilike(search_pattern),
                    AppMenu.title.ilike(search_pattern),
                    AppMenu.icon.ilike(search_pattern)
                )
            )
        
        # Total de registros (con filtros aplicados)
        total = self.session.exec(
            select(func.count()).select_from(base_stmt.subquery())
        ).one()
        
        # Datos paginados
        stmt = base_stmt.order_by(AppMenu.order, AppMenu.label).offset(offset).limit(limit)
        menus = self.session.exec(stmt).all()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": [self._build_app_menu_response(m) for m in menus]
        }

    def get_by_id(self, menu_id: int, profile_id: int) -> dict:
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
        
        return self._build_app_menu_response(menu)

    def update(self, menu_id: int, menu_in: AppMenuUpdate, profile_id: int) -> AppMenu:
        db_menu = self.session.get(AppMenu, menu_id)
        if not db_menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"estado": "error", "mensaje": "Menú no encontrado"}
            )
        
        # Validar permiso si cambia el módulo
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
        db_menu = self.session.get(AppMenu, menu_id)
        if not db_menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"estado": "error", "mensaje": "Menú no encontrado"}
            )
        
        # Validar permiso
        if db_menu.module_id:
            allowed_modules = self._get_allowed_module_ids(profile_id)
            if db_menu.module_id not in allowed_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"estado": "error", "mensaje": "No tienes permiso para eliminar este menú"}
                )
        
        self.session.delete(db_menu)
        self.session.commit()
        return True