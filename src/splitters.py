PROGRAMA_COLUMNS = {
    "tab_programas": [
        "id_programa",
        "cod_orgao_sup_programa",
        "desc_orgao_sup_programa",
        "cod_programa",
        "nome_programa",
        "acao_orcamentaria",
    ],
    "rlc_dados_disponibilizacao_programas": [
        "id_programa",
        "sit_programa",
        "data_disponibilizacao",
        "ano_disponibilizacao",
        "dt_prog_ini_receb_prop",
        "dt_prog_fim_receb_prop",
        "dt_prog_ini_emenda_par",
        "dt_prog_fim_emenda_par",
        "dt_prog_ini_benef_esp",
        "dt_prog_fim_benef_esp",
    ],
    "rlc_dados_uf_modalidade_programas": [
        "id_programa",
        "uf_programa",
        "modalidade_programa",
    ],
}

CONSORCIO_COLUMNS = {
    "tab_consorcios": [
        "cnpj_consorcio",
        "nome_consorcio",
        "codigo_cnae_primario",
        "desc_cnae_primario",
    ],
    "rlc_consorcios_participantes_propostas": [
        "id_proposta",
        "cnpj_consorcio",
        "cnpj_participante",
    ],
}

CONSORCIO_DEDUPE_COLUMNS = {
    "tab_consorcios": ["cnpj_consorcio"],
}

CONSORCIO_REQUIRED_COLUMNS = {
    "rlc_consorcios_participantes_propostas": [
        "id_proposta",
        "cnpj_consorcio",
        "cnpj_participante",
    ],
}

EMENDA_COLUMNS = {
    "tab_emendas": [
        "nr_emenda",
        "nome_parlamentar",
        "tipo_parlamentar",
    ],
    "rlc_emendas_propostas_proponentes": [
        "nr_emenda",
        "id_proposta",
        "identif_proponente",
    ],
    "tab_beneficiarios_emendas": [
        "id_proposta",
        "beneficiario_emenda",
        "nr_emenda",
        "qualif_proponente",
        "ind_impositivo",
        "valor_repasse_proposta_emenda",
        "valor_repasse_emenda",
        "cod_programa_emenda",
    ],
}

EMENDA_CSV_SOURCES = {
    "rlc_emendas_propostas_proponentes": {
        "identif_proponente": "beneficiario_emenda",
    },
}

EMENDA_REQUIRED_COLUMNS = {
    "tab_emendas": ["nr_emenda"],
    "rlc_emendas_propostas_proponentes": [
        "nr_emenda",
        "id_proposta",
        "identif_proponente",
    ],
    "tab_beneficiarios_emendas": [
        "nr_emenda",
        "id_proposta",
        "beneficiario_emenda",
    ],
}

# Dedupe na staging pela chave natural — siconv_emenda.csv tem 1 linha por
# beneficiário/proposta; tab_emendas precisa de 1 linha por nr_emenda.
EMENDA_DEDUPE_COLUMNS = {
    "tab_emendas": ["nr_emenda"],
    "rlc_emendas_propostas_proponentes": [
        "nr_emenda",
        "id_proposta",
        "identif_proponente",
    ],
    "tab_beneficiarios_emendas": [
        "nr_emenda",
        "id_proposta",
        "beneficiario_emenda",
    ],
}

CIPI_CSV_SOURCES = {
    "tab_contratos_cipi": {
        "tipo_aquisicao_contato": "tipo_aquisicao_contrato",
    },
    "tab_empenhos_cipi": {
        "projeto_investimento": "id_projeto_investimento",
    },
    "tab_execucao_fisica_cipi": {},
}

CIPI_COLUMNS = {
    "tab_empenhos_cipi": [
        "ug_emitente",
        "nr_empenho",
        "fonte_recurso",
        "natureza_despesa",
        "plano_interno",
        "ptres",
        "valor_empenho",
        "informacoes_complementares",
        "data_emissao",
        "projeto_investimento",
        "sistema_origem",
    ],
    "tab_execucao_fisica_cipi": [
        "cpf_responsavel_operacao",
        "especificacao_outros",
        "id_projeto_investimento",
        "id_situacao",
        "data_situacao",
        "percentual_execucao",
        "id_tipo_indicativo_paralisada",
        "justificativa",
    ],
}

