#router/face_detection/face_detection_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.face_detection import FaceDetectionRequest, FaceDetectionResponse
from services.face_detection.face_detection_service import FaceDetectionService
from middleware.auth import get_current_user

router = APIRouter(
    prefix="/face-detection",
    tags=["Portfolio: Face Detection"]
)

@router.post(
    "/detect",
    response_model=FaceDetectionResponse,
    status_code=status.HTTP_200_OK
)
async def detect_faces(
    body: FaceDetectionRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Detecta caras y ojos en una imagen.
    
    Métodos disponibles:
    - **haarcascade**: OpenCV clásico, rápido y liviano
    - **mediapipe**: Google MediaPipe, más preciso y moderno
    - **both**: Combina ambos métodos y elimina duplicados
    
    Retorna:
    - Coordenadas de cada cara detectada
    - Coordenadas de los ojos dentro de cada cara
    - Tiempo de procesamiento
    - Imagen procesada con bounding boxes dibujados (base64)
    """
    try:
        service = FaceDetectionService(session)
        return await service.detect_faces(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
