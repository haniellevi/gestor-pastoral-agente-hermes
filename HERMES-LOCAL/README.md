# 🤖 Hermes Local: Gestão Pastoral Inteligente

Este diretório contém a estrutura de configuração local, scripts auxiliares de automação, integrações (WhatsApp/Telegram e Supabase) e o Dashboard de BI em Streamlit do ecossistema de agentes do Pastor Raniel Levi.

---

## Hermes 2.0 MVP

A versão 2.0 simplifica a operação em torno de um webhook único e um painel operacional enxuto.

- Webhook principal: `POST /webhook/botconversa`
- Health check: `GET /health`
- Dashboard padrão: `dashboard/app_v2.py`
- Dashboard legado preservado: `dashboard/app.py`
- Documento técnico: `docs/HERMES_2_0_IMPLEMENTACAO.md`
- Migration Supabase: `supabase/migrations/20260605143000_hermes_v2_mvp.sql`

Para rodar o painel v2 localmente:

```bash
streamlit run dashboard/app_v2.py
```

Para rodar a API local:

```bash
uvicorn integrations.webhook_server:app --host 0.0.0.0 --port 5050
```

---

## 🛠️ 1. Como Instalar o Hermes Agent Localmente no seu Windows

O script de instalação oficial da Nous Research provisiona automaticamente o **Python 3.11**, **Node.js**, **uv (gerenciador de pacotes)**, **ripgrep** e **ffmpeg**, isolando a instalação em `%LOCALAPPDATA%\hermes`.

### Passo a Passo da Instalação:

1.  Abra o **PowerShell** como Administrador no seu Windows.
2.  Copie, cole e execute o comando abaixo:
    ```powershell
    iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
    ```
3.  Aguarde a conclusão do download e configuração automática de todas as dependências.
4.  **Feche o terminal PowerShell e abra-o novamente** para que as novas variáveis de ambiente e o comando `hermes` sejam recarregados.

---

## ⚙️ 2. Configurando o seu Projeto

Após instalar o Hermes no seu computador, faremos o setup das chaves de API e das integrações. 

### Passo 1: Inicializando o Setup
Dentro desta pasta `HERMES-LOCAL`, abra o terminal e execute:
```bash
hermes setup
```
Este assistente guiará você na escolha do seu provedor de inteligência artificial (ex: OpenRouter para uso de modelos em nuvem como Llama 3 / Claude, ou Ollama caso queira rodar modelos 100% locais e de graça no seu computador).

### Passo 2: Configurando o Telegram (Recomendado para Testes Iniciais)
O Telegram é extremamente fácil e estável de integrar localmente:
1.  Abra o aplicativo do **Telegram** no seu celular ou PC.
2.  Pesquise pelo usuário **`@BotFather`** (o bot oficial do Telegram para criação de outros bots).
3.  Envie o comando `/newbot` e siga as instruções para dar um nome (ex: `RuteAssistenteBot`) e um usuário.
4.  O `@BotFather` te enviará um **Token de API** (uma longa sequência de letras e números). Guarde este token!
5.  No terminal do seu PC, rode:
    ```bash
    hermes gateway
    ```
    E insira o Token fornecido para ligar o agente ao Telegram.

---

## 📁 3. Estrutura de Pastas Planejada para o Projeto

Ao longo do desenvolvimento, criaremos os seguintes arquivos nesta pasta:
*   `/database/` - Scripts de migração SQL.
*   `/dashboard/` - Código do Dashboard interativo em Streamlit (`app.py`).
*   `/agents/` - Prompts e arquivos de configuração personalizados para Rute, Caleb, Barnabé e Neemias.
*   `/integrations/` - Scripts de integração com as APIs do Google.
*   `run_local.bat` - Script de um clique para iniciar os bots do Hermes e o Dashboard no seu computador simultaneamente.

---

## 📅 4. Integração com Google APIs (Google Calendar, Sheets, Gmail, etc.)

Esta funcionalidade permite que a agente **Rute** sincronize de forma bidirecional a agenda local do SQLite com a do seu celular (Google Calendar), além de preparar o sistema para as próximas integrações.

### Como configurar em 3 passos simples:

1. **Baixe o arquivo de credenciais:**
   Siga os passos do **Passo 1 — Criar as Credenciais OAuth** enviados pelo Pastor, faça o download do arquivo JSON e salve-o na sua pasta de **Downloads** do Windows (o script irá encontrá-lo automaticamente) ou em outra pasta conhecida.

2. **Execute a Autenticação (OAuth):**
   Abra o terminal na pasta `HERMES-LOCAL` e execute o comando abaixo (substituindo pelo caminho do seu arquivo JSON caso ele não esteja na pasta de Downloads):
   ```bash
   python integrations/google_auth.py --secrets "C:\Caminho\Para\Seu\client_secret_xxxxx.json"
   ```
   *Nota: Se o arquivo estiver em Downloads, basta rodar apenas `python integrations/google_auth.py`.*
   Isso abrirá uma janela no seu navegador solicitando autorização. Faça login com a conta da igreja (`igrejafiladelfiacorrente@gmail.com`) e autorize o aplicativo. Um arquivo de token seguro (`integrations/token.json`) será gerado.

3. **Rode a Sincronização:**
   Para sincronizar a agenda local com o Google Calendar agora, execute no terminal:
   ```bash
   python integrations/google_calendar_sync.py
   ```
   Os novos compromissos criados no banco local serão enviados para a agenda Google, e os eventos criados no celular nos últimos 7 dias / próximos 30 dias serão importados para o banco SQLite com categorização automática!
