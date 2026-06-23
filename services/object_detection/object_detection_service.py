#services/object_detection/object_detection_service.py
import time
import cv2
import numpy as np
import os
import base64
import pathlib
from typing import List, Optional
from sqlmodel import Session

from schemas.object_detection import (
    ObjectDetectionRequest,
    ObjectDetectionResponse,
    ObjectDetection,
    BoundingBox,
)


# Clases COCO (80 clases)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


class ObjectDetectionService:
    """
    Servicio de detección de objetos usando YOLOv8.
    
    Soporta los modelos:
    - yolov8n.pt (nano) - Más rápido, menor precisión
    - yolov8s.pt (small) - Balance velocidad/precisión
    - yolov8m.pt (medium) - Mayor precisión
    - yolov8l.pt (large) - Alta precisión
    - yolov8x.pt (xlarge) - Máxima precisión, más lento
    """
    
    # Cache de modelos cargados para no recargar en cada request
    _model_cache: dict = {}
    
    def __init__(self, session: Session = None):
        self.session = session
    
    def _load_model(self, model_name: str):
        """Carga el modelo YOLOv8 (con caché)"""
        if model_name not in self._model_cache:
            print(f"📦 Cargando modelo {model_name}...")
            try:
                from ultralytics import YOLO
                model = YOLO(model_name)
                self._model_cache[model_name] = model
                print(f"✅ Modelo {model_name} cargado correctamente")
            except Exception as e:
                print(f"❌ Error al cargar modelo {model_name}: {e}")
                raise
        return self._model_cache[model_name]
    
    async def detect_objects(self, request: ObjectDetectionRequest) -> ObjectDetectionResponse:
        """Detecta objetos en una imagen usando YOLOv8"""
        start_time = time.time()
        
        # Construir ruta absoluta
        base_dir = pathlib.Path(__file__).parent.parent.parent
        full_path = base_dir / request.image_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Imagen no encontrada: {request.image_path}")
        
        # Cargar imagen
        image = cv2.imread(str(full_path))
        if image is None:
            raise ValueError(f"No se pudo leer la imagen: {request.image_path}")
        
        image_height, image_width = image.shape[:2]
        
        # Cargar modelo
        model = self._load_model(request.model)
        
        # Ejecutar predicción
        # verbose=False para no imprimir logs de YOLO
        results = model(
            str(full_path),
            conf=request.confidence_threshold,
            verbose=False,
            device='cpu'  # Forzar CPU (cambiar a 'cuda' si hay GPU)
        )
        
        # Procesar resultados
        detections: List[ObjectDetection] = []
        result = results[0]  # Solo una imagen
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                # Obtener coordenadas (xyxy: x1, y1, x2, y2)
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                
                # Convertir a formato x, y, width, height
                x = int(x1)
                y = int(y1)
                width = int(x2 - x1)
                height = int(y2 - y1)
                
                # Obtener clase y confianza
                class_id = int(boxes.cls[i].item())
                confidence = float(boxes.conf[i].item())
                class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f"unknown_{class_id}"
                
                detections.append(ObjectDetection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=round(confidence, 4),
                    bounding_box=BoundingBox(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                    )
                ))
        
        # Generar imagen procesada con bounding boxes
        processed_image_url = self._draw_detections(image.copy(), detections)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ObjectDetectionResponse(
            image_path=request.image_path,
            model_used=request.model,
            confidence_threshold=request.confidence_threshold,
            total_objects=len(detections),
            detections=detections,
            image_width=image_width,
            image_height=image_height,
            processing_time_ms=processing_time_ms,
            processed_image_url=processed_image_url,
        )
    
    def _draw_detections(self, image: np.ndarray, detections: List[ObjectDetection]) -> str:
        """Dibuja las detecciones en la imagen y retorna como base64"""
        # Colores para cada clase (usando un hash simple para consistencia)
        colors = {}
        
        for det in detections:
            # Generar color único por clase
            if det.class_id not in colors:
                # Usar HSV para generar colores distintivos
                hue = (det.class_id * 137) % 180
                color_bgr = tuple(int(c) for c in cv2.cvtColor(
                    np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR
                )[0][0])
                colors[det.class_id] = color_bgr
            
            color = colors[det.class_id]
            
            bbox = det.bounding_box
            
            # Dibujar rectángulo
            cv2.rectangle(
                image,
                (bbox.x, bbox.y),
                (bbox.x + bbox.width, bbox.y + bbox.height),
                color,
                2
            )
            
            # Etiqueta con clase y confianza
            label = f"{det.class_name} {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Fondo para la etiqueta
            cv2.rectangle(
                image,
                (bbox.x, bbox.y - label_size[1] - 10),
                (bbox.x + label_size[0], bbox.y),
                color,
                -1
            )
            
            # Texto de la etiqueta
            cv2.putText(
                image,
                label,
                (bbox.x, bbox.y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        # Convertir a base64
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"