-- Controle de execução da carga SICONV / Transferências Discricionárias
-- Schema: transfere_pro_transferegov (ou CONTROLE_CARGA_SCHEMA no .env)
--
-- Arquivo unificado: instalação + migração (idempotente).
-- Seguro para bancos novos e existentes — execute sempre este arquivo.

CREATE SCHEMA IF NOT EXISTS transfere_pro_transferegov;

CREATE SEQUENCE IF NOT EXISTS transfere_pro_transferegov.controle_carga_id_seq;
CREATE SEQUENCE IF NOT EXISTS transfere_pro_transferegov.controle_carga_dia_id_seq;

-- ---------------------------------------------------------------------------
-- controle_carga_dia — uma linha por execução (várias cargas no mesmo dia)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.controle_carga_dia
(
    id integer NOT NULL DEFAULT nextval(
        'transfere_pro_transferegov.controle_carga_dia_id_seq'::regclass
    ),
    dt_carga date NOT NULL DEFAULT CURRENT_DATE,
    seq_execucao_dia smallint NOT NULL,
    dt_inicio timestamp without time zone NOT NULL,
    dt_fim timestamp without time zone,
    status character varying NOT NULL DEFAULT 'EXECUTANDO'::character varying,
    qtd_arquivos_extraidos integer NOT NULL DEFAULT 0,
    qtd_arquivos_carregados integer NOT NULL DEFAULT 0,
    qtd_arquivos_erro integer NOT NULL DEFAULT 0,
    qtd_arquivos_pulados integer NOT NULL DEFAULT 0,
    mensagem text,
    log_arquivo character varying,
    CONSTRAINT controle_carga_dia_pkey PRIMARY KEY (id),
    CONSTRAINT uq_controle_carga_dia_data_seq UNIQUE (dt_carga, seq_execucao_dia),
    CONSTRAINT chk_controle_carga_dia_status CHECK (
        status::text = ANY (
            ARRAY[
                'EXECUTANDO'::character varying,
                'CARREGANDO'::character varying,
                'SUCESSO'::character varying,
                'CORRIGIDO/SUCESSO'::character varying,
                'ERRO'::character varying,
                'PARCIAL'::character varying
            ]::text[]
        )
    )
);

COMMENT ON TABLE transfere_pro_transferegov.controle_carga_dia IS
    'Uma linha por execução do pipeline; várias linhas por dt_carga (manhã/tarde/retry).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.dt_carga IS
    'Dia civil da carga (permite consultar todas as execuções do dia).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.seq_execucao_dia IS
    'Ordem da execução no dia: 1=primeira, 2=segunda (ex. após erro ou carga da tarde).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.qtd_arquivos_extraidos IS
    'CSVs extraídos dos ZIPs nesta execução.';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.qtd_arquivos_carregados IS
    'Tabelas/arquivos carregados com sucesso (MERGE concluído).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.qtd_arquivos_erro IS
    'Tabelas/arquivos com falha na carga.';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga_dia.qtd_arquivos_pulados IS
    'Tabelas ignoradas (chave em revisão, excluídas ou sem CSV).';

CREATE INDEX IF NOT EXISTS idx_controle_carga_dia_dt_carga
    ON transfere_pro_transferegov.controle_carga_dia (dt_carga DESC, seq_execucao_dia DESC);

CREATE INDEX IF NOT EXISTS idx_controle_carga_dia_dt_inicio
    ON transfere_pro_transferegov.controle_carga_dia (dt_inicio DESC);

-- ---------------------------------------------------------------------------
-- controle_carga — uma linha por tabela/arquivo processado
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transfere_pro_transferegov.controle_carga
(
    id integer NOT NULL DEFAULT nextval(
        'transfere_pro_transferegov.controle_carga_id_seq'::regclass
    ),
    id_controle_carga_dia integer,
    endpoint character varying NOT NULL,
    dt_inicio timestamp without time zone NOT NULL,
    dt_fim timestamp without time zone,
    status character varying NOT NULL DEFAULT 'EXECUTANDO'::character varying,
    total_registros integer,
    qtd_registros_inseridos integer,
    qtd_registros_atualizados integer,    
    id_controle_carga_refatorado integer,
    mensagem text,
    CONSTRAINT controle_carga_pkey PRIMARY KEY (id),
    CONSTRAINT chk_status CHECK (
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
    )
);

-- ---------------------------------------------------------------------------
-- Migração: bancos com controle_carga na versão anterior (sem novas colunas)
-- ---------------------------------------------------------------------------

ALTER TABLE transfere_pro_transferegov.controle_carga
    ADD COLUMN IF NOT EXISTS qtd_registros_inseridos integer,
    ADD COLUMN IF NOT EXISTS qtd_registros_atualizados integer,
    ADD COLUMN IF NOT EXISTS id_controle_carga_dia integer,
    ADD COLUMN IF NOT EXISTS id_controle_carga_refatorado integer;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_controle_carga_dia'
          AND conrelid = 'transfere_pro_transferegov.controle_carga'::regclass
    ) THEN
        ALTER TABLE transfere_pro_transferegov.controle_carga
            ADD CONSTRAINT fk_controle_carga_dia
            FOREIGN KEY (id_controle_carga_dia)
            REFERENCES transfere_pro_transferegov.controle_carga_dia (id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_controle_carga_refatorado'
          AND conrelid = 'transfere_pro_transferegov.controle_carga'::regclass
    ) THEN
        ALTER TABLE transfere_pro_transferegov.controle_carga
            ADD CONSTRAINT fk_controle_carga_refatorado
            FOREIGN KEY (id_controle_carga_refatorado)
            REFERENCES transfere_pro_transferegov.controle_carga (id);
    END IF;
END $$;

ALTER TABLE transfere_pro_transferegov.controle_carga
    DROP CONSTRAINT IF EXISTS chk_status;

ALTER TABLE transfere_pro_transferegov.controle_carga
    ADD CONSTRAINT chk_status CHECK (
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

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga.qtd_registros_inseridos IS
    'Registros inseridos no MERGE (INSERT).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga.qtd_registros_atualizados IS
    'Registros atualizados no MERGE (UPDATE).';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga.id_controle_carga_dia IS
    'Execução diária (controle_carga_dia) à qual este arquivo pertence.';

COMMENT ON COLUMN transfere_pro_transferegov.controle_carga.id_controle_carga_refatorado IS
    'Registro de ERRO anterior corrigido (CORRIGIDO/SUCESSO) ou não corrigido (ERRO NÃO CORRIGIDO).';

CREATE INDEX IF NOT EXISTS idx_controle_carga_endpoint_dt
    ON transfere_pro_transferegov.controle_carga (endpoint, dt_inicio DESC);

CREATE INDEX IF NOT EXISTS idx_controle_carga_dia
    ON transfere_pro_transferegov.controle_carga (id_controle_carga_dia);

CREATE INDEX IF NOT EXISTS idx_controle_carga_refatorado
    ON transfere_pro_transferegov.controle_carga (id_controle_carga_refatorado);
