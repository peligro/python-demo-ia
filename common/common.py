#api/common/common.py
from datetime import datetime, timedelta
import bcrypt
from typing import Optional
from fastapi import status, HTTPException
from fastapi.responses import JSONResponse


import os
from dotenv import load_dotenv
load_dotenv()

#email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def formatear_fecha(fecha: datetime) -> str:
    return fecha.strftime("%d/%m/%Y")


def generate_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def send_mail(html: str, asunto: str, para: str):
    msg = MIMEMultipart('alternative')  # ✅ Corregido
    msg['Subject'] = asunto
    msg['From'] = os.getenv('SMTP_USER')
    msg['To'] = para
    msg.attach(MIMEText(html, 'html'))

    # ✅ Conexión segura con STARTTLS
    server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT', 587)))
    server.starttls()
    server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    server.sendmail(os.getenv('SMTP_USER'), para, msg.as_string())
    server.quit()


def format_error_response(message: str = "Ocurrió un error inesperado", detail: str = None, status_code: int = 500):
    """
    Formatea respuesta de error según ENVIRONMENT.
    El campo 'detalle' solo se incluye en local/staging.
    """
    env = os.getenv("ENVIRONMENT", "production")
    
    response = {
        "estado": "error",
        "mensaje": message
    }
    
    # Solo incluir detalle en entornos no productivos
    if env in ["local", "staging"] and detail:
        response["detalle"] = detail
    
    return JSONResponse(status_code=status_code, content=response)