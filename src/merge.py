import logging

from src.db_meta import (
    get_load_timestamp_column,
    get_table_columns,
    qualified_staging,
    qualified_table,
)
from src.keys import get_key, is_merge_ready
from src.staging import STAGING_LOADED_COLUMNS

logger = logging.getLogger(__name__)


def build_update_sql(
    table: str,
    key_columns: list[str],
    data_columns: list[str],
    ts_column: str | None,
) -> str:
    set_parts = [f'"{col}" = s."{col}"' for col in data_columns]
    if ts_column:
        set_parts.append(f'"{ts_column}" = now()')
    where_parts = [f'd."{col}" = s."{col}"' for col in key_columns]
    return (
        f"UPDATE {qualified_table(table)} AS d SET "
        + ", ".join(set_parts)
        + f" FROM {qualified_staging(table)} AS s WHERE "
        + " AND ".join(where_parts)
    )


def build_insert_sql(
    table: str,
    key_columns: list[str],
    insert_columns: list[str],
    ts_column: str | None,
) -> str:
    cols = list(insert_columns)
    select_exprs = [f's."{col}"' for col in insert_columns]
    if ts_column and ts_column not in cols:
        cols.append(ts_column)
        select_exprs.append("now()")

    key_match = " AND ".join(f'd."{col}" = s."{col}"' for col in key_columns)
    cols_sql = ", ".join(f'"{c}"' for c in cols)
    select_sql = ", ".join(select_exprs)
    return (
        f"INSERT INTO {qualified_table(table)} ({cols_sql}) "
        f"SELECT {select_sql} FROM {qualified_staging(table)} AS s "
        f"WHERE NOT EXISTS (SELECT 1 FROM {qualified_table(table)} AS d WHERE {key_match})"
    )


def merge_table(conn, target_table: str) -> dict:
    if not is_merge_ready(target_table):
        logger.warning(
            "Tabela %s ignorada: chave não validada (status revisar)",
            target_table,
        )
        return {"updated": 0, "inserted": 0, "skipped": True}

    loaded_columns = STAGING_LOADED_COLUMNS.get(target_table)
    if not loaded_columns:
        raise ValueError(f"Staging sem colunas carregadas para {target_table}")

    key_columns = get_key(target_table)
    dest_columns = get_table_columns(conn, target_table)
    ts_column = get_load_timestamp_column(dest_columns)

    data_columns = [
        c
        for c in loaded_columns
        if c not in key_columns and c not in {"dte_carga", "data_carga"}
    ]
    insert_columns = [
        c for c in loaded_columns if c not in {"dte_carga", "data_carga"}
    ]

    update_sql = build_update_sql(target_table, key_columns, data_columns, ts_column)
    insert_sql = build_insert_sql(
        target_table, key_columns, insert_columns, ts_column
    )

    with conn.cursor() as cur:
        updated = 0
        if data_columns or ts_column:
            cur.execute(update_sql)
            updated = cur.rowcount
        cur.execute(insert_sql)
        inserted = cur.rowcount

    conn.commit()
    return {"updated": updated, "inserted": inserted, "skipped": False}


def truncate_reload_table(conn, target_table: str) -> dict:
    loaded_columns = STAGING_LOADED_COLUMNS.get(target_table)
    if not loaded_columns:
        raise ValueError(f"Staging sem colunas carregadas para {target_table}")

    dest_columns = get_table_columns(conn, target_table)
    ts_column = get_load_timestamp_column(dest_columns)

    insert_columns = [
        c for c in loaded_columns if c not in {"dte_carga", "data_carga"}
    ]
    cols = list(insert_columns)
    select_exprs = [f's."{col}"' for col in insert_columns]
    if ts_column and ts_column not in cols:
        cols.append(ts_column)
        select_exprs.append("now()")

    cols_sql = ", ".join(f'"{c}"' for c in cols)
    select_sql = ", ".join(select_exprs)
    insert_sql = (
        f"INSERT INTO {qualified_table(target_table)} ({cols_sql}) "
        f"SELECT {select_sql} FROM {qualified_staging(target_table)} AS s"
    )

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {qualified_table(target_table)}")
        cur.execute(insert_sql)
        inserted = cur.rowcount

    conn.commit()
    logger.info(
        "Tabela %s: TRUNCATE + INSERT de %s linhas",
        target_table,
        inserted,
    )
    return {
        "updated": 0,
        "inserted": inserted,
        "skipped": False,
        "truncate_reload": True,
    }
