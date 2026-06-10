# api/services/rag_pdf/s3_service.py
import os
import uuid
import logging
import re
from fastapi import UploadFile
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Service:
    """Servicio para subir PDFs a S3/LocalStack"""
    
    def __init__(self):
        from api.aws.aws import get_conection
        self.s3 = get_conection()
        self.bucket = os.getenv("S3_BUCKET_NAME", "curso-udemy")
        self.prefix = os.getenv("S3_RAG_PREFIX", "rag-pdfs/")

    def upload_file(self, file: UploadFile) -> str:
        """Sube archivo a S3 y retorna la clave (key)"""
        # Resetear puntero del archivo por si fue leído previamente
        file.file.seek(0)
        
        file_key = f"{self.prefix}{uuid.uuid4().hex}_{self._sanitize_filename(file.filename)}"
        
        try:
            self.s3.upload_fileobj(
                Fileobj=file.file,
                Bucket=self.bucket,
                Key=file_key,
                ExtraArgs={
                    "ContentType": file.content_type or "application/pdf",
                    "Metadata": {"original-filename": file.filename}
                }
            )
            logger.info(f"✅ PDF subido a S3: {file_key}")
            return file_key
        except ClientError as e:
            logger.error(f"❌ Error subiendo a S3: {e}")
            raise RuntimeError(f"Error al subir archivo: {e}")
        finally:
            # Buena práctica: cerrar el archivo después de usarlo
            file.file.close()

    def _sanitize_filename(self, filename: str) -> str:
        """Limpia el nombre de archivo para evitar problemas en S3"""
        # Reemplazar caracteres problemáticos por guiones
        return re.sub(r'[^\w\.\-]', '_', filename.lower())

    def file_exists(self, file_key: str) -> bool:
        """Verifica si un archivo existe en S3"""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=file_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Genera URL pre-firmada para descarga temporal"""
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': file_key},
            ExpiresIn=expires_in
        )