from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from database.database import get_session
from services.state.state_service import StateService
from schemas.state import StateCreate, StateUpdate, StateRead, StatePublic

router = APIRouter(prefix="/states", tags=["State"])


def get_state_service(session: Session = Depends(get_session)) -> StateService:
    return StateService(session)


@router.get("", response_model=list[StatePublic])
async def list_states(
    service: StateService = Depends(get_state_service)
):
    return service.get_all()


@router.get("/{state_id}", response_model=StatePublic)
async def get_state(
    state_id: int,
    service: StateService = Depends(get_state_service)
):
    return service.get_by_id(state_id)


@router.post("", response_model=StateRead, status_code=status.HTTP_201_CREATED)
async def create_state(
    state_in: StateCreate,
    service: StateService = Depends(get_state_service)
):
    return service.create(state_in)


@router.put("/{state_id}", response_model=StateRead)
async def update_state(
    state_id: int,
    state_in: StateUpdate,
    service: StateService = Depends(get_state_service)
):
    return service.update(state_id, state_in)


@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(
    state_id: int,
    service: StateService = Depends(get_state_service)
):
    service.delete(state_id)
    return None