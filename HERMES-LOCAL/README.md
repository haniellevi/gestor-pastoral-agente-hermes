# 🤖 Hermes Local: Gestão Pastoral Inteligente

Este diretório contém a estrutura de configuração local, scripts auxiliares de automação, integrações (WhatsApp/Telegram e Supabase) e o Dashboard de BI em Streamlit do ecossistema de agentes do Pastor Raniel Levi.

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
*   `/database/` - Scripts de migração SQL para o Supabase.
*   `/dashboard/` - Código do Dashboard interativo em Streamlit (`app.py`).
*   `/agents/` - Prompts e arquivos de configuração personalizados para Rute, Caleb, Barnabé e Neemias.
*   `run_local.bat` - Script de um clique para iniciar os bots do Hermes e o Dashboard no seu computador simultaneamente.
