
from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Localiza o arquivo .env na pasta principal do VetCare
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Configura os dados de conexão
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

# Cria a conexão com o PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Testa a conexão
def testar_conexao():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT current_database()")
        )
        return resultado.scalar()
