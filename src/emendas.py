import logging

from src.db_meta import qualified_table
from src.keys import get_key

logger = logging.getLogger(__name__)


def dedupe_table_by_natural_key(conn, table: str) -> int:
    """Remove duplicados na destino, mantendo 1 linha por chave natural.

    Preferência: registro com dte_carga/data_carga mais recente; empate por ctid.
    """
    key_columns = get_key(table)
    if not key_columns:
        return 0

    dest = qualified_table(table)
    partition = ", ".join(f'"{c}"' for c in key_columns)
    order_parts = []
    dest_cols = {c.lower() for c in _table_columns(conn, table)}
    if "dte_carga" in dest_cols:
        order_parts.append('"dte_carga" DESC NULLS LAST')
    if "data_carga" in dest_cols:
        order_parts.append('"data_carga" DESC NULLS LAST')
    order_parts.append("ctid DESC")
    order_sql = ", ".join(order_parts)

    sql = f"""
    DELETE FROM {dest} AS d
    WHERE d.ctid IN (
        SELECT ctid
        FROM (
            SELECT
                ctid,
                ROW_NUMBER() OVER (
                    PARTITION BY {partition}
                    ORDER BY {order_sql}
                ) AS rn
            FROM {dest}
        ) ranked
        WHERE ranked.rn > 1
    )
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        removed = cur.rowcount
    conn.commit()
    if removed:
        logger.warning(
            "Removidos %s duplicados de %s (chave %s)",
            removed,
            table,
            ", ".join(key_columns),
        )
    return removed


def _table_columns(conn, table: str) -> list[str]:
    from src.db_meta import get_table_columns

    return get_table_columns(conn, table)


def update_emendas_resumo(conn) -> None:
    tab_emendas = qualified_table("tab_emendas")
    tab_benef = qualified_table("tab_beneficiarios_emendas")

    sql = f"""
    UPDATE {tab_emendas} AS e
    SET
        qtd_beneficiarios = COALESCE(agg.qtd_beneficiarios, 0),
        qtd_impositivo = COALESCE(agg.qtd_impositivo, 0),
        qtd_nao_impositivo = COALESCE(agg.qtd_nao_impositivo, 0),
        qtd_propostas = COALESCE(agg.qtd_propostas, 0),
        qtd_programas = COALESCE(agg.qtd_programas, 0),
        valor_total_repasse_emenda = COALESCE(agg.valor_total_repasse_emenda, 0),
        valor_total_repasse_proposta_emenda = COALESCE(agg.valor_total_repasse_proposta_emenda, 0),
        dte_carga = now()
    FROM (
        SELECT
            nr_emenda,
            COUNT(beneficiario_emenda) AS qtd_beneficiarios,
            COUNT(*) FILTER (WHERE upper(trim(ind_impositivo)) = 'SIM') AS qtd_impositivo,
            COUNT(*) FILTER (
                WHERE upper(trim(ind_impositivo)) = 'NÃO'
                   OR upper(translate(trim(ind_impositivo), 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ', 'AAAAAEEEEIIIIOOOOOUUUUC')) = 'NAO'
            ) AS qtd_nao_impositivo,
            COUNT(DISTINCT id_proposta) AS qtd_propostas,
            COUNT(DISTINCT cod_programa_emenda) AS qtd_programas,
            COALESCE(SUM(valor_repasse_emenda), 0) AS valor_total_repasse_emenda,
            COALESCE(SUM(valor_repasse_proposta_emenda), 0) AS valor_total_repasse_proposta_emenda
        FROM {tab_benef}
        GROUP BY nr_emenda
    ) AS agg
    WHERE e.nr_emenda = agg.nr_emenda
    """

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
