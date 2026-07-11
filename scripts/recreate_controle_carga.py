"""Recria controle_carga e controle_carga_dia no schema configurado em .env."""
from pathlib import Path

from src.config import get_connection, get_controle_carga_schema

SQL_PATH = Path(__file__).resolve().parent.parent / "docs" / "sql" / "controle_carga.sql"

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


def main() -> None:
    schema = get_controle_carga_schema()
    sql = SQL_PATH.read_text(encoding="utf-8").replace(
        "transfere_pro_transferegov", schema
    )
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{schema}"."controle_carga" CASCADE')
            cur.execute(f'DROP TABLE IF EXISTS "{schema}"."controle_carga_dia" CASCADE')
            cur.execute(f'DROP SEQUENCE IF EXISTS "{schema}".controle_carga_id_seq')
            cur.execute(f'DROP SEQUENCE IF EXISTS "{schema}".controle_carga_dia_id_seq')
            cur.execute(sql)
            cur.execute(PULADO_STATUS_SQL.format(schema=f'"{schema}"'))
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name IN ('controle_carga', 'controle_carga_dia')
                ORDER BY table_name
                """,
                (schema,),
            )
            tables = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

    if len(tables) != 2:
        raise SystemExit(f"Falha: tabelas criadas={tables}")

    print(f"Schema: {schema}")
    print("Tabelas recriadas: controle_carga, controle_carga_dia")


if __name__ == "__main__":
    main()
