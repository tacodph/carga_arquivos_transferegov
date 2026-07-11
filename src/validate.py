from pathlib import Path

from src.config import EXTRACTED_DIR, get_connection, get_db_config
from src.db_meta import qualified_table, table_exists
from src.keys import is_merge_ready


def check_data_carga(conn) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT MAX(data_carga) FROM {qualified_table('tab_data_carga')}"
        )
        row = cur.fetchone()
        return str(row[0]) if row and row[0] else None


def _count_table(conn, table: str) -> int:
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(c.reltuples::bigint, 0)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = %s
            """,
            (schema, table),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def validate_table(conn, table: str, csv_path: Path | None = None) -> dict:
    result = {
        "table": table,
        "exists": table_exists(conn, table),
        "row_count_destino": 0,
        "csv_path": str(csv_path) if csv_path else None,
        "merge_ready": is_merge_ready(table),
        "orphan_fk_count": 0,
    }
    if not result["exists"]:
        return result

    result["row_count_destino"] = _count_table(conn, table)
    return result


def validate_run(conn, catalog_index: dict[str, str]) -> list[dict]:
    report = []
    for table, csv_name in sorted(catalog_index.items()):
        csv_path = EXTRACTED_DIR / csv_name if csv_name else None
        report.append(validate_table(conn, table, csv_path))
    return report


def register_data_carga(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {qualified_table('tab_data_carga')} (data_carga) "
            "VALUES (CURRENT_DATE)"
        )
    conn.commit()
