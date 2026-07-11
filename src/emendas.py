from src.db_meta import qualified_table


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
