# Tabelas com chave em revisão que usam TRUNCATE + INSERT completo do CSV
TRUNCATE_RELOAD_TABLES: frozenset[str] = frozenset({
    "tab_acomp_obras_contratos_medicoes_modulo_empresas",
    "tab_acomp_obras_valores_itens_medicao_modulo_empresas",
    "tab_apoiadores_emendas_programas",
    "tab_contratos_cipi",
    "tab_coordenadas_obras",
    "tab_cronograma_desembolso",
    "tab_desbloqueio_cr",
    "tab_historico_projeto_basico",
    "tab_ingresso_contrapartida",
    "tab_inst_cont_contratos_lotes_empresas_modulo_empresas",
    "tab_inst_cont_metas_submetas_po_modulo_empresas",
    "tab_inst_cont_proposta_aio_modulo_empresas",
    "tab_itens_licitacao",
    "tab_justificativas_proposta",
    "tab_obtv_convenente",
    "tab_pagamento_tributo",
    "tab_plano_aplicacao_detalhado",
    "tab_projeto_basico_acffo_modulo_empresas",
    "tab_projeto_basico_lae_modulo_empresas",
    "tab_projeto_basico_metas_modulo_empresas",
    "tab_projeto_basico_proposta_modulo_empresas",
    "tab_projeto_basico_submetas_modulo_empresas",
    "tab_prorroga_oficios",
    "tab_resposta_selecao_pac",
    "tab_resumo_fisico_financeiro",
    "tab_solicitacao_ajuste_pt",
    "tab_solicitacao_alteracao",
    "tab_solicitacao_rendimento_aplicacao",
    "tab_termo_aditivo",
    "tab_vrpl_lote_fornecedor_licitacao_modulo_empresas",
    "tab_vrpl_metas_submetas_modulo_empresas",
    "tab_vrpl_proposta_licitacao_modulo_empresas",
})

