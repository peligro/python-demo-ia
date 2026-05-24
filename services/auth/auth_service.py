from sqlmodel import Session, select
from models.user import User
from models.user_metadata import UserMetadata
from common.common import verify_password, generate_hash
from common.redis_client import redis_client
from datetime import datetime, timezone
import secrets
import os

class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.session_ttl = int(os.getenv("SESSION_TTL", 86400))
    
    def login(self, email: str, password: str, remember: bool = False) -> tuple[str, User]:
        """
        Login: valida credenciales, genera token, guarda en Redis y DB
        Retorna: (token, user)
        """
        # Buscar usuario
        user = self.session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise ValueError("Credenciales inválidas")
        
        # Verificar password
        if not verify_password(password, user.password):
            raise ValueError("Credenciales inválidas")
        
        # Verificar estado activo (state_id=1)
        metadata = self.session.exec(
            select(UserMetadata).where(UserMetadata.user_id == user.id)
        ).first()
        if not metadata or metadata.state_id != 1:
            raise ValueError("Usuario inactivo o bloqueado")
        
        # Generar token seguro (64 bytes = 128 caracteres hex)
        token = secrets.token_hex(64)
        
        # Guardar en Redis con TTL
        ttl = self.session_ttl * 2 if remember else self.session_ttl
        redis_client.set_session(token, user.id, ttl)
        
        # Actualizar remember_token en DB (backup)
        user.remember_token = token
        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.commit()
        
        return token, user
    
    def logout(self, token: str):
        """Logout: invalida token en Redis y DB"""
        # Agregar a blacklist (API C2)
        redis_client.blacklist_token(token, self.session_ttl)
        
        # Eliminar de Redis
        redis_client.delete_session(token)
        
        # Limpiar en DB
        user = self.session.exec(select(User).where(User.remember_token == token)).first()
        if user:
            user.remember_token = None
            user.updated_at = datetime.now(timezone.utc)
            self.session.add(user)
            self.session.commit()
