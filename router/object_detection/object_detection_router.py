#router/object_detection/object_detection_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.object_detection import (
    ObjectDetectionRequest,
    ObjectDetectionResponse,
)
from services.object_detection.object_detection_service import ObjectDetectionService
from middleware.auth import get_current_user

router = APIRouter(
    prefix="/object-detection",
    tags=["Portfolio: Object Detection"]
)


@router.post(
    "/detect",
    response_model=ObjectDetectionResponse,
    status_code=status.HTTP_200_OK
)
async def detect_objects(
    body: ObjectDetectionRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Detección de objetos con YOLOv8
    
    Detecta hasta 80 tipos de objetos diferentes en una imagen usando
    modelos YOLOv8 pre-entrenados con el dataset COCO.
    
    Modelos disponibles:
    - yolov8n.pt: Nano (más rápido, ~6MB)
    - yolov8s.pt: Small (balance, ~22MB)
    - yolov8m.pt: Medium (precisión media, ~52MB)
    - yolov8l.pt: Large (alta precisión, ~87MB)
    - yolov8x.pt: X-Large (máxima precisión, ~136MB)
    
    Clases detectadas (80):
    Personas, vehículos (auto, bus, bicicleta, etc.), animales,
    objetos cotidianos, comida, muebles, electrónicos, y más.
    """
    try:
        service = ObjectDetectionService(session)
        return await service.detect_objects(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/classes",
    status_code=status.HTTP_200_OK
)
async def get_classes(
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna la lista de 80 clases que YOLOv8 puede detectar
    """
    from services.object_detection.object_detection_service import COCO_CLASSES
    
    return {
        "total_classes": len(COCO_CLASSES),
        "classes": COCO_CLASSES,
    }