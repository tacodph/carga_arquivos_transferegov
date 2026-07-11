# Prompt 04 — MERGE Incremental

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 4 (MERGE incremental) do pipeline SICONV.

## Contexto
Fases 1-3 implementadas: config, catalog, download, extract, keys, staging.
Estratégia: UPDATE registros existentes + INSERT novos, usando chaves naturais.

## Leia antes de codar
- docs/ESTRATEGIA_INCREMENTAL.md (UPDATE, INSERT, transações)
- docs/CHAVES_NATURAIS.md
- src/keys.py
- src/staging.py

## Entregáveis

1. src/merge.py:
   - Função merge_table(conn, target_table, staging_table=None):
     a. Carregar staging (se csv_path fornecido, integrar com staging.py)
     b. UPDATE destino SET colunas = staging WHERE chave_natural coincide
     c. INSERT destino SELECT FROM staging WHERE NOT EXISTS (chave no destino)
     d. Atualizar dte_carga = now() (ou data_carga conforme tabela)
     e. Retornar dict: {updated: int, inserted: int, skipped: bool}
   - Função build_update_sql(table, key_columns, all_columns)
   - Função build_insert_sql(table, key_columns, all_columns)
   - Pular tabelas com requires_manual_key=True (log warning)
   - Uma transação por tabela (commit após sucesso, rollback em erro)

2. Tratamento de colunas de carga:
   - Se tabela tem dte_carga → setar now() no UPDATE e INSERT
   - Se tabela tem data_carga → setar now() no UPDATE e INSERT
   - Não sobrescrever colunas da chave natural no UPDATE

## Restrições
- PROIBIDO: TRUNCATE em tabelas destino
- PROIBIDO: ON CONFLICT (sem UNIQUE constraints no DDL)
- Respeitar ordem FK ao chamar merge_table em lote (usar load-order.md)
- Não implementar DELETE de registros ausentes no dump

## Critérios de aceite
- [ ] merge_table("tab_propostas") executa UPDATE + INSERT sem erro
- [ ] Segunda execução do mesmo CSV resulta em updated > 0, inserted = 0 (ou poucos)
- [ ] dte_carga atualizado nas linhas modificadas
- [ ] Tabelas "revisar" são puladas com warning no log

## Teste sugerido
python -c "
from src.config import get_connection
from src.staging import create_staging_table, load_csv_to_staging, truncate_staging
from src.merge import merge_table
conn = get_connection()
create_staging_table(conn, 'tab_propostas')
load_csv_to_staging(conn, 'data/extracted/siconv_proposta.csv', 'tab_propostas')
r1 = merge_table(conn, 'tab_propostas')
print('1a execução:', r1)
truncate_staging(conn, 'tab_propostas')
load_csv_to_staging(conn, 'data/extracted/siconv_proposta.csv', 'tab_propostas')
r2 = merge_table(conn, 'tab_propostas')
print('2a execução:', r2)
conn.close()
"
```
