from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from common.redis_client import redis_client
from sqlmodel import Session, select
from database.database import get_session
from models.user import User
from models.user_metadata import UserMetadata
from models.profile_module import ProfileModule
from models.profile_module_item import ProfileModuleItem
from models.module import Module
from models.item import Item
from typing import Optional

async def get_current_user(
    request: Request,
    session: Session = Depends(get_session)
) -> dict:
    """
    Middleware para obtener usuario actual desde cookie + Redis
    Retorna: {"user": User, "metadata": UserMetadata, "modules": [...]}
    """
    # 1. Obtener token de cookie
    token = request.cookies.get("remember_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # 2. Verificar blacklist (API C2)
    if redis_client.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o inválida"
        )
    
    # 3. Buscar sesión en Redis
    session_data = redis_client.get_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada en Redis"
        )
    
    # 4. Cargar usuario desde DB
    user_id = session_data["user_id"]
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    # 5. Cargar metadata
    metadata = session.exec(
        select(UserMetadata).where(UserMetadata.user_id == user_id)
    ).first()
    
    # 6. Cargar módulos + items del perfil (API C1 - BOLA prevention)
    if metadata and metadata.profile_id:
        # Obtener ProfileModules
        profile_modules = session.exec(
            select(ProfileModule).where(ProfileModule.profile_id == metadata.profile_id)
        ).all()
        
        modules_with_items = []
        for pm in profile_modules:
            module = session.get(Module, pm.module_id)
            if module:
                # Obtener items de este module
                profile_module_items = session.exec(
                    select(ProfileModuleItem).where(
                        ProfileModuleItem.profile_module_id == pm.id
                    )
                ).all()
                
                items = []
                for pmi in profile_module_items:
                    item = session.get(Item, pmi.item_id)
                    if item:
                        items.append(item)
                
                modules_with_items.append({
                    "module": module,
                    "items": items
                })
    else:
        modules_with_items = []
    
    return {
        "user": user,
        "metadata": metadata,
        "modules_with_items": modules_with_items
    }

# Dependency para usar en rutas
def require_auth(current_user: dict = Depends(get_current_user)):
    """Dependency que retorna el usuario autenticado"""
    return current_user
