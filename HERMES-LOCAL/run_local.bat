@echo off
title Gestao Pastoral - Hermes Local
echo ===================================================
echo   INICIALIZADOR DO ECOSSISTEMA GESTAO PASTORAL
echo ===================================================
echo.

set VENV_PATH=C:\Users\hanie\AppData\Local\hermes\hermes-agent\.venv
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set PIP_EXE=%VENV_PATH%\Scripts\pip.exe
set HERMES_EXE=%VENV_PATH%\Scripts\hermes.exe

:: 1. Verificando dependencias Python para o Streamlit
echo [1/3] Verificando dependencias do Streamlit no venv do Hermes...
"%PIP_EXE%" show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando streamlit, pandas e numpy...
    "%PIP_EXE%" install streamlit pandas numpy
) else (
    echo [OK] Dependencias encontradas no venv.
)
echo.

:: 2. Iniciando o Dashboard Streamlit em segundo plano
echo [2/3] Iniciando o Dashboard Streamlit (BI)...
start "Dashboard Gestao Pastoral" cmd /k ""%PYTHON_EXE%" -m streamlit run dashboard/app.py"
echo.

:: 3. Iniciando o Gateway Hermes
echo [3/3] Iniciando o Gateway Hermes...
echo O terminal do bot do Telegram/WhatsApp abrira a seguir.
echo Para fechar tudo, basta fechar as janelas pretas do terminal.
echo.
pause
start "Hermes Gateway" cmd /k ""%HERMES_EXE%" gateway"

echo.
echo ===================================================
echo   Inicializadores abertos em janelas separadas!
echo ===================================================
pause

