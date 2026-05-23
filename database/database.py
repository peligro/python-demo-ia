from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

is_local = os.getenv("ENVIRONMENT", "production") == "local"

DATABASE_URL=os.getenv('DATABASE_URL')

connect_args = {}
if is_local:
    connect_args["sslmode"] = "disable"  # No hay SSL en local
else:
    connect_args["sslmode"] = "require"  # SSL obligatorio en producción

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def get_session():
    return Session(engine)