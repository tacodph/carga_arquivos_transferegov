# Prompt 05 — Orquestrador CLI

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 5 (orquestrador CLI) do pipeline SICONV.

## Contexto
Fases 1-4 implementadas. Todos os módulos src/ funcionam individualmente.
Pipeline completo: catálogo → download → extract → merge (ordem FK) → tab_data_carga.

## Leia antes de codar
- docs/CARGA_DISCRICIONARIAS.md (fluxo completo)
- .claude/skills/transferegov-schema/load-order.md (ordem FK)
- src/catalog.py, download.py, extract.py, merge.py

## Entregáveis

1. src/orchestrator.py com CLI (argparse):
   - `python -m src.orchestrator run` — pipeline completo
   - `python -m src.orchestrator run-table <tabela>` — uma tabela
   - `python -m src.orchestrator download-only` — só download + extract
   - `python -m src.orchestrator list-tables` — listar tabelas do catálogo

2. Comportamento de `run`:
   a. load_catalog()
   b. download_all()
   c. extract_csvs()
   d. Para cada tabela em load_order (que tenha CSV no catálogo):
      - Localizar CSV correspondente
      - staging → merge_table()
      - Log: tabela, updated, inserted, tempo
   e. INSERT em tab_data_carga (data_carga = CURRENT_DATE)
   f. Resumo final: tabelas processadas, erros, tempo total

3. Tratamento de CSVs multi-tabela:
   - siconv_programa.csv → split para 3 tabelas (placeholder ou função split_programa)
   - siconv_emenda.csv → split para 2 tabelas (placeholder ou função split_emenda)
   - Documentar TODO se split não for implementado nesta fase

4. Logging para logs/ com timestamp no nome do arquivo

## Restrições
- Ordem FK obrigatória (load-order.md)
- Falha em uma tabela não interrompe as demais (log error, continuar)
- tab_data_carga só atualizada se pelo menos 1 tabela processada com sucesso

## Critérios de aceite
- [ ] `python -m src.orchestrator list-tables` lista tabelas
- [ ] `python -m src.orchestrator download-only` baixa e extrai CSVs
- [ ] `python -m src.orchestrator run-table tab_programas` processa uma tabela
- [ ] `python -m src.orchestrator run` executa pipeline respeitando ordem FK
- [ ] Log salvo em logs/

## Teste sugerido
python -m src.orchestrator download-only
python -m src.orchestrator run-table tab_proponentes
python -m src.orchestrator run-table tab_programas
```
