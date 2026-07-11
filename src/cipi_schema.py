import logging

from src.config import get_db_config
from src.db_meta import get_table_column_types, qualified_table

logger = logging.getLogger(__name__)

CIPI_TEXT_COLUMNS = frozenset({
    "id_projeto_investimento",
    "projeto_investimento",
    "nr_contrato",
})

PROJETO_INVESTIMENTO_COLUMNS = frozenset({
    "id_projeto_investimento",
    "projeto_investimento",
})


def is_cipi_text_column(column_name: str | None) -> bool:
    return bool(column_name and column_name in CIPI_TEXT_COLUMNS)


def is_projeto_investimento_column(column_name: str | None) -> bool:
    return bool(column_name and column_name in PROJETO_INVESTIMENTO_COLUMNS)


def ensure_cipi_text_columns(conn, table: str) -> None:
    """CIPI usa valores alfanuméricos (ex.: 109593.15-77, 131/2025); ajusta integer para varchar."""
    column_types = get_table_column_types(conn, table)
    for column in CIPI_TEXT_COLUMNS:
        if column not in column_types:
            continue
        if column_types[column] not in {"integer", "bigint", "smallint"}:
            continue
        qualified = qualified_table(table)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                ALTER TABLE {qualified}
                ALTER COLUMN "{column}" TYPE character varying
                USING "{column}"::text
                """
            )
        conn.commit()
        logger.info(
            "Coluna %s.%s alterada para character varying (valor CIPI)",
            table,
            column,
        )


def ensure_projeto_investimento_text(conn, table: str) -> None:
    ensure_cipi_text_columns(conn, table)


def ensure_percentual_execucao_range(conn, table: str) -> None:
    """Percentual no CSV chega a ~102; DDL original numeric(3,2) estoura."""
    if table != "tab_execucao_fisica_cipi":
        return
    schema = get_db_config().schema
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT numeric_precision
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = 'percentual_execucao'
            """,
            (schema, table),
        )
        row = cur.fetchone()
    if not row or row[0] is None or row[0] >= 6:
        return
    qualified = qualified_table(table)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            ALTER TABLE {qualified}
            ALTER COLUMN percentual_execucao TYPE numeric(6, 2)
            USING percentual_execucao::numeric
            """
        )
    conn.commit()
    logger.info(
        "Coluna %s.percentual_execucao alterada para numeric(6,2)",
        table,
    )


def prepare_cipi_table(conn, table: str) -> None:
    if table in {"tab_contratos_cipi", "tab_execucao_fisica_cipi"}:
        ensure_cipi_text_columns(conn, table)
    if table == "tab_execucao_fisica_cipi":
        ensure_percentual_execucao_range(conn, table)
