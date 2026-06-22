#services/ocr/ocr_service.py
import time
import cv2
import numpy as np
import os
import base64
import re
import pytesseract
from typing import List, Dict, Any, Optional
from sqlmodel import Session
from PIL import Image
import pdfplumber
from schemas.ocr import (
    OCRBasicRequest,
    OCRBasicResponse,
    OCRPreprocessRequest,
    OCRPreprocessResponse,
    ExtractDataRequest,
    ExtractDataResponse,
    ExtractedData,
    CompareDocumentsRequest,
    CompareDocumentsResponse,
    ExtractInvoiceRequest,
    ExtractInvoiceResponse,
    InvoiceData
)
import pathlib


class OCRService:
    """
    Servicio de OCR (Optical Character Recognition) con Tesseract.
    Soporta 5 funcionalidades:
    1. OCR Básico - Extracción simple de texto
    2. OCR con Preprocesamiento - Mejora de imagen antes de OCR
    3. Extracción de Datos - Regex para emails, teléfonos, RUTs
    4. Comparación de Documentos - Diferencias entre dos imágenes
    5. Extracción de Facturas - Extracción estructurada de facturas PDF
    """
    
    def __init__(self, session: Session = None):
        self.session = session
        
        # Verificar que Tesseract esté instalado
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract OCR cargado correctamente - Versión: {version}")
        except Exception as e:
            print(f"❌ ERROR: Tesseract OCR no está disponible: {e}")
            raise
    
    async def ocr_basic(self, request: OCRBasicRequest) -> OCRBasicResponse:
        """OCR básico - Extrae texto de imagen"""
        start_time = time.time()
        
        # Construir ruta absoluta
        base_dir = pathlib.Path(__file__).parent.parent.parent
        full_path = base_dir / request.image_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Imagen no encontrada: {request.image_path}")
        
        # Cargar imagen con PIL
        image = Image.open(full_path)
        
        # Configurar Tesseract con parámetros optimizados
        custom_config = r'--oem 3 --psm 6'  # LSTM + Single block
        
        # Extraer texto con Tesseract
        extracted_text = pytesseract.image_to_string(
            image, 
            lang=request.language,
            config=custom_config
        )
        
        # Calcular confianza (usando datos de Tesseract)
        data = pytesseract.image_to_data(
            image, 
            lang=request.language, 
            output_type=pytesseract.Output.DICT,
            config=custom_config
        )
        confidences = [float(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Contar palabras
        word_count = len(extracted_text.split())
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return OCRBasicResponse(
            image_path=request.image_path,
            extracted_text=extracted_text.strip(),
            language_used=request.language,
            confidence=round(avg_confidence, 2),
            word_count=word_count,
            processing_time_ms=processing_time_ms
        )
    
    async def ocr_preprocess(self, request: OCRPreprocessRequest) -> OCRPreprocessResponse:
        """OCR con preprocesamiento mejorado"""
        start_time = time.time()
        
        # Construir ruta absoluta
        base_dir = pathlib.Path(__file__).parent.parent.parent
        full_path = base_dir / request.image_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Imagen no encontrada: {request.image_path}")
        
        # Cargar imagen con OpenCV
        image = cv2.imread(str(full_path))
        
        # Aplicar preprocesamiento según el tipo
        preprocessing_applied = []
        
        if request.preprocessing == "auto":
            image = self._smart_preprocess(image)
            preprocessing_applied = ["smart_auto"]
        elif request.preprocessing == "grayscale":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            preprocessing_applied = ["grayscale"]
        elif request.preprocessing == "binarize":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            preprocessing_applied = ["grayscale", "binarize"]
        elif request.preprocessing == "denoise":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            preprocessing_applied = ["grayscale", "denoise"]
        elif request.preprocessing == "deskew":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = self._deskew(image)
            preprocessing_applied = ["grayscale", "deskew"]
        elif request.preprocessing == "enhance":
            image = self._enhance_for_ocr(image)
            preprocessing_applied = ["enhance"]
        
        # Convertir a PIL para Tesseract
        pil_image = Image.fromarray(image)
        
        # Configurar Tesseract con parámetros optimizados
        custom_config = r'--oem 3 --psm 6'
        
        # Extraer texto
        extracted_text = pytesseract.image_to_string(
            pil_image, 
            lang=request.language,
            config=custom_config
        )
        
        # Calcular confianza
        data = pytesseract.image_to_data(
            pil_image, 
            lang=request.language, 
            output_type=pytesseract.Output.DICT,
            config=custom_config
        )
        confidences = [float(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Contar palabras
        word_count = len(extracted_text.split())
        
        # Generar imagen preprocesada en base64
        preprocessed_image_url = self._image_to_base64(image)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return OCRPreprocessResponse(
            image_path=request.image_path,
            preprocessing_applied=", ".join(preprocessing_applied),
            extracted_text=extracted_text.strip(),
            language_used=request.language,
            confidence=round(avg_confidence, 2),
            word_count=word_count,
            processing_time_ms=processing_time_ms,
            preprocessed_image_url=preprocessed_image_url
        )
    
    async def extract_data(self, request: ExtractDataRequest) -> ExtractDataResponse:
        """Extracción de datos estructurados usando regex"""
        start_time = time.time()
        
        base_dir = pathlib.Path(__file__).parent.parent.parent
        full_path = base_dir / request.image_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Imagen no encontrada: {request.image_path}")
        
        image = Image.open(full_path)
        raw_text = pytesseract.image_to_string(image, lang=request.language)
        
        # Extraer patrones según lo solicitado
        extracted_data = ExtractedData()
        
        if "email" in request.extract_patterns:
            extracted_data.emails = self._extract_emails(raw_text)
        
        if "phone" in request.extract_patterns:
            extracted_data.phones = self._extract_phones(raw_text)
        
        if "rut" in request.extract_patterns:
            extracted_data.ruts = self._extract_ruts(raw_text)
        
        if "date" in request.extract_patterns:
            extracted_data.dates = self._extract_dates(raw_text)
        
        if "url" in request.extract_patterns:
            extracted_data.urls = self._extract_urls(raw_text)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ExtractDataResponse(
            image_path=request.image_path,
            extracted_data=extracted_data,
            raw_text=raw_text.strip(),
            language_used=request.language,
            processing_time_ms=processing_time_ms
        )
    
    async def compare_documents(self, request: CompareDocumentsRequest) -> CompareDocumentsResponse:
        """Compara dos documentos y retorna diferencias"""
        start_time = time.time()
        
        base_dir = pathlib.Path(__file__).parent.parent.parent
        
        # Cargar primera imagen
        path_1 = base_dir / request.image_path_1
        if not os.path.exists(path_1):
            raise FileNotFoundError(f"Imagen 1 no encontrada: {request.image_path_1}")
        
        # Cargar segunda imagen
        path_2 = base_dir / request.image_path_2
        if not os.path.exists(path_2):
            raise FileNotFoundError(f"Imagen 2 no encontrada: {request.image_path_2}")
        
        # Extraer texto de ambas imágenes
        image_1 = Image.open(path_1)
        image_2 = Image.open(path_2)
        
        text_1 = pytesseract.image_to_string(image_1, lang=request.language).strip()
        text_2 = pytesseract.image_to_string(image_2, lang=request.language).strip()
        
        # Calcular similitud
        similarity_score = self._calculate_similarity(text_1, text_2)
        
        # Encontrar diferencias
        differences = self._find_differences(text_1, text_2)
        
        # Determinar si son idénticos
        are_identical = text_1 == text_2
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return CompareDocumentsResponse(
            image_path_1=request.image_path_1,
            image_path_2=request.image_path_2,
            text_1=text_1,
            text_2=text_2,
            similarity_score=round(similarity_score, 2),
            differences=differences,
            are_identical=are_identical,
            processing_time_ms=processing_time_ms
        )
    
    # ✅ MÉTODO CORREGIDO: Ahora acepta ruta directa (string) o request
    async def extract_invoice(self, file_path: str, language: str = "spa") -> ExtractInvoiceResponse:
        """Extrae datos estructurados de una factura PDF"""
        start_time = time.time()
        
        # Construir ruta absoluta
        base_dir = pathlib.Path(__file__).parent.parent.parent
        
        # Si la ruta es absoluta (tempfile), usarla directamente
        if os.path.isabs(file_path):
            full_path = pathlib.Path(file_path)
        else:
            full_path = base_dir / file_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"PDF no encontrado: {file_path}")
        
        # Extraer texto del PDF
        invoice_data = InvoiceData()
        full_text = ""
        
        try:
            with pdfplumber.open(full_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n"
                    
                    # Extraer tablas si existen
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            for row in table:
                                if row:
                                    full_text += " | ".join(str(cell) for cell in row if cell) + "\n"
            
            # Procesar texto extraído
            invoice_data = self._parse_invoice_text(full_text)
            invoice_data.raw_text = full_text.strip()
            
        except Exception as e:
            # Si falla pdfplumber, intentar con OCR
            print(f"⚠️ Error al extraer PDF con pdfplumber: {e}")
            print("🔄 Intentando con OCR...")
            
            # Convertir PDF a imagen y aplicar OCR
            invoice_data = await self._extract_invoice_with_ocr(full_path, language)
            invoice_data.raw_text = full_text.strip()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ExtractInvoiceResponse(
            file_path=str(file_path),
            invoice_data=invoice_data,
            processing_time_ms=processing_time_ms
        )

    async def _extract_invoice_with_ocr(self, pdf_path: pathlib.Path, language: str) -> InvoiceData:
        """Extrae datos de PDF usando OCR (para PDFs escaneados)"""
        try:
            from pdf2image import convert_from_path
            
            # Convertir PDF a imágenes
            images = convert_from_path(str(pdf_path), dpi=300)
            
            full_text = ""
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang=language)
                full_text += text + "\n"
            
            return self._parse_invoice_text(full_text)
            
        except ImportError:
            print("❌ pdf2image no está instalado. Instala: pip install pdf2image")
            raise ValueError("Se requiere pdf2image para OCR en PDFs escaneados")
        except Exception as e:
            print(f"❌ Error en OCR de PDF: {e}")
            return InvoiceData(raw_text="Error al procesar PDF")

    def _parse_invoice_text(self, text: str) -> InvoiceData:
        """Analiza texto de factura y extrae datos estructurados"""
        invoice_data = InvoiceData()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            line_upper = line.upper()
            
            # Extraer RUT/RUC
            if 'RUT' in line_upper or 'RUC' in line_upper:
                rut_match = re.search(r'(?:RUT|RUC)[:\s\.]+(\d{1,3}\.?\d{3}\.?\d{3}[-.]?\d)', line, re.IGNORECASE)
                if rut_match:
                    rut = rut_match.group(1)
                    if not invoice_data.ruc_emitter:
                        invoice_data.ruc_emitter = rut
                    elif not invoice_data.ruc_client:
                        invoice_data.ruc_client = rut
            
            # Extraer número de factura
            if any(x in line_upper for x in ['FACTURA', 'INVOICE', 'N°', 'NUMERO', 'BOLETA']):
                number_match = re.search(r'(?:N°|NUMERO|FACTURA|BOLETA)[:\s]+([A-Z0-9-]+)', line, re.IGNORECASE)
                if number_match:
                    invoice_data.invoice_number = number_match.group(1)
            
            # Extraer fecha
            if any(x in line_upper for x in ['FECHA', 'DATE', 'EMISIÓN', 'EMISION']):
                date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', line)
                if date_match:
                    if not invoice_data.invoice_date:
                        invoice_data.invoice_date = date_match.group(1)
            
            # Extraer totales (formato chileno y peruano)
            total_patterns = [
                (r'TOTAL[:\s]+\$?\s*([\d.,]+)', 'total'),
                (r'SUBTOTAL[:\s]+\$?\s*([\d.,]+)', 'subtotal'),
                (r'NETO[:\s]+\$?\s*([\d.,]+)', 'subtotal'),
                (r'IVA[:\s]+\$?\s*([\d.,]+)', 'tax'),
                (r'IGV[:\s]+\$?\s*([\d.,]+)', 'tax'),
                (r'IMPUESTO[:\s]+\$?\s*([\d.,]+)', 'tax'),
            ]
            
            for pattern, field in total_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Limpiar formato de número (quitar puntos de miles, reemplazar coma por punto)
                    value_str = match.group(1).replace('.', '').replace(',', '.')
                    try:
                        value = float(value_str)
                        if field == 'total':
                            invoice_data.total = value
                        elif field == 'subtotal':
                            invoice_data.subtotal = value
                        elif field == 'tax':
                            invoice_data.tax = value
                    except ValueError:
                        pass
            
            # Extraer nombre emisor (primeras líneas con "Razón Social" o nombre empresa)
            if any(x in line_upper for x in ['RAZÓN SOCIAL', 'RAZON SOCIAL', 'RAZ. SOCIAL']):
                name_match = re.search(r'(?:RAZÓN SOCIAL|RAZON SOCIAL|RAZ\. SOCIAL)[:\s]+(.+)', line, re.IGNORECASE)
                if name_match:
                    invoice_data.emitter_name = name_match.group(1).strip()
            
            # Extraer dirección
            if any(x in line_upper for x in ['DIRECCIÓN', 'DIRECCION', 'DIR.']):
                addr_match = re.search(r'(?:DIRECCIÓN|DIRECCION|DIR\.?)[:\s]+(.+)', line, re.IGNORECASE)
                if addr_match:
                    if not invoice_data.emitter_address:
                        invoice_data.emitter_address = addr_match.group(1).strip()
        
        return invoice_data
    
    # ========================================================================
    # MÉTODOS PRIVADOS DE PREPROCESAMIENTO
    # ========================================================================
    
    def _smart_preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocesamiento inteligente que detecta el tipo de imagen"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        contrast = gray.std()
        
        if contrast < 50:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        return binary
    
    def _enhance_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Mejora específica para texto en fondos complejos"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        edges = cv2.Canny(enhanced, 50, 150)
        
        kernel = np.ones((3,3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(
            dilated_edges, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        mask = np.zeros_like(enhanced)
        for contour in contours:
            if cv2.contourArea(contour) > 100:
                cv2.drawContours(mask, [contour], -1, 255, -1)
        
        result = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        result = cv2.bitwise_and(result, result, mask=mask)
        
        return result
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Corrige la inclinación de la imagen"""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convierte imagen a base64"""
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    
    # ========================================================================
    # MÉTODOS PRIVADOS DE EXTRACCIÓN DE PATRONES
    # ========================================================================
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extrae emails del texto"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(pattern, text)))
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extrae números de teléfono (formato chileno e internacional)"""
        patterns = [
            r'\+?56\s?9\s?\d{4}\s?\d{4}',
            r'9\s?\d{4}\s?\d{4}',
            r'\+?\d{1,3}\s?\d{9,10}',
        ]
        
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def _extract_ruts(self, text: str) -> List[str]:
        """Extrae RUTs chilenos"""
        pattern = r'\d{1,3}\.?\d{3}\.?\d{3}[-.]?\d'
        return list(set(re.findall(pattern, text)))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrae fechas en varios formatos"""
        patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}\.\d{2}\.\d{4}',
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))
        
        return list(set(dates))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extrae URLs del texto"""
        pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return list(set(re.findall(pattern, text)))
    
    # ========================================================================
    # MÉTODOS PRIVADOS DE COMPARACIÓN
    # ========================================================================
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos (0-100)"""
        if not text1 or not text2:
            return 0.0
        
        import difflib
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio() * 100
    
    def _find_differences(self, text1: str, text2: str) -> List[str]:
        """Encuentra diferencias entre dos textos"""
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        
        differences = []
        
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            if line1 != line2:
                if line1 and not line2:
                    differences.append(f"Línea {i+1} solo en documento 1: {line1[:50]}...")
                elif line2 and not line1:
                    differences.append(f"Línea {i+1} solo en documento 2: {line2[:50]}...")
                else:
                    differences.append(f"Línea {i+1} diferente:")
                    differences.append(f"  Doc1: {line1[:50]}...")
                    differences.append(f"  Doc2: {line2[:50]}...")
        
        return differences[:10]