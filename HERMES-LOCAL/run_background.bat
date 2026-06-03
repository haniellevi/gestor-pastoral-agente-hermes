@echo off
:: Script para rodar o ecossistema Hermes em segundo plano (fallback manual)
:: Cada processo roda em janela independente e oculta
set VENV_PATH=C:\Users\hanie\AppData\Local\hermes\hermes-agent\.venv
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set HERMES_EXE=%VENV_PATH%\Scripts\hermes.exe

cd /d "c:\Users\hanie\OneDrive\Documentos\WORKSPACE\Projetos Locais\Gestao Pastoral - Pr Raniel Levi\HERMES-LOCAL"

:: Streamlit Dashboard - janela minimizada e independente
start "" /MIN "%PYTHON_EXE%" -m streamlit run dashboard/app.py --browser.gatherUsageStats false

:: Aguarda 3s para evitar conflito de porta
timeout /t 3 /nobreak >nul

:: Hermes Gateway - janela minimizada e independente
set SHELL=cmd.exe
start "" /MIN "%HERMES_EXE%" gateway

:: Monitor de Conhecimento (Sincronização com o GitHub)
start "" /MIN "%PYTHON_EXE%" integrations\watch_knowledge.py

:: Servidor Webhook Hermes - em segundo plano
start "" /MIN "%PYTHON_EXE%" integrations\webhook_server.py

:: Túnel Ngrok Estático - em segundo plano
start "" /MIN ngrok http 5050 --domain=rolanda-unpent-elliana.ngrok-free.dev

:: Log
echo %date% %time% - Hermes iniciado manualmente (Streamlit + Gateway + Watcher + Webhook + Ngrok) >> startup_log.txt
