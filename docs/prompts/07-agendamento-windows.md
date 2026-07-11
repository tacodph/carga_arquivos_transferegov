# Prompt 07 — Agendamento no Windows Task Scheduler

Copie o bloco abaixo e cole no Claude Code.

---

## Prompt

```
Implemente o agendamento diário da carga SICONV no Agendador de Tarefas do Windows.

## Contexto
Fases 1-6 implementadas. Orquestrador CLI funcional (`python -m src.orchestrator run`).
Objetivo: executar a carga automaticamente todos os dias às **09:15**, sem depender de terminal aberto.
Ambiente: Windows 10/11, projeto em `carga_arquivos_transferegov`, venv em `.venv/`.

## Leia antes de codar
- docs/CARGA_DISCRICIONARIAS.md (fluxo completo)
- src/orchestrator.py (comando `run`)
- src/config.py (PROJECT_ROOT, LOGS_DIR)
- docs/prompts/05-orquestrador.md e 06-validacao.md

## Entregáveis

1. **scripts/run_carga.bat** — wrapper para o Agendador:
   - Resolver `PROJECT_ROOT` a partir do diretório do script (`%~dp0\..`)
   - `cd /d` para a raiz do projeto (obrigatório: `.env` e imports relativos)
   - Executar: `.venv\Scripts\python.exe -m src.orchestrator run`
   - Propagar código de saída (`exit /b %ERRORLEVEL%`)
   - Não usar `activate.bat` (caminhos absolutos são mais confiáveis no scheduler)

2. **scripts/run_carga.ps1** — equivalente PowerShell (opcional, mas entregar):
   - Mesma lógica do `.bat`
   - `$PSScriptRoot` para localizar a raiz do projeto
   - `exit $LASTEXITCODE` ao final

3. **scripts/register_tarefa.ps1** — registro automatizado da tarefa:
   - Parâmetros opcionais: `-Horario "09:15"`, `-NomeTarefa "Carga SICONV TransfereGov"`
   - Usar `Register-ScheduledTask` (não XML manual)
   - Ação: executar `run_carga.bat` com `WorkingDirectory` = raiz do projeto
   - Gatilho: diário no horário informado (padrão 09:15)
   - Configurações: `StartWhenAvailable`, `AllowStartIfOnBatteries`, `DontStopIfGoingOnBatteries`
   - Exigir execução como administrador apenas se necessário; documentar no script
   - Idempotente: remover tarefa existente com mesmo nome antes de recriar, ou usar `-Force`

4. **docs/AGENDAMENTO_WINDOWS.md** — guia operacional:
   - Pré-requisitos (PostgreSQL ativo, `.env` configurado, `run` manual OK)
   - Instalação rápida: `.\scripts\register_tarefa.ps1`
   - Configuração manual no `taskschd.msc` (passo a passo com campos exatos)
   - Como testar: botão "Executar" no Agendador + verificação de logs
   - Onde ver resultado: `logs/carga_*.log`, `logs/resumo_*.json`, `python -m src.orchestrator status`
   - Troubleshooting: caminho errado, venv ausente, PostgreSQL parado, conta sem permissão

## Configuração da tarefa (referência)

| Campo | Valor |
|-------|-------|
| Nome | `Carga SICONV TransfereGov` |
| Programa/script | `{PROJECT_ROOT}\scripts\run_carga.bat` |
| Iniciar em | `{PROJECT_ROOT}` |
| Gatilho | Diário, 09:15 |
| Executar com privilégios mais altos | Apenas se a conta de serviço exigir |

Alternativa sem `.bat` (documentar, não usar como padrão):

| Campo | Valor |
|-------|-------|
| Programa | `{PROJECT_ROOT}\.venv\Scripts\python.exe` |
| Argumentos | `-m src.orchestrator run` |
| Iniciar em | `{PROJECT_ROOT}` |

## Restrições
- Não alterar lógica do pipeline (orchestrator, merge, staging)
- Não commitar `.env` nem credenciais
- Scripts devem funcionar com caminhos que contenham espaços
- Horário padrão: 09:15 (configurável via parâmetro do `register_tarefa.ps1`)
- Logs do pipeline continuam em `logs/` via `logging_config` existente; o wrapper não precisa redirecionar stdout

## Critérios de aceite
- [ ] `scripts\run_carga.bat` executa `run` com sucesso a partir do Explorer ou cmd
- [ ] `scripts\register_tarefa.ps1` cria a tarefa diária às 09:15 sem erro
- [ ] Tarefa aparece no Agendador (`taskschd.msc`) com nome e caminhos corretos
- [ ] "Executar" manualmente no Agendador dispara a carga e gera `logs/carga_*.log`
- [ ] `docs/AGENDAMENTO_WINDOWS.md` cobre instalação automática e manual
- [ ] Código de saída != 0 quando o pipeline falha (Agendador registra falha)

## Teste sugerido
cd D:\claude\claude_code\carga_arquivos_transferegov
.\scripts\run_carga.bat
echo %ERRORLEVEL%

# Registrar tarefa (PowerShell como usuário com permissão)
.\scripts\register_tarefa.ps1 -Horario "09:15"

# Verificar tarefa
Get-ScheduledTask -TaskName "Carga SICONV TransfereGov"
Start-ScheduledTask -TaskName "Carga SICONV TransfereGov"

# Após execução
python -m src.orchestrator status
Get-ChildItem logs\carga_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```
