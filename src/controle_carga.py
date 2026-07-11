import logging
import os

from src.config import get_controle_carga_schema

logger = logging.getLogger(__name__)

STATUS_EXECUTANDO = "EXECUTANDO"
STATUS_CARREGANDO = "CARREGANDO"
STATUS_SUCESSO = "SUCESSO"
STATUS_PARCIAL = "PARCIAL"
STATUS_ERRO = "ERRO"
STATUS_ERRO_NAO_CORRIGIDO = "ERRO NÃO CORRIGIDO"
STATUS_CORRIGIDO_SUCESSO = "CORRIGIDO/SUCESSO"
STATUS_PULADO = "PULADO"

ERROR_STATUSES = frozenset({STATUS_ERRO, STATUS_ERRO_NAO_CORRIGIDO})

PIPELINE_ENDPOINT = "pipeline/siconv-incremental"


def is_controle_enabled() -> bool:
    return os.getenv("CONTROLE_CARGA_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_controle_schema() -> str:
    return get_controle_carga_schema()


def qualified_controle_table() -> str:
    schema = get_controle_schema()
    return f'"{schema}"."controle_carga"'


def controle_table_exists(conn) -> bool:
    schema = get_controle_schema()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = 'controle_carga'
            """,
            (schema,),
        )
        exists = cur.fetchone() is not None
    if not exists:
        logger.warning(
            "Tabela %s.controle_carga não encontrada; controle em banco desabilitado",
            schema,
        )
    return exists


def _table_endpoint(table: str) -> str:
    return f"siconv/{table}"


def get_last_pending_error_id(
    conn,
    endpoint: str,
    exclude_id: int | None = None,
) -> int | None:
    """Último ERRO/ERRO NÃO CORRIGIDO do endpoint ainda sem CORRIGIDO/SUCESSO vinculado."""
    table = qualified_controle_table()
    query = f"""
        SELECT c.id
        FROM {table} c
        WHERE c.endpoint = %s
          AND c.status IN (%s, %s)
          AND c.dt_fim IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM {table} fix
              WHERE fix.id_controle_carga_refatorado = c.id
                AND fix.status = %s
          )
    """
    params: list = [endpoint, STATUS_ERRO, STATUS_ERRO_NAO_CORRIGIDO, STATUS_CORRIGIDO_SUCESSO]
    if exclude_id is not None:
        query += " AND c.id <> %s"
        params.append(exclude_id)
    query += " ORDER BY c.dt_inicio DESC LIMIT 1"
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return row[0] if row else None


def get_last_finished_status(conn, endpoint: str, exclude_id: int | None = None) -> str | None:
    table = qualified_controle_table()
    query = f"""
        SELECT status
        FROM {table}
        WHERE endpoint = %s AND dt_fim IS NOT NULL
    """
    params: list = [endpoint]
    if exclude_id is not None:
        query += " AND id <> %s"
        params.append(exclude_id)
    query += " ORDER BY dt_inicio DESC LIMIT 1"
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return row[0] if row else None


def start_controle(
    conn,
    endpoint: str,
    status: str = STATUS_CARREGANDO,
    id_controle_carga_dia: int | None = None,
) -> int | None:
    if not is_controle_enabled() or not controle_table_exists(conn):
        return None
    table = qualified_controle_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {table} (
                endpoint, dt_inicio, status, id_controle_carga_dia
            )
            VALUES (%s, now(), %s, %s)
            RETURNING id
            """,
            (endpoint, status, id_controle_carga_dia),
        )
        controle_id = cur.fetchone()[0]
    conn.commit()
    logger.debug(
        "controle_carga id=%s endpoint=%s status=%s carga_dia=%s",
        controle_id,
        endpoint,
        status,
        id_controle_carga_dia,
    )
    return controle_id


