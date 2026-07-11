from src.config import get_db_config


def qualified_table(table_name: str) -> str:
    schema = get_db_config().schema
    return f'"{schema}"."{table_name}"'


def staging_table_name(target_table: str) -> str:
    return f"stg_{target_table}"


def qualified_staging(target_table: str) -> str:
    return f'"{staging_table_name(target_table)}"'


def normalize_column(name: str) -> str:
    return name.strip().lower().replace("\ufeff", "").replace("\xef\xbb\xbf", "")


def get_table_columns(conn, table_name: str) -> list[str]:
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table_name),
        )
        return [row[0] for row in cur.fetchall()]


def table_exists(conn, table_name: str) -> bool:
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table_name),
        )
        return cur.fetchone() is not None


def get_table_column_types(conn, table_name: str) -> dict[str, str]:
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table_name),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def get_table_column_char_max_lengths(conn, table_name: str) -> dict[str, int]:
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND character_maximum_length IS NOT NULL
            ORDER BY ordinal_position
            """,
            (schema, table_name),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


INTEGER_TYPES = {
    "integer",
    "bigint",
    "smallint",
}

NUMERIC_TYPES = INTEGER_TYPES | {
    "numeric",
    "double precision",
    "real",
    "decimal",
}


def get_load_timestamp_column(columns: list[str]) -> str | None:
    if "dte_carga" in columns:
        return "dte_carga"
    if "data_carga" in columns:
        return "data_carga"
    return None
