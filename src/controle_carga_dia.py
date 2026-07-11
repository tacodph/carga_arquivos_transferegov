import logging
from datetime import date

from src.controle_carga import (
    STATUS_CORRIGIDO_SUCESSO,
    STATUS_ERRO,
    STATUS_EXECUTANDO,
    STATUS_PARCIAL,
    STATUS_SUCESSO,
    is_controle_enabled,
)
from src.config import get_controle_carga_schema

logger = logging.getLogger(__name__)

CARGA_DIA_ENDPOINT = "pipeline/siconv-dia"


def qualified_carga_dia_table() -> str:
    schema = get_controle_carga_schema()
    return f'"{schema}"."controle_carga_dia"'


def carga_dia_table_exists(conn) -> bool:
    schema = get_controle_carga_schema()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = 'controle_carga_dia'
            """,
            (schema,),
        )
        exists = cur.fetchone() is not None
    if not exists:
        logger.warning(
            "Tabela %s.controle_carga_dia não encontrada; controle diário desabilitado",
            schema,
        )
    return exists


def _next_seq_execucao_dia(conn, dt_carga: date) -> int:
    table = qualified_carga_dia_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COALESCE(MAX(seq_execucao_dia), 0) + 1
            FROM {table}
            WHERE dt_carga = %s
            """,
            (dt_carga,),
        )
        return int(cur.fetchone()[0])


def _get_last_finished_status_dia(conn, dt_carga: date, exclude_id: int | None = None) -> str | None:
    table = qualified_carga_dia_table()
    query = f"""
        SELECT status
        FROM {table}
        WHERE dt_carga = %s AND dt_fim IS NOT NULL
    """
    params: list = [dt_carga]
    if exclude_id is not None:
        query += " AND id <> %s"
        params.append(exclude_id)
    query += " ORDER BY dt_inicio DESC LIMIT 1"
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return row[0] if row else None


def start_carga_dia(
    conn,
    qtd_arquivos_extraidos: int,
    log_arquivo: str | None = None,
    dt_carga: date | None = None,
) -> int | None:
    if not is_controle_enabled() or not carga_dia_table_exists(conn):
        return None

    dt_carga = dt_carga or date.today()
    seq = _next_seq_execucao_dia(conn, dt_carga)
    table = qualified_carga_dia_table()

    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {table} (
                dt_carga, seq_execucao_dia, dt_inicio, status,
                qtd_arquivos_extraidos, log_arquivo
            )
            VALUES (%s, %s, now(), %s, %s, %s)
            RETURNING id
            """,
            (dt_carga, seq, STATUS_EXECUTANDO, qtd_arquivos_extraidos, log_arquivo),
        )
        carga_dia_id = cur.fetchone()[0]
    conn.commit()
    logger.info(
        "controle_carga_dia id=%s dt_carga=%s seq=%s extraidos=%s",
        carga_dia_id,
        dt_carga,
        seq,
        qtd_arquivos_extraidos,
    )
    return carga_dia_id


def _resolve_status_dia(
    conn,
    dt_carga: date,
    carga_dia_id: int,
    carregados: int,
    erros: int,
) -> str:
    if erros == 0 and carregados > 0:
        previous = _get_last_finished_status_dia(conn, dt_carga, exclude_id=carga_dia_id)
        if previous in {STATUS_ERRO, STATUS_PARCIAL}:
            return STATUS_CORRIGIDO_SUCESSO
        return STATUS_SUCESSO
    if erros > 0 and carregados > 0:
        return STATUS_PARCIAL
    if erros > 0:
        return STATUS_ERRO
    return STATUS_PARCIAL


def finish_carga_dia(
    conn,
    carga_dia_id: int | None,
    qtd_arquivos_carregados: int,
    qtd_arquivos_erro: int,
    qtd_arquivos_pulados: int = 0,
    mensagem: str | None = None,
    dt_carga: date | None = None,
) -> None:
    if carga_dia_id is None:
        return

    dt_carga = dt_carga or date.today()
    status = _resolve_status_dia(
        conn, dt_carga, carga_dia_id, qtd_arquivos_carregados, qtd_arquivos_erro
    )
    if status == STATUS_PARCIAL and not mensagem:
        mensagem = (
            f"{qtd_arquivos_carregados} carregado(s), "
            f"{qtd_arquivos_erro} erro(s), "
            f"{qtd_arquivos_pulados} pulado(s)"
        )

    table = qualified_carga_dia_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE {table}
            SET dt_fim = now(),
                status = %s,
                qtd_arquivos_carregados = %s,
                qtd_arquivos_erro = %s,
                qtd_arquivos_pulados = %s,
                mensagem = %s
            WHERE id = %s
            """,
            (
                status,
                qtd_arquivos_carregados,
                qtd_arquivos_erro,
                qtd_arquivos_pulados,
                mensagem[:4000] if mensagem else None,
                carga_dia_id,
            ),
        )
    conn.commit()
    logger.info(
        "controle_carga_dia id=%s finalizado status=%s carregados=%s erros=%s",
        carga_dia_id,
        status,
        qtd_arquivos_carregados,
        qtd_arquivos_erro,
    )


def get_carga_dia_by_id(conn, carga_dia_id: int) -> dict | None:
    if not carga_dia_table_exists(conn):
        return None
    table = qualified_carga_dia_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, dt_carga, seq_execucao_dia, dt_inicio, dt_fim, status,
                   qtd_arquivos_extraidos, qtd_arquivos_carregados,
                   qtd_arquivos_erro, qtd_arquivos_pulados, mensagem, log_arquivo
            FROM {table}
            WHERE id = %s
            """,
            (carga_dia_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "dt_carga": row[1].isoformat() if row[1] else None,
        "seq_execucao_dia": row[2],
        "dt_inicio": row[3].isoformat() if row[3] else None,
        "dt_fim": row[4].isoformat() if row[4] else None,
        "status": row[5],
        "qtd_arquivos_extraidos": row[6],
        "qtd_arquivos_carregados": row[7],
        "qtd_arquivos_erro": row[8],
        "qtd_arquivos_pulados": row[9],
        "mensagem": row[10],
        "log_arquivo": row[11],
    }


def list_carga_dia(
    conn,
    limit: int = 20,
    dt_carga: date | None = None,
) -> list[dict]:
    if not carga_dia_table_exists(conn):
        return []

    table = qualified_carga_dia_table()
    query = f"""
        SELECT id, dt_carga, seq_execucao_dia, dt_inicio, dt_fim, status,
               qtd_arquivos_extraidos, qtd_arquivos_carregados,
               qtd_arquivos_erro, qtd_arquivos_pulados, mensagem, log_arquivo
        FROM {table}
    """
    params: list = []
    if dt_carga is not None:
        query += " WHERE dt_carga = %s"
        params.append(dt_carga)
    query += " ORDER BY dt_inicio DESC LIMIT %s"
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "dt_carga": row[1].isoformat() if row[1] else None,
            "seq_execucao_dia": row[2],
            "dt_inicio": row[3].isoformat() if row[3] else None,
            "dt_fim": row[4].isoformat() if row[4] else None,
            "status": row[5],
            "qtd_arquivos_extraidos": row[6],
            "qtd_arquivos_carregados": row[7],
            "qtd_arquivos_erro": row[8],
            "qtd_arquivos_pulados": row[9],
            "mensagem": row[10],
            "log_arquivo": row[11],
        }
        for row in rows
    ]


def list_carga_dia_hoje(conn) -> list[dict]:
    return list_carga_dia(conn, limit=50, dt_carga=date.today())