def finish_controle(
    conn,
    controle_id: int | None,
    status: str,
    total_registros: int | None = None,
    qtd_registros_inseridos: int | None = None,
    qtd_registros_atualizados: int | None = None,
    id_controle_carga_refatorado: int | None = None,
    mensagem: str | None = None,
) -> None:
    if controle_id is None:
        return
    table = qualified_controle_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE {table}
            SET dt_fim = now(),
                status = %s,
                total_registros = %s,
                qtd_registros_inseridos = %s,
                qtd_registros_atualizados = %s,
                id_controle_carga_refatorado = %s,
                mensagem = %s
            WHERE id = %s
            """,
            (
                status,
                total_registros,
                qtd_registros_inseridos,
                qtd_registros_atualizados,
                id_controle_carga_refatorado,
                mensagem[:4000] if mensagem else None,
                controle_id,
            ),
        )
    conn.commit()
    logger.debug(
        "controle_carga id=%s finalizado status=%s ins=%s upd=%s ref=%s",
        controle_id,
        status,
        qtd_registros_inseridos,
        qtd_registros_atualizados,
        id_controle_carga_refatorado,
    )


def resolve_success_status(
    conn,
    endpoint: str,
    controle_id: int,
) -> tuple[str, int | None]:
    pending_id = get_last_pending_error_id(conn, endpoint, exclude_id=controle_id)
    if pending_id is not None:
        return STATUS_CORRIGIDO_SUCESSO, pending_id
    return STATUS_SUCESSO, None


def resolve_error_status(
    conn,
    endpoint: str,
    controle_id: int,
) -> tuple[str, int | None]:
    pending_id = get_last_pending_error_id(conn, endpoint, exclude_id=controle_id)
    if pending_id is not None:
        return STATUS_ERRO_NAO_CORRIGIDO, pending_id
    return STATUS_ERRO, None


def start_table_carga(
    conn,
    table: str,
    id_controle_carga_dia: int | None = None,
) -> int | None:
    return start_controle(
        conn,
        _table_endpoint(table),
        STATUS_CARREGANDO,
        id_controle_carga_dia=id_controle_carga_dia,
    )


def finish_table_carga_success(
    conn,
    controle_id: int | None,
    table: str,
    result: dict,
) -> None:
    if controle_id is None:
        return
    endpoint = _table_endpoint(table)
    inserted = int(result.get("inserted", 0) or 0)
    updated = int(result.get("updated", 0) or 0)
    total = inserted + updated
    status, ref_id = resolve_success_status(conn, endpoint, controle_id)
    finish_controle(
        conn,
        controle_id,
        status,
        total_registros=total,
        qtd_registros_inseridos=inserted,
        qtd_registros_atualizados=updated,
        id_controle_carga_refatorado=ref_id,
    )
    logger.info(
        "controle_carga id=%s endpoint=%s status=%s ins=%s upd=%s total=%s",
        controle_id,
        endpoint,
        status,
        inserted,
        updated,
        total,
    )


def finish_table_carga_skipped(
    conn,
    controle_id: int | None,
    table: str,
    reason: str,
) -> None:
    if controle_id is None:
        return
    endpoint = _table_endpoint(table)
    finish_controle(
        conn,
        controle_id,
        STATUS_PULADO,
        total_registros=0,
        qtd_registros_inseridos=0,
        qtd_registros_atualizados=0,
        mensagem=reason[:4000],
    )
    logger.info(
        "controle_carga id=%s endpoint=%s status=%s motivo=%s",
        controle_id,
        endpoint,
        STATUS_PULADO,
        reason[:200],
    )


def finish_table_carga_error(
    conn,
    controle_id: int | None,
    table: str,
    error: str,
    partial_inserted: int | None = None,
    partial_updated: int | None = None,
) -> None:
    if controle_id is None:
        return
    endpoint = _table_endpoint(table)
    if partial_inserted is not None or partial_updated is not None:
        ins = partial_inserted or 0
        upd = partial_updated or 0
        finish_controle(
            conn,
            controle_id,
            STATUS_PARCIAL,
            total_registros=ins + upd,
            qtd_registros_inseridos=ins,
            qtd_registros_atualizados=upd,
            mensagem=error[:4000],
        )
        return
    status, ref_id = resolve_error_status(conn, endpoint, controle_id)
    finish_controle(
        conn,
        controle_id,
        status,
        id_controle_carga_refatorado=ref_id,
        mensagem=error[:4000],
    )


def start_pipeline_carga(conn, id_controle_carga_dia: int | None = None) -> int | None:
    return start_controle(
        conn,
        PIPELINE_ENDPOINT,
        STATUS_EXECUTANDO,
        id_controle_carga_dia=id_controle_carga_dia,
    )


def finish_pipeline_carga(
    conn,
    controle_id: int | None,
    processed: int,
    error_count: int,
    mensagem: str | None = None,
) -> None:
    if controle_id is None:
        return
    if error_count == 0 and processed > 0:
        status, ref_id = resolve_success_status(conn, PIPELINE_ENDPOINT, controle_id)
    elif error_count > 0 and processed > 0:
        status, ref_id = STATUS_PARCIAL, None
    elif error_count > 0:
        status, ref_id = resolve_error_status(conn, PIPELINE_ENDPOINT, controle_id)
    else:
        status, ref_id = STATUS_PARCIAL, None
        mensagem = mensagem or "Nenhuma tabela processada"
    finish_controle(
        conn,
        controle_id,
        status,
        total_registros=processed,
        id_controle_carga_refatorado=ref_id,
        mensagem=mensagem,
    )


def get_latest_finished_status_for_carga_dia(
    conn,
    carga_dia_id: int,
    endpoint: str,
) -> str | None:
    if not controle_table_exists(conn):
        return None
    table = qualified_controle_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT status
            FROM {table}
            WHERE id_controle_carga_dia = %s
              AND endpoint = %s
              AND dt_fim IS NOT NULL
            ORDER BY dt_inicio DESC
            LIMIT 1
            """,
            (carga_dia_id, endpoint),
        )
        row = cur.fetchone()
    return row[0] if row else None


