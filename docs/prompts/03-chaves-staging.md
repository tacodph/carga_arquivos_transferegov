# Prompt 03 — Chaves Naturais e Staging

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 3 (chaves naturais e staging) do pipeline SICONV.

## Contexto
Fases 1-2 implementadas. CSVs extraídos em data/extracted/.
Estratégia: staging + MERGE (sem ON CONFLICT, sem TRUNCATE em tabelas destino).

## Leia antes de codar
- docs/CHAVES_NATURAIS.md (65 tabelas com chaves e status)
- docs/ESTRATEGIA_INCREMENTAL.md (seção staging)
- .claude/skills/transferegov-carga-incremental/SKILL.md

## Entregáveis

1. src/keys.py:
   - Dict TABLE_KEYS com todas as 65 tabelas do catálogo
   - Cada entrada: {columns: list[str], status: str, requires_manual_key: bool}
   - Status "definida" → requires_manual_key = False
   - Status "revisar" → requires_manual_key = True
   - Função get_key(table_name) → list[str]
   - Função is_merge_ready(table_name) → bool (True se status == "definida")

2. src/staging.py:
   - Função create_staging_table(conn, target_table) → cria stg_<tabela> (TEMP ou TRUNCATE se existir)
   - Função load_csv_to_staging(conn, csv_path, target_table, delimiter=';', encoding='latin-1')
   - Usar COPY do PostgreSQL para performance
   - Detectar header do CSV automaticamente
   - Função truncate_staging(conn, target_table)
   - Retornar contagem de linhas carregadas

## Restrições
- Staging usa prefixo stg_ (ex: stg_tab_propostas)
- TRUNCATE permitido apenas em tabelas staging, nunca em destino
- Tabelas com requires_manual_key=True devem gerar warning e ser puladas
- Validar que colunas do CSV são compatíveis com a tabela destino (amostrar header)

## Critérios de aceite
- [ ] keys.py cobre 65 tabelas
- [ ] is_merge_ready("tab_propostas") retorna True
- [ ] is_merge_ready("tab_consorcios") retorna False (revisar)
- [ ] load_csv_to_staging carrega siconv_proposta.csv em stg_tab_propostas
- [ ] Contagem de linhas no staging > 0

## Teste sugerido
python -c "
from src.config import get_connection
from src.staging import create_staging_table, load_csv_to_staging
from src.keys import is_merge_ready
conn = get_connection()
assert is_merge_ready('tab_propostas')
create_staging_table(conn, 'tab_propostas')
count = load_csv_to_staging(conn, 'data/extracted/siconv_proposta.csv', 'tab_propostas')
print(f'Linhas staging: {count}')
conn.commit()
conn.close()
"
```