TABLE_KEYS: dict[str, dict] = {
    "rlc_dados_disponibilizacao_programas": {"columns": ["id_programa"], "status": "definida", "requires_manual_key": False},
    "rlc_dados_obrasgov_geral": {"columns": ["id_obra"], "status": "revisar", "requires_manual_key": True},
    "rlc_dados_uf_modalidade_programas": {"columns": ["id_programa", "uf_programa", "modalidade_programa"], "status": "definida", "requires_manual_key": False},
    "rlc_empenhos_desembolsos": {"columns": ["id_desembolso", "id_empenho"], "status": "definida", "requires_manual_key": False},
    "rlc_historico_situacao": {"columns": ["id_proposta", "nr_convenio", "dia_historico_sit"], "status": "definida", "requires_manual_key": False},
    "rlc_programa_proponente": {"columns": ["id_programa", "id_proponente"], "status": "definida", "requires_manual_key": False},
    "rlc_programa_proposta": {"columns": ["id_programa", "id_proposta"], "status": "definida", "requires_manual_key": False},
    "rlc_consorcios_participantes_propostas": {
        "columns": ["id_proposta", "cnpj_consorcio", "cnpj_participante"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "rlc_emendas_propostas_proponentes": {
        "columns": ["nr_emenda", "id_proposta", "identif_proponente"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "rlc_proposta_formalizacao_pac": {"columns": ["id_proposta_selecao_pac", "id_proposta"], "status": "definida", "requires_manual_key": False},
    "tab_acomp_obras_contratos_medicoes_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_acomp_obras_valores_itens_medicao_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_apoiadores_emendas_programas": {"columns": ["id_programa", "nr_emenda"], "status": "revisar", "requires_manual_key": True},
    "tab_beneficiarios_emendas": {
        "columns": ["nr_emenda", "id_proposta", "beneficiario_emenda"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_consorcios": {"columns": ["cnpj_consorcio"], "status": "definida", "requires_manual_key": False},
    "tab_contratos": {
        "columns": ["id_licitacao", "id_contrato"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_contratos_cipi": {"columns": ["id_contrato"], "status": "definida", "requires_manual_key": False},
    "tab_convenios": {"columns": ["nr_convenio"], "status": "definida", "requires_manual_key": False},
    "tab_coordenadas_obras": {"columns": ["id_meta", "nr_coordenada"], "status": "revisar", "requires_manual_key": True},
    "tab_cronograma_desembolso": {"columns": ["id_proposta", "nr_parcela"], "status": "revisar", "requires_manual_key": True},
    "tab_data_carga": {"columns": ["data_carga"], "status": "definida", "requires_manual_key": False},
    "tab_desbloqueio_cr": {"columns": ["id_desbloqueio"], "status": "revisar", "requires_manual_key": True},
    "tab_desbloqueio_recurso_cr": {"columns": ["id_desbloqueio"], "status": "revisar", "requires_manual_key": True},
    "tab_desembolsos": {"columns": ["id_desembolso"], "status": "definida", "requires_manual_key": False},
    "tab_dl": {"columns": ["id_dl"], "status": "definida", "requires_manual_key": False},
    "tab_emendas": {"columns": ["nr_emenda"], "status": "definida", "requires_manual_key": False},
    "tab_empenhos": {"columns": ["id_empenho"], "status": "definida", "requires_manual_key": False},
    "tab_empenhos_cipi": {
        "columns": ["nr_empenho", "projeto_investimento"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_etapas_crono_fisico": {"columns": ["id_etapa"], "status": "definida", "requires_manual_key": False},
    "tab_execucao_fisica_cipi": {
        "columns": [
            "especificacao_outros",
            "id_projeto_investimento",
            "id_situacao",
            "data_situacao",
        ],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_fornecedores_licitacoes": {
        "columns": ["identificacao_fornecedor"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_historico_projeto_basico": {"columns": ["id_proposta", "dt_historico"], "status": "revisar", "requires_manual_key": True},
    "tab_ingresso_contrapartida": {"columns": ["id_ingresso"], "status": "revisar", "requires_manual_key": True},
    "tab_inst_cont_contratos_lotes_empresas_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_inst_cont_metas_submetas_po_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_inst_cont_proposta_aio_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_itens_dl": {"columns": ["id_dl", "nr_item"], "status": "revisar", "requires_manual_key": True},
    "tab_itens_licitacao": {"columns": ["id_licitacao", "nr_item"], "status": "revisar", "requires_manual_key": True},
    "tab_justificativas_proposta": {"columns": ["id_proposta"], "status": "revisar", "requires_manual_key": True},
    "tab_licitacao": {"columns": ["id_licitacao"], "status": "definida", "requires_manual_key": False},
    "tab_meta_crono_fisico": {"columns": ["id_meta"], "status": "definida", "requires_manual_key": False},
    "tab_obtv_convenente": {"columns": ["id_obtv"], "status": "revisar", "requires_manual_key": True},
    "tab_pagamento_tributo": {"columns": ["id_pagamento", "id_tributo"], "status": "revisar", "requires_manual_key": True},
    "tab_pagamentos": {"columns": ["nr_mov_fin"], "status": "definida", "requires_manual_key": False},
    "tab_pergunta_selecao_pac": {
        "columns": ["id_pergunta_selecao_pac"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_plano_aplicacao_detalhado": {"columns": ["id_proposta", "nr_item"], "status": "revisar", "requires_manual_key": True},
    "tab_programas": {"columns": ["id_programa"], "status": "definida", "requires_manual_key": False},
    "tab_projeto_basico_acffo_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_projeto_basico_lae_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_projeto_basico_metas_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_projeto_basico_proposta_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_projeto_basico_submetas_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_prop_inst_indicadores_estados": {"columns": ["id_proposta", "uf"], "status": "revisar", "requires_manual_key": True},
    "tab_prop_inst_indicadores_municipios": {"columns": ["id_proposta", "cod_munic_ibge"], "status": "revisar", "requires_manual_key": True},
    "tab_proponentes": {"columns": ["id_proponente"], "status": "definida", "requires_manual_key": False},
    "tab_propostas": {"columns": ["id_proposta"], "status": "definida", "requires_manual_key": False},
    "tab_propostas_canceladas": {"columns": ["id_proposta"], "status": "definida", "requires_manual_key": False},
    "tab_propostas_selecao_pac": {"columns": ["id_proposta_selecao_pac"], "status": "definida", "requires_manual_key": False},
    "tab_prorroga_oficios": {"columns": ["nr_convenio", "nr_oficio"], "status": "revisar", "requires_manual_key": True},
    "tab_resposta_selecao_pac": {"columns": ["id_proposta", "id_pergunta"], "status": "revisar", "requires_manual_key": True},
    "tab_resumo_fisico_financeiro": {"columns": ["id_proposta"], "status": "revisar", "requires_manual_key": True},
    "tab_solicitacao_ajuste_pt": {"columns": ["id_solicitacao"], "status": "revisar", "requires_manual_key": True},
    "tab_solicitacao_alteracao": {"columns": ["id_solicitacao"], "status": "revisar", "requires_manual_key": True},
    "tab_solicitacao_rendimento_aplicacao": {"columns": ["id_solicitacao"], "status": "revisar", "requires_manual_key": True},
    "tab_termo_aditivo": {"columns": ["nr_convenio", "nr_aditivo"], "status": "revisar", "requires_manual_key": True},
    "tab_vrpl_lote_fornecedor_licitacao_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_vrpl_metas_submetas_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
    "tab_vrpl_proposta_licitacao_modulo_empresas": {"columns": ["id_proposta", "id_registro"], "status": "revisar", "requires_manual_key": True},
}


def get_key(table_name: str) -> list[str]:
    entry = TABLE_KEYS.get(table_name)
    if not entry:
        raise KeyError(f"Tabela sem chave configurada: {table_name}")
    return entry["columns"]


def is_merge_ready(table_name: str) -> bool:
    entry = TABLE_KEYS.get(table_name)
    return bool(entry and entry["status"] == "definida" and not entry["requires_manual_key"])


def is_truncate_reload(table_name: str) -> bool:
    return table_name in TRUNCATE_RELOAD_TABLES
