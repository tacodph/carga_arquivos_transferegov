# Prompt 06 — Validação e Monitoramento

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 6 (validação e monitoramento) do pipeline SICONV.

## Contexto
Fases 1-5 implementadas. Orquestrador CLI funcional.
Necessário: validação pós-carga, logs estruturados e verificação de integridade.

## Leia antes de codar
- docs/ESTRATEGIA_INCREMENTAL.md (seção "Validação pós-MERGE")
- docs/CARGA_DISCRICIONARIAS.md
- src/orchestrator.py

## Entregáveis

1. src/validate.py:
   - Função validate_table(conn, table, csv_path) → dict:
     - row_count_staging: int
     - row_count_destino: int
     - updated_last_run: int (se disponível no log)
     - inserted_last_run: int
     - orphan_fk_count: int (para rlc_* tables, verificar FKs órfãs)
   - Função validate_run(conn, catalog) → relatório consolidado
   - Função check_data_carga(conn) → última data em tab_data_carga

2. Melhorias no logging (src/orchestrator.py ou src/logging_config.py):
   - Formato: timestamp, nível, tabela, ação, contagem, duração
   - Arquivo: logs/carga_YYYYMMDD_HHMMSS.log
   - Resumo JSON: logs/resumo_YYYYMMDD_HHMMSS.json

3. Comando CLI adicional:
   - `python -m src.orchestrator validate` — validação pós-carga
   - `python -m src.orchestrator status` — última carga (tab_data_carga)

## Restrições
- Validação FK órfã: warning, não bloqueia pipeline
- Não alterar lógica de MERGE (apenas validar e reportar)
- Relatório legível no terminal e salvo em arquivo

## Critérios de aceite
- [ ] `python -m src.orchestrator status` mostra última data_carga
- [ ] `python -m src.orchestrator validate` gera relatório por tabela
- [ ] Log estruturado em logs/ com resumo JSON
- [ ] Contagem destino >= contagem após primeira carga
- [ ] tab_data_carga contém registro da última execução

## Teste sugerido
python -m src.orchestrator run-table tab_propostas
python -m src.orchestrator status
python -m src.orchestrator validate
cat logs/resumo_*.json
```
