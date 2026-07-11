# TransfereGov / SICONV — Documentação do Banco de Dados

> Sistema de Convênios, Contratos de Repasse e Transferências Voluntárias  
> **Banco:** `bd_portal` | **Schema:** `public` | **PostgreSQL 12.20**  
> **54 tabelas · 540 colunas · 59 restrições (FK)**  
> Documentado com SchemaSpy 6.1.0 — agosto/2025

---

## Sumário

1. [Visão Geral](#1-visão-geral-do-banco-de-dados)
2. [Arquitetura e Organização](#2-arquitetura-e-organização)
3. [Ciclo de Vida de um Instrumento](#3-ciclo-de-vida-de-um-instrumento)
4. [Relacionamentos — Chaves Estrangeiras](#4-relacionamentos--chaves-estrangeiras)
5. [Dicionário de Dados](#5-dicionário-de-dados)
   - 5.1 [Tabelas Núcleo](#51-tabelas-núcleo)
   - 5.2 [Fluxo Financeiro](#52-fluxo-financeiro)
   - 5.3 [Gestão de Projetos](#53-gestão-de-projetos)
   - 5.4 [Licitação e Contratos](#54-licitação-e-contratos)
   - 5.5 [Gestão do Convênio](#55-gestão-do-convênio)
   - 5.6 [Histórico e Auditoria](#56-histórico-e-auditoria)
   - 5.7 [Emendas Parlamentares](#57-emendas-parlamentares)
   - 5.8 [Proponentes e Propostas](#58-proponentes-e-propostas)
   - 5.9 [Tabelas Associativas (N:N)](#59-tabelas-associativas-nn)
   - 5.10 [Dados Geográficos](#510-dados-geográficos)
   - 5.11 [Programa Novo PAC](#511-programa-novo-pac)
   - 5.12 [Módulo de Empresas (VRPL/ACFFO)](#512-módulo-de-empresas-vrplacffo)
   - 5.13 [Acompanhamento de Obras](#513-acompanhamento-de-obras)
6. [Índice Alfabético de Tabelas](#6-índice-alfabético-de-tabelas)

---

## 1. Visão Geral do Banco de Dados

O banco **`bd_portal`** é o repositório central do sistema **TransfereGov** (anteriormente denominado SICONV — Sistema de Gestão de Convênios, Contratos de Repasse e Termos de Parceria). Trata-se da plataforma do Governo Federal brasileiro responsável por gerenciar todo o ciclo de vida das transferências voluntárias de recursos federais para estados, municípios, entidades privadas sem fins lucrativos e empresas públicas.

| Atributo | Valor |
|---|---|
| Banco de Dados | `bd_portal` |
| Schema | `public` |
| SGBD | PostgreSQL 12.20 |
| Total de Tabelas | 54 |
| Total de Colunas | 540 |
| Total de Restrições (FK) | 59 |
| Ferramenta de Documentação | SchemaSpy 6.1.0 |
| Data da Documentação | Agosto de 2025 |

---

## 2. Arquitetura e Organização

### 2.1 Hierarquia Central

O banco segue uma hierarquia clara de entidades principais:

```
PROGRAMA  ──────────────────────────────►  define os programas de governo
    │
    └──► PROPONENTES  ──────────────────►  cadastro das entidades receptoras
              │
              └──► PROPOSTA  ──────────►  solicitação formal (20 filhos)
                       │
                       └──► CONVENIO  ►  instrumento formalizado (14 filhos)
```

- A tabela **`proposta`** é o eixo central, recebendo referências de **20 tabelas filhas**.
- A tabela **`convenio`** é o segundo eixo, com **14 tabelas filhas** registrando a execução.

### 2.2 Grupos Funcionais

| Grupo | Tabelas | Qtd |
|---|---|---|
| **Núcleo** | `proposta`, `convenio`, `programa`, `proponentes` | 4 |
| **Fluxo Financeiro** | `desembolso`, `empenho`, `empenho_desembolso`, `pagamento`, `obtv_convenente`, `pagamento_tributo`, `ingresso_contrapartida`, `desbloqueio_cr`, `cronograma_desembolso`, `solicitacao_rendimento_aplicacao` | 10 |
| **Gestão de Projetos** | `meta_crono_fisico`, `etapa_crono_fisico`, `plano_aplicacao_detalhado`, `ajuste_plano_trabalho` | 4 |
| **Licitação e Contratos** | `licitacao`, `contrato`, `itens_licitacao`, `itens_dl`, `dl` | 5 |
| **Gestão do Convênio** | `termo_aditivo`, `solicitacao_alteracao`, `prorroga_oficio` | 3 |
| **Histórico e Auditoria** | `historico_situacao`, `historico_projeto_basico` | 2 |
| **Emendas Parlamentares** | `emenda`, `apoiadores_emendas_programas` | 2 |
| **Proponentes e Propostas** | `consorcios`, `justificativas_proposta`, `proposta_cancelada` | 3 |
| **Tabelas Associativas (N:N)** | `programa_proposta`, `programa_proponentes` | 2 |
| **Dados Geográficos** | `siconv_coordenadas_obra`, `siconv_resumo_fisico_financeiro` | 2 |
| **Programa Novo PAC** | `proposta_selecao_pac`, `pergunta_selecao_pac`, `resposta_selecao_pac`, `siconv_proposta_formalizacao_pac` | 4 |
| **Módulo de Empresas (VRPL/ACFFO)** | `vrpl_proposta_licitacao_modulo_empresas`, `vrpl_metas_submetas_modulo_empresas`, `vrpl_lotes_fornecedores_licitacao_modulo_empresas`, `projeto_basico_acffo_modulo_empresas`, `projeto_basico_lae_modulo_empresas`, `projeto_basico_metas_modulo_empresas`, `projeto_basico_submetas_modulo_empresas`, `projeto_basico_proposta_modulo_empresas`, `inst_cont_proposta_aio_modulo_empresas`, `inst_cont_contratos_lotes_empresas_modulo_empresas`, `inst_cont_metas_submetas_po_modulo_empresas` | 11 |
| **Acompanhamento de Obras** | `acomp_obras_contratos_medicoes_modulo_empresas`, `acomp_obras_valores_itens_medicao_modulo_empresas` | 2 |

---

## 3. Ciclo de Vida de um Instrumento

O ciclo de vida de uma transferência voluntária no TransfereGov percorre as seguintes fases:

1. **Disponibilização do Programa** — O órgão concedente cadastra um programa (`PROGRAMA`) definindo modalidade, período de recebimento de propostas e UFs habilitadas.
2. **Cadastro da Proposta** — O proponente (`PROPONENTES`) submete uma proposta (`PROPOSTA`) vinculada ao programa, informando objeto, valores, cronograma físico (`META_CRONO_FISICO` / `ETAPA_CRONO_FISICO`) e plano de aplicação (`PLANO_APLICACAO_DETALHADO`).
3. **Análise e Aprovação** — O concedente analisa o projeto básico (`HISTORICO_PROJETO_BASICO`) e a proposta muda de situação (`HISTORICO_SITUACAO`).
4. **Formalização** — A proposta aprovada origina um `CONVENIO`, com numeração reservada entre **700000 e 999999**.
5. **Execução Financeira** — O concedente emite empenhos (`EMPENHO`) e desembolsos (`DESEMBOLSO`). O convenente realiza pagamentos (`PAGAMENTO`) e registra ingressos de contrapartida (`INGRESSO_CONTRAPARTIDA`).
6. **Licitação e Contratação** — O convenente registra licitações (`LICITACAO`), contratos com fornecedores (`CONTRATO`) e itens adquiridos (`ITENS_LICITACAO`).
7. **Aditivos e Prorrogações** — Alterações são registradas via `SOLICITACAO_ALTERACAO`, `TERMO_ADITIVO` e `PRORROGA_OFICIO`.
8. **Prestação de Contas** — O convênio transita pelas situações de prestação de contas até ser encerrado.

---

## 4. Relacionamentos — Chaves Estrangeiras

> Todas as 59 FK possuem regra de exclusão **RESTRICT** (impede exclusão do pai se houver filhos).

| Tabela Origem | Coluna | Tabela Destino (PK) |
|---|---|---|
| `proposta` | `IDENTIF_PROPONENTE` | `proponentes (IDENTIF_PROPONENTE)` |
| `convenio` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `programa_proposta` | `ID_PROGRAMA` | `programa (ID_PROGRAMA)` |
| `programa_proposta` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `programa_proponentes` | `ID_PROGRAMA` | `programa (ID_PROGRAMA)` |
| `programa_proponentes` | `ID_PROPONENTE` | `proponentes (ID_PROPONENTE)` |
| `desembolso` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `empenho` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `empenho_desembolso` | `ID_DESEMBOLSO` | `desembolso (ID_DESEMBOLSO)` |
| `empenho_desembolso` | `ID_EMPENHO` | `empenho (ID_EMPENHO)` |
| `pagamento` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `obtv_convenente` | `NR_MOV_FIN` | `pagamento (NR_MOV_FIN)` |
| `pagamento_tributo` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `ingresso_contrapartida` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `desbloqueio_cr` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `cronograma_desembolso` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `cronograma_desembolso` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `solicitacao_rendimento_aplicacao` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `meta_crono_fisico` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `meta_crono_fisico` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `etapa_crono_fisico` | `ID_META` | `meta_crono_fisico (ID_META)` |
| `plano_aplicacao_detalhado` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `ajuste_plano_trabalho` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `licitacao` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `contrato` | `ID_LICITACAO` | `licitacao (ID_LICITACAO)` |
| `itens_licitacao` | `ID_LICITACAO` | `licitacao (ID_LICITACAO)` |
| `termo_aditivo` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `termo_aditivo` | `ID_SOLICITACAO` | `solicitacao_alteracao (ID_SOLICITACAO)` |
| `solicitacao_alteracao` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `prorroga_oficio` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `historico_situacao` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `historico_situacao` | `NR_CONVENIO` | `convenio (NR_CONVENIO)` |
| `historico_projeto_basico` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `emenda` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `apoiadores_emendas_programas` | `ID_PROGRAMA` | `programa (ID_PROGRAMA)` |
| `consorcios` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `justificativas_proposta` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `siconv_coordenadas_obra` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `siconv_resumo_fisico_financeiro` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `proposta_selecao_pac` | `ID_PROGRAMA` | `programa (ID_PROGRAMA)` |
| `proposta_selecao_pac` | `ID_PROPONENTE` | `proponentes (ID_PROPONENTE)` |
| `pergunta_selecao_pac` | `ID_PROGRAMA` | `programa (ID_PROGRAMA)` |
| `resposta_selecao_pac` | `ID_PERGUNTA_SELECAO_PAC` | `pergunta_selecao_pac (ID_PERGUNTA_SELECAO_PAC)` |
| `resposta_selecao_pac` | `ID_PROPOSTA_SELECAO_PAC` | `proposta_selecao_pac (ID_PROPOSTA_SELECAO_PAC)` |
| `siconv_proposta_formalizacao_pac` | `ID_PROPOSTA_SELECAO_PAC` | `proposta_selecao_pac (ID_PROPOSTA_SELECAO_PAC)` |
| `siconv_proposta_formalizacao_pac` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `vrpl_proposta_licitacao_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `vrpl_proposta_licitacao_modulo_empresas` | `ID_LICITACAO_VRPL` | `vrpl_lotes_fornecedores_licitacao_modulo_empresas (ID_LICITACAO_VRPL)` |
| `vrpl_metas_submetas_modulo_empresas` | `ID_PROPOSTA_VRPL` | `vrpl_proposta_licitacao_modulo_empresas (ID_PROPOSTA_VRPL)` |
| `projeto_basico_acffo_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `projeto_basico_lae_modulo_empresas` | `ID_ACFFO` | `projeto_basico_acffo_modulo_empresas (ID_ACFFO)` |
| `projeto_basico_lae_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `projeto_basico_metas_modulo_empresas` | `ID_QCI_ACFFO` | `projeto_basico_lae_modulo_empresas (ID_QCI_ACFFO)` |
| `projeto_basico_submetas_modulo_empresas` | `ID_META_PROJETO_BASICO` | `projeto_basico_metas_modulo_empresas (ID_META_PROJETO_BASICO)` |
| `projeto_basico_proposta_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `inst_cont_proposta_aio_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |
| `inst_cont_contratos_lotes_empresas_modulo_empresas` | `ID_PROPOSTA_INSTRUMENTO_CONTRATUAL` | `inst_cont_proposta_aio_modulo_empresas (ID_PROPOSTA_INSTRUMENTO_CONTRATUAL)` |
| `inst_cont_metas_submetas_po_modulo_empresas` | `ID_PROPOSTA_INSTRUMENTO_CONTRATUAL` | `inst_cont_proposta_aio_modulo_empresas (ID_PROPOSTA_INSTRUMENTO_CONTRATUAL)` |
| `acomp_obras_contratos_medicoes_modulo_empresas` | `ID_PROPOSTA` | `proposta (ID_PROPOSTA)` |

---

## 5. Dicionário de Dados

> **Legenda:** `PK` = Chave Primária · `FK` = Chave Estrangeira · `NN` = NOT NULL

---

### 5.1 Tabelas Núcleo

---

#### `proposta`

Tabela central do sistema. Registra todas as propostas de transferência voluntária submetidas pelos proponentes ao governo federal.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | PK | NN | Código sequencial do sistema para uma proposta |
| `UF_PROPONENTE` | | Sim | UF do Proponente (AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO) |
| `MUNIC_PROPONENTE` | | Sim | Município do Proponente |
| `COD_MUNIC_IBGE` | | Sim | Código IBGE do Município |
| `COD_ORGAO_SUP` | | Sim | Código do Órgão Superior do Concedente |
| `DESC_ORGAO_SUP` | | Sim | Nome do Órgão Superior do Concedente |
| `NATUREZA_JURIDICA` | | Sim | Natureza Jurídica do Proponente (Adm Pública Estadual, Municipal, Consórcio Público, Empresa pública, OSC) |
| `NR_PROPOSTA` | | Sim | Número da Proposta gerado pelo Siconv |
| `DIA_PROP` | | Sim | Dia do cadastro da Proposta |
| `MES_PROP` | | Sim | Mês do cadastro da Proposta |
| `ANO_PROP` | | Sim | Ano do cadastro da Proposta |
| `DIA_PROPOSTA` | | Sim | Data completa do cadastro da Proposta |
| `COD_ORGAO` | | Sim | Código do Órgão ou Entidade Concedente |
| `DESC_ORGAO` | | Sim | Nome do Órgão ou Entidade Concedente |
| `MODALIDADE` | | Sim | Modalidade: CONTRATO DE REPASSE, CONVENIO, TERMO DE COLABORACAO, TERMO DE FOMENTO, TERMO DE PARCERIA |
| `IDENTIF_PROPONENTE` | FK | Sim | CNPJ do Proponente → `proponentes` |
| `NM_PROPONENTE` | | Sim | Nome da Entidade Proponente |
| `CEP_PROPONENTE` | | Sim | CEP do Proponente |
| `ENDERECO_PROPONENTE` | | Sim | Endereço do Proponente |
| `BAIRRO_PROPONENTE` | | Sim | Bairro do Proponente |
| `NM_BANCO` | | Sim | Nome do Banco para depósito do recurso |
| `SITUACAO_CONTA` | | Sim | Situação da conta bancária (Aguardando Retorno do Banco, Enviada, Cadastrada, Registrada, etc.) |
| `SITUACAO_PROJETO_BASICO` | | Sim | Situação atual do Projeto Básico/Termo de Referência |
| `SIT_PROPOSTA` | | Sim | Situação atual da Proposta (Cadastrada, Em Análise, Aprovada, Rejeitada, etc.) |
| `DIA_INIC_VIGENCIA_PROPOSTA` | | Sim | Data Início da Vigência da Proposta |
| `DIA_FIM_VIGENCIA_PROPOSTA` | | Sim | Data Fim da Vigência da Proposta |
| `OBJETO_PROPOSTA` | | Sim | Descrição do Objeto da Proposta |
| `ITEM_INVESTIMENTO` | | Sim | Itens de Investimento da proposta |
| `ENVIADA_MANDATARIA` | | Sim | Indica se o Contrato de Repasse foi enviado para Instituição Mandatária (SIM, NÃO, NÃO APLICÁVEL) |
| `VL_GLOBAL_PROP` | | Sim | Valor Global da proposta (Repasse + Contrapartida) |
| `VL_REPASSE_PROP` | | Sim | Valor de Repasse do Governo Federal |
| `VL_CONTRAPARTIDA_PROP` | | Sim | Valor da Contrapartida do convenente |
| `NOME_SUBTIPO_PROPOSTA` | | Sim | Nome do subtipo de instrumento |
| `DESCRICAO_SUBTIPO_PROPOSTA` | | Sim | Descrição do subtipo do instrumento |
| `CD_AGENCIA` | | Sim | Código da Agência bancária |
| `CD_CONTA` | | Sim | Código da Conta bancária |

---

#### `convenio`

Registra os instrumentos formalizados (convênios, contratos de repasse, termos de colaboração, etc.) derivados das propostas aprovadas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | PK | NN | Número gerado pelo Siconv — faixa reservada de **700000 a 999999** |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `DIA` | | Sim | Dia da assinatura |
| `MES` | | Sim | Mês da assinatura |
| `ANO` | | Sim | Ano da assinatura |
| `DIA_ASSIN_CONV` | | Sim | Data de assinatura do Convênio |
| `SIT_CONVENIO` | | Sim | Situação atual (Em execução, Anulado, Prestação de Contas enviada, Aprovada, Inadimplente, etc.) |
| `SUBSITUACAO_CONV` | | Sim | Sub-Situação (Convênio, Cancelado, Encerrado, Proposta, Em aditivação) |
| `SITUACAO_PUBLICACAO` | | Sim | Situação da publicação (Publicado, Transferido para IN) |
| `INSTRUMENTO_ATIVO` | | Sim | Convênio ainda não finalizado (SIM, NÃO) |
| `IND_OPERA_OBTV` | | Sim | Opera com OBTV — Ordem Bancária de Transferência de Valores (SIM, NÃO) |
| `NR_PROCESSO` | | Sim | Número interno do processo físico |
| `UG_EMITENTE` | | Sim | Número da Unidade Gestora |
| `DIA_PUBL_CONV` | | Sim | Data da Publicação do Convênio |
| `DIA_INIC_VIGENC_CONV` | | Sim | Data de Início de Vigência |
| `DIA_FIM_VIGENC_CONV` | | Sim | Data de Fim de Vigência |
| `DIA_FIM_VIGENC_ORIGINAL_CONV` | | Sim | Data de Fim de Vigência Original (sem TAs e Prorrogas) |
| `DIAS_PREST_CONTAS` | | Sim | Prazo para a Prestação de Contas |
| `DIA_LIMITE_PREST_CONTAS` | | Sim | Data limite para Prestação de Contas |
| `DATA_SUSPENSIVA` | | Sim | Data prevista para resolução da Cláusula Suspensiva |
| `DATA_RETIRADA_SUSPENSIVA` | | Sim | Data de retirada da situação de Cláusula Suspensiva |
| `DIAS_CLAUSULA_SUSPENSIVA` | | Sim | Quantidade de dias calculado na Cláusula Suspensiva |
| `SITUACAO_CONTRATACAO` | | Sim | Situação da Contratação (Cláusula Suspensiva, Liminar Judicial, Normal) |
| `IND_ASSINADO` | | Sim | Convênio assinado (SIM, NÃO) |
| `MOTIVO_SUSPENSAO` | | Sim | Motivo de suspensão da cláusula suspensiva |
| `IND_FOTO` | | Sim | Possui foto (SIM, NÃO) |
| `QTDE_CONVENIOS` | | Sim | Quantidade de Instrumentos Assinados |
| `QTD_TA` | | Sim | Quantidade de Termos Aditivos |
| `QTD_PRORROGA` | | Sim | Quantidade de Prorrogas de Ofício |
| `VL_GLOBAL_CONV` | | Sim | Valor global (Repasse + Contrapartida) |
| `VL_REPASSE_CONV` | | Sim | Valor total do aporte do Governo Federal |
| `VL_CONTRAPARTIDA_CONV` | | Sim | Valor total da Contrapartida do convenente |
| `VL_EMPENHADO_CONV` | | Sim | Valor total empenhado do Governo Federal |
| `VL_DESEMBOLSADO_CONV` | | Sim | Valor total desembolsado para a conta do instrumento |
| `VL_SALDO_REMAN_TESOURO` | | Sim | Valores devolvidos ao Tesouro ao término |
| `VL_SALDO_REMAN_CONVENENTE` | | Sim | Valores devolvidos ao Convenente ao término |
| `VL_RENDIMENTO_APLICACAO` | | Sim | Valores de rendimento de aplicação financeira |
| `VL_INGRESSO_CONTRAPARTIDA` | | Sim | Total de ingressos de contrapartida |
| `VL_SALDO_CONTA` | | Sim | Saldo estimado em conta |
| `VALOR_GLOBAL_ORIGINAL_CONV` | | Sim | Valor Global Original do instrumento |

---

#### `programa`

Tabela raiz que define os programas de governo que financiam as transferências voluntárias.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROGRAMA` | PK | NN | Código sequencial do sistema para um Programa |
| `COD_ORGAO_SUP_PROGRAMA` | | Sim | Código do Órgão executor do Programa |
| `DESC_ORGAO_SUP_PROGRAMA` | | Sim | Nome do Órgão executor do Programa |
| `COD_PROGRAMA` | | Sim | Chave do programa (Cód.Órgão + Ano + Cód.Sequencial) |
| `NOME_PROGRAMA` | | Sim | Descrição do Programa de Governo |
| `SIT_PROGRAMA` | | Sim | Situação (Cadastrado, Disponibilizado, Inativo) |
| `DATA_DISPONIBILIZACAO` | | Sim | Data de disponibilização do Programa |
| `ANO_DISPONIBILIZACAO` | | Sim | Ano de disponibilização |
| `DT_PROG_INI_RECEB_PROP` | | Sim | Data início para recebimento de propostas voluntárias |
| `DT_PROG_FIM_RECEB_PROP` | | Sim | Data fim para recebimento de propostas voluntárias |
| `DT_PROG_INI_EMENDA_PAR` | | Sim | Data início para propostas de Emenda Parlamentar |
| `DT_PROG_FIM_EMENDA_PAR` | | Sim | Data fim para propostas de Emenda Parlamentar |
| `DT_PROG_INI_BENEF_ESP` | | Sim | Data início para propostas de beneficiário específico |
| `DT_PROG_FIM_BENEF_ESP` | | Sim | Data fim para propostas de beneficiário específico |
| `MODALIDADE_PROGRAMA` | | Sim | Modalidade (CONTRATO DE REPASSE, CONVENIO, TERMO DE COLABORACAO, FOMENTO, PARCERIA) |
| `NATUREZA_JURIDICA_PROGRAMA` | | Sim | Natureza Jurídica atendida pelo Programa |
| `UF_PROGRAMA` | | Sim | UFs habilitadas (nulo = atende todo o Brasil) |
| `ACAO_ORCAMENTARIA` | | Sim | Número da Ação Orçamentária |
| `NOME_SUBTIPO_PROGRAMA` | | Sim | Nome do subtipo de instrumento |
| `DESCRICAO_SUBTIPO_PROGRAMA` | | Sim | Descrição do subtipo do instrumento |

---

#### `proponentes`

Cadastro das entidades proponentes (municípios, estados, OSCs, empresas públicas) que submetem propostas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPONENTE` | PK | NN | Identificador único do proponente |
| `IDENTIF_PROPONENTE` | | NN | CNPJ do Proponente (índice único) |
| `NM_PROPONENTE` | | Sim | Nome da Entidade Proponente |
| `MUNICIPIO_PROPONENTE` | | Sim | Município do Proponente |
| `UF_PROPONENTE` | | Sim | UF do Proponente |
| `ENDERECO_PROPONENTE` | | Sim | Endereço do Proponente |
| `BAIRRO_PROPONENTE` | | Sim | Bairro do Proponente |
| `CEP_PROPONENTE` | | Sim | CEP do Proponente |
| `EMAIL_PROPONENTE` | | Sim | E-mail do Proponente |
| `TELEFONE_PROPONENTE` | | Sim | Telefone do Proponente |
| `FAX_PROPONENTE` | | Sim | Fax do Proponente |

---

### 5.2 Fluxo Financeiro

---

#### `desembolso`

Registra as Ordens Bancárias (OB) emitidas pelo Governo Federal para a conta do instrumento.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_DESEMBOLSO` | PK | NN | Identificador único do desembolso |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `DT_ULT_DESEMBOLSO` | | Sim | Data da última Ordem Bancária gerada |
| `QTD_DIAS_SEM_DESEMBOLSO` | | Sim | Indicador de dias sem desembolso (90, 180, 365 dias) |
| `DATA_DESEMBOLSO` | | Sim | Data da Ordem Bancária |
| `ANO_DESEMBOLSO` | | Sim | Ano da Ordem Bancária |
| `MES_DESEMBOLSO` | | Sim | Mês da Ordem Bancária |
| `NR_SIAFI` | | Sim | Número do documento no SIAFI |
| `UG_EMITENTE_DH` | | Sim | Código da Unidade Gestora emissora |
| `OBSERVACAO_DH` | | Sim | Observação do documento hábil |
| `VL_DESEMBOLSADO` | | Sim | Valor disponibilizado para a conta do instrumento |

---

#### `empenho`

Registra as Notas de Empenho emitidas no SIAFI para os convênios.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_EMPENHO` | PK | NN | Identificador único do empenho |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_EMPENHO` | | Sim | Número da Nota de Empenho |
| `TIPO_NOTA` | | Sim | Código do Tipo de Empenho |
| `DESC_TIPO_NOTA` | | Sim | Descrição do Tipo (Empenho Original, Anulação, Reforço, Estorno, etc.) |
| `DATA_EMISSAO` | | Sim | Data de emissão do empenho |
| `COD_SITUACAO_EMPENHO` | | Sim | Código da situação atual |
| `DESC_SITUACAO_EMPENHO` | | Sim | Descrição da situação (Registrado no SIAFI, Enviado) |
| `UG_EMITENTE` | | Sim | Unidade Gestora Emitente |
| `UG_RESPONSAVEL` | | Sim | Unidade Gestora Responsável |
| `FONTE_RECURSO` | | Sim | Fonte de Recurso da Nota de Empenho |
| `NATUREZA_DESPESA` | | Sim | Código da natureza de despesa |
| `PLANO_INTERNO` | | Sim | Plano Interno (até 11 dígitos alfa-numéricos) |
| `PTRES` | | Sim | Programa de Trabalho Resumido |
| `VALOR_EMPENHO` | | Sim | Valor empenhado |
| `RESULTADO_PRIMARIO` | | Sim | Resultado primário do empenho |
| `OBSERVACAO_EMPENHO` | | Sim | Observação do empenho |
| `DESCRICAO_EMENDA_SIAFI` | | Sim | Descrição da emenda SIAFI |

---

#### `empenho_desembolso`

Tabela de junção que associa empenhos a desembolsos (relação N:N).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_DESEMBOLSO` | FK | Sim | → `desembolso` |
| `ID_EMPENHO` | FK | Sim | → `empenho` |
| `VALOR_GRUPO` | | Sim | Valor presente nos dados orçamentários da OB |

---

#### `pagamento`

Registra os pagamentos realizados aos fornecedores a partir da conta do instrumento.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_MOV_FIN` | PK | NN | Número identificador da movimentação financeira |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `IDENTIF_FORNECEDOR` | | Sim | CNPJ/CPF do Fornecedor |
| `NOME_FORNECEDOR` | | Sim | Nome do Fornecedor |
| `TP_MOV_FINANCEIRA` | | Sim | Tipo da movimentação (Pagamento a favorecido, com OBTV) |
| `DATA_PAG` | | Sim | Data da realização do pagamento |
| `NR_DL` | | Sim | Número do Documento de Liquidação |
| `DESC_DL` | | Sim | Descrição do DL (Diárias, Duplicata, Fatura, Nota Fiscal, Folha de Pagamento, etc.) |
| `VL_PAGO` | | Sim | Valor do pagamento |
| `ID_DL` | | Sim | Identificador do Documento de Liquidação |
| `DATA_EMISSAO_DL` | | Sim | Data de Emissão do Documento de Liquidação |

---

#### `obtv_convenente`

Registra os pagamentos via OBTV (Ordem Bancária de Transferência de Valores) diretamente aos favorecidos.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_MOV_FIN` | FK | Sim | → `pagamento` |
| `IDENTIF_FAVORECIDO_OBTV_CONV` | | Sim | CNPJ/CPF do Favorecido recebedor |
| `NM_FAVORECIDO_OBTV_CONV` | | Sim | Nome do Favorecido recebedor |
| `TP_AQUISICAO` | | Sim | Tipo de Aquisição |
| `VL_PAGO_OBTV_CONV` | | Sim | Valor pago ao favorecido |

---

#### `pagamento_tributo`

Registra o pagamento de tributos vinculados ao convênio.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `DATA_TRIBUTO` | | Sim | Data da realização do pagamento do tributo |
| `VL_PAG_TRIBUTOS` | | Sim | Valor do tributo |

---

#### `ingresso_contrapartida`

Registra os ingressos de contrapartida disponibilizados pelo convenente na conta do instrumento.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `DT_INGRESSO_CONTRAPARTIDA` | | Sim | Data da disponibilização do recurso pelo Convenente |
| `VL_INGRESSO_CONTRAPARTIDA` | | Sim | Valor disponibilizado pelo Convenente |

---

#### `desbloqueio_cr`

Controla o desbloqueio de recursos para contratos de repasse.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_OB` | | Sim | Número da OB (Ordem Bancária) |
| `DATA_CADASTRO` | | Sim | Data de Cadastro |
| `DATA_ENVIO` | | Sim | Data de envio da solicitação de desbloqueio |
| `TIPO_RECURSO_DESBLOQUEIO` | | Sim | Tipo do Recurso (OB, INGRESSO CONTRAPARTIDA, RENDIMENTO APLICAÇÃO) |
| `VL_TOTAL_DESBLOQUEIO` | | Sim | Valor total de desbloqueio |
| `VL_DESBLOQUEADO` | | Sim | Valor desbloqueado |
| `VL_BLOQUEADO` | | Sim | Valor bloqueado |

---

#### `cronograma_desembolso`

Define o cronograma previsto de desembolso por parcelas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_PARCELA_CRONO_DESEMBOLSO` | | Sim | Número da Parcela |
| `MES_CRONO_DESEMBOLSO` | | Sim | Mês do Desembolso previsto |
| `ANO_CRONO_DESEMBOLSO` | | Sim | Ano do Desembolso previsto |
| `TIPO_RESP_CRONO_DESEMBOLSO` | | Sim | Tipo do Responsável (Concedente, Convenente, Rendimento de Aplicação) |
| `VALOR_PARCELA_CRONO_DESEMBOLSO` | | Sim | Valor da Parcela |

---

#### `solicitacao_rendimento_aplicacao`

Registra solicitações de uso de rendimento de aplicação financeira.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SOLICITACAO_REND_APLICACAO` | PK | NN | Identificador único |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_SOLICITACAO_REND_APLICACAO` | | Sim | Número único da solicitação por instrumento |
| `STATUS_SOLICITACAO_REND_APLICACAO` | | Sim | Situação (Aguardando Análise, Cadastrado, Cancelado, Em Análise, Autorizada, Recusada, etc.) |
| `DATA_SOLICITACAO_REND_APLICACAO` | | Sim | Data da solicitação |
| `VALOR_SOLICITACAO_REND_APLICACAO` | | Sim | Valor solicitado |
| `VALOR_APROVADO_SOLICITACAO_REND_APLICACAO` | | Sim | Valor aprovado pelo Concedente |

---

### 5.3 Gestão de Projetos

---

#### `meta_crono_fisico`

Define as metas físicas do cronograma de execução de um convênio/proposta.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_META` | PK | NN | Código sequencial para uma Meta |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `COD_PROGRAMA` | | Sim | Código do Programa |
| `NOME_PROGRAMA` | | Sim | Descrição do Programa de Governo |
| `NR_META` | | Sim | Número da Meta |
| `TIPO_META` | | Sim | Tipo da Meta (NORMAL / APLICAÇÃO) |
| `DESC_META` | | Sim | Especificação da Meta |
| `DATA_INICIO_META` | | Sim | Data de início da Meta |
| `DATA_FIM_META` | | Sim | Data de término da Meta |
| `UF_META` | | Sim | UF da Meta |
| `MUNICIPIO_META` | | Sim | Município da Meta |
| `ENDERECO_META` | | Sim | Endereço da Meta |
| `CEP_META` | | Sim | CEP da Meta |
| `QTD_META` | | Sim | Quantidade da Meta |
| `UND_FORNECIMENTO_META` | | Sim | Unidade de Fornecimento da Meta |
| `VL_META` | | Sim | Valor da Meta |

---

#### `etapa_crono_fisico`

Define as etapas de execução vinculadas a cada meta do cronograma físico.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_ETAPA` | PK | NN | Código sequencial para uma Etapa |
| `ID_META` | FK | Sim | → `meta_crono_fisico` |
| `NR_ETAPA` | | Sim | Número da Etapa |
| `DESC_ETAPA` | | Sim | Especificação da etapa |
| `DATA_INICIO_ETAPA` | | Sim | Data de início prevista |
| `DATA_FIM_ETAPA` | | Sim | Data fim prevista |
| `UF_ETAPA` | | Sim | UF da Etapa |
| `MUNICIPIO_ETAPA` | | Sim | Município da Etapa |
| `ENDERECO_ETAPA` | | Sim | Endereço da Etapa |
| `CEP_ETAPA` | | Sim | CEP da Etapa |
| `QTD_ETAPA` | | Sim | Quantidade |
| `UND_FORNECIMENTO_ETAPA` | | Sim | Unidade de fornecimento |
| `VL_ETAPA` | | Sim | Valor total da etapa |

---

#### `plano_aplicacao_detalhado`

Detalha os itens do plano de aplicação dos recursos por natureza de despesa.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `SIGLA` | | Sim | UF da localidade do item |
| `MUNICIPIO` | | Sim | Município do item |
| `NATUREZA_AQUISICAO` | | Sim | Código de natureza de aquisição |
| `DESCRICAO_ITEM` | | Sim | Descrição do Item |
| `CEP_ITEM` | | Sim | CEP do item |
| `ENDERECO_ITEM` | | Sim | Endereço do item |
| `TIPO_DESPESA_ITEM` | | Sim | Tipo da Despesa (SERVICO, BEM, OUTROS, TRIBUTO, OBRA, DESPESA_ADMINISTRATIVA) |
| `NATUREZA_DESPESA` | | Sim | Natureza da Despesa |
| `SIT_ITEM` | | Sim | Situação atual do Item (APROVADO) |
| `COD_NATUREZA_DESPESA` | | Sim | Código de 8 dígitos da natureza de despesa |
| `QTD_ITEM` | | Sim | Quantidade de Itens |
| `VALOR_UNITARIO_ITEM` | | Sim | Valor unitário do item |
| `VALOR_TOTAL_ITEM` | | Sim | Valor total do item |
| `ID_ITEM_PAD` | | Sim | Identificador único do item do plano de aplicação |

---

#### `ajuste_plano_trabalho`

Registra solicitações de ajuste no plano de trabalho do convênio.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_AJUSTE_PT` | PK | NN | Identificador único do Ajuste |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NR_AJUSTE_PT` | | Sim | Número da solicitação (sequencial + ano) |
| `DATA_SOLICITACAO_AJUSTE_PT` | | Sim | Data de solicitação |
| `SITUACAO_SOLICITACAO_AJUSTE_PT` | | Sim | Situação (Ajustado, Aprovado, Autorizado, Cadastrado, Em Análise, Não Autorizado, Parecer Emitido) |

---

### 5.4 Licitação e Contratos

---

#### `licitacao`

Registra os processos de execução (licitações, dispensas, inexigibilidades) vinculados aos convênios.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_LICITACAO` | PK | NN | Identificador único da licitação |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_LICITACAO` | | Sim | Número do Processo de Execução |
| `MODALIDADE_LICITACAO` | | Sim | Modalidade (Convite, Tomada de Preços, Concorrência, Pregão, etc.) |
| `TP_PROCESSO_COMPRA` | | Sim | Tipo (Dispensa, Inexigibilidade, Licitação, Cotação Prévia, Pesquisa de Mercado) |
| `TIPO_LICITACAO` | | Sim | Tipo da licitação (Menor Preço, Melhor Técnica, Pregão Eletrônico, etc.) |
| `NR_PROCESSO_LICITACAO` | | Sim | Número do Processo informado pelo usuário |
| `DATA_PUBLICACAO_LICITACAO` | | Sim | Data de publicação |
| `DATA_ABERTURA_LICITACAO` | | Sim | Data de abertura |
| `DATA_ENCERRAMENTO_LICITACAO` | | Sim | Data de encerramento |
| `DATA_HOMOLOGACAO_LICITACAO` | | Sim | Data de homologação |
| `STATUS_LICITACAO` | | Sim | Status (Concluído, Em Elaboração) |
| `SITUACAO_ACEITE_PROCESSO_EXECU` | | Sim | Situação do aceite do processo de execução |
| `SISTEMA_ORIGEM` | | Sim | Nome do Sistema de Origem da Licitação |
| `SITUACAO_SISTEMA` | | Sim | Situação da Licitação no Sistema externo |
| `VALOR_LICITACAO` | | Sim | Valor da Licitação |
| `DATA_ANALISE_ACEITE` | | Sim | Data de aceite da análise |
| `DATA_ENVIO_ANALISE` | | Sim | Data de envio da análise |

---

#### `contrato`

Registra os contratos celebrados com fornecedores a partir dos processos de licitação.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_CONTRATO` | PK | NN | Identificador único do contrato |
| `ID_LICITACAO` | FK | Sim | → `licitacao` |
| `NR_CONTRATO` | | Sim | Número do contrato (sequencial pelo sistema) |
| `DATA_PUBLICACAO_CONTRATO` | | Sim | Data da publicação do contrato |
| `DATA_ASSINATURA_CONTRATO` | | Sim | Data da assinatura |
| `DATA_INICIO_VIGENCIA_CONTRATO` | | Sim | Data de início de vigência |
| `DATA_FIM_VIGENCIA_CONTRATO` | | Sim | Data fim de vigência |
| `OBJETO_CONTRATO` | | Sim | Objeto do contrato |
| `TIPO_AQUISICAO_CONTRATO` | | Sim | Tipo da aquisição (SERVICO_DE_ENGENHARIA, SERVICO, MATERIAL_SERVICO, OBRAS, MATERIAL) |
| `VALOR_GLOBAL_CONTRATO` | | Sim | Valor global do contrato |
| `ID_FORNECEDOR_CONTRATO` | | Sim | Identificação do fornecedor (CNPJ, CPF ou Inscrição Genérica) |
| `NOME_FORNECEDOR_CONTRATO` | | Sim | Razão Social do fornecedor |

---

#### `itens_licitacao`

Detalha os itens constantes do processo de licitação.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_ITEM_LICITACAO` | PK | NN | Identificador do item da licitação |
| `ID_LICITACAO` | FK | Sim | → `licitacao` |
| `SEQUENCIAL_ITEM_LICITACAO` | | Sim | Sequencial do item |
| `DESCRICAO_ITEM_LICITACAO` | | Sim | Descrição do item |
| `TIPO_UNIDADE_ITEM_LICITACAO` | | Sim | Tipo de unidade |
| `QUANTIDADE_ITEM_LICITACAO` | | Sim | Quantidade |
| `PRECO_UNITARIO_ITEM_LICITACAO` | | Sim | Preço unitário |
| `NOME_FORNECEDOR_ITEM_LICITACAO` | | Sim | Nome do fornecedor vencedor |
| `IDENTIFICACAO_FORNECEDOR_ITEM_LICITACAO` | | Sim | CNPJ/CPF do fornecedor vencedor |
| `VALOR_TOTAL_ITEM_LICITACAO` | | Sim | Valor total do item |

---

#### `itens_dl`

Itens constantes do Documento de Liquidação (nota fiscal, fatura, etc.).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_ITEM_DL` | PK | NN | Identificador do Item do Documento de Liquidação |
| `NOME_ITEM_DL` | | Sim | Nome do Item |
| `QTD_ITEM_DL` | | Sim | Quantidade do Item |
| `UNIDADE_ITEM_DL` | | Sim | Unidade do Item |
| `VALOR_TOTAL_ITEM_DL` | | Sim | Valor Total do Item |
| `DESCRICAO_ITEM_DL` | | Sim | Descrição do Item |

---

### 5.5 Gestão do Convênio

---

#### `termo_aditivo`

Registra os Termos Aditivos que modificam o convênio (valores, prazos, objeto).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `ID_SOLICITACAO` | FK | Sim | → `solicitacao_alteracao` |
| `NUMERO_TA` | | Sim | Número do Termo Aditivo |
| `TIPO_TA` | | Sim | Tipo do Termo Aditivo |
| `VL_GLOBAL_TA` | | Sim | Valor Global referente ao TA |
| `VL_REPASSE_TA` | | Sim | Valor de Repasse referente ao TA |
| `VL_CONTRAPARTIDA_TA` | | Sim | Valor de Contrapartida referente ao TA |
| `DT_ASSINATURA_TA` | | Sim | Data da assinatura do TA |
| `DT_INICIO_TA` | | Sim | Data Início de Vigência do TA |
| `DT_FIM_TA` | | Sim | Data Fim de Vigência do TA |
| `JUSTIFICATIVA_TA` | | Sim | Justificativa para o TA |

---

#### `solicitacao_alteracao`

Registra as solicitações de alteração enviadas pelo convenente ao concedente.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SOLICITACAO` | PK | NN | Identificador único |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_SOLICITACAO` | | Sim | Número sequencial + ano da solicitação |
| `SITUACAO_SOLICITACAO` | | Sim | Situação (ACEITA, RECUSADA, EM_ANALISE, CADASTRADA) |
| `OBJETO_SOLICITACAO` | | Sim | Objeto de alteração |
| `DATA_SOLICITACAO` | | Sim | Data da solicitação |

---

#### `prorroga_oficio`

Registra as Prorrogas de Ofício que estendem a vigência sem alteração de valor.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `NR_PRORROGA` | | Sim | Número da Prorrogação de Ofício |
| `DT_INICIO_PRORROGA` | | Sim | Data Início de Vigência |
| `DT_FIM_PRORROGA` | | Sim | Data Fim de Vigência |
| `DIAS_PRORROGA` | | Sim | Dias de prorrogação |
| `DT_ASSINATURA_PRORROGA` | | Sim | Data de assinatura |
| `SIT_PRORROGA` | | Sim | Situação (DISPONIBILIZADA, PUBLICADA) |

---

### 5.6 Histórico e Auditoria

---

#### `historico_situacao`

Registra o histórico de todas as situações pelas quais uma proposta/convênio passou ao longo do tempo.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NR_CONVENIO` | FK | Sim | → `convenio` |
| `DIA_HISTORICO_SIT` | | Sim | Data de entrada da situação no sistema |
| `HISTORICO_SIT` | | Sim | Situação histórica |
| `DIAS_HISTORICO_SIT` | | Sim | Dias em que permaneceu na situação |
| `COD_HISTORICO_SIT` | | Sim | Código da situação com ordem cronológica do ciclo de vida |

---

#### `historico_projeto_basico`

Registra o histórico de análise do Projeto Básico / Termo de Referência.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `DATA_HIST_PB_TR` | | Sim | Data de registro |
| `SITUACAO_HIST_PB_TR` | | Sim | Situação (ELA=Em Elaboração, ANL=Em Análise, SCP=Complementação Solicitada, COM=Em Complementação, ACT=Aceita) |
| `EVENTO_HIST_PB_TR` | | Sim | Indicador do Evento |
| `VERSAO_DOC_PB_TR` | | Sim | Número da Versão no sistema de versionamento |

---

### 5.7 Emendas Parlamentares

---

#### `emenda`

Registra as emendas parlamentares vinculadas a propostas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `QUALIF_PROPONENTE` | | Sim | Qualificação do proponente |
| `COD_PROGRAMA_EMENDA` | | Sim | Código do programa (Cód.Órgão + Ano + Cód.Sequencial) |
| `NR_EMENDA` | | Sim | Número da Emenda Parlamentar |
| `NOME_PARLAMENTAR` | | Sim | Nome do Parlamentar |
| `BENEFICIARIO_EMENDA` | | Sim | CNPJ do Proponente beneficiário |
| `IND_IMPOSITIVO` | | Sim | Orçamento Impositivo — INDIVIDUAL + ano ≥ 2014 (SIM, NÃO) |
| `TIPO_PARLAMENTAR` | | Sim | Tipo (INDIVIDUAL, COMISSAO, BANCADA) |
| `VALOR_REPASSE_PROPOSTA_EMENDA` | | Sim | Valor da Emenda cadastrada na proposta |
| `VALOR_REPASSE_EMENDA` | | Sim | Valor da Emenda assinada |

---

#### `apoiadores_emendas_programas`

Registra os parlamentares apoiadores de emendas vinculadas a programas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_CNPJ_PROGRAMA_EMENDA_APOIADORES_EMENDAS` | PK | NN | Chave primária |
| `NUMERO_EMENDA_APOIADORES_EMENDAS` | | Sim | Número da emenda |
| `NOME_PARLAMENTAR_APOIADORES_EMENDAS` | | Sim | Nome do Parlamentar |
| `INDICACAO_APOIADORES_EMENDAS` | | Sim | Indicação |
| `PARLAMENTAR_SOLICITANTE_APOIADORES_EMENDAS` | | Sim | Parlamentar solicitante |
| `CPF_PF_SOLICITANTE_APOIADORES_EMENDAS` | | Sim | CPF do solicitante PF |
| `NOME_PF_SOLICITANTE_APOIADORES_EMENDAS` | | Sim | Nome do solicitante PF |
| `CNPJ_PJ_SOLICITANTE_APOIADORES_EMENDAS` | | Sim | CNPJ do solicitante PJ |
| `NOME_PJ_SOLICITANTE_APOIADORES_EMENDAS` | | Sim | Nome do solicitante PJ |
| `CNPJ_PROPONENTE_APOIADORES_EMENDAS` | | Sim | CNPJ do Proponente |
| `NOME_PROPONENTE_APOIADORES_EMENDAS` | | Sim | Nome do Proponente |
| `VALOR_REPASSE_PROPOSTA_APOIADORES_EMENDAS` | | Sim | Valor de repasse da proposta |
| `ID_PROGRAMA` | FK | Sim | → `programa` |

---

### 5.8 Proponentes e Propostas

---

#### `consorcios`

Registra os consórcios vinculados a propostas, com seus participantes.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `CNPJ_CONSORCIO` | | Sim | CNPJ do Consórcio |
| `NOME_CONSORCIO` | | Sim | Razão Social do Consórcio |
| `CODIGO_CNAE_PRIMARIO` | | Sim | Código CNAE Primário na Receita Federal |
| `DESC_CNAE_PRIMARIO` | | Sim | Descrição do CNAE Primário |
| `CODIGO_CNAE_SECUNDARIO` | | Sim | Código CNAE Secundário |
| `DESC_CNAE_SECUNDARIO` | | Sim | Descrição do CNAE Secundário |
| `CNPJ_PARTICIPANTE` | | Sim | CNPJ dos Participantes do Consórcio |
| `NOME_PARTICIPANTE` | | Sim | Nome dos participantes do Consórcio |

---

#### `justificativas_proposta`

Armazena os textos de justificativa e contextualização das propostas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `CARACTERIZACAO_INTERESSES_RECI` | | Sim | Caracterização dos interesses recíprocos |
| `PUBLICO_ALVO` | | Sim | Público alvo da proposta |
| `PROBLEMA_A_SER_RESOLVIDO` | | Sim | Problema a ser resolvido |
| `RESULTADOS_ESPERADOS` | | Sim | Resultados esperados |
| `RELACAO_PROPOSTA_OBJETIVOS_PRO` | | Sim | Relação da proposta com objetivos do programa |
| `CAPACIDADE_TECNICA` | | Sim | Capacidade Técnica e Gerencial |
| `JUSTIFICATIVA` | | Sim | Justificativa da solicitação |

---

#### `proposta_cancelada`

Armazena propostas que foram canceladas, espelhando os campos da tabela `proposta`.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | PK | NN | Código da proposta cancelada |
| `UF_PROPONENTE` | | Sim | UF do Proponente |
| `MUNIC_PROPONENTE` | | Sim | Município do Proponente |
| `MODALIDADE` | | Sim | Modalidade do instrumento |
| `SIT_PROPOSTA` | | Sim | Situação: Proposta/Plano de Trabalho Cancelados |
| `VL_GLOBAL_PROP` | | Sim | Valor Global |
| `VL_REPASSE_PROP` | | Sim | Valor de Repasse |
| `VL_CONTRAPARTIDA_PROP` | | Sim | Valor da Contrapartida |
| *(demais colunas)* | | | Espelha os campos da tabela `proposta` |

---

### 5.9 Tabelas Associativas (N:N)

---

#### `programa_proposta`

Tabela associativa entre programa e proposta (relação N:N).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROGRAMA` | FK | NN | → `programa` (parte da PK composta) |
| `ID_PROPOSTA` | FK | NN | → `proposta` (parte da PK composta) |

---

#### `programa_proponentes`

Tabela associativa entre programa e proponentes (relação N:N).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROGRAMA` | FK | NN | → `programa` (parte da PK composta) |
| `ID_PROPONENTE` | FK | NN | → `proponentes` (parte da PK composta) |

---

### 5.10 Dados Geográficos

---

#### `siconv_coordenadas_obra`

Registra as coordenadas geográficas das obras vinculadas a propostas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NOME_PROJETO_CADASTRO_OBRA` | | Sim | Nome do projeto da obra |
| `LATITUDE_CADASTRO_OBRA` | | Sim | Latitude da obra |
| `LONGITUDE_CADASTRO_OBRA` | | Sim | Longitude da obra |

---

#### `siconv_resumo_fisico_financeiro`

Resumo do percentual de execução física e financeira da proposta.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `VALOR_TOTAL_RESUMO_FISICO_FINANCEIRO` | | Sim | Valor total |
| `PERCENTUAL_EXECUCAO_RESUMO_FISICO_FINANCEIRO` | | Sim | Percentual de execução |
| `VALOR_REALIZADO_RESUMO_FISICO_FINANCEIRO` | | Sim | Valor realizado |

---

### 5.11 Programa Novo PAC

---

#### `proposta_selecao_pac`

Propostas submetidas ao Programa Novo PAC para seleção.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA_SELECAO_PAC` | PK | NN | Identificador único |
| `ID_PROGRAMA` | FK | Sim | → `programa` |
| `ID_PROPONENTE` | FK | Sim | → `proponentes` |
| `NR_PROPOSTA_SELECAO_PAC` | | Sim | Número da Proposta do Novo PAC |
| `DATA_CADASTRO_PROPOSTA_SELECAO_PAC` | | Sim | Data de Cadastro |
| `DATA_ENVIO_PROPOSTA_SELECAO_PAC` | | Sim | Data de Envio |
| `OBJETO_PROPOSTA_SELECAO_PAC` | | Sim | Objeto da proposta |
| `SITUACAO_PROPOSTA_SELECAO_PAC` | | Sim | Situação da proposta PAC |
| `VALOR_TOTAL_PROPOSTA_SELECAO_PAC` | | Sim | Valor Total |
| `JUSTIFICATIVA_PROPOSTA_SELECAO_PAC` | | Sim | Justificativa |
| `TEM_ANEXO_PROPOSTA_SELECAO_PAC` | | Sim | Possui anexos (SIM, NÃO) |

---

#### `pergunta_selecao_pac`

Perguntas do formulário de seleção do Programa Novo PAC.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PERGUNTA_SELECAO_PAC` | PK | NN | Identificador único da pergunta |
| `ID_PROGRAMA` | FK | Sim | → `programa` |
| `PERGUNTA_SELECAO_PAC` | | Sim | Texto da pergunta |

---

#### `resposta_selecao_pac`

Respostas das propostas PAC para cada pergunta do formulário.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PERGUNTA_SELECAO_PAC` | FK | NN | → `pergunta_selecao_pac` (parte da PK) |
| `ID_PROPOSTA_SELECAO_PAC` | FK | NN | → `proposta_selecao_pac` (parte da PK) |
| `RESPOSTA_SELECAO_PAC` | | Sim | Resposta da pergunta |

---

#### `siconv_proposta_formalizacao_pac`

Liga a proposta PAC selecionada à proposta formal no Siconv.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA_SELECAO_PAC` | FK | Sim | → `proposta_selecao_pac` |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `NR_RESERVADO_PAC` | | Sim | Número reservado PAC |

---

### 5.12 Módulo de Empresas (VRPL/ACFFO)

> Conjunto de tabelas que suporta a **Verificação da Regularidade da Licitação (VRPL)** e a **Análise e Controle de Financiamento de Obras (ACFFO)**, módulos utilizados por instituições mandatárias (como Caixa Econômica Federal) na análise técnica de obras.

---

#### `vrpl_proposta_licitacao_modulo_empresas`

Cabeçalho da proposta VRPL — víncula proposta e licitação no módulo de empresas.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA_VRPL` | PK | NN | Identificador único da proposta VRPL |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `ID_LICITACAO_VRPL` | FK | Sim | → `vrpl_lotes_fornecedores_licitacao_modulo_empresas` |
| `ULTIMA_VERSAO_PROPOSTA_VRPL` | | Sim | Versão atual da Proposta do VRPL |
| `SITUACAO_VRPL` | | Sim | Sigla da Situação da Documentação |
| `SITUACAO_PARECER_VRPL` | | Sim | Situação do Parecer |
| `EMISSAO_PARECER_VRPL` | | Sim | Indicador da Emissão do Parecer |
| `DATA_EMISSAO_PARECER_VRPL` | | Sim | Data da Emissão do Parecer |
| `DATA_ACEITE_LICITACAO_VRPL` | | Sim | Data do Aceite da Licitação |

---

#### `vrpl_metas_submetas_modulo_empresas`

Metas e submetas da análise técnica VRPL, incluindo dados de obras.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SUBMETA_VRPL` | PK | NN | Identificador único da submeta |
| `ID_META_VRPL` | | Sim | Identificador da meta |
| `ID_PO_VRPL` | | Sim | Identificador da planilha orçamentária |
| `ID_PROPOSTA_VRPL` | FK | Sim | → `vrpl_proposta_licitacao_modulo_empresas` |
| `NUMERO_META_VRPL` | | Sim | Número da Meta |
| `DESCRICAO_META_VRPL` | | Sim | Descrição da Meta |
| `NUMERO_LOTE_LICITACAO_VRPL` | | Sim | Número do Lote |
| `NUMERO_SUBMETA_VRPL` | | Sim | Número da Submeta |
| `DESCRICAO_SUBMETA_VRPL` | | Sim | Descrição da Submeta |
| `SITUACAO_SUBMETA_VRPL` | | Sim | Situação da Submeta |
| `VALOR_TOTAL_LICITADO_VRPL` | | Sim | Valor total licitado |
| `DATA_PREVISAO_INICIO_OBRA_PO_VRPL` | | Sim | Data de previsão do início da obra |
| `DATABASE_PO_VRPL` | | Sim | Data-base do VRPL |
| `SIGLA_LOCALIDADE_PO_VRPL` | | Sim | Sigla da Localidade |
| `ACOMPANHADO_POR_EVENTO_PO_VRPL` | | Sim | PO acompanhada por eventos |
| `QUANTIDADE_ITENS_META_VRPL` | | Sim | Quantidade de itens |
| `DESCRICAO_SUBITEM_INVESTIMENTO_META_VRPL` | | Sim | Descrição do Subitem |
| `UNIDADE_ITEM_INVESTIMENTO_META_VRPL` | | Sim | Unidade do item |

---

#### `vrpl_lotes_fornecedores_licitacao_modulo_empresas`

Lotes e fornecedores associados às licitações no módulo VRPL.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_LICITACAO_VRPL` | PK | NN | Identificador único da licitação VRPL |
| `ID_LOTE_LICITACAO_VRPL` | | Sim | Identificador do lote |
| `NUMERO_LOTE_LICITACAO_VRPL` | | Sim | Número do Lote |
| `RAZAO_SOCIAL_FORNECEDOR_LICITACAO_VRPL` | | Sim | Razão Social do Fornecedor |
| `TIPO_IDENTIFICACAO_FORNECEDOR_LICITACAO_VRPL` | | Sim | CPF ou CNPJ |
| `IDENTIFICACAO_FORNECEDOR_LICITACAO_VRPL` | | Sim | CPF ou CNPJ do Fornecedor |

---

#### `projeto_basico_acffo_modulo_empresas`

Análise e Controle de Financiamento de Obras (ACFFO) — cabeçalho do projeto básico.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_ACFFO` | PK | NN | Identificador único do ACFFO |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `ULTIMA_VERSAO_PROJETO_BASICO` | | Sim | Versão atual do Projeto Básico |
| `APELIDO_EMPREENDIMENTO_PROJETO_BASICO` | | Sim | Apelido do empreendimento |
| `SITUACAO_PROJETO_BASICO` | | Sim | Situação do Projeto Básico |
| `SITUACAO_SPA` | | Sim | Situação do SPA |
| `DATA_ACEITE_PROJETO_BASICO` | | Sim | Data do aceite |

---

#### `projeto_basico_lae_modulo_empresas`

Lista de Análise e Exigências (LAE) vinculadas ao projeto básico.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_QCI_ACFFO` | PK | NN | Identificador único da LAE |
| `ID_ACFFO` | FK | Sim | → `projeto_basico_acffo_modulo_empresas` |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `SITUACAO_LAE_PROJETO_BASICO` | | Sim | Situação da LAE |
| `EMISSAO_LAE_PROJETO_BASICO` | | Sim | Emissão da LAE |
| `DATA_EMISSAO_LAE_PROJETO_BASICO` | | Sim | Data de Emissão da LAE |

---

#### `projeto_basico_metas_modulo_empresas`

Metas do projeto básico no módulo ACFFO.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_META_PROJETO_BASICO` | PK | NN | Identificador único da meta |
| `ID_QCI_ACFFO` | FK | Sim | → `projeto_basico_lae_modulo_empresas` |
| `NUMERO_META_PROJETO_BASICO` | | Sim | Número da Meta |
| `DESCRICAO_META_PROJETO_BASICO` | | Sim | Descrição da Meta |
| `NOME_ITEM_INVESTIMENTO_META` | | Sim | Nome do Item de Investimento |
| `DESCRICAO_SUBITEM_INVESTIMENTO_META` | | Sim | Descrição do Subitem |
| `QUANTIDADE_ITENS_META_PROJETO_BASICO` | | Sim | Quantidade de itens |
| `UNIDADE_ITEM_INVESTIMENTO_META` | | Sim | Código da unidade de fornecimento |

---

#### `projeto_basico_submetas_modulo_empresas`

Submetas do projeto básico, com dados financeiros e cronograma de obras.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SUBMETA_PROJETO_BASICO` | PK | NN | Identificador único |
| `ID_META_PROJETO_BASICO` | FK | Sim | → `projeto_basico_metas_modulo_empresas` |
| `LOTE_SUBMETA_PROJETO_BASICO` | | Sim | Número do Lote |
| `NUMERO_SUBMETA_PROJETO_BASICO` | | Sim | Número da Submeta |
| `DESCRICAO_SUBMETA_PROJETO_BASICO` | | Sim | Descrição da Submeta |
| `SITUACAO_SUBMETA_PROJETO_BASICO` | | Sim | Situação |
| `VALOR_REPASSE_SUBMETA_PROJETO_BASICO` | | Sim | Valor do Repasse |
| `VALOR_CONTRAPARTIDA_SUBMETA_PROJETO_BASICO` | | Sim | Valor da Contrapartida |
| `VALOR_OUTROS_SUBMETA_PROJETO_BASICO` | | Sim | Valor Outros |
| `VALOR_TOTAL_SUBMETA_PROJETO_BASICO` | | Sim | Valor Total |
| `DATA_PREVISAO_INICIO_OBRA_PROJETO_BASICO` | | Sim | Data de previsão do início da obra |
| `QUANTIDADE_MESES_DURACAO_OBRA_PROJETO_BASICO` | | Sim | Quantidade de meses de duração |
| `DATABASE_OBRA_PROJETO_BASICO` | | Sim | Data-base da planilha orçamentária |
| `SIGLA_LOCALIDADE_OBRA_PROJETO_BASICO` | | Sim | Sigla da localidade |
| `OBRA_ACOMPANHADA_POR_EVENTO_PROJETO_BASICO` | | Sim | Acompanhamento por eventos |

---

#### `projeto_basico_proposta_modulo_empresas`

Associação entre proposta e o projeto básico no módulo ACFFO.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA_ACFFO` | PK | NN | Identificador único |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `VALOR_GLOBAL_PROPOSTA_PROJETO_BASICO` | | Sim | Valor Global da Proposta do Projeto Básico |

---

#### `inst_cont_proposta_aio_modulo_empresas`

Cabeçalho dos Instrumentos Contratuais — AIO (Autorização de Início de Obra).

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_PROPOSTA_INSTRUMENTO_CONTRATUAL` | PK | NN | Identificador único |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `ID_AIO_INSTRUMENTO_CONTRATUAL` | | Sim | Identificador do AIO |
| `SITUACAO_AIO_INSTRUMENTO_CONTRATUAL` | | Sim | Situação da Emissão do AIO |
| `DATA_EMISSAO_AIO_INSTRUMENTO_CONTRATUAL` | | Sim | Data de Emissão do AIO |

---

#### `inst_cont_contratos_lotes_empresas_modulo_empresas`

Contratos e lotes de empresas executoras nos instrumentos contratuais.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_CONTRATO_INSTRUMENTO_CONTRATUAL` | PK | NN | Identificador único |
| `ID_PROPOSTA_INSTRUMENTO_CONTRATUAL` | FK | Sim | → `inst_cont_proposta_aio_modulo_empresas` |
| `ID_LOTE_INSTRUMENTO_CONTRATUAL` | | Sim | Identificador do lote |
| `NUMERO_INSTRUMENTO_CONTRATUAL` | | Sim | Número do Instrumento Contratual |
| `SITUACAO_INSTRUMENTO_CONTRATUAL` | | Sim | Situação |
| `DATA_ASSINATURA_INSTRUMENTO_CONTRATUAL` | | Sim | Data de Assinatura |
| `DATA_INICIO_VIGENCIA_INSTRUMENTO_CONTRATUAL` | | Sim | Data de Início de Vigência |
| `DATA_FIM_VIGENCIA_INSTRUMENTO_CONTRATUAL` | | Sim | Data de Fim de Vigência |
| `NUMERO_LOTE_INSTRUMENTO_CONTRATUAL` | | Sim | Número do Lote |
| `RAZAO_SOCIAL_EMPRESA_EXECUTORA_INSTRUMENTO_CONTRATUAL` | | Sim | Razão Social do Executor |
| `TIPO_IDENTIFICACAO_EMPRESA_EXECUTORA_INSTRUMENTO_CONTRATUAL` | | Sim | Tipo de identificação (CPF ou CNPJ) |
| `IDENTIFICACAO_EMPRESA_EXECUTORA_INSTRUMENTO_CONTRATUAL` | | Sim | CPF ou CNPJ do Executor |

---

#### `inst_cont_metas_submetas_po_modulo_empresas`

Metas, submetas e planilhas orçamentárias dos instrumentos contratuais.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SUBMETA_INSTRUMENTO_CONTRATUAL` | PK | NN | Identificador único da submeta |
| `ID_META_INSTRUMENTO_CONTRATUAL` | | Sim | Identificador da meta |
| `ID_PO_INSTRUMENTO_CONTRATUAL` | | Sim | Identificador da planilha orçamentária |
| `ID_PROPOSTA_INSTRUMENTO_CONTRATUAL` | FK | Sim | → `inst_cont_proposta_aio_modulo_empresas` |
| `ID_LOTE_INSTRUMENTO_CONTRATUAL` | | Sim | Identificador do lote |
| `NUMERO_META_INSTRUMENTO_CONTRATUAL` | | Sim | Número da Meta |
| `DESCRICAO_META_INSTRUMENTO_CONTRATUAL` | | Sim | Descrição da Meta |
| `NUMERO_SUBMETA_INSTRUMENTO_CONTRATUAL` | | Sim | Número da Submeta |
| `DESCRICAO_SUBMETA_INSTRUMENTO_CONTRATUAL` | | Sim | Descrição da Submeta |
| `SITUACAO_SUBMETA_INSTRUMENTO_CONTRATUAL` | | Sim | Situação da Submeta |
| `VALOR_TOTAL_LICITADO_INSTRUMENTO_CONTRATUAL` | | Sim | Valor Total Licitado |
| `DATA_PREVISAO_INICIO_OBRA_INSTRUMENTO_CONTRATUAL` | | Sim | Data de Previsão do Início da Obra |
| `DATABASE_PO_VRPL_INSTRUMENTO_CONTRATUAL` | | Sim | Data-base do instrumento |
| `SIGLA_LOCALIDADE_PO_INSTRUMENTO_CONTRATUAL` | | Sim | Sigla da Localidade |
| `ACOMPANHADO_POR_EVENTO_PO_INSTRUMENTO_CONTRATUAL` | | Sim | Acompanhado por eventos |

---

### 5.13 Acompanhamento de Obras

---

#### `acomp_obras_contratos_medicoes_modulo_empresas`

Registra as medições de contratos de obras para acompanhamento físico.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_MEDICAO_ACOMPANHAMENTO_OBRA` | PK | NN | Identificador único da medição |
| `ID_PROPOSTA` | FK | Sim | → `proposta` |
| `ID_CONTRATO_MEDICAO_ACOMPANHAMENTO_OBRA` | | Sim | Identificador do contrato de medição |
| `DATA_INICIO_OBRA_CONTRATO_ACOMPANHAMENTO_OBRA` | | Sim | Data de Início da Obra do Contrato |
| `CNPJ_FORNECEDOR_CONTRATO_ACOMPANHAMENTO_OBRA` | | Sim | CNPJ do Fornecedor |
| `NUMERO_MEDICAO_ACOMPANHAMENTO_OBRA` | | Sim | Número Sequencial da Medição |
| `SITUACAO_MEDICAO_ACOMPANHAMENTO_OBRA` | | Sim | Situação da Medição |
| `DATA_INICIO_MEDICAO_OBJETO_ACOMPANHAMENTO_OBRA` | | Sim | Data Inicial da Medição |
| `DATA_FIM_MEDICAO_OBJETO_ACOMPANHAMENTO_OBRA` | | Sim | Data Final da Medição |
| `QTD_DIAS_SEM_MEDICAO_ACOMPANHAMENTO_OBRA` | | Sim | Quantidade de Dias sem Medição |

---

#### `acomp_obras_valores_itens_medicao_modulo_empresas`

Valores acumulados de execução física por submeta nas medições de obras.

| Coluna | PK | Nulo? | Descrição |
|---|---|---|---|
| `ID_SUBMETA_VRPL` | PK | NN | Identificador único da submeta |
| `ID_CONTRATO_MEDICAO_ACOMPANHAMENTO_OBRA` | | Sim | Identificador do contrato de medição |
| `VALOR_EXECUCAO_FISICA_ACUMULADA_TOTAL_ACOMPANHAMENTO_OBRA` | | Sim | Valor Total Acumulado da Execução Física |
| `VALOR_EXECUCAO_FISICA_ACUMULADA_CONCEDENTE_ACOMPANHAMENTO_OBRA` | | Sim | Valor Acumulado — parte do Concedente |
| `VALOR_EXECUCAO_FISICA_ACUMULADA_CONVENENTE_ACOMPANHAMENTO_OBRA` | | Sim | Valor Acumulado — parte do Convenente |
| `VALOR_EXECUCAO_FISICA_ACUMULADA_EMPRESA_ACOMPANHAMENTO_OBRA` | | Sim | Valor Acumulado — parte da Empresa |

---

## 6. Índice Alfabético de Tabelas

| Tabela | Grupo Funcional |
|---|---|
| `acomp_obras_contratos_medicoes_modulo_empresas` | Acompanhamento de Obras |
| `acomp_obras_valores_itens_medicao_modulo_empresas` | Acompanhamento de Obras |
| `ajuste_plano_trabalho` | Gestão de Projetos |
| `apoiadores_emendas_programas` | Emendas Parlamentares |
| `consorcios` | Proponentes e Propostas |
| `contrato` | Licitação e Contratos |
| `convenio` | Núcleo |
| `cronograma_desembolso` | Fluxo Financeiro |
| `desbloqueio_cr` | Fluxo Financeiro |
| `desembolso` | Fluxo Financeiro |
| `emenda` | Emendas Parlamentares |
| `empenho` | Fluxo Financeiro |
| `empenho_desembolso` | Fluxo Financeiro |
| `etapa_crono_fisico` | Gestão de Projetos |
| `historico_projeto_basico` | Histórico e Auditoria |
| `historico_situacao` | Histórico e Auditoria |
| `ingresso_contrapartida` | Fluxo Financeiro |
| `inst_cont_contratos_lotes_empresas_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `inst_cont_metas_submetas_po_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `inst_cont_proposta_aio_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `itens_dl` | Licitação e Contratos |
| `itens_licitacao` | Licitação e Contratos |
| `justificativas_proposta` | Proponentes e Propostas |
| `licitacao` | Licitação e Contratos |
| `meta_crono_fisico` | Gestão de Projetos |
| `obtv_convenente` | Fluxo Financeiro |
| `pagamento` | Fluxo Financeiro |
| `pagamento_tributo` | Fluxo Financeiro |
| `pergunta_selecao_pac` | Programa Novo PAC |
| `plano_aplicacao_detalhado` | Gestão de Projetos |
| `programa` | Núcleo |
| `programa_proponentes` | Tabelas Associativas (N:N) |
| `programa_proposta` | Tabelas Associativas (N:N) |
| `projeto_basico_acffo_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `projeto_basico_lae_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `projeto_basico_metas_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `projeto_basico_proposta_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `projeto_basico_submetas_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `proponentes` | Núcleo |
| `proposta` | Núcleo |
| `proposta_cancelada` | Proponentes e Propostas |
| `proposta_selecao_pac` | Programa Novo PAC |
| `prorroga_oficio` | Gestão do Convênio |
| `resposta_selecao_pac` | Programa Novo PAC |
| `siconv_coordenadas_obra` | Dados Geográficos |
| `siconv_proposta_formalizacao_pac` | Programa Novo PAC |
| `siconv_resumo_fisico_financeiro` | Dados Geográficos |
| `solicitacao_alteracao` | Gestão do Convênio |
| `solicitacao_rendimento_aplicacao` | Fluxo Financeiro |
| `termo_aditivo` | Gestão do Convênio |
| `vrpl_lotes_fornecedores_licitacao_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `vrpl_metas_submetas_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |
| `vrpl_proposta_licitacao_modulo_empresas` | Módulo de Empresas (VRPL/ACFFO) |

---

*Documentação gerada a partir do schema `bd_portal.public.xml` — SchemaSpy 6.1.0 — agosto/2025*
