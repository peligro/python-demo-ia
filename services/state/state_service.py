#services/state/state_service.py
from sqlmodel import Session, select, and_
from models.state import State
from schemas.state import StateCreate, StateUpdate
from datetime import datetime
from sqlalchemy import desc
from fastapi import HTTPException, status


class StateService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, state_in: StateCreate) -> State:
        existing = self.session.exec(
            select(State).where(State.name == state_in.name)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El estado '{state_in.name}' ya existe"
            )
        
        db_state = State.model_validate(state_in)
        db_state.created_at = datetime.now()
        db_state.updated_at = datetime.now()
        
        self.session.add(db_state)
        self.session.commit()
        self.session.refresh(db_state)
        return db_state

    def get_all(self) -> list[State]:
        statement = select(State).order_by(desc(State.id))
        return self.session.exec(statement).all()

    def get_by_id(self, state_id: int) -> State:
        state = self.session.get(State, state_id)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {state_id} no encontrado"
            )
        return state

    def update(self, state_id: int, state_in: StateUpdate) -> State:
        db_state = self.get_by_id(state_id)
        
        if state_in.name is not None:
            existing = self.session.exec(
                select(State).where(
                    and_(State.name == state_in.name, State.id != state_id)
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El estado '{state_in.name}' ya existe"
                )
            db_state.name = state_in.name
        
        db_state.updated_at = datetime.now()
        self.session.add(db_state)
        self.session.commit()
        self.session.refresh(db_state)
        return db_state

    def delete(self, state_id: int) -> bool:
        db_state = self.get_by_id(state_id)
        self.session.delete(db_state)
        self.session.commit()
        return True