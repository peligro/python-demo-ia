# middleware/rbac.py
from fastapi import Depends, HTTPException, status, Request
from sqlmodel import Session, select
from database.database import get_session
from models.user_metadata import UserMetadata
from models.profile_module import ProfileModule
from models.profile_module_item import ProfileModuleItem
from models.module import Module
from models.item import Item
from middleware.auth import get_current_user
from typing import Optional


def require_permission(
    module_slug: Optional[str] = None,
    item_code: Optional[str] = None,
    special_codes: Optional[list[str]] = None
):
    """
    Dependency que valida permisos de usuario.
    
    Returns:
        callable: La función permission_checker para usar con Depends()
    """
    async def permission_checker(
        request: Request,
        current_user: dict = Depends(get_current_user),
        session: Session = Depends(get_session)
    ):
        user = current_user["user"]
        metadata = current_user["metadata"]
        
        # Si no tiene perfil asignado, no tiene permisos
        if not metadata or not metadata.profile_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"estado": "error", "mensaje": "No autenticado"}
            )
        
        # 1. Cargar todos los módulos del perfil
        profile_modules = session.exec(
            select(ProfileModule)
            .where(ProfileModule.profile_id == metadata.profile_id)
        ).all()
        
        # 2. Construir sets de permisos
        user_module_slugs = set()
        user_item_codes = set()
        
        for pm in profile_modules:
            module = session.get(Module, pm.module_id)
            if module:
                user_module_slugs.add(module.slug)
                
                # Cargar items de este módulo
                profile_module_items = session.exec(
                    select(ProfileModuleItem)
                    .where(ProfileModuleItem.profile_module_id == pm.id)
                ).all()
                
                for pmi in profile_module_items:
                    item = session.get(Item, pmi.item_id)
                    if item:
                        user_item_codes.add(item.code)
        
        # 3. Verificar códigos especiales (admin override)
        if special_codes:
            for code in special_codes:
                if code in user_item_codes:
                    return {"user": user, "metadata": metadata, "has_permission": True}
        
        # 4. Verificar módulo específico
        if module_slug:
            if module_slug not in user_module_slugs:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"estado": "error", "mensaje": "No autenticado"}
                )
            
            # Si no requiere item específico, con tener el módulo basta
            if not item_code:
                return {"user": user, "metadata": metadata, "has_permission": True}
            
            # 5. Verificar item específico dentro del módulo
            if item_code and item_code not in user_item_codes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"estado": "error", "mensaje": "No autenticado"}
                )
            
            return {"user": user, "metadata": metadata, "has_permission": True}
        
        # Si no se especificó módulo ni item, denegar
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"estado": "error", "mensaje": "No autenticado"}
        )
    
    # ✅ Retornar la función directa, NO Depends()
    return permission_checker


# ============================================================================
# Helpers para usar en routers (igual que en Go)
# ============================================================================

def require_module(module_slug: str):
    """
    Requiere que el usuario tenga el módulo.
    Uso: dependencies=[Depends(require_module("/settings/users"))]
    """
    from common.constants import VIEW_ALL_REGISTER
    return require_permission(module_slug=module_slug, special_codes=[VIEW_ALL_REGISTER])


def require_item(module_slug: str, item_code: str):
    """
    Requiere que el usuario tenga el módulo + item específico.
    Uso: dependencies=[Depends(require_item("/settings/users", "view_all_register"))]
    """
    from common.constants import VIEW_ALL_REGISTER
    return require_permission(
        module_slug=module_slug,
        item_code=item_code,
        special_codes=[VIEW_ALL_REGISTER]
    )


def require_any_special_code(*codes: str):
    """
    Requiere que el usuario tenga CUALQUIERA de los códigos especiales.
    Uso: dependencies=[Depends(require_any_special_code("view_all_register", "admin_override"))]
    """
    return require_permission(special_codes=list(codes))