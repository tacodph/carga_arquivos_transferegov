from pathlib import Path

from dotenv import load_dotenv
import os
import psycopg2
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
EXTRACTED_DIR = DATA_DIR / "extracted"
LOGS_DIR = PROJECT_ROOT / "logs"

# CSVs/tabelas excluídos da carga (usar somente em bloqueios temporários)
EXCLUDED_CSV_FILES: frozenset[str] = frozenset()
EXCLUDED_TABLES: frozenset[str] = frozenset()

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    schema: str


def get_db_config() -> DbConfig:
    return DbConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        schema=os.getenv("DB_SCHEMA", "transfere_pro_transferegov"),
    )


def get_controle_carga_schema() -> str:
    return os.getenv(
        "CONTROLE_CARGA_SCHEMA",
        "transfere_pro_transferegov",
    )


def get_copy_chunk_rows() -> int:
    value = int(os.getenv("COPY_CHUNK_ROWS", "50000"))
    return max(1000, value)


def get_csv_encoding() -> str:
    """Encoding dos CSVs SICONV (dump público em UTF-8)."""
    return os.getenv("CSV_ENCODING", "utf-8-sig")


def get_connection():
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.name,
        user=cfg.user,
        password=cfg.password,
        options=f"-c search_path={cfg.schema},public",
    )
