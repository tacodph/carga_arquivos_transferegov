# Ordem de carga — transfere_pro_transferegov

Derivada de `D:\projetos_herd\transferepro\database\seeders\transfere_pro_transferegov\seed-order.php`.

Carregar nesta sequência para respeitar dependências FK. Marcar cada tabela ao concluir.

```
Task Progress:
- [ ]  1. tab_programas
- [ ]  2. tab_proponentes
- [ ]  3. tab_consorcios
- [ ]  4. rlc_dados_disponibilizacao_programas
- [ ]  5. rlc_dados_uf_modalidade_programas
- [ ]  6. tab_pergunta_selecao_pac
- [ ]  7. tab_apoiadores_emendas_programas
- [ ]  8. rlc_programa_proponente
- [ ]  9. tab_propostas
- [ ] 10. tab_propostas_canceladas
- [ ] 11. tab_propostas_selecao_pac
- [ ] 12. rlc_programa_proposta
- [ ] 13. rlc_proposta_formalizacao_pac
- [ ] 14. tab_resposta_selecao_pac
- [ ] 15. tab_convenios
- [ ] 16. tab_participantes_consorcios
- [ ] 17. rlc_emendas_propostas_proponentes
- [ ] 18. tab_emendas
- [ ] 19. tab_beneficiarios_emendas
- [ ] 20. rlc_historico_situacao
- [ ] 21. tab_justificativas_proposta
- [ ] 22. tab_coordenadas_obras
- [ ] 23. tab_cronograma_desembolso
- [ ] 24. tab_plano_aplicacao_detalhado
- [ ] 25. tab_resumo_fisico_financeiro
- [ ] 26. tab_solicitacao_ajuste_pt
- [ ] 27. tab_data_carga
- [ ] 28. tab_historico_projeto_basico
- [ ] 29. tab_projeto_basico_acffo_modulo_empresas
- [ ] 30. tab_projeto_basico_lae_modulo_empresas
- [ ] 31. tab_projeto_basico_metas_modulo_empresas
- [ ] 32. tab_projeto_basico_proposta_modulo_empresas
- [ ] 33. tab_projeto_basico_submetas_modulo_empresas
- [ ] 34. tab_acomp_obras_contratos_medicoes_modulo_empresas
- [ ] 35. tab_acomp_obras_valores_itens_medicao_modulo_empresas
- [ ] 36. tab_vrpl_proposta_licitacao_modulo_empresas
- [ ] 37. tab_vrpl_metas_submetas_modulo_empresas
- [ ] 38. tab_vrpl_lote_fornecedor_licitacao_modulo_empresas
- [ ] 39. tab_inst_cont_proposta_aio_modulo_empresas
- [ ] 40. tab_inst_cont_contratos_lotes_empresas_modulo_empresas
- [ ] 41. tab_inst_cont_metas_submetas_po_modulo_empresas
- [ ] 42. tab_meta_crono_fisico
- [ ] 43. tab_etapas_crono_fisico
- [ ] 44. tab_licitacao
- [ ] 45. tab_contratos
- [ ] 46. tab_itens_licitacao
- [ ] 47. tab_fornecedores_licitacoes
- [ ] 48. tab_empenhos
- [ ] 49. tab_desembolsos
- [ ] 50. rlc_empenhos_desembolsos
- [ ] 51. tab_pagamentos
- [ ] 52. tab_pagamento_tributo
- [ ] 53. tab_desbloqueio_cr
- [ ] 54. tab_ingresso_contrapartida
- [ ] 55. tab_prorroga_oficios
- [ ] 56. tab_termo_aditivo
- [ ] 57. tab_solicitacao_alteracao
- [ ] 58. tab_solicitacao_rendimento_aplicacao
- [ ] 59. tab_obtv_convenente
```

## Notas

- `tab_data_carga` (posição 27) registra metadados da carga — atualizar ao final da execução, não no início
- Tabelas do XLSX que não aparecem aqui podem não ter seeder no transferepro — verificar migrations antes de carregar
- Total seed-order.php: 59 tabelas | Total XLSX: 62 mapeamentos — validar cobertura cruzada ao implementar
