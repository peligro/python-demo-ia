#services/face_detection/face_detection_service.py

import time
import cv2
import numpy as np
import os
import base64
from typing import List
from sqlmodel import Session
from schemas.face_detection import (
    FaceDetectionRequest,
    FaceDetectionResponse,
    FaceDetection,
    BoundingBox,
    EyeDetection
)
import pathlib


class FaceDetectionService:
    """
    Servicio de detección de caras y ojos usando Haar Cascade (OpenCV)
    """
    
    FACE_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    EYE_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_eye.xml'
    
    def __init__(self, session: Session):
        self.session = session
        
        self.face_cascade = cv2.CascadeClassifier(self.FACE_CASCADE_PATH)
        self.eye_cascade = cv2.CascadeClassifier(self.EYE_CASCADE_PATH)
        
        if self.face_cascade.empty():
            print("❌ ERROR: No se pudo cargar haarcascade_frontalface_default.xml")
        else:
            print("✅ Haar Cascade cargado correctamente")
    
    async def detect_faces(self, request: FaceDetectionRequest) -> FaceDetectionResponse:
        start_time = time.time()
        
        base_dir = pathlib.Path(__file__).parent.parent.parent
        full_path = base_dir / request.image_path

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Imagen no encontrada: {request.image_path}")
        
        image = cv2.imread(full_path)
        if image is None:
            raise ValueError(f"No se pudo leer la imagen: {request.image_path}")
        
        image_height, image_width = image.shape[:2]
        
        # Usar solo Haar Cascade
        faces = self._detect_haarcascade(image, request)
        method_used = "haarcascade"
        
        processed_image_url = self._draw_detections(image.copy(), faces)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return FaceDetectionResponse(
            image_path=request.image_path,
            method_used=method_used,
            total_faces_detected=len(faces),
            faces=faces,
            image_width=image_width,
            image_height=image_height,
            processing_time_ms=processing_time_ms,
            processed_image_url=processed_image_url
        )
    
    def _detect_haarcascade(self, image: np.ndarray, request: FaceDetectionRequest) -> List[FaceDetection]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        scale_factor = request.scale_factor or 1.05
        min_neighbors = request.min_neighbors or 3
        min_face_size = request.min_face_size or 30
        
        print(f"🔍 Parámetros Haar: scaleFactor={scale_factor}, minNeighbors={min_neighbors}, minSize={min_face_size}")
        
        faces_rect = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(min_face_size, min_face_size),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        print(f"✅ Caras detectadas: {len(faces_rect)}")
        
        faces: List[FaceDetection] = []
        
        for idx, (x, y, w, h) in enumerate(faces_rect):
            roi_gray = gray[y:y+h, x:x+w]
            
            eyes_rect = self.eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(15, 15)
            )
            
            left_eye = None
            right_eye = None
            eyes_detected = 0
            
            if len(eyes_rect) > 0:
                eyes_sorted = sorted(eyes_rect, key=lambda e: e[0])
                
                if len(eyes_sorted) >= 2:
                    ex, ey, ew, eh = eyes_sorted[0]
                    left_eye = BoundingBox(
                        x=int(x + ex), y=int(y + ey),
                        width=int(ew), height=int(eh),
                        confidence=0.9
                    )
                    
                    ex, ey, ew, eh = eyes_sorted[1]
                    right_eye = BoundingBox(
                        x=int(x + ex), y=int(y + ey),
                        width=int(ew), height=int(eh),
                        confidence=0.9
                    )
                    eyes_detected = 2
                elif len(eyes_sorted) == 1:
                    ex, ey, ew, eh = eyes_sorted[0]
                    left_eye = BoundingBox(
                        x=int(x + ex), y=int(y + ey),
                        width=int(ew), height=int(eh),
                        confidence=0.8
                    )
                    eyes_detected = 1
            
            faces.append(FaceDetection(
                face_id=idx + 1,
                bounding_box=BoundingBox(
                    x=int(x), y=int(y),
                    width=int(w), height=int(h),
                    confidence=0.85
                ),
                eyes=EyeDetection(
                    left_eye=left_eye,
                    right_eye=right_eye,
                    total_eyes_detected=eyes_detected
                )
            ))
        
        return faces
    
    def _draw_detections(self, image: np.ndarray, faces: List[FaceDetection]) -> str:
        for face in faces:
            cv2.rectangle(
                image,
                (face.bounding_box.x, face.bounding_box.y),
                (face.bounding_box.x + face.bounding_box.width, 
                 face.bounding_box.y + face.bounding_box.height),
                (0, 255, 0),
                2
            )
            
            label = f"Face {face.face_id} ({face.bounding_box.confidence:.2f})"
            cv2.putText(
                image, label,
                (face.bounding_box.x, face.bounding_box.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 2
            )
            
            if face.eyes.left_eye:
                cv2.rectangle(
                    image,
                    (face.eyes.left_eye.x, face.eyes.left_eye.y),
                    (face.eyes.left_eye.x + face.eyes.left_eye.width,
                     face.eyes.left_eye.y + face.eyes.left_eye.height),
                    (255, 0, 0), 2
                )
            
            if face.eyes.right_eye:
                cv2.rectangle(
                    image,
                    (face.eyes.right_eye.x, face.eyes.right_eye.y),
                    (face.eyes.right_eye.x + face.eyes.right_eye.width,
                     face.eyes.right_eye.y + face.eyes.right_eye.height),
                    (255, 0, 0), 2
                )
        
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"