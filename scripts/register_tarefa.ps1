# Registra tarefa diaria no Agendador de Tarefas do Windows para a carga SICONV.
# Uso: .\scripts\register_tarefa.ps1 [-Horario "09:15"] [-NomeTarefa "Carga SICONV TransfereGov"]
#
# Nao exige administrador para tarefas do usuario atual.
# Para conta de servico ou "Executar estando o usuario desconectado", pode ser necessario
# executar como administrador e informar credenciais na criacao da tarefa.

param(
    [string]$Horario = "09:15",
    [string]$NomeTarefa = "Carga SICONV TransfereGov"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BatPath = Join-Path $ProjectRoot "scripts\run_carga.bat"

if (-not (Test-Path $BatPath)) {
    Write-Error "Script nao encontrado: $BatPath"
    exit 1
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "venv nao encontrado. Crie com: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}

try {
    $hora = [DateTime]::ParseExact($Horario, "HH:mm", $null)
} catch {
    Write-Error "Horario invalido: $Horario (use formato HH:mm, ex.: 09:15)"
    exit 1
}

$At = (Get-Date).Date.AddHours($hora.Hour).AddMinutes($hora.Minute)

$existing = Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removendo tarefa existente: $NomeTarefa"
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
}

$Action = New-ScheduledTaskAction `
    -Execute $BatPath `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At $At

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)

Register-ScheduledTask `
    -TaskName $NomeTarefa `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Carga incremental SICONV/TransfereGov (python -m src.orchestrator run)" | Out-Null

Write-Host "Tarefa registrada com sucesso."
Write-Host "  Nome:     $NomeTarefa"
Write-Host "  Horario:  diario as $Horario"
Write-Host "  Script:   $BatPath"
Write-Host "  Pasta:    $ProjectRoot"
Write-Host ""
Write-Host "Testar:  Start-ScheduledTask -TaskName '$NomeTarefa'"
Write-Host "Status:  python -m src.orchestrator status"
