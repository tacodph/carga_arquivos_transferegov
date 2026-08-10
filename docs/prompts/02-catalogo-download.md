# Prompt 02 — Catálogo, Download e Extração

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 2 (catálogo, download, extração) do pipeline SICONV.

## Contexto
A fase 1 (setup) já está implementada: src/config.py, requirements.txt, diretórios.
Catálogo de mapeamentos: data/lista_arquivo_tabela.xlsx (62 linhas, aba transferepro).
Fonte de download: API pública TransfereGov (ZIPs individuais por CSV).

## Leia antes de codar
- docs/CARGA_DISCRICIONARIAS.md (fontes, catálogo, casos especiais)
- .claude/skills/transferegov-carga-arquivos/SKILL.md
- src/config.py (paths, DOWNLOAD_BASE_URL e conexão)

## Entregáveis

1. src/catalog.py:
   - Função load_catalog() lendo o XLSX
   - Retorna lista de dicts: {arquivo, tabelas: list[str], grupo, zip_name, link}
   - Tratar tabelas múltiplas (split por vírgula na coluna tabela)
   - Derivar zip_name de arquivo.csv → arquivo.zip
   - Derivar link de DOWNLOAD_BASE_URL + zip_name
   - Função get_unique_zips() deduplicando downloads

2. src/download.py:
   - Função download_zip(url, dest_path) com urllib
   - Função download_all(catalog) baixando ZIPs únicos para data/downloads/
   - Verificar tamanho > 0 e integridade do ZIP
   - Pular download se arquivo já existe e é válido (cache local)
   - Retry em falhas de rede

3. src/extract.py:
   - Função extract_csvs(catalog, downloads_dir, extracted_dir)
   - Extrair apenas CSVs listados no catálogo (streaming em chunks)
   - Manter nomes originais em data/extracted/

## Restrições
- Base URL: https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov
- Um ZIP por CSV do catálogo (não usar mais siconv.zip monolítico)
- Não implementar carga no banco nesta fase
- Não referenciar ~$lista_arquivo_tabela.xlsx

## Critérios de aceite
- [ ] load_catalog() retorna 62 entradas
- [ ] get_unique_zips() retorna 62 ZIPs (1 por CSV)
- [ ] nenhum zip_name igual a siconv.zip
- [ ] download_all() baixa ZIPs para data/downloads/
- [ ] extract_csvs() extrai CSVs para data/extracted/
- [ ] siconv_convenio.csv existe em data/extracted/ após extração

## Teste sugerido
python -c "
from src.catalog import load_catalog, get_unique_zips
from src.download import download_all
from src.extract import extract_csvs
from src.config import DOWNLOADS_DIR, EXTRACTED_DIR
cat = load_catalog()
zips = get_unique_zips(cat)
print(f'Entradas: {len(cat)}, ZIPs: {len(zips)}')
assert len(zips) == 62
assert all(z['zip_name'] != 'siconv.zip' for z in zips)
download_all(cat)
extract_csvs(cat, DOWNLOADS_DIR, EXTRACTED_DIR)
"
```
