---
name: transferegov-carga-incremental
description: >-
  Implements incremental SICONV/TransfereGov data load using staging tables and
  MERGE (UPDATE existing rows by natural key, INSERT new rows) into
  transfere_pro_transferegov. Use when working on incremental load, upsert,
  update existing data, staging, merge, dte_carga, natural keys, or
  reprocessing CSV dumps without truncate.
---

# TransfereGov — Carga Incremental

## Estratégia

**Staging + MERGE** — sem TRUNCATE em tabelas destino, sem ON CONFLICT (DDL sem UNIQUE).

```
CSV → stg_<tabela> → UPDATE destino → INSERT destino → registrar tab_data_carga
```

Documentação completa: `docs/ESTRATEGIA_INCREMENTAL.md`

## Por tabela

1. COPY CSV para `stg_<tabela>`
2. UPDATE destino WHERE chave_natural coincide (setar `dte_carga = now()`)
3. INSERT destino WHERE NOT EXISTS (chave no destino)
4. TRUNCATE apenas staging
5. Commit transação

## Chaves naturais

Definidas em `docs/CHAVES_NATURAIS.md` e `src/keys.py`.

| Status | Ação |
|--------|------|
| `definida` | Implementar MERGE |
| `revisar` | Confirmar chave no CSV antes de MERGE; `requires_manual_key = True` |

Exemplos:

| Tabela | Chave |
|--------|-------|
| `tab_propostas` | `id_proposta` |
| `tab_convenios` | `nr_convenio` |
| `rlc_programa_proposta` | `id_programa, id_proposta` |
| `tab_contratos` | `cod_licitacao, num_contrato` |

## SQL de referência

### UPDATE

```sql
UPDATE transfere_pro_transferegov.tab_propostas AS d
SET col1 = s.col1, dte_carga = now()
FROM stg_tab_propostas AS s
WHERE d.id_proposta = s.id_proposta;
```

### INSERT

```sql
INSERT INTO transfere_pro_transferegov.tab_propostas (...)
SELECT ..., now()
FROM stg_tab_propostas AS s
WHERE NOT EXISTS (
    SELECT 1 FROM transfere_pro_transferegov.tab_propostas AS d
    WHERE d.id_proposta = s.id_proposta
);
```

## Colunas de rastreio

| Coluna | Quando atualizar |
|--------|------------------|
| `dte_carga` | UPDATE e INSERT (maioria das tabelas) |
| `data_carga` | UPDATE e INSERT (`tab_convenios` e outras) |
| `tab_data_carga` | INSERT com `CURRENT_DATE` ao final do pipeline |

## Política de deleção

Registros ausentes no dump **não são deletados**. Escopo: INSERT + UPDATE apenas.

## Transações

- Uma transação por tabela
- Falha em uma tabela não reverte as anteriores
- Log de erro por tabela; pipeline continua

## Anti-padrões

- TRUNCATE em tabelas destino
- ON CONFLICT sem UNIQUE constraint
- Inventar chaves naturais
- Ignorar tabelas com status `revisar` sem validação

## Prompts de implementação

Siga a ordem em `docs/prompts/README.md`:

1. Setup Python
2. Catálogo e download
3. Chaves e staging
4. **MERGE incremental** (este skill)
5. Orquestrador
6. Validação

## Recursos

- Estratégia: `docs/ESTRATEGIA_INCREMENTAL.md`
- Chaves: `docs/CHAVES_NATURAIS.md`
- Ordem FK: [../transferegov-schema/load-order.md](../transferegov-schema/load-order.md)
- Download/mapeamento: [../transferegov-carga-arquivos/SKILL.md](../transferegov-carga-arquivos/SKILL.md)
