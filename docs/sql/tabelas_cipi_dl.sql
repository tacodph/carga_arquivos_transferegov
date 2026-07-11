-- Tabelas de carga SICONV: CIPI e DL (discricionárias)
-- Schema: transfere_pro_transferegov (substituído pelo script conforme .env)

CREATE SCHEMA IF NOT EXISTS transfere_pro_transferegov;

-- ---------------------------------------------------------------------------
-- tab_contratos_cipi — siconv_contrato_cipi.csv
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_contratos_cipi (
    id_contrato integer,
    nr_contrato character varying,
    data_inicio_vigencia_contrato date,
    data_fim_vigencia_contrato date,
    data_assinatura_contrato date,
    data_publicacao_contrato date,
    objeto_contrato text,
    nr_processo_licitacao character varying,
    receita_despesa character varying,
    cod_orgao character varying,
    desc_orgao character varying,
    id_fornecedor_contrato character varying,
    nome_fornecedor_contrato character varying,
    tipo_aquisicao_contrato character varying,
    nr_licitacao character varying,
    valor_global_contrato numeric(19, 2),
    valor_acumulado numeric(19, 2),
    id_projeto_investimento character varying,
    link_transparencia text,
    modalidade_licitacao character varying,
    situacao character varying,
    sistema_origem character varying,
    dte_carga date
);

-- ---------------------------------------------------------------------------
-- tab_empenhos_cipi — siconv_empenho_cipi.csv
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_empenhos_cipi (
    ug_emitente integer,
    nr_empenho character varying(75),
    fonte_recurso character varying,
    natureza_despesa character varying,
    plano_interno character varying,
    ptres character varying,
    valor_empenho numeric(19, 2),
    informacoes_complementares text,
    data_emissao date,
    projeto_investimento character varying,
    sistema_origem character varying,
    dte_carga date
);

-- ---------------------------------------------------------------------------
-- tab_execucao_fisica_cipi — siconv_execucao_fisica_cipi.csv
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_execucao_fisica_cipi (
    cpf_responsavel_operacao character varying,
    especificacao_outros character varying,
    id_projeto_investimento character varying,
    id_situacao integer,
    data_situacao date,
    percentual_execucao numeric(6, 2),
    id_tipo_indicativo_paralisada integer,
    justificativa text,
    dte_carga date
);

-- ---------------------------------------------------------------------------
-- tab_dl — siconv_dl.csv
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_dl (
    id_dl integer,
    id_proposta integer,
    id_licitacao integer,
    id_contrato integer,
    data_emissao date,
    numero character varying,
    descricao text,
    razao_social character varying,
    valor_original numeric(19, 2),
    valor numeric(19, 2),
    status character varying,
    dte_carga date
);