CIPI_REQUIRED_COLUMNS = {
    "tab_contratos_cipi": ["id_contrato"],
    "tab_empenhos_cipi": ["nr_empenho", "projeto_investimento"],
    "tab_execucao_fisica_cipi": [
        "especificacao_outros",
        "id_projeto_investimento",
        "id_situacao",
        "data_situacao",
    ],
}

CIPI_DEDUPE_COLUMNS = {
    "tab_empenhos_cipi": ["nr_empenho", "projeto_investimento"],
    "tab_execucao_fisica_cipi": [
        "especificacao_outros",
        "id_projeto_investimento",
        "id_situacao",
        "data_situacao",
    ],
}


DL_CSV_SOURCES = {
    "tab_dl": {
        "data_emissao": "data_de_emissao",
    },
}

DL_COLUMNS = {
    "tab_dl": [
        "id_dl",
        "id_proposta",
        "id_licitacao",
        "id_contrato",
        "data_emissao",
        "numero",
        "descricao",
        "razao_social",
        "valor_original",
        "valor",
        "status",
    ],
}

DL_REQUIRED_COLUMNS = {
    "tab_dl": ["id_dl"],
}


def is_programa_split_table(table_name: str) -> bool:
    return table_name in PROGRAMA_COLUMNS


def get_programa_columns(table_name: str) -> list[str]:
    return PROGRAMA_COLUMNS[table_name]


def is_consorcio_split_table(table_name: str) -> bool:
    return table_name in CONSORCIO_COLUMNS


def get_consorcio_columns(table_name: str) -> list[str]:
    return CONSORCIO_COLUMNS[table_name]


def get_consorcio_dedupe_columns(table_name: str) -> list[str] | None:
    return CONSORCIO_DEDUPE_COLUMNS.get(table_name)


def get_consorcio_required_columns(table_name: str) -> list[str] | None:
    return CONSORCIO_REQUIRED_COLUMNS.get(table_name)


def is_emenda_split_table(table_name: str) -> bool:
    return table_name in EMENDA_COLUMNS


def get_emenda_columns(table_name: str) -> list[str]:
    return EMENDA_COLUMNS[table_name]


def get_emenda_required_columns(table_name: str) -> list[str] | None:
    return EMENDA_REQUIRED_COLUMNS.get(table_name)


def get_emenda_dedupe_columns(table_name: str) -> list[str] | None:
    return EMENDA_DEDUPE_COLUMNS.get(table_name)


def get_emenda_csv_sources(table_name: str) -> dict[str, str] | None:
    return EMENDA_CSV_SOURCES.get(table_name)


def is_cipi_table(table_name: str) -> bool:
    return table_name in CIPI_CSV_SOURCES


def get_cipi_csv_sources(table_name: str) -> dict[str, str] | None:
    return CIPI_CSV_SOURCES.get(table_name)


def get_cipi_columns(table_name: str) -> list[str] | None:
    return CIPI_COLUMNS.get(table_name)


def get_cipi_dedupe_columns(table_name: str) -> list[str] | None:
    return CIPI_DEDUPE_COLUMNS.get(table_name)


def get_cipi_required_columns(table_name: str) -> list[str] | None:
    return CIPI_REQUIRED_COLUMNS.get(table_name)


def is_dl_table(table_name: str) -> bool:
    return table_name in DL_CSV_SOURCES


def get_dl_csv_sources(table_name: str) -> dict[str, str] | None:
    return DL_CSV_SOURCES.get(table_name)


def get_dl_columns(table_name: str) -> list[str] | None:
    return DL_COLUMNS.get(table_name)


def get_dl_required_columns(table_name: str) -> list[str] | None:
    return DL_REQUIRED_COLUMNS.get(table_name)


# Compatibilidade com imports antigos
is_cipi_contrato_table = is_cipi_table
get_cipi_contrato_csv_sources = get_cipi_csv_sources
get_cipi_contrato_dedupe_columns = get_cipi_dedupe_columns
get_cipi_contrato_required_columns = get_cipi_required_columns
