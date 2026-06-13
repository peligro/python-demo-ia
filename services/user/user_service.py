#services/user/user_service.py
from sqlmodel import Session, select, and_, func
from sqlalchemy.orm import selectinload
from models.user import User
from models.user_metadata import UserMetadata
from schemas.user import UserCreate, UserUpdate
from common.common import generate_hash
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import Optional


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_in: UserCreate) -> User:
        # Validar email único
        existing = self.session.exec(
            select(User).where(User.email == user_in.email)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado"
            )
        
        # Crear usuario
        db_user = User.model_validate(user_in)
        db_user.password = generate_hash(user_in.password)
        db_user.created_at = datetime.now(timezone.utc)
        db_user.updated_at = datetime.now(timezone.utc)
        
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        
        # ✅ CREAR METADATA CON VALORES POR DEFECTO O LOS ENVIADOS
        default_meta = UserMetadata(
            user_id=db_user.id,
            phone=user_in.phone,
            state_id=user_in.state_id or 1,      # 1 = Activo por defecto
            profile_id=user_in.profile_id or 3   # 3 = Sin Acceso por defecto
        )
        self.session.add(default_meta)
        self.session.commit()
        
        return db_user

    def get_paginated_with_metadata(
        self,
        page: int = 1,
        limit: int = 20,
        name: Optional[str] = None,
        email: Optional[str] = None,
        state_id: Optional[int] = None,
        profile_id: Optional[int] = None
    ) -> dict:
        offset = (page - 1) * limit
        
        # Query base con OUTER JOIN para acceder a user_metadata
        stmt = select(User).outerjoin(UserMetadata, User.id == UserMetadata.user_id)
        count_stmt = select(func.count(User.id.distinct())).outerjoin(
            UserMetadata, User.id == UserMetadata.user_id
        )
        
        # ✅ Cargar relaciones en 1 sola query (evita N+1)
        stmt = stmt.options(
            selectinload(User.user_meta).selectinload(UserMetadata.profile),
            selectinload(User.user_meta).selectinload(UserMetadata.state)
        )

        # Construir filtros dinámicos
        conditions = []
        if name:
            conditions.append(User.name.ilike(f"%{name}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email}%"))
        if state_id is not None:
            conditions.append(UserMetadata.state_id == state_id)
        if profile_id is not None:
            conditions.append(UserMetadata.profile_id == profile_id)

        if conditions:
            where_clause = and_(*conditions)
            stmt = stmt.where(where_clause)
            count_stmt = count_stmt.where(where_clause)

        # Total de registros
        total = self.session.exec(count_stmt).one()

        # Aplicar paginación y orden
        stmt = stmt.order_by(User.id.desc()).offset(offset).limit(limit)
        users = self.session.exec(stmt).all()

        return {"total": total, "page": page, "limit": limit, "data": users}

    def get_by_id(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return user

    def update(self, user_id: int, user_in: UserUpdate) -> User:
        db_user = self.get_by_id(user_id)
        
        # Actualizar campos del usuario
        if user_in.email and user_in.email != db_user.email:
            existing = self.session.exec(
                select(User).where(and_(User.email == user_in.email, User.id != user_id))
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está en uso por otro usuario"
                )
            db_user.email = user_in.email
            
        if user_in.name:
            db_user.name = user_in.name
            
        if user_in.password:
            db_user.password = generate_hash(user_in.password)
        
        db_user.updated_at = datetime.now(timezone.utc)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        
        # ✅ ACTUALIZAR METADATA (profile_id, state_id, phone)
        metadata = self.session.exec(
            select(UserMetadata).where(UserMetadata.user_id == user_id)
        ).first()
        
        if metadata:
            # Actualizar solo los campos que vinieron en el request
            if user_in.phone is not None:
                metadata.phone = user_in.phone
            if user_in.profile_id is not None:
                metadata.profile_id = user_in.profile_id
            if user_in.state_id is not None:
                metadata.state_id = user_in.state_id
            
            self.session.add(metadata)
            self.session.commit()
        
        return db_user

    def delete(self, user_id: int) -> bool:
        db_user = self.get_by_id(user_id)
        self.session.delete(db_user)
        self.session.commit()
        return True