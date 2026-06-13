"""
Servicio de colas para API - Soporte multi-proveedor (Redis/SQS/Kafka).
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
# Kafka
from confluent_kafka import Producer, KafkaError

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


class KafkaQueueService:
    """Proveedor Apache Kafka"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.topic = os.getenv("KAFKA_TOPIC_JOBS", "rag-pdf-jobs")
        
        # Configuración del producer
        self.producer = Producer({
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': 'rag-pdf-api',
            'acks': 'all',  # Espera confirmación de todos los replicas
            'retries': 5,
            'retry.backoff.ms': 500,
            'linger.ms': 5,  # Espera 5ms para agrupar mensajes
            'batch.num.messages': 100,
        })
        
        logger.info(f"✅ [KAFKA] Producer inicializado: {self.bootstrap_servers}")
    
    def delivery_report(self, err, msg):
        """Callback llamado cuando el mensaje es entregado (o falla)"""
        if err is not None:
            logger.error(f"❌ [KAFKA] Error entregando mensaje: {err}")
        else:
            logger.debug(
                f"✅ [KAFKA] Mensaje entregado a {msg.topic()} "
                f"partición [{msg.partition()}] @ offset {msg.offset()}"
            )
    
    def enqueue(self, payload: Dict[str, Any]) -> str:
        try:
            # Generar key para particionado consistente (opcional)
            key = str(payload.get("job_id", ""))
            
            # Serializar payload
            value = json.dumps(payload, default=str).encode('utf-8')
            
            # Enviar mensaje asíncrono
            self.producer.produce(
                topic=self.topic,
                key=key.encode('utf-8') if key else None,
                value=value,
                callback=self.delivery_report,
                headers=[
                    ('source', b'rag-pdf-upload'),
                    ('timestamp', datetime.utcnow().isoformat().encode('utf-8'))
                ]
            )
            
            # Flush para asegurar entrega (timeout 5s)
            self.producer.flush(timeout=5.0)
            
            # Generar ID único para el mensaje
            message_id = f"kafka:{datetime.utcnow().timestamp()}-{payload.get('job_id')}"
            
            logger.info(
                f"📤 [KAFKA] Mensaje encolado en {self.topic}: "
                f"job_id={payload.get('job_id')}"
            )
            return message_id
            
        except KafkaError as e:
            logger.error(f"❌ [KAFKA] Error encolando: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ [KAFKA] Error inesperado: {e}")
            raise
    
    def __del__(self):
        """Cleanup al destruir el producer"""
        if hasattr(self, 'producer'):
            self.producer.flush(timeout=5.0)


class QueueServiceFactory:
    """Factory para instanciar el proveedor correcto"""
    
    _providers = {
        "redis": RedisQueueService,
        "sqs": SQSQueueService,
        "kafka": KafkaQueueService,  # ← NUEVO
    }
    
    @classmethod
    def get_provider(cls, provider_name: str = "redis") -> QueueProvider:
        """
        Obtiene una instancia del proveedor de cola.
        
        Args:
            provider_name: "redis" (default), "sqs" o "kafka"
        
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