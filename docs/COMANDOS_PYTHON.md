# Comandos Python — Carga SICONV

Guia passo a passo para executar o pipeline de carga incremental no terminal.

Todos os comandos devem ser executados na **raiz do projeto** (`carga_arquivos_transferegov`).

---

## Comando único — carga completa

Para executar **toda a carga** (download, extração, staging, MERGE e atualização de `tab_data_carga`) em um único passo:

```powershell
cd D:\claude\claude_code\carga_arquivos_transferegov
.\.venv\Scripts\Activate.ps1
python -m src.orchestrator run
```

Esse é o comando usado pelo Agendador de Tarefas do Windows (`scripts/run_carga.bat`).

**O que o `run` faz automaticamente:**

1. Baixa os ZIPs do repositório público SICONV (com cache)
2. Extrai os CSVs para `data/extracted/`
3. Processa cada tabela na ordem de FK (`load_order`)
4. Grava logs em `logs/carga_*.log` e resumo em `logs/resumo_*.json`
5. Registra controle em `transfere_pro_transferegov.controle_carga`
6. Atualiza `tab_data_carga` se ao menos uma tabela for processada

---

## Passo a passo — primeira execução

### 1. Entrar na pasta do projeto

```powershell
cd D:\claude\claude_code\carga_arquivos_transferegov
```

### 2. Criar o ambiente virtual (apenas na primeira vez)

```powershell
python -m venv .venv
```

### 3. Ativar o ambiente virtual

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**CMD:**

```cmd
.\.venv\Scripts\activate.bat
```

### 4. Instalar dependências (apenas na primeira vez)

```powershell
pip install -r requirements.txt
```

### 5. Configurar o `.env` (apenas na primeira vez)

Copie o exemplo e preencha as credenciais:

```powershell
copy .env.example .env
```

Edite `.env` com host, porta, banco, usuário e senha do PostgreSQL.

### 6. Criar tabelas de controle de carga (apenas na primeira vez)

Execute o SQL unificado no banco `transferepro` (instalação e migração idempotente):

```powershell
psql -h localhost -p 5433 -U postgres -d transferepro -f docs\sql\controle_carga.sql
```

- `controle_carga_dia` — resumo por execução (várias cargas no mesmo dia)
- `controle_carga` — detalhe por tabela/arquivo (inseridos, atualizados, status, vínculo com carga do dia)

### 7. Listar tabelas do catálogo (opcional — conferência)

```powershell
python -m src.orchestrator list-tables
```

### 8. Testar com uma tabela pequena (recomendado antes do `run` completo)

```powershell
python -m src.orchestrator run-table tab_programas
python -m src.orchestrator run-table tab_proponentes
```

### 9. Executar a carga completa

```powershell
python -m src.orchestrator run
```

### 10. Verificar resultado

```powershell
python -m src.orchestrator status
python -m src.orchestrator validate
```

---

## Passo a passo — execução diária (rotina)

Quando o ambiente já está configurado, basta:

```powershell
cd D:\claude\claude_code\carga_arquivos_transferegov
.\.venv\Scripts\Activate.ps1
python -m src.orchestrator run
python -m src.orchestrator status
```

Ou, sem ativar o venv:

```powershell
cd D:\claude\claude_code\carga_arquivos_transferegov
.\.venv\Scripts\python.exe -m src.orchestrator run
```

---

## Comandos disponíveis

| Comando | Descrição |
|---------|-----------|
| `python -m src.orchestrator run` | **Carga completa** — único comando para todo o pipeline |
| `python -m src.orchestrator run-table <tabela>` | Carga de **uma tabela** específica |
| `python -m src.orchestrator download-only` | Apenas download dos ZIPs e extração dos CSVs |
| `python -m src.orchestrator list-tables` | Lista tabelas, CSV de origem e status da chave |
| `python -m src.orchestrator status` | Última `data_carga` e controle de carga em banco |
| `python -m src.orchestrator validate` | Validação pós-carga (contagens, integridade) |

---

## Comandos por cenário

### Só baixar e extrair arquivos (sem carregar no banco)

```powershell
python -m src.orchestrator download-only
```

### Recarregar uma tabela após correção

```powershell
python -m src.orchestrator run-table tab_meta_crono_fisico
```

### Ver o log da última execução

```powershell
Get-ChildItem logs\carga_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content logs\carga_20260620_094640.log -Tail 30
```

### Ver o resumo JSON da última execução

```powershell
Get-ChildItem logs\resumo_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

## Agendamento automático (Windows)

Para executar o `run` diariamente às 09:15 sem terminal aberto:

```powershell
.\scripts\register_tarefa.ps1 -Horario "09:15"
```

Detalhes em [AGENDAMENTO_WINDOWS.md](AGENDAMENTO_WINDOWS.md).

---

## Referência rápida

```
┌─────────────────────────────────────────────────────────────┐
│  COMANDO PRINCIPAL (carga inteira):                         │
│                                                             │
│    python -m src.orchestrator run                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
