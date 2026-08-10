# Chaves Naturais por Tabela

Referência para MERGE incremental. Chaves derivadas das migrations do transferepro e do catálogo XLSX.

**Legenda de status:**

| Status | Significado |
|--------|-------------|
| `definida` | Pronta para implementar MERGE |
| `revisar` | Confirmar contra header do CSV antes de implementar |

## Tabelas do catálogo XLSX (65 tabelas)

| Tabela | Chave natural | Tipo | Status | Observação |
|--------|---------------|------|--------|------------|
| `rlc_dados_disponibilizacao_programas` | `id_programa, uf, modalidade` | composta | definida | Split de siconv_programa.csv |
| `rlc_dados_obrasgov_geral` | `id_obra` | simples | revisar | Tabela CIPI; confirmar no CSV |
| `rlc_dados_uf_modalidade_programas` | `id_programa, uf, modalidade` | composta | definida | Split de siconv_programa.csv |
| `rlc_empenhos_desembolsos` | `id_desembolso, id_empenho` | composta | definida | |
| `rlc_emendas_propostas_proponentes` | `nr_emenda, id_proposta, identif_proponente` | composta | definida | Split de siconv_emenda.csv; `identif_proponente` ← `beneficiario_emenda` |
| `rlc_historico_situacao` | `id_proposta, nr_convenio, dia_historico_sit` | composta | definida | |
| `rlc_programa_proponente` | `id_programa, id_proponente` | composta | definida | |
| `rlc_programa_proposta` | `id_programa, id_proposta` | composta | definida | |
| `rlc_consorcios_participantes_propostas` | `id_proposta, cnpj_consorcio, cnpj_participante` | composta | definida | Split de siconv_consorcios.csv |
| `rlc_proposta_formalizacao_pac` | `id_proposta_selecao_pac, id_proposta` | composta | definida | UNIQUE no DDL |
| `tab_acomp_obras_contratos_medicoes_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_acomp_obras_valores_itens_medicao_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_apoiadores_emendas_programas` | `id_programa, nr_emenda` | composta | revisar | |
| `tab_beneficiarios_emendas` | `nr_emenda, id_proposta, beneficiario_emenda` | composta | definida | Split de siconv_emenda.csv; dedupe na staging pela chave |
| `tab_consorcios` | `cnpj_consorcio` | simples | definida | Split de siconv_consorcios.csv |
| `tab_contratos` | `cod_licitacao, num_contrato` | composta | definida | Sem PK formal; usar par licitação+contrato |
| `tab_contratos_cipi` | `id_contrato_cipi` | simples | revisar | Tabela CIPI |
| `tab_convenios` | `nr_convenio` | simples | definida | Index idx_tab_conv_nr_convenios |
| `tab_coordenadas_obras` | `id_meta, nr_coordenada` | composta | revisar | Confirmar no CSV |
| `tab_cronograma_desembolso` | `id_proposta, nr_parcela` | composta | revisar | Confirmar no CSV |
| `tab_data_carga` | `data_carga` | simples | definida | Registro global; inserir nova data por execução |
| `tab_desbloqueio_cr` | `id_desbloqueio` | simples | revisar | |
| `tab_desbloqueio_recurso_cr` | `id_desbloqueio` | simples | revisar | |
| `tab_desembolsos` | `id_desembolso` | simples | definida | |
| `tab_dl` | `id_dl` | simples | revisar | Confirmar no CSV |
| `tab_emendas` | `nr_emenda` | simples | definida | Index idx_tabemendas_nr_emenda; CSV tem N linhas/emenda — dedupe obrigatório na staging |
| `tab_empenhos` | `id_empenho` | simples | definida | |
| `tab_empenhos_cipi` | `id_empenho_cipi` | simples | revisar | Tabela CIPI |
| `tab_etapas_crono_fisico` | `id_etapa` | simples | definida | Confirmar no CSV |
| `tab_execucao_fisica_cipi` | `id_execucao` | simples | revisar | Tabela CIPI |
| `tab_historico_projeto_basico` | `id_proposta, dt_historico` | composta | revisar | |
| `tab_ingresso_contrapartida` | `id_ingresso` | simples | revisar | |
| `tab_inst_cont_contratos_lotes_empresas_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_inst_cont_metas_submetas_po_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_inst_cont_proposta_aio_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_itens_dl` | `id_dl, nr_item` | composta | revisar | Confirmar colunas no CSV |
| `tab_itens_licitacao` | `id_licitacao, nr_item` | composta | revisar | Confirmar colunas no CSV |
| `tab_justificativas_proposta` | `id_proposta` | simples | revisar | |
| `tab_licitacao` | `id_licitacao` | simples | definida | |
| `tab_meta_crono_fisico` | `id_meta` | simples | definida | |
| `tab_obtv_convenente` | `id_obtv` | simples | revisar | |
| `tab_pagamento_tributo` | `id_pagamento, id_tributo` | composta | revisar | |
| `tab_pagamentos` | `id_pagamento` | simples | definida | |
| `tab_pergunta_selecao_pac` | `id_pergunta_selecao_pac` | simples | definida | Chave única confirmada |
| `tab_plano_aplicacao_detalhado` | `id_proposta, nr_item` | composta | revisar | Confirmar no CSV |
| `tab_programas` | `id_programa` | simples | definida | |
| `tab_projeto_basico_acffo_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_projeto_basico_lae_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_projeto_basico_metas_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_projeto_basico_proposta_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_projeto_basico_submetas_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_prop_inst_indicadores_estados` | `id_proposta, uf` | composta | revisar | |
| `tab_prop_inst_indicadores_municipios` | `id_proposta, cod_munic_ibge` | composta | revisar | |
| `tab_proponentes` | `id_proponente` | simples | definida | CNPJ/identificador do proponente |
| `tab_propostas` | `id_proposta` | simples | definida | |
| `tab_propostas_canceladas` | `id_proposta` | simples | definida | Mesma chave da proposta cancelada |
| `tab_propostas_selecao_pac` | `id_proposta_selecao_pac` | simples | definida | UNIQUE no DDL |
| `tab_prorroga_oficios` | `nr_convenio, nr_oficio` | composta | revisar | |
| `tab_resposta_selecao_pac` | `id_proposta, id_pergunta` | composta | revisar | |
| `tab_resumo_fisico_financeiro` | `id_proposta` | simples | revisar | |
| `tab_solicitacao_ajuste_pt` | `id_solicitacao` | simples | revisar | |
| `tab_solicitacao_alteracao` | `id_solicitacao` | simples | revisar | |
| `tab_solicitacao_rendimento_aplicacao` | `id_solicitacao` | simples | revisar | |
| `tab_termo_aditivo` | `nr_convenio, nr_aditivo` | composta | revisar | |
| `tab_vrpl_lote_fornecedor_licitacao_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_vrpl_metas_submetas_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |
| `tab_vrpl_proposta_licitacao_modulo_empresas` | `id_proposta, id_registro` | composta | revisar | Módulo empresas; confirmar chave no CSV |

## Resumo

| Status | Quantidade |
|--------|------------|
| definida | 22 |
| revisar | 43 |

## Uso em `src/keys.py`

```python
TABLE_KEYS = {
    "tab_propostas": {
        "columns": ["id_proposta"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_contratos": {
        "columns": ["cod_licitacao", "num_contrato"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "tab_consorcios": {
        "columns": ["cnpj_consorcio"],
        "status": "definida",
        "requires_manual_key": False,
    },
    "rlc_consorcios_participantes_propostas": {
        "columns": ["id_proposta", "cnpj_consorcio", "cnpj_participante"],
        "status": "definida",
        "requires_manual_key": False,
    },
}
```

## Como validar chaves pendentes

1. Baixar e extrair o CSV correspondente
2. Comparar header do CSV com colunas da migration
3. Identificar coluna(s) que identificam unicamente cada registro
4. Atualizar este documento e `keys.py`
5. Alterar status para `definida`

## Referências

- Migrations: `D:\projetos_herd\transferepro\database\migrations\transfere_pro_transferegov\`
- Estratégia MERGE: [`ESTRATEGIA_INCREMENTAL.md`](ESTRATEGIA_INCREMENTAL.md)
- Catálogo: `data/lista_arquivo_tabela.xlsx`
