# Emendas por ano com parlamentar normalizado

Carga em `src/emendas_parlamentar.py`, DDL em `docs/sql/emendas_parlamentar.sql`
(migration Laravel `2026_10_23_100000_create_emendas_parlamentar_tables.php`).

Roda sozinha no fim do loop do pipeline, quando `tab_beneficiarios_emendas`
está na lista de tabelas (`run` e `resume`). Também dá para rodar à parte, com
os CSVs já extraídos:

```
python -m src emendas-parlamentar
```

Se as tabelas novas não existirem, o passo é pulado com aviso. As tabelas
antigas (`tab_emendas`, `tab_beneficiarios_emendas`, `rlc_emendas_propostas_proponentes`,
`tab_apoiadores_emendas_programas`) continuam sendo carregadas como antes até
o app migrar.

## Regras

- **Parlamentar = código do autor** = `left(nr_emenda, 4)`. No siconv cada
  código tem um nome só; no apoiadores o nome vem com grafias e acentos
  corrompidos. Uma pessoa pode ter vários códigos (deputado que virou senador),
  então `tab_parlamentares` agrupa os códigos de `tab_autores_emendas`.
- **Alias:** cada grafia normalizada (upper, sem acento, só letras/dígitos)
  aponta para um parlamentar em `tab_parlamentares_alias`. É assim que o
  `parlamentar_solicitante` do apoiadores vira `id_parlamentar_solicitante`.
- **Revisão:** código cujo nome no apoiadores pertence a outro parlamentar fica
  com `tab_autores_emendas.fl_revisar = true` (5 casos na carga de 22/10/2026).
- **Ano** = dígitos 6 a 9 do `cod_programa_emenda`. O `nr_emenda` sozinho se
  repete entre anos.
- **Sem proposta:** `id_proposta = 0`. Quando a indicação vira proposta, a linha
  com 0 é inativada e a linha com a proposta entra.
- **Chave duplicada** (só ocorre sem proposta, 177 linhas): fica a de maior
  `valor_repasse_proposta_emenda`.

## Incremental e update

Cada carga é a foto completa do CSV:

1. CSV → staging temporária (normalizada em Python).
2. `INSERT ... ON CONFLICT (chave) DO UPDATE ... WHERE row_hash mudou OR inativo`:
   chave nova entra, chave existente só é regravada se algo mudou.
3. Chaves ativas que não vieram na foto → `fl_ativo = false`, `dte_inativacao`.
   Pulado se a foto tiver menos de 80% das linhas ativas (CSV parcial).
4. `REFRESH MATERIALIZED VIEW vw_emendas_resumo_ano`.

Consultas devem filtrar `fl_ativo`.

## Números da carga de teste (CSVs de 22/10/2026)

| Tabela | Linhas |
| --- | --- |
| tab_emendas_beneficiarios_ano | 290.774 (7.504 sem nr_emenda descartadas) |
| tab_emendas_apoiadores | 292.437 |
| tab_autores_emendas | 1.900 códigos, 173 sem nome em nenhuma fonte (emendas 2009–2015) |
| tab_parlamentares | 1.651 |

Solicitantes do apoiadores sem parlamentar: 601 de 11.763 linhas (55 nomes,
em geral quem não tem emenda federal própria no siconv).

## Outras fontes do mesmo parlamentar

As cargas de transferências especiais (`../tranferencias_especiais`) e fundo a fundo
(`../transferencias_fundo_a_fundo`) usam as mesmas `tab_autores_emendas`,
`tab_parlamentares` e `tab_parlamentares_alias`, pelo mesmo código do autor:

- especiais: `planos_acao_especiais.codigo_parlamentar_emenda_plano_acao`
  (view `se_api_transferencias_especiais.vw_emendas_especiais_parlamentar`);
- fundo a fundo: dígitos 5 a 8 de `programas_beneficiarios_faf.numero_emenda_beneficiario_programa`
  (view `base_transferencias_fundo_fundo.vw_emendas_faf_parlamentar`).

Elas só acrescentam códigos que o siconv não tem (`origem` = `especiais` ou `faf`),
dão nome a códigos sem nome e gravam suas grafias como alias; o nome do siconv
nunca é sobrescrito. As três cargas usam a mesma trava
(`pg_advisory_xact_lock(7465100)`) ao gravar parlamentar. Nas duas views,
`nr_emenda` = autor + sequencial com 4 dígitos, no formato do siconv.
