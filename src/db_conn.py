import logging
import time

import psycopg2

from src.config import get_connection

logger = logging.getLogger(__name__)

_CONNECTION_ERRORS = (psycopg2.InterfaceError, psycopg2.OperationalError, ConnectionError)
_RECONNECT_RETRIES = 5
_RECONNECT_DELAY_S = 3.0


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

    last_exc: Exception | None = None
    for attempt in range(1, _RECONNECT_RETRIES + 1):
        try:
            return get_connection()
        except (ConnectionError, *_CONNECTION_ERRORS, OSError) as exc:
            last_exc = exc
            if attempt < _RECONNECT_RETRIES:
                logger.warning(
                    "Reconexão PostgreSQL falhou (tentativa %s/%s): %s; "
                    "aguardando %.0fs...",
                    attempt,
                    _RECONNECT_RETRIES,
                    exc,
                    _RECONNECT_DELAY_S * attempt,
                )
                time.sleep(_RECONNECT_DELAY_S * attempt)
    if last_exc is not None:
        raise last_exc
    raise ConnectionError("Falha ao reconectar ao PostgreSQL")


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
