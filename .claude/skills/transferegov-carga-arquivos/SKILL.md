---
name: transferegov-carga-arquivos
description: >-
  Downloads SICONV/TransfereGov CSV dumps from
  api-publica.transferegov.gestao.gov.br/downloads/dadosgov, maps files to
  PostgreSQL tables via lista_arquivo_tabela.xlsx, and ingests into
  transfere_pro_transferegov. Use when working on bulk file load, CSV ingestion,
  ZIP extraction, carga de arquivos, lista_arquivo_tabela, tab_ or rlc_ tables,
  or SICONV discricionarias data pipeline.
---

# TransfereGov — Carga de Arquivos

## Catálogo de mapeamentos

Fonte de verdade: `data/lista_arquivo_tabela.xlsx` (aba `transferepro`, 62 linhas).

| Coluna | Descrição |
|--------|-----------|
| `arquivo` | Nome do CSV dentro do ZIP |
| `tabela` | Tabela destino no schema `transfere_pro_transferegov` |
| `grupo_funcional` | Agrupamento lógico (12 grupos) |
| `arquivo_zipado` | Nome do ZIP que contém o CSV |
| `link` | URL de download completa |

### Exemplos de mapeamento

```
siconv_convenio.csv          → tab_convenios                    (Tabelas Nucleo)         ← siconv_convenio.zip
siconv_empenho_desembolso.csv → rlc_empenhos_desembolsos        (Fluxo Financeiro)       ← siconv_empenho_desembolso.zip
siconv_programa_proposta.csv  → rlc_programa_proposta           (Proponentes e Propostas) ← siconv_programa_proposta.zip
siconv_dados_obrasgov_geral.csv → rlc_dados_obrasgov_geral     (Dados Cipi)             ← siconv_dados_obrasgov_geral.zip
```

### CSVs com múltiplas tabelas destino

Dois arquivos alimentam mais de uma tabela — exigem split ou carga derivada:

| CSV | Tabelas destino |
|-----|-----------------|
| `siconv_programa.csv` | `tab_programas`, `rlc_dados_disponibilizacao_programas`, `rlc_dados_uf_modalidade_programas` |
| `siconv_emenda.csv` | `tab_emendas`, `tab_beneficiarios_emendas` |

Ao implementar, definir com o usuário como separar os dados de cada CSV nessas tabelas.

## ZIPs de download

Cada CSV do catálogo tem um ZIP individual na API pública:

Base URL: `https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov`

Regra: `siconv_convenio.csv` → `siconv_convenio.zip` →
`https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov/siconv_convenio.zip`

`src/catalog.py` deriva `zip_name` e `link` a partir do nome do CSV e de `DOWNLOAD_BASE_URL`
(não depende mais do monolito `siconv.zip` em `repositorio.dados.gov.br`).

Arquivos fora do catálogo (ex.: `app_parceriasgov_necessidades.zip`) são ignorados.

## Workflow de carga

```
Task Progress:
- [ ] 1. Ler lista_arquivo_tabela.xlsx
- [ ] 2. Baixar ZIPs (deduplicar por arquivo_zipado)
- [ ] 3. Extrair CSVs dos ZIPs
- [ ] 4. Validar: CSV existe no ZIP e tabela existe no schema destino
- [ ] 5. Carregar tabelas na ordem FK (ver skill transferegov-schema)
- [ ] 6. Registrar execução em tab_data_carga
```

### Passo 1 — Ler catálogo

Ler o XLSX e produzir lista de `{arquivo, tabela, grupo_funcional, arquivo_zipado, link}`.

### Passo 2 — Download

- Baixar cada ZIP único uma vez
- Salvar em diretório de staging (ex.: `data/downloads/` ou `data/staging/`)
- Verificar integridade (tamanho > 0, ZIP válido)

### Passo 3 — Extração

- Extrair apenas os CSVs listados no catálogo
- Manter nomes originais dos arquivos

### Passo 4 — Validação pré-carga

Para cada par arquivo↔tabela:

1. CSV extraído existe no filesystem
2. Tabela destino existe em `transfere_pro_transferegov` (consultar migrations em transferepro)
3. Colunas do CSV são compatíveis com a tabela (amostrar header)

### Passo 5 — Ingestão incremental

- Carregar na ordem definida em `load-order.md` (skill `transferegov-schema`)
- Estratégia: **staging + MERGE** (UPDATE + INSERT por chave natural)
- Ver `docs/ESTRATEGIA_INCREMENTAL.md` e skill `transferegov-carga-incremental`
- **Proibido:** TRUNCATE em tabelas destino
- Processar em lotes para tabelas grandes

### Passo 6 — Registro

Atualizar `tab_data_carga` com timestamp da execução.

## Validações pós-carga

- Contagem de linhas inseridas por tabela
- Comparar com contagem de linhas do CSV (descontando header)
- Verificar FKs: nenhum registro órfão nas tabelas `rlc_*`
- Log de erros por tabela (linhas rejeitadas, tipo incompatível)

## Anti-padrões

- **Não inventar nomes de tabela** — usar exclusivamente o XLSX
- **Não carregar fora da ordem FK** — viola integridade referencial
- **Não misturar com Transferências Especiais** — domínio e API diferentes (`../etl_transferencias_especiais/`)
- **Não referenciar `~$lista_arquivo_tabela.xlsx`** — arquivo temporário do Excel
- **Não assumir stack** — Python, Pentaho ou PHP só com decisão do usuário

## Leitura do XLSX (referência)

```python
import openpyxl

wb = openpyxl.load_workbook("data/lista_arquivo_tabela.xlsx", read_only=True)
ws = wb.active
for row in ws.iter_rows(min_row=2, values_only=True):
    arquivo, tabela, grupo, zip_name, link = row
    if arquivo:
        print(arquivo, tabela, zip_name)
```

## Recursos adicionais

- Carga incremental: [../transferegov-carga-incremental/SKILL.md](../transferegov-carga-incremental/SKILL.md)
- Estratégia MERGE: `docs/ESTRATEGIA_INCREMENTAL.md`
- Ordem de carga FK: [../transferegov-schema/load-order.md](../transferegov-schema/load-order.md)
- Schema e hierarquia: [../transferegov-schema/SKILL.md](../transferegov-schema/SKILL.md)
- Prompts de desenvolvimento: `docs/prompts/README.md`
- Dicionário completo: `docs/Documentacao_Banco_TransfereGov.md`
