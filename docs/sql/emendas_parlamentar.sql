-- Emendas por ano + normalização do parlamentar (discricionárias)
-- Schema: transfere_pro_transferegov
--
-- Fontes: siconv_emenda.csv e apoiadores_emendas_programas.csv
-- Carga: src/emendas_parlamentar.py (upsert por chave natural + row_hash,
-- inativação lógica do que sumiu da foto). Ver docs/EMENDAS_PARLAMENTAR.md.
--
-- O parlamentar é identificado pelo código do autor = left(nr_emenda, 4).
-- Uma pessoa pode ter vários códigos (ex.: deputado que virou senador).

CREATE SCHEMA IF NOT EXISTS transfere_pro_transferegov;

-- ---------------------------------------------------------------------------
-- tab_parlamentares — pessoa, comissão, bancada ou relator
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_parlamentares (
    id_parlamentar serial PRIMARY KEY,
    nome_parlamentar character varying(200) NOT NULL,
    nome_normalizado character varying(200) NOT NULL,
    tipo_parlamentar character varying(30),
    fl_revisar boolean NOT NULL DEFAULT false,
    dte_inclusao timestamp without time zone NOT NULL DEFAULT now(),
    dte_carga timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tab_parlamentares_nome_normalizado
    ON transfere_pro_transferegov.tab_parlamentares USING btree (nome_normalizado);

-- ---------------------------------------------------------------------------
-- tab_autores_emendas — código do autor (4 primeiros dígitos do nr_emenda)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_autores_emendas (
    cod_autor character(4) PRIMARY KEY,
    id_parlamentar integer REFERENCES transfere_pro_transferegov.tab_parlamentares (id_parlamentar),
    nome_parlamentar character varying(200),
    nome_normalizado character varying(200),
    tipo_parlamentar character varying(30),
    origem character varying(30) NOT NULL DEFAULT 'siconv_emenda',
    fl_revisar boolean NOT NULL DEFAULT false,
    dte_inclusao timestamp without time zone NOT NULL DEFAULT now(),
    dte_carga timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tab_autores_emendas_id_parlamentar
    ON transfere_pro_transferegov.tab_autores_emendas USING btree (id_parlamentar);

-- ---------------------------------------------------------------------------
-- tab_parlamentares_alias — cada grafia vista, normalizada, aponta para a pessoa
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_parlamentares_alias (
    nome_normalizado character varying(200) PRIMARY KEY,
    nome_original character varying(200),
    id_parlamentar integer NOT NULL REFERENCES transfere_pro_transferegov.tab_parlamentares (id_parlamentar),
    origem character varying(30) NOT NULL,
    dte_carga timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tab_parlamentares_alias_id_parlamentar
    ON transfere_pro_transferegov.tab_parlamentares_alias USING btree (id_parlamentar);

-- ---------------------------------------------------------------------------
-- tab_emendas_beneficiarios_ano — siconv_emenda.csv
-- Grão: emenda no ano × programa × beneficiário × proposta (0 = sem proposta)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_emendas_beneficiarios_ano (
    id bigserial PRIMARY KEY,
    ano smallint NOT NULL,
    nr_emenda character varying(10) NOT NULL,
    cod_autor character(4) NOT NULL,
    cod_programa_emenda character varying(20) NOT NULL,
    beneficiario_emenda character varying(20) NOT NULL,
    id_proposta integer NOT NULL DEFAULT 0,
    qualif_proponente character varying(100),
    ind_impositivo character varying(5),
    tipo_parlamentar character varying(30),
    valor_repasse_proposta_emenda numeric(19,2),
    valor_repasse_emenda numeric(19,2),
    row_hash character(32) NOT NULL,
    fl_ativo boolean NOT NULL DEFAULT true,
    dte_inclusao timestamp without time zone NOT NULL DEFAULT now(),
    dte_carga timestamp without time zone NOT NULL DEFAULT now(),
    dte_inativacao timestamp without time zone,
    CONSTRAINT uq_tab_emendas_beneficiarios_ano
        UNIQUE (ano, nr_emenda, cod_programa_emenda, beneficiario_emenda, id_proposta)
);

CREATE INDEX IF NOT EXISTS idx_tab_emendas_benef_ano_cod_autor
    ON transfere_pro_transferegov.tab_emendas_beneficiarios_ano USING btree (cod_autor);
CREATE INDEX IF NOT EXISTS idx_tab_emendas_benef_ano_beneficiario
    ON transfere_pro_transferegov.tab_emendas_beneficiarios_ano USING btree (beneficiario_emenda);
CREATE INDEX IF NOT EXISTS idx_tab_emendas_benef_ano_id_proposta
    ON transfere_pro_transferegov.tab_emendas_beneficiarios_ano USING btree (id_proposta);

-- ---------------------------------------------------------------------------
-- tab_emendas_apoiadores — apoiadores_emendas_programas.csv
-- Grão: registro cnpj×programa×emenda × parlamentar solicitante ('' = nenhum)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.tab_emendas_apoiadores (
    id_cnpj_programa_emenda integer NOT NULL,
    parlamentar_solicitante character varying(200) NOT NULL DEFAULT '',
    nr_emenda character varying(10),
    cod_autor character(4),
    ano smallint,
    nome_parlamentar character varying(200),
    indicacao character varying(30),
    id_parlamentar_solicitante integer REFERENCES transfere_pro_transferegov.tab_parlamentares (id_parlamentar),
    id_programa integer,
    cnpj_proponente character varying(20),
    nome_proponente character varying(255),
    valor_repasse_proposta numeric(19,2),
    row_hash character(32) NOT NULL,
    fl_ativo boolean NOT NULL DEFAULT true,
    dte_inclusao timestamp without time zone NOT NULL DEFAULT now(),
    dte_carga timestamp without time zone NOT NULL DEFAULT now(),
    dte_inativacao timestamp without time zone,
    CONSTRAINT pk_tab_emendas_apoiadores PRIMARY KEY (id_cnpj_programa_emenda, parlamentar_solicitante)
);

CREATE INDEX IF NOT EXISTS idx_tab_emendas_apoiadores_cod_autor
    ON transfere_pro_transferegov.tab_emendas_apoiadores USING btree (cod_autor);
CREATE INDEX IF NOT EXISTS idx_tab_emendas_apoiadores_nr_emenda
    ON transfere_pro_transferegov.tab_emendas_apoiadores USING btree (nr_emenda);
CREATE INDEX IF NOT EXISTS idx_tab_emendas_apoiadores_solicitante
    ON transfere_pro_transferegov.tab_emendas_apoiadores USING btree (id_parlamentar_solicitante);
CREATE INDEX IF NOT EXISTS idx_tab_emendas_apoiadores_cnpj
    ON transfere_pro_transferegov.tab_emendas_apoiadores USING btree (cnpj_proponente);

-- ---------------------------------------------------------------------------
-- vw_emendas_resumo_ano — substitui os agregados da tab_emendas, por ano
-- ---------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS transfere_pro_transferegov.vw_emendas_resumo_ano AS
SELECT
    b.ano,
    b.nr_emenda,
    b.cod_autor,
    a.id_parlamentar,
    COALESCE(p.nome_parlamentar, a.nome_parlamentar) AS nome_parlamentar,
    a.tipo_parlamentar,
    COUNT(DISTINCT b.beneficiario_emenda) AS qtd_beneficiarios,
    COUNT(*) FILTER (WHERE b.ind_impositivo = 'SIM') AS qtd_impositivo,
    COUNT(*) FILTER (WHERE b.ind_impositivo = 'NAO') AS qtd_nao_impositivo,
    COUNT(DISTINCT NULLIF(b.id_proposta, 0)) AS qtd_propostas,
    COUNT(DISTINCT b.cod_programa_emenda) AS qtd_programas,
    COALESCE(SUM(b.valor_repasse_emenda), 0) AS valor_total_repasse_emenda,
    COALESCE(SUM(b.valor_repasse_proposta_emenda), 0) AS valor_total_repasse_proposta_emenda
FROM transfere_pro_transferegov.tab_emendas_beneficiarios_ano AS b
JOIN transfere_pro_transferegov.tab_autores_emendas AS a ON a.cod_autor = b.cod_autor
LEFT JOIN transfere_pro_transferegov.tab_parlamentares AS p ON p.id_parlamentar = a.id_parlamentar
WHERE b.fl_ativo
GROUP BY b.ano, b.nr_emenda, b.cod_autor, a.id_parlamentar,
         COALESCE(p.nome_parlamentar, a.nome_parlamentar), a.tipo_parlamentar
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS uq_vw_emendas_resumo_ano
    ON transfere_pro_transferegov.vw_emendas_resumo_ano USING btree (ano, nr_emenda);
CREATE INDEX IF NOT EXISTS idx_vw_emendas_resumo_ano_parlamentar
    ON transfere_pro_transferegov.vw_emendas_resumo_ano USING btree (id_parlamentar);
