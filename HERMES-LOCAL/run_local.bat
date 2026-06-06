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
echo [1/5] Verificando dependencias do Streamlit no venv do Hermes...
"%PIP_EXE%" show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando streamlit, pandas e numpy...
    "%PIP_EXE%" install streamlit pandas numpy
) else (
    echo [OK] Dependencias encontradas no venv.
)
echo.

:: 2. Iniciando o Dashboard Streamlit em segundo plano
echo [2/5] Iniciando o Dashboard Hermes 2.0...
start "Dashboard Hermes 2.0" cmd /k ""%PYTHON_EXE%" -m streamlit run dashboard/app_v2.py"
echo.

:: 3. Iniciando o Servidor de Webhook do Hermes
echo [3/5] Iniciando o Servidor de Webhook do Hermes (BotConversa Integration)...
start "Hermes Webhook" cmd /k ""%PYTHON_EXE%" integrations/webhook_server.py"
echo.

:: 4. Iniciando o Túnel Ngrok
echo [4/5] Iniciando o Túnel Ngrok na porta 5050...
start "Ngrok Tunnel" cmd /k "ngrok http 5050 --domain=rolanda-unpent-elliana.ngrok-free.dev"
echo.

:: 5. Iniciando o Gateway Hermes
echo [5/5] Iniciando o Gateway Hermes...
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
