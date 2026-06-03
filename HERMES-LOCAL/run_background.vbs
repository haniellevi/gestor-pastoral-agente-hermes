' ============================================================
' Hermes Startup Script - Gestao Pastoral
' Lanca Streamlit Dashboard + Hermes Gateway de forma 100% oculta
' Sem janelas CMD, sem interrupcoes visuais
' ============================================================
Dim WshShell
Set WshShell = CreateObject("WScript.Shell")

' Define caminhos fixos
Dim ProjectDir, VenvPath, PythonExe, HermesExe
ProjectDir = "c:\Users\hanie\OneDrive\Documentos\WORKSPACE\Projetos Locais\Gestao Pastoral - Pr Raniel Levi\HERMES-LOCAL"
VenvPath = "C:\Users\hanie\AppData\Local\hermes\hermes-agent\.venv"
PythonExe = VenvPath & "\Scripts\python.exe"
HermesExe = VenvPath & "\Scripts\hermes.exe"

WshShell.CurrentDirectory = ProjectDir

' 1) Streamlit Dashboard - oculto, independente
WshShell.Run """" & PythonExe & """ -m streamlit run dashboard\app.py --browser.gatherUsageStats false", 0, False

' Pequena pausa para garantir que o Streamlit nao conflite
WScript.Sleep 3000

' 2) Hermes Gateway (Telegram) - oculto, independente
WshShell.Run """" & HermesExe & """ gateway", 0, False

' 3) Monitor de Conhecimento (Sincronização com GitHub) - oculto, independente
WshShell.Run """" & PythonExe & """ integrations\watch_knowledge.py", 0, False

' 4) Servidor Webhook (Integração BotConversa) - oculto, independente
WshShell.Run """" & PythonExe & """ integrations\webhook_server.py", 0, False

' 5) Túnel Ngrok Estático - oculto, independente
WshShell.Run "ngrok http 5050 --domain=rolanda-unpent-elliana.ngrok-free.dev", 0, False

' Opcional: log de inicializacao
Dim FSO, LogFile
Set FSO = CreateObject("Scripting.FileSystemObject")
Set LogFile = FSO.OpenTextFile(ProjectDir & "\startup_log.txt", 8, True)
LogFile.WriteLine Now & " - Hermes iniciado: Streamlit + Gateway + Watcher + Webhook + Ngrok"
LogFile.Close

' Finaliza - o VBS nao precisa ficar rodando, os processos sao independentes
Set WshShell = Nothing
Set FSO = Nothing
