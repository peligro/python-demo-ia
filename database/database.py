#api/database/database.py
from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

is_local = os.getenv("ENVIRONMENT", "production") == "local"
DATABASE_URL = os.getenv('DATABASE_URL')

connect_args = {}
if is_local:
    connect_args["sslmode"] = "disable"
else:
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    echo=False,          
    pool_pre_ping=True,      # <-- Verifica conexión antes de usarla (evita timeout)
    connect_args=connect_args
)

def get_session():
    """Dependency para FastAPI: usa yield para cerrar sesión automáticamente"""
    with Session(engine) as session:
        yield session