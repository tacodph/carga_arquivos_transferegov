"""Cria tabelas ausentes no schema (controle + CIPI/DL) e lista o que foi recriado."""
from pathlib import Path

from src.config import get_connection, get_controle_carga_schema, get_db_config
from src.load_order import LOAD_ORDER

SQL_CONTROLE = (
    Path(__file__).resolve().parent.parent / "docs" / "sql" / "controle_carga.sql"
)
SQL_CARGA = Path(__file__).resolve().parent.parent / "docs" / "sql" / "tabelas_cipi_dl.sql"

PULADO_STATUS_SQL = """
ALTER TABLE {schema}.controle_carga DROP CONSTRAINT IF EXISTS chk_status;
ALTER TABLE {schema}.controle_carga ADD CONSTRAINT chk_status CHECK (
    status::text = ANY (
        ARRAY[
            'EXECUTANDO'::character varying,
            'CARREGANDO'::character varying,
            'SUCESSO'::character varying,
            'CORRIGIDO/SUCESSO'::character varying,
            'ERRO'::character varying,
            'ERRO NÃO CORRIGIDO'::character varying,
            'PARCIAL'::character varying,
            'PULADO'::character varying
        ]::text[]
    )
);
"""

TABELAS_CONTROLE = ("controle_carga", "controle_carga_dia")
TABELAS_CARGA = (
    "tab_contratos_cipi",
    "tab_empenhos_cipi",
    "tab_execucao_fisica_cipi",
    "tab_dl",
)


def _existing_tables(conn, schema: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """,
            (schema,),
        )
        return {row[0] for row in cur.fetchall()}


def _apply_sql(conn, sql_path: Path, schema: str) -> None:
    sql = sql_path.read_text(encoding="utf-8").replace(
        "transfere_pro_transferegov", schema
    )
    with conn.cursor() as cur:
        cur.execute(sql)


def main() -> None:
    cfg = get_db_config()
    controle_schema = get_controle_carga_schema()
    schema = cfg.schema

    conn = get_connection()
    conn.autocommit = True
    try:
        before_data = _existing_tables(conn, schema)
        before_ctrl = _existing_tables(conn, controle_schema)

        recriadas: list[str] = []

        missing_ctrl = [t for t in TABELAS_CONTROLE if t not in before_ctrl]
        if missing_ctrl:
            with conn.cursor() as cur:
                cur.execute(
                    f'DROP TABLE IF EXISTS "{controle_schema}"."controle_carga" CASCADE'
                )
                cur.execute(
                    f'DROP TABLE IF EXISTS "{controle_schema}"."controle_carga_dia" CASCADE'
                )
                cur.execute(
                    f'DROP SEQUENCE IF EXISTS "{controle_schema}".controle_carga_id_seq'
                )
                cur.execute(
                    f'DROP SEQUENCE IF EXISTS "{controle_schema}".controle_carga_dia_id_seq'
                )
            _apply_sql(conn, SQL_CONTROLE, controle_schema)
            with conn.cursor() as cur:
                cur.execute(
                    PULADO_STATUS_SQL.format(schema=f'"{controle_schema}"')
                )
            recriadas.extend(f"{controle_schema}.{t}" for t in TABELAS_CONTROLE)

        missing_carga = [
            t
            for t in TABELAS_CARGA
            if t in LOAD_ORDER and t not in before_data
        ]
        if missing_carga:
            _apply_sql(conn, SQL_CARGA, schema)
            recriadas.extend(f"{schema}.{t}" for t in missing_carga)

        after_data = _existing_tables(conn, schema)
        after_ctrl = _existing_tables(conn, controle_schema)
    finally:
        conn.close()

    ainda_ausentes = [
        t for t in LOAD_ORDER if t not in after_data
    ]
    sem_csv = []
    sql_derivada = ["tab_fornecedores_licitacoes"]

    print(f"Schema dados: {schema}")
    print(f"Schema controle: {controle_schema}")
    print()
    print("=== TABELAS RECRIADAS ===")
    if recriadas:
        for nome in recriadas:
            print(f"  - {nome}")
    else:
        print("  (nenhuma — todas já existiam)")

    print()
    print("=== AINDA AUSENTES NO BANCO (LOAD_ORDER) ===")
    for t in ainda_ausentes:
        if t in sql_derivada:
            motivo = "derivada de tab_itens_licitacao (SQL)"
        elif t in sem_csv:
            motivo = "sem CSV no catálogo"
        else:
            motivo = "sem DDL/migration"
        print(f"  - {t} ({motivo})")

    if sem_csv:
        print()
        print("=== SEM CSV NO CATÁLOGO (não recriável pela carga) ===")
        for t in sem_csv:
            print(f"  - {t}")

    if sql_derivada:
        print()
        print("=== CARGA SQL DERIVADA (sem CSV próprio) ===")
        for t in sql_derivada:
            print(f"  - {t}")

    print()
    print("=== CONTROLE ===")
    for t in TABELAS_CONTROLE:
        ok = t in after_ctrl
        print(f"  - {controle_schema}.{t}: {'OK' if ok else 'AUSENTE'}")


if __name__ == "__main__":
    main()