def close_stuck_controle_records(
    conn,
    carga_dia_id: int,
    mensagem: str = "Interrompido; retomada manual",
) -> list[int]:
    """Fecha registros abertos (CARREGANDO/EXECUTANDO) da execução do dia."""
    if not is_controle_enabled() or not controle_table_exists(conn):
        return []
    table = qualified_controle_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE {table}
            SET dt_fim = now(),
                status = CASE
                    WHEN status = %s THEN %s
                    WHEN status = %s THEN %s
                    ELSE %s
                END,
                mensagem = COALESCE(NULLIF(mensagem, ''), %s)
            WHERE id_controle_carga_dia = %s
              AND dt_fim IS NULL
            RETURNING id, endpoint, status
            """,
            (
                STATUS_CARREGANDO,
                STATUS_ERRO,
                STATUS_EXECUTANDO,
                STATUS_PARCIAL,
                STATUS_ERRO,
                mensagem,
                carga_dia_id,
            ),
        )
        rows = cur.fetchall()
    conn.commit()
    for row in rows:
        logger.info(
            "controle_carga id=%s endpoint=%s fechado como %s",
            row[0],
            row[1],
            row[2],
        )
    return [row[0] for row in rows]


def recount_carga_dia_table_stats(
    conn,
    carga_dia_id: int,
    load_order: list[str],
) -> tuple[int, int, int]:
    """Conta carregados, erros e pulados pelo último status de cada tabela no dia."""
    success_statuses = {STATUS_SUCESSO, STATUS_CORRIGIDO_SUCESSO}
    error_statuses = {STATUS_ERRO, STATUS_ERRO_NAO_CORRIGIDO, STATUS_PARCIAL}
    carregados = 0
    erros = 0
    pulados = 0
    for table in load_order:
        if table == "tab_data_carga":
            continue
        status = get_latest_finished_status_for_carga_dia(
            conn, carga_dia_id, _table_endpoint(table)
        )
        if status in success_statuses:
            carregados += 1
        elif status in error_statuses:
            erros += 1
        else:
            pulados += 1
    return carregados, erros, pulados


def list_recent_controle(conn, limit: int = 20) -> list[dict]:
    if not controle_table_exists(conn):
        return []
    table = qualified_controle_table()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, endpoint, dt_inicio, dt_fim, status, total_registros,
                   qtd_registros_inseridos, qtd_registros_atualizados,
                   id_controle_carga_dia, id_controle_carga_refatorado, mensagem
            FROM {table}
            ORDER BY dt_inicio DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "endpoint": row[1],
            "dt_inicio": row[2].isoformat() if row[2] else None,
            "dt_fim": row[3].isoformat() if row[3] else None,
            "status": row[4],
            "total_registros": row[5],
            "qtd_registros_inseridos": row[6],
            "qtd_registros_atualizados": row[7],
            "id_controle_carga_dia": row[8],
            "id_controle_carga_refatorado": row[9],
            "mensagem": row[10],
        }
        for row in rows
    ]
