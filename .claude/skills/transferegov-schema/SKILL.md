---
name: transferegov-schema
description: >-
  Describes TransfereGov/SICONV database schema conventions, entity hierarchy,
  functional groups, and FK-aware load order for transfere_pro_transferegov.
  Use when working with tab_ or rlc_ tables, schema migrations, foreign key
  dependencies, seed order, Documentacao_Banco_TransfereGov, or planning
  SICONV discricionarias data load sequence.
---

# TransfereGov — Schema e Ordem de Carga

## Hierarquia central

```
PROGRAMA  →  define os programas de governo
    └── PROPONENTES  →  entidades receptoras
            └── PROPOSTA  →  solicitação formal (20 tabelas filhas)
                    └── CONVENIO  →  instrumento formalizado (14 tabelas filhas)
```

- `proposta` é o eixo central (20 FKs de tabelas filhas)
- `convenio` é o segundo eixo (14 FKs de tabelas filhas)

## Modelo fonte vs destino

| Aspecto | Fonte (SICONV) | Destino (transferepro) |
|---------|----------------|------------------------|
| Banco | `bd_portal` | `transferepro` |
| Schema | `public` | `transfere_pro_transferegov` |
| Nomes | singular (`proposta`, `convenio`) | prefixo + plural (`tab_propostas`, `tab_convenios`) |
| Relacionamentos | tabelas associativas | prefixo `rlc_*` (`rlc_programa_proposta`) |

Não traduzir nomes manualmente — o XLSX (`data/lista_arquivo_tabela.xlsx`) já traz o nome destino.

## Prefixos de tabela

| Prefixo | Tipo | Exemplo |
|---------|------|---------|
| `tab_*` | Entidade principal | `tab_programas`, `tab_convenios`, `tab_empenhos` |
| `rlc_*` | Relacionamento N:N ou tabela associativa | `rlc_programa_proposta`, `rlc_empenhos_desembolsos` |

## Grupos funcionais (12)

Alinhados ao XLSX e à seção 2.2 de `docs/Documentacao_Banco_TransfereGov.md`:

| Grupo | Tabelas típicas |
|-------|-----------------|
| Tabelas Nucleo | `tab_programas`, `tab_proponentes`, `tab_propostas`, `tab_convenios` |
| Proponentes e Propostas | `tab_consorcios`, `rlc_programa_proponente`, `rlc_programa_proposta` |
| Fluxo Financeiro | `tab_empenhos`, `tab_desembolsos`, `tab_pagamentos`, `rlc_empenhos_desembolsos` |
| Gestao de Projetos e Obras | `tab_meta_crono_fisico`, `tab_coordenadas_obras` |
| Licitacao e Contratos | `tab_licitacao`, `tab_contratos`, `tab_itens_licitacao` |
| Gestao do Convenio | `tab_termo_aditivo`, `tab_solicitacao_alteracao`, `tab_prorroga_oficios` |
| Historico e Auditoria | `rlc_historico_situacao`, `tab_historico_projeto_basico` |
| Emendas Parlamentares | `tab_emendas`, `tab_apoiadores_emendas_programas` |
| Programa Novo PAC | `rlc_proposta_formalizacao_pac`, `tab_propostas_selecao_pac` |
| Modulo de Empresas (VRPL/ACFFO) | `tab_vrpl_*`, `tab_projeto_basico_*`, `tab_inst_cont_*` |
| Dados Cipi | `rlc_dados_obrasgov_geral`, `tab_contratos_cipi` |
| Indicadores | tabelas de indicadores do XLSX |

## Ordem de carga

Carregar tabelas na ordem de dependências FK. Lista completa em [load-order.md](load-order.md) (59 tabelas, derivada de `seed-order.php` do transferepro).

Regra geral:

1. Tabelas núcleo primeiro (`tab_programas` → `tab_proponentes` → `tab_propostas` → `tab_convenios`)
2. Relacionamentos (`rlc_*`) após as entidades que referenciam
3. Fluxo financeiro após convênios (`tab_empenhos` → `tab_desembolsos` → `rlc_empenhos_desembolsos` → `tab_pagamentos`)
4. `tab_data_carga` — registrar ao final da execução

## DDL de referência

Migrations destino: `D:\projetos_herd\transferepro\database\migrations\transfere_pro_transferegov\`

Seeders de amostra (validação): `D:\projetos_herd\transferepro\database\seeders\transfere_pro_transferegov\`

## Dicionário completo

Para colunas, tipos e FKs detalhados de cada tabela fonte, consultar `docs/Documentacao_Banco_TransfereGov.md` — não duplicar aqui.

## Recursos adicionais

- Carga incremental: [../transferegov-carga-incremental/SKILL.md](../transferegov-carga-incremental/SKILL.md)
- Chaves naturais: `docs/CHAVES_NATURAIS.md`
- Workflow de download e ingestão: [../transferegov-carga-arquivos/SKILL.md](../transferegov-carga-arquivos/SKILL.md)
- Checklist de ordem: [load-order.md](load-order.md)
