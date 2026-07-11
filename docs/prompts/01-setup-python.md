# Prompt 01 — Setup Python

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente a fase 1 (setup) do pipeline de carga SICONV em Python.

## Contexto
Projeto: carga_arquivos_transferegov
Objetivo: carga incremental de CSVs do repositório público SICONV para PostgreSQL
Schema destino: transfere_pro_transferegov
Stack: Python 3.10+

## Leia antes de codar
- CLAUDE.md
- docs/CARGA_DISCRICIONARIAS.md (seção "Estrutura de diretórios Python")
- .env (configuração existente)

## Entregáveis

1. requirements.txt com:
   - psycopg2-binary
   - python-dotenv
   - openpyxl
   - pandas

2. .env.example (sem senha) com variáveis:
   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SCHEMA

3. src/config.py:
   - Carrega .env via python-dotenv
   - Expõe dataclass ou dict com configuração de conexão
   - Função get_connection() retornando conexão psycopg2
   - Constantes para paths: DATA_DIR, DOWNLOADS_DIR, EXTRACTED_DIR, LOGS_DIR

4. Criar diretórios vazios (com .gitkeep):
   - data/downloads/
   - data/extracted/
   - logs/
   - src/

5. src/__init__.py vazio

## Restrições
- Não implementar download, merge ou orquestrador nesta fase
- Não criar README
- Usar paths relativos ao diretório do projeto
- Não commitar .env

## Critérios de aceite
- [ ] pip install -r requirements.txt funciona
- [ ] python -c "from src.config import get_connection; get_connection().close()" conecta ao PostgreSQL
- [ ] Diretórios data/downloads, data/extracted, logs existem

## Teste sugerido
python -c "from src.config import get_connection; conn = get_connection(); cur = conn.cursor(); cur.execute('SELECT 1'); print('OK:', cur.fetchone()); conn.close()"
```
