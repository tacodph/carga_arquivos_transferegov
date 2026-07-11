# Carga de Transferências Discricionárias — SICONV/TransfereGov

Especificação do pipeline de ingestão dos dumps públicos SICONV para PostgreSQL.

## Objetivo

Consumir arquivos CSV do repositório público do governo federal, mapear cada arquivo à tabela de destino e carregar incrementalmente no schema `transfere_pro_transferegov`.

**Escopo:** transferências discricionárias (62 arquivos CSV → 65 tabelas destino).

**Fora de escopo:** Transferências Especiais via API REST (`../etl_transferencias_especiais/`).

## Fontes de dados

Base URL: `https://repositorio.dados.gov.br/seges/detru/`

| ZIP | URL | Conteúdo |
|-----|-----|----------|
| `siconv.zip` | https://repositorio.dados.gov.br/seges/detru/siconv.zip | Maioria dos CSVs (~57 arquivos) |
| `siconv_dados_obrasgov_geral.zip` | https://repositorio.dados.gov.br/seges/detru/siconv_dados_obrasgov_geral.zip | Dados CIPI obrasgov |
| `siconv_contrato_cipi.csv.zip` | https://repositorio.dados.gov.br/seges/detru/siconv_contrato_cipi.csv.zip | Contratos CIPI |
| `siconv_empenho_cipi.csv.zip` | https://repositorio.dados.gov.br/seges/detru/siconv_empenho_cipi.csv.zip | Empenhos CIPI |
| `siconv_execucao_fisica_cipi.csv.zip` | https://repositorio.dados.gov.br/seges/detru/siconv_execucao_fisica_cipi.csv.zip | Execução física CIPI |

Baixar cada ZIP uma única vez (deduplicar por `arquivo_zipado`). URLs completas estão na coluna `link` do catálogo.

## Catálogo de mapeamentos

**Arquivo:** `data/lista_arquivo_tabela.xlsx` (aba `transferepro`)

| Coluna | Descrição |
|--------|-----------|
| `arquivo` | Nome do CSV dentro do ZIP |
| `tabela` | Tabela destino (pode listar múltiplas, separadas por vírgula) |
| `grupo_funcional` | Agrupamento lógico (12 grupos) |
| `arquivo_zipado` | Nome do ZIP |
| `link` | URL de download |

### Casos especiais — CSV com múltiplas tabelas

| CSV | Tabelas destino | Ação |
|-----|-----------------|------|
| `siconv_programa.csv` | `tab_programas`, `rlc_dados_disponibilizacao_programas`, `rlc_dados_uf_modalidade_programas` | Split do CSV por regra de negócio |
| `siconv_emenda.csv` | `tab_emendas`, `tab_beneficiarios_emendas` | Split do CSV por regra de negócio |

## Destino

| Atributo | Valor |
|----------|-------|
| SGBD | PostgreSQL |
| Schema | `transfere_pro_transferegov` |
| Tabelas entidade | prefixo `tab_*` |
| Tabelas relacionamento | prefixo `rlc_*` |
| DDL | `D:\projetos_herd\transferepro\database\migrations\transfere_pro_transferegov\` |

## Configuração (`.env`)

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=transferepro
DB_USER=postgres
DB_PASSWORD=<senha>
DB_SCHEMA=transfere_pro_transferegov
```

Ver `.env.example` na raiz do projeto.

## Stack de implementação

**Python** com:

- `psycopg2` — conexão PostgreSQL
- `pandas` — manipulação de CSV (opcional, para splits)
- `openpyxl` — leitura do catálogo XLSX
- `python-dotenv` — configuração

## Fluxo do pipeline

```
1. Ler catálogo (lista_arquivo_tabela.xlsx)
2. Baixar ZIPs únicos → data/downloads/
3. Extrair CSVs → data/extracted/
4. Para cada tabela (ordem FK):
   a. COPY CSV → tabela staging (stg_<tabela>)
   b. UPDATE registros existentes (chave natural)
   c. INSERT registros novos
   d. Atualizar dte_carga / data_carga
5. Registrar execução em tab_data_carga
```

Detalhes da estratégia incremental: [`ESTRATEGIA_INCREMENTAL.md`](ESTRATEGIA_INCREMENTAL.md)

Chaves naturais por tabela: [`CHAVES_NATURAIS.md`](CHAVES_NATURAIS.md)

## Ordem de carga

Respeitar dependências FK. Lista completa em [`.claude/skills/transferegov-schema/load-order.md`](../.claude/skills/transferegov-schema/load-order.md).

Ordem resumida:

1. Núcleo: `tab_programas` → `tab_proponentes` → `tab_propostas` → `tab_convenios`
2. Relacionamentos: `rlc_*` após entidades referenciadas
3. Financeiro: `tab_empenhos` → `tab_desembolsos` → `rlc_empenhos_desembolsos` → `tab_pagamentos`
4. Registro: `tab_data_carga` ao final

## Estrutura de diretórios Python

```
carga_arquivos_transferegov/
├── .env / .env.example
├── requirements.txt
├── src/
│   ├── config.py          # lê .env
│   ├── catalog.py         # lê XLSX
│   ├── download.py        # baixa ZIPs
│   ├── extract.py         # extrai CSVs
│   ├── keys.py            # chaves naturais por tabela
│   ├── staging.py         # COPY → stg_*
│   ├── merge.py           # UPDATE + INSERT incremental
│   └── orchestrator.py    # pipeline CLI
├── data/
│   ├── lista_arquivo_tabela.xlsx
│   ├── downloads/         # ZIPs baixados
│   └── extracted/         # CSVs extraídos
├── logs/                  # logs de execução
└── docs/
    ├── CARGA_DISCRICIONARIAS.md   # este arquivo
    ├── ESTRATEGIA_INCREMENTAL.md
    ├── CHAVES_NATURAIS.md
    └── prompts/                   # prompts para Claude Code
```

## Desenvolvimento com Claude Code

Siga os prompts faseados em [`docs/prompts/README.md`](prompts/README.md).

Skills de domínio em `.claude/skills/`:

| Skill | Uso |
|-------|-----|
| `transferegov-carga-arquivos` | Download, extração, mapeamento |
| `transferegov-schema` | Convenções, ordem FK |
| `transferegov-carga-incremental` | MERGE, UPSERT, staging |

## Referências

| Documento | Conteúdo |
|-----------|----------|
| `docs/Documentacao_Banco_TransfereGov.md` | Modelo fonte SICONV (54 tabelas, FKs) |
| `docs/ESTRATEGIA_INCREMENTAL.md` | Regras de carga incremental |
| `docs/CHAVES_NATURAIS.md` | Chaves naturais por tabela |
| `CLAUDE.md` | Contexto geral do projeto |
