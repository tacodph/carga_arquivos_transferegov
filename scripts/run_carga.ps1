# Wrapper PowerShell — carga SICONV incremental (Agendador de Tarefas)
$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Python do venv nao encontrado: $Python"
    exit 1
}

& $Python -m src.orchestrator run
exit $LASTEXITCODE
