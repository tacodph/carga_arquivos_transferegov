# carga_arquivos_transferegov

Pipeline de carga incremental dos dumps públicos SICONV/TransfereGov (transferências discricionárias) para PostgreSQL.

## Objetivo

Baixar CSVs do repositório público do governo, mapear cada arquivo à tabela de destino e ingerir incrementalmente (INSERT + UPDATE) no schema `transfere_pro_transferegov`.

**Escopo:** 62 arquivos CSV → 65 tabelas destino (discricionárias).

**Fora de escopo:** Transferências Especiais (API REST) — ver `../etl_transferencias_especiais/`.

## Stack de implementação

**Python 3.10+** com `psycopg2`, `python-dotenv`, `openpyxl`, `pandas`.

Guia de desenvolvimento faseado: [`docs/prompts/README.md`](docs/prompts/README.md).

## Carga incremental

Estratégia: **staging + MERGE** (sem TRUNCATE em tabelas destino).

1. CSV → `stg_<tabela>` (staging)
2. UPDATE registros existentes por chave natural
3. INSERT registros novos
4. Atualizar `dte_carga` / `data_carga`
5. Registrar execução em `tab_data_carga`

Detalhes: [`docs/ESTRATEGIA_INCREMENTAL.md`](docs/ESTRATEGIA_INCREMENTAL.md)

## Configuração (`.env`)

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=transferepro
DB_USER=postgres
DB_PASSWORD=<senha>
DB_SCHEMA=transfere_pro_transferegov
```

Template: `.env.example`

## Arquivos de referência obrigatórios

| Arquivo | Papel |
|---------|-------|
| `data/lista_arquivo_tabela.xlsx` | Fonte de verdade: `arquivo → tabela → grupo → zip → URL` |
| `docs/CARGA_DISCRICIONARIAS.md` | Especificação completa do pipeline |
| `docs/ESTRATEGIA_INCREMENTAL.md` | Regras de MERGE incremental |
| `docs/CHAVES_NATURAIS.md` | Chaves naturais por tabela (65 tabelas) |
| `docs/Documentacao_Banco_TransfereGov.md` | Modelo fonte `bd_portal` (54 tabelas, FKs) |
| `D:\projetos_herd\transferepro\database\seeders\transfere_pro_transferegov\seed-order.php` | Ordem de carga por FK |
| `D:\projetos_herd\transferepro\database\migrations\transfere_pro_transferegov\` | DDL das tabelas destino |

## Convenções de destino

| Atributo | Valor |
|----------|-------|
| Schema | `transfere_pro_transferegov` |
| Tabelas de entidade | prefixo `tab_*` |
| Tabelas de relacionamento | prefixo `rlc_*` |

## Skills de domínio

Ativar as skills em `.claude/skills/` ao trabalhar neste projeto:

| Skill | Quando usar |
|-------|-------------|
| `transferegov-carga-arquivos` | Download de ZIPs, extração CSV, mapeamento arquivo-tabela |
| `transferegov-schema` | Convenções de schema, hierarquia, ordem FK |
| `transferegov-carga-incremental` | MERGE, staging, chaves naturais, UPSERT |

## Regras de implementação

1. **Carga incremental** — nunca TRUNCATE em tabelas destino
2. **Validar contra o XLSX** — mapeamento arquivo↔tabela em `lista_arquivo_tabela.xlsx`
3. **Respeitar ordem FK** — ordem em `load-order.md`
4. **Chaves naturais** — consultar `docs/CHAVES_NATURAIS.md`; tabelas `revisar` exigem confirmação no CSV
5. **Registrar carga** — atualizar `tab_data_carga` ao final
6. **Ignorar** `~$lista_arquivo_tabela.xlsx`

## Fontes de dados públicas

Base URL: `https://repositorio.dados.gov.br/seges/detru/`

5 ZIPs: `siconv.zip`, `siconv_dados_obrasgov_geral.zip`, `siconv_contrato_cipi.csv.zip`, `siconv_empenho_cipi.csv.zip`, `siconv_execucao_fisica_cipi.csv.zip`

## Estrutura do projeto

```
carga_arquivos_transferegov/
├── CLAUDE.md
├── .env / .env.example
├── requirements.txt
├── src/                    # código Python (a implementar)
├── data/
│   ├── lista_arquivo_tabela.xlsx
│   ├── downloads/
│   └── extracted/
├── logs/
├── docs/
│   ├── CARGA_DISCRICIONARIAS.md
│   ├── ESTRATEGIA_INCREMENTAL.md
│   ├── CHAVES_NATURAIS.md
│   └── prompts/            # prompts faseados para Claude Code
└── .claude/skills/
```
