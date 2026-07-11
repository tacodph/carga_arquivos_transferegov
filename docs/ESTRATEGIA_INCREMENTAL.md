# Estratégia de Carga Incremental

Regras para ingestão incremental (INSERT + UPDATE) dos dumps SICONV sem TRUNCATE.

## Por que staging + MERGE

As migrations do schema `transfere_pro_transferegov` **não definem PRIMARY KEY nem UNIQUE** na maioria das tabelas. Portanto:

- `ON CONFLICT` do PostgreSQL **não funciona** diretamente
- `COPY` direto para tabela destino causaria duplicatas em reprocessamento
- A solução é carregar em staging e fazer MERGE manual

## Fluxo por tabela

```
CSV → stg_<tabela> → UPDATE destino → INSERT destino → limpar staging
```

### 1. Staging

Criar tabela temporária ou persistente por execução:

```sql
CREATE TEMP TABLE stg_tab_propostas (LIKE transfere_pro_transferegov.tab_propostas INCLUDING ALL);
-- ou TRUNCATE stg_tab_propostas se persistente
COPY stg_tab_propostas FROM '/path/siconv_proposta.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'LATIN1');
```

Ajustar `DELIMITER` e `ENCODING` conforme o CSV real (validar no primeiro download).

### 2. UPDATE — registros existentes

```sql
UPDATE transfere_pro_transferegov.tab_propostas AS d
SET
    col1 = s.col1,
    col2 = s.col2,
    -- todas as colunas exceto chave natural
    dte_carga = now()
FROM stg_tab_propostas AS s
WHERE d.id_proposta = s.id_proposta;
```

Para tabelas com chave composta:

```sql
WHERE d.id_programa = s.id_programa
  AND d.id_proposta = s.id_proposta
```

### 3. INSERT — registros novos

```sql
INSERT INTO transfere_pro_transferegov.tab_propostas (col1, col2, ..., dte_carga)
SELECT s.col1, s.col2, ..., now()
FROM stg_tab_propostas AS s
WHERE NOT EXISTS (
    SELECT 1 FROM transfere_pro_transferegov.tab_propostas AS d
    WHERE d.id_proposta = s.id_proposta
);
```

### 4. Limpar staging

```sql
TRUNCATE stg_tab_propostas;  -- OK apenas na staging, nunca na destino
```

## Colunas de rastreio

| Coluna | Tabelas | Comportamento |
|--------|---------|---------------|
| `dte_carga` | Maioria das `tab_*` e `rlc_*` | Atualizar para `now()` em UPDATE e INSERT |
| `data_carga` | `tab_convenios`, algumas outras | Atualizar para `now()` em UPDATE e INSERT |
| `tab_data_carga` | Tabela de registro global | INSERT com data da execução ao final do pipeline |

## Chaves naturais

Definidas em [`CHAVES_NATURAIS.md`](CHAVES_NATURAIS.md) e implementadas em `src/keys.py`.

| Status | Significado | Ação |
|--------|-------------|------|
| `definida` | Chave validada contra migration/index | Implementar MERGE |
| `revisar` | Chave provisória | Confirmar contra header do CSV antes de implementar |
| `pendente` | Sem chave identificada | Bloquear MERGE até definição manual |

Tabelas com status `revisar` devem ter `requires_manual_key = True` em `keys.py` até confirmação.

## Tabelas `rlc_*` (chaves compostas)

Mesma lógica, mas o `WHERE` e o `NOT EXISTS` usam todas as colunas da chave:

```sql
-- rlc_programa_proposta
WHERE d.id_programa = s.id_programa AND d.id_proposta = s.id_proposta
```

## CSVs com múltiplas tabelas destino

### `siconv_programa.csv` → 3 tabelas

1. Carregar CSV completo em staging genérica
2. Filtrar/subset para cada tabela destino
3. MERGE independente em cada uma:
   - `tab_programas` (chave: `id_programa`)
   - `rlc_dados_disponibilizacao_programas` (chave: `id_programa, uf, modalidade`)
   - `rlc_dados_uf_modalidade_programas` (chave: `id_programa, uf, modalidade`)

### `siconv_emenda.csv` → 2 tabelas

1. Split por estrutura de colunas
2. MERGE em `tab_emendas` (chave: `nr_emenda`)
3. MERGE em `tab_beneficiarios_emendas` (chave: `nr_emenda, identif_proponente`)

## Política para registros removidos

**Não deletar** registros que desapareceram do dump. Escopo inicial:

- INSERT para registros novos
- UPDATE para registros existentes
- DELETE/soft-delete: fora de escopo (implementar futuramente se necessário)

## Transações

- Uma transação por tabela (COMMIT após MERGE bem-sucedido)
- Falha em uma tabela não reverte as anteriores (processamento independente)
- Log de erro por tabela; pipeline continua com as demais

## Registro global

Ao final de execução bem-sucedida:

```sql
INSERT INTO transfere_pro_transferegov.tab_data_carga (data_carga)
VALUES (CURRENT_DATE);
```

## Anti-padrões

| Proibido | Motivo |
|----------|--------|
| `TRUNCATE` em tabelas destino | Perde histórico; carga deve ser incremental |
| `ON CONFLICT` sem UNIQUE constraint | Falha silenciosa ou erro SQL |
| Inventar chaves naturais | Duplicatas ou updates incorretos |
| Carregar fora da ordem FK | Viola integridade referencial |
| Ignorar `dte_carga` | Perde rastreabilidade da carga |

## Validação pós-MERGE

Por tabela:

1. Contagem de linhas no staging
2. Contagem de UPDATEs executados
3. Contagem de INSERTs executados
4. `UPDATE + INSERT` deve ser ≤ linhas do staging (chaves duplicadas no CSV geram alerta)
5. Verificar FKs órfãs nas tabelas `rlc_*` (warning, não bloqueia)
