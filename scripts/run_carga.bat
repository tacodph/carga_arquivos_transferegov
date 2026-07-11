@echo off
setlocal

rem Wrapper para o Agendador de Tarefas do Windows — carga SICONV incremental
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%" || exit /b 1

set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo ERRO: Python do venv nao encontrado: %PYTHON% >&2
    exit /b 1
)

"%PYTHON%" -m src.orchestrator run
exit /b %ERRORLEVEL%
