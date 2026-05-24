from datetime import datetime, timedelta
import bcrypt
from typing import Optional
from fastapi import status, HTTPException


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


