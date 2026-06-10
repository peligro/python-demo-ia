# api/services/queue/queue_service.py
"""
Servicio de colas para API - Soporte multi-proveedor (Redis/SQS).
Totalmente independiente del worker.
"""
import os
import json
import logging
from typing import Dict, Any, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from datetime import datetime

# Redis
import redis
# SQS
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@runtime_checkable
class QueueProvider(Protocol):
    """Interface para proveedores de cola"""
    def enqueue(self, payload: Dict[str, Any]) -> str:
        """Encola un mensaje y retorna un ID único"""
        ...


class RedisQueueService:
    """Proveedor Redis Streams"""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        self.stream_name = os.getenv("REDIS_STREAM", "rag-jobs")
    
    def enqueue(self, payload: Dict[str, Any]) -> str:
        try:
            message_id = self.redis.xadd(
                name=self.stream_name,
                fields={"payload": json.dumps(payload, default=str)},
                maxlen=10000
            )
            logger.info(f"📤 [REDIS] Mensaje encolado en {self.stream_name}: {message_id}")
            return f"redis:{message_id}"
        except Exception as e:
            logger.error(f"❌ [REDIS] Error encolando: {e}")
            raise


class SQSQueueService:
    """Proveedor AWS SQS"""
    
    def __init__(self):
        from api.aws.aws import get_conection  # Tu conexión existente
        # Reutilizamos la lógica de conexión de tu aws.py
        if os.getenv('ENVIRONMENT') == 'local':
            self.sqs = boto3.client(
                "sqs",
                region_name=os.getenv('AWS_REGION', 'us-west-2'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                endpoint_url=os.getenv('AWS_SECRET_ACCESS_URL')
            )
        else:
            self.sqs = boto3.client(
                "sqs",
                region_name=os.getenv('AWS_REGION', 'us-west-2'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        
        self.queue_url = os.getenv("SQS_QUEUE_URL")
        if not self.queue_url:
            raise ValueError("SQS_QUEUE_URL no configurada en .env")
    
    def enqueue(self, payload: Dict[str, Any]) -> str:
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(payload, default=str),
                MessageAttributes={
                    "source": {
                        "DataType": "String",
                        "StringValue": "rag-pdf-upload"
                    }
                }
            )
            message_id = response["MessageId"]
            logger.info(f"📤 [SQS] Mensaje encolado en {self.queue_url}: {message_id}")
            return f"sqs:{message_id}"
        except ClientError as e:
            logger.error(f"❌ [SQS] Error encolando: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ [SQS] Error inesperado: {e}")
            raise


class QueueServiceFactory:
    """Factory para instanciar el proveedor correcto"""
    
    _providers = {
        "redis": RedisQueueService,
        "sqs": SQSQueueService,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str = "redis") -> QueueProvider:
        """
        Obtiene una instancia del proveedor de cola.
        
        Args:
            provider_name: "redis" (default) o "sqs"
        
        Returns:
            Instancia de QueueProvider
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            logger.warning(f"Proveedor '{provider_name}' no soportado, usando Redis por defecto")
            provider_class = RedisQueueService
        
        return provider_class()


# Mantener backwards compatibility
class QueueService:
    """Wrapper para compatibilidad con código existente"""
    
    def __init__(self, provider: str = "redis"):
        self._provider = QueueServiceFactory.get_provider(provider)
    
    def enqueue(self, payload: Dict[str, Any]) -> str:
        return self._provider.enqueue(payload)