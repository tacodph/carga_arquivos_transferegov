# Prompts para desenvolvimento no Claude Code

Prompts faseados para implementar o pipeline de carga incremental SICONV em Python.

## Pré-requisitos

Antes de executar os prompts:

1. Migrations do transferepro aplicadas (`transfere_pro_transferegov` schema existe)
2. `.env` configurado com credenciais PostgreSQL (copiar de `.env.example`)
3. Python 3.10+ instalado
4. Catálogo em `data/lista_arquivo_tabela.xlsx` presente

## Ordem de execução

Execute os prompts **na sequência**. Cada fase depende da anterior.

| # | Arquivo | Entrega | Depende de |
|---|---------|---------|------------|
| 1 | [01-setup-python.md](01-setup-python.md) | Estrutura do projeto, config, requirements | — |
| 2 | [02-catalogo-download.md](02-catalogo-download.md) | Leitura XLSX, download e extração ZIPs | Fase 1 |
| 3 | [03-chaves-staging.md](03-chaves-staging.md) | Chaves naturais, staging, COPY | Fases 1–2 |
| 4 | [04-merge-incremental.md](04-merge-incremental.md) | MERGE UPDATE+INSERT | Fases 1–3 |
| 5 | [05-orquestrador.md](05-orquestrador.md) | CLI do pipeline completo | Fases 1–4 |
| 6 | [06-validacao.md](06-validacao.md) | Logs, validação, tab_data_carga | Fases 1–5 |
| 7 | [07-agendamento-windows.md](07-agendamento-windows.md) | Agendador de Tarefas Windows (09:15) | Fases 1–6 |

## Como usar

1. Abra o Claude Code no diretório `carga_arquivos_transferegov`
2. Copie o conteúdo do prompt da fase atual
3. Cole como mensagem no Claude Code
4. Verifique os critérios de aceite antes de avançar
5. Execute o comando de teste sugerido

## Documentação de referência

| Documento | Quando consultar |
|-----------|------------------|
| `docs/CARGA_DISCRICIONARIAS.md` | Visão geral do pipeline |
| `docs/ESTRATEGIA_INCREMENTAL.md` | Regras de MERGE |
| `docs/CHAVES_NATURAIS.md` | Chaves por tabela |
| `CLAUDE.md` | Contexto e convenções |
| `.claude/skills/` | Skills de domínio |

## Skills ativas

O Claude Code deve ativar automaticamente:

- `transferegov-carga-arquivos` — download e mapeamento
- `transferegov-schema` — ordem FK e convenções
- `transferegov-carga-incremental` — MERGE e staging

## Teste incremental recomendado

Após cada fase, testar com uma tabela pequena antes do pipeline completo:

```
tab_programas  →  siconv_programa.csv  (após split)
tab_proponentes →  siconv_proponentes.csv
```

Depois expandir para tabelas maiores (`tab_propostas`, `tab_convenios`).

## Pós-pipeline

Após validação (fase 6) e com `run` estável, execute a fase 7 para agendar a carga diária às 09:15 no Windows Task Scheduler.
