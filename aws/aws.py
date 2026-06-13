# api/aws/aws.py
import boto3
from dotenv import load_dotenv
load_dotenv()
import os


def get_aws_client(service: str = "s3"):
    """
    Cliente genérico de AWS que soporta múltiples servicios.
    
    Args:
        service: Tipo de servicio ("s3", "sqs", "lambda", "dynamodb", etc.)
    
    Returns:
        Cliente boto3 configurado para el servicio especificado
    """
    if os.getenv('ENVIRONMENT') == 'local':
        client = boto3.client(
            service,
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            endpoint_url=os.getenv('AWS_SECRET_ACCESS_URL')
        )
    else:
        client = boto3.client(
            service,
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    return client


# Mantener backwards compatibility
def get_conection():
    """Función legacy - usa get_aws_client('s3') en su lugar"""
    return get_aws_client("s3")