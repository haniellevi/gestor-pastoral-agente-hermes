# Deploy inicial na VPS Hostinger

Servidor informado:

```text
ssh root@2.25.167.107
Ubuntu 24.04 LTS
```

## 1. O que será publicado primeiro

Nesta primeira etapa sobem dois serviços:

- `hermes-api` em `http://IP_DA_VPS:5050`
- `hermes-dashboard` em `http://IP_DA_VPS:8501`

O objetivo é validar webhooks e painel. Depois entraremos com domínio, HTTPS e proxy reverso.

## 2. Comando para rodar no terminal web da Hostinger

No terminal da VPS, rode:

```bash
curl -fsSL https://raw.githubusercontent.com/haniellevi/gestor-pastoral-agente-hermes/feature/instalacao-hermes/deploy/hostinger_bootstrap.sh | bash
```

Na primeira execução, o script vai:

- instalar Docker;
- clonar o repositório em `/opt/hermes-filadelfia`;
- criar `.env` a partir de `.env.example`;
- parar antes de subir containers, para você preencher segredos.

## 3. Editar variáveis

Depois da primeira execução:

```bash
cd /opt/hermes-filadelfia
nano .env
```

Preencha:

```text
SUPABASE_URL=https://bymrxgwjkbbqfzuuvhyk.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
BOTCONVERSA_API_KEY=...
BOTCONVERSA_BASE_URL=https://backend.botconversa.com.br/api/v1/webhook
```

Não coloque `SUPABASE_SERVICE_ROLE_KEY` em GitHub, site público ou BotConversa.

## 4. Subir containers

Depois de salvar `.env`:

```bash
cd /opt/hermes-filadelfia
docker compose up -d --build
docker compose ps
```

## 5. Testar

```bash
curl http://localhost:5050/health
```

Pelo navegador:

```text
http://2.25.167.107:5050/health
http://2.25.167.107:8501
```

## 6. Próximo passo

Depois que estiver respondendo:

- configurar domínio;
- colocar Caddy/Nginx com HTTPS;
- apontar BotConversa para URL HTTPS;
- ativar worker recorrente para Google Drive e Calendar.

