# Agendamento da carga no Windows Task Scheduler

Execução automática diária do pipeline SICONV (`python -m src.orchestrator run`) às **09:15**, sem terminal aberto.

## Pré-requisitos

1. PostgreSQL ativo e acessível (`.env` com `DB_HOST`, `DB_PORT`, `DB_NAME`, etc.)
2. Virtualenv criado e dependências instaladas:
   ```powershell
   cd D:\claude\claude_code\carga_arquivos_transferegov
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```
3. Carga manual bem-sucedida pelo menos uma vez:
   ```powershell
   .\.venv\Scripts\python.exe -m src.orchestrator run-table tab_programas
   ```
4. Tabela `controle_carga` criada (opcional, mas recomendado): `docs/sql/controle_carga.sql`

## Instalação rápida (automática)

No PowerShell, na raiz do projeto:

```powershell
cd D:\claude\claude_code\carga_arquivos_transferegov
.\scripts\register_tarefa.ps1 -Horario "09:15"
```

Parâmetros opcionais:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `-Horario` | `09:15` | Horário diário (formato `HH:mm`) |
| `-NomeTarefa` | `Carga SICONV TransfereGov` | Nome no Agendador |

## Testar manualmente

```powershell
# Via script wrapper (mesmo que o Agendador usa)
.\scripts\run_carga.bat
echo $LASTEXITCODE

# Ou disparar a tarefa agendada
Start-ScheduledTask -TaskName "Carga SICONV TransfereGov"
```

## Onde ver o resultado

| Recurso | Caminho / comando |
|---------|-------------------|
| Log da execução | `logs/carga_YYYYMMDD_HHMMSS.log` |
| Resumo JSON | `logs/resumo_YYYYMMDD_HHMMSS.json` |
| Última carga + controle | `python -m src.orchestrator status` |
| Controle em banco | `transfere_pro_transferegov.controle_carga` |

```powershell
Get-ChildItem logs\carga_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python -m src.orchestrator status
```

## Configuração manual (`taskschd.msc`)

1. Abrir **Agendador de Tarefas** (`Win+R` → `taskschd.msc`)
2. **Criar Tarefa Básica...**
3. Nome: `Carga SICONV TransfereGov`
4. Gatilho: **Diariamente**, às **09:15**
5. Ação: **Iniciar um programa**
6. Preencher:

| Campo | Valor |
|-------|-------|
| Programa/script | `D:\claude\claude_code\carga_arquivos_transferegov\scripts\run_carga.bat` |
| Iniciar em | `D:\claude\claude_code\carga_arquivos_transferegov` |

7. Em **Propriedades** → **Configurações**:
   - Marcar *Iniciar a tarefa assim que possível após uma inicialização agendada perdida*
   - Marcar *Executar tarefa assim que possível após perder o agendamento*
8. **Executar** com o usuário que possui acesso ao PostgreSQL e à pasta do projeto

### Alternativa sem `.bat` (não recomendado)

| Campo | Valor |
|-------|-------|
| Programa | `D:\claude\claude_code\carga_arquivos_transferegov\.venv\Scripts\python.exe` |
| Argumentos | `-m src.orchestrator run` |
| Iniciar em | `D:\claude\claude_code\carga_arquivos_transferegov` |

O `.bat` é preferível: valida o venv e propaga o código de saída corretamente.

## Scripts do projeto

| Arquivo | Função |
|---------|--------|
| `scripts/run_carga.bat` | Wrapper para o Agendador (padrão) |
| `scripts/run_carga.ps1` | Equivalente PowerShell |
| `scripts/register_tarefa.ps1` | Registra/atualiza a tarefa diária |

## Troubleshooting

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| Tarefa não inicia | Caminho errado em "Iniciar em" | Deve ser a **raiz** do projeto (onde está `.env`) |
| `python.exe` não encontrado | venv ausente | `python -m venv .venv` + `pip install -r requirements.txt` |
| Carga falha silenciosamente | PostgreSQL parado | Verificar serviço na porta do `.env` (`DB_PORT`) |
| Código de saída 1 | Erro no pipeline | Ver `logs/carga_*.log` mais recente |
| Sem permissão de rede/DB | Conta do Agendador diferente | Executar tarefa com o mesmo usuário que testou manualmente |
| Tarefa não roda com PC desligado | Esperado | Agendador só executa com máquina ligada; use `StartWhenAvailable` (já configurado no script) |

## Remover a tarefa

```powershell
Unregister-ScheduledTask -TaskName "Carga SICONV TransfereGov" -Confirm:$false
```
