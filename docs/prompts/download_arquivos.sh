#!/bin/bash
# =============================================================================
# download_transferegov.sh
# Baixa e descompacta todos os arquivos ZIP do TransfereGov
# URL base: https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov/
# =============================================================================

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES — ajuste conforme necessário
# ---------------------------------------------------------------------------
BASE_URL="https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov"
DEST_DIR="${1:-/data/transferegov}"   # diretório de destino (1º argumento ou padrão)
UNZIP_DIR="${DEST_DIR}/extraidos"     # subpasta para arquivos descompactados
LOG_FILE="${DEST_DIR}/download.log"
MANTER_ZIP=false                      # true = mantém os .zip após extrair
PARALELO=false                        # true = downloads em paralelo (experimental)

# ---------------------------------------------------------------------------
# LISTA DE ARQUIVOS (65 arquivos — atualizado em 21/07/2026)
# ---------------------------------------------------------------------------
ARQUIVOS=(
  "apoiadores_emendas_programas.zip"
  "app_parceriasgov_necessidades_aprovadas.zip"
  "app_parceriasgov_necessidades.zip"
  "data_carga_mobile.zip"
  "data_carga_siconv.zip"
  "siconv_acomp_obras_contratos_medicoes_modulo_empresas.zip"
  "siconv_acomp_obras_valores_itens_medicao_modulo_empresas.zip"
  "siconv_consorcios.zip"
  "siconv_contrato_cipi.zip"
  "siconv_contrato.zip"
  "siconv_convenio.zip"
  "siconv_coordenadas_obra.zip"
  "siconv_cronograma_desembolso.zip"
  "siconv_dados_obrasgov_geral.zip"
  "siconv_desbloqueio_cr.zip"
  "siconv_desbloqueio_recurso_cr.zip"
  "siconv_desembolso.zip"
  "siconv_dl.zip"
  "siconv_emenda.zip"
  "siconv_empenho_cipi.zip"
  "siconv_empenho_desembolso.zip"
  "siconv_empenho.zip"
  "siconv_etapa_crono_fisico.zip"
  "siconv_execucao_fisica_cipi.zip"
  "siconv_historico_projeto_basico.zip"
  "siconv_historico_situacao.zip"
  "siconv_ingresso_contrapartida.zip"
  "siconv_inst_cont_contratos_lotes_empresas_modulo_empresas.zip"
  "siconv_inst_cont_metas_submetas_po_modulo_empresas.zip"
  "siconv_inst_cont_proposta_aio_modulo_empresas.zip"
  "siconv_itens_dl.zip"
  "siconv_itens_licitacao.zip"
  "siconv_justificativas_proposta.zip"
  "siconv_licitacao.zip"
  "siconv_meta_crono_fisico.zip"
  "siconv_obtv_convenente.zip"
  "siconv_pagamento_tributo.zip"
  "siconv_pagamento.zip"
  "siconv_pergunta_selecao_pac.zip"
  "siconv_plano_aplicacao_detalhado.zip"
  "siconv_programa_proponentes.zip"
  "siconv_programa_proposta.zip"
  "siconv_programa.zip"
  "siconv_projeto_basico_acffo_modulo_empresas.zip"
  "siconv_projeto_basico_lae_modulo_empresas.zip"
  "siconv_projeto_basico_metas_modulo_empresas.zip"
  "siconv_projeto_basico_proposta_modulo_empresas.zip"
  "siconv_projeto_basico_submetas_modulo_empresas.zip"
  "siconv_prop_inst_indicadores_estados.zip"
  "siconv_prop_inst_indicadores_municipios.zip"
  "siconv_proponentes.zip"
  "siconv_proposta_cancelada.zip"
  "siconv_proposta_formalizacao_pac.zip"
  "siconv_proposta_selecao_pac.zip"
  "siconv_proposta.zip"
  "siconv_prorroga_oficio.zip"
  "siconv_resposta_selecao_pac.zip"
  "siconv_resumo_fisico_financeiro.zip"
  "siconv_solicitacao_ajuste_pt.zip"
  "siconv_solicitacao_alteracao.zip"
  "siconv_solicitacao_rendimento_aplicacao.zip"
  "siconv_termo_aditivo.zip"
  "siconv_vrpl_lotes_fornecedores_licitacao_modulo_empresas.zip"
  "siconv_vrpl_metas_submetas_modulo_empresas.zip"
  "siconv_vrpl_proposta_licitacao_modulo_empresas.zip"
)

# ---------------------------------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------------------------------
log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

baixar_e_extrair() {
  local arquivo="$1"
  local url="${BASE_URL}/${arquivo}"
  local destino="${DEST_DIR}/${arquivo}"

  log "Baixando: ${arquivo}"
  if curl -fsSL --retry 3 --retry-delay 5 -o "$destino" "$url"; then
    log "OK download: ${arquivo}"

    log "Extraindo: ${arquivo}"
    if unzip -oq "$destino" -d "$UNZIP_DIR"; then
      log "OK extração: ${arquivo}"
      if [ "$MANTER_ZIP" = false ]; then
        rm -f "$destino"
        log "ZIP removido: ${arquivo}"
      fi
    else
      log "ERRO ao extrair: ${arquivo}" >&2
      return 1
    fi
  else
    log "ERRO ao baixar: ${url}" >&2
    return 1
  fi
}

# ---------------------------------------------------------------------------
# INÍCIO
# ---------------------------------------------------------------------------
ERROS=0
TOTAL=${#ARQUIVOS[@]}

log "======================================================"
log "Iniciando download de ${TOTAL} arquivos do TransfereGov"
log "Destino: ${DEST_DIR}"
log "======================================================"

mkdir -p "$DEST_DIR" "$UNZIP_DIR"

if [ "$PARALELO" = true ]; then
  # Downloads em paralelo — útil para arquivos pequenos, cuidado com a banda
  for arquivo in "${ARQUIVOS[@]}"; do
    baixar_e_extrair "$arquivo" &
  done
  wait
else
  CONTADOR=0
  for arquivo in "${ARQUIVOS[@]}"; do
    CONTADOR=$((CONTADOR + 1))
    log "Progresso: ${CONTADOR}/${TOTAL}"
    baixar_e_extrair "$arquivo" || ERROS=$((ERROS + 1))
  done
fi

log "======================================================"
log "Concluído. Erros: ${ERROS}/${TOTAL}"
log "======================================================"

exit $ERROS
