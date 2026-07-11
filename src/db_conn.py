import logging

import psycopg2

from src.config import get_connection

logger = logging.getLogger(__name__)

_CONNECTION_ERRORS = (psycopg2.InterfaceError, psycopg2.OperationalError)


def is_connection_ok(conn) -> bool:
    if conn is None or conn.closed:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except _CONNECTION_ERRORS:
        return False


def reconnect(conn=None):
    if conn is not None:
        try:
            if not conn.closed:
                conn.close()
        except Exception:
            pass
    return get_connection()


def ensure_connection(conn):
    if is_connection_ok(conn):
        return conn
    logger.warning("Conexão PostgreSQL perdida; reconectando...")
    return reconnect(conn)


def safe_rollback(conn) -> None:
    if conn is None or conn.closed:
        return
    try:
        conn.rollback()
    except _CONNECTION_ERRORS:
        pass
