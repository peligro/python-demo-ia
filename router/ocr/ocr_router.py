#router/ocr/ocr_router.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.ocr import (
    OCRBasicRequest,
    OCRBasicResponse,
    OCRPreprocessRequest,
    OCRPreprocessResponse,
    ExtractDataRequest,
    ExtractDataResponse,
    CompareDocumentsRequest,
    CompareDocumentsResponse,
    ExtractInvoiceResponse
)
from services.ocr.ocr_service import OCRService
from middleware.auth import get_current_user

import os
import tempfile


router = APIRouter(
    prefix="/ocr",
    tags=["Portfolio: OCR"]
)


@router.post(
    "/basic",
    response_model=OCRBasicResponse,
    status_code=status.HTTP_200_OK
)
async def ocr_basic(
    body: OCRBasicRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    OCR Básico - Extrae texto de una imagen
    
    Extrae texto plano de una imagen usando Tesseract OCR.
    Soporta español, inglés o ambos.
    """
    try:
        service = OCRService(session)
        return await service.ocr_basic(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/preprocess",
    response_model=OCRPreprocessResponse,
    status_code=status.HTTP_200_OK
)
async def ocr_preprocess(
    body: OCRPreprocessRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    OCR con Preprocesamiento - Mejora imagen antes de OCR
    
    Aplica técnicas de preprocesamiento para mejorar la precisión del OCR.
    """
    try:
        service = OCRService(session)
        return await service.ocr_preprocess(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/extract",
    response_model=ExtractDataResponse,
    status_code=status.HTTP_200_OK
)
async def extract_data(
    body: ExtractDataRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Extracción de Datos Estructurados
    
    Extrae información específica usando OCR + Regex:
    - Emails, Teléfonos, RUTs, Fechas, URLs
    """
    try:
        service = OCRService(session)
        return await service.extract_data(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/compare",
    response_model=CompareDocumentsResponse,
    status_code=status.HTTP_200_OK
)
async def compare_documents(
    body: CompareDocumentsRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Comparación de Documentos
    
    Compara dos imágenes con texto y retorna diferencias.
    """
    try:
        service = OCRService(session)
        return await service.compare_documents(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ ENDPOINT CORREGIDO: Ahora funciona correctamente con upload de PDF
@router.post(
    "/extract-invoice",
    response_model=ExtractInvoiceResponse,
    status_code=status.HTTP_200_OK
)
async def extract_invoice(
    file: UploadFile = File(..., description="Archivo PDF de factura"),
    current_user: dict = Depends(get_current_user)
):
    """
    Extrae datos estructurados de una factura PDF
    
    Soporta PDFs nativos (texto seleccionable) y PDFs escaneados (OCR).
    Extrae: número de factura, fecha, RUT emisor/cliente, totales, etc.
    """
    # Validar que sea PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF"
        )
    
    # Guardar archivo temporal
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # ✅ CORREGIDO: Pasar session (opcional) y usar await
        service = OCRService()  # session es opcional ahora
        result = await service.extract_invoice(tmp_path, language="spa")
        
        return result
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar factura: {str(e)}")
    finally:
        # ✅ Limpiar archivo temporal
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post(
    "/extract-invoice-static",
    response_model=ExtractInvoiceResponse,
    status_code=status.HTTP_200_OK
)
async def extract_invoice_static(
    file_path: str = "static/pdfs/factura.pdf",
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Extrae datos de factura PDF desde ruta estática (sin upload)
    
    Útil para pruebas con archivos ya guardados en static/pdfs/
    """
    try:
        service = OCRService(session)
        return await service.extract_invoice(file_path, language="spa")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar factura: {str(e)}")