# 06 - Webhook `/webhook_audio_tts`

**Data:** 2026-06-05  
**Status:** Proposto para implementação

---

## 1. Objetivo

Converter texto em áudio e enviar para o contato no WhatsApp via BotConversa API.

Usado quando o Assistente GPT decide que a resposta seria melhor em áudio (conteúdo pastoral, resposta longa, resposta a áudio recebido).

---

## 2. Endpoint

```
POST /webhook_audio_tts
```

**Chamado por:** BotConversa (bloco de Integração/Webhook), ativado pela tag `[RESPOSTA_AUDIO]` no final da resposta da IA.

---

## 3. Payload

```json
{
  "evento": "resposta_audio",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "texto_resposta": "Graça e Paz! Recebi seu pedido de oração e vou registrar aqui em nossa lista de intercessão. Que Deus te abençoe grandemente.",
  "voz": "elevenlabs",
  "tom": "pastoral",
  "contexto": "pedido_oracao",
  "resumo_ia": "Resposta em áudio para pedido de oração"
}
```

### Campos

| Campo | Obrigatório | Descrição |
|---|---|---|
| `subscriber_id` | Sim | ID do contato no BotConversa |
| `nome` | Não | Nome do contato |
| `telefone` | Não | Telefone do contato |
| `texto_resposta` | **Sim** | Texto que será convertido em áudio |
| `voz` | Não | `elevenlabs` (padrão) ou `openai` |
| `tom` | Não | `pastoral` (padrão), `normal`, `acolhedor` |
| `contexto` | Não | Contexto para log: `pedido_oracao`, `aconselhamento`, `informacao`, `boas_vindas` |
| `resumo_ia` | Não | Resumo para auditoria |

---

## 4. Resposta

```json
{
  "status": "ok",
  "message": "Áudio gerado e enviado com sucesso",
  "provider_used": "elevenlabs",
  "audio_duration_seconds": 12,
  "botconversa_message_id": "msg_abc123"
}
```

---

## 5. Implementação

### 5.1 Integração com ElevenLabs

```python
import requests
import json
import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Voice ID padrão


def gerar_audio_elevenlabs(texto: str, voz_id: str = None) -> bytes:
    """Gera áudio MP3 a partir de texto usando ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY não configurada")

    voice_id = voz_id or ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    data = {
        "text": texto,
        "model_id": "eleven_flash_v2_5",  # Rápido e de alta qualidade
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.2,
        }
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.content
```

### 5.2 Integração com OpenAI TTS (fallback)

```python
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def gerar_audio_openai(texto: str) -> bytes:
    """Gera áudio MP3 usando OpenAI TTS (fallback mais barato)."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não configurada")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",  # Voz feminina, calorosa
        input=texto,
    )
    return response.content
```

### 5.3 Endpoint completo

```python
import tempfile
from pathlib import Path

AUDIO_CACHE_DIR = Path(__file__).resolve().parents[1] / "audio_cache"
AUDIO_CACHE_DIR.mkdir(exist_ok=True)


async def audio_tts_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook TTS: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    subscriber_id = payload.get("subscriber_id")
    texto = payload.get("texto_resposta", "").strip()
    voz = payload.get("voz", "elevenlabs")

    if not texto:
        return JSONResponse({"status": "error", "message": "texto_resposta é obrigatório."}, status_code=400)
    
    if not subscriber_id or str(subscriber_id).strip().startswith("{{"):
        # Teste do BotConversa — só valida
        return JSONResponse({"status": "ok", "message": "Conexão TTS estabelecida (modo teste)"})

    try:
        subscriber_id = int(subscriber_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "subscriber_id inválido."}, status_code=400)

    try:
        # 1. Gera áudio
        provider = voz if voz in ("elevenlabs", "openai") else "elevenlabs"
        if provider == "elevenlabs":
            audio_bytes = gerar_audio_elevenlabs(texto)
        else:
            audio_bytes = gerar_audio_openai(texto)

        # 2. Salva arquivo temporário
        audio_filename = f"audio_{subscriber_id}_{int(time.time())}.mp3"
        audio_path = AUDIO_CACHE_DIR / audio_filename
        audio_path.write_bytes(audio_bytes)

        # 3. Envia via BotConversa API
        client = BotConversaClient()
        # A API BotConversa permite enviar mídia (áudio) para um subscriber
        # Se o client não tiver método send_media, implementar ou usar send_message com URL
        message_result = client.send_media(
            subscriber_id=subscriber_id,
            media_type="audio",
            media_url=str(audio_path),  # Ou upload para URL pública
            caption="",  # Áudio não precisa de legenda
        )

        # 4. Registra no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        is_pg = not isinstance(conn, sqlite3.Connection)
        
        if not is_pg:
            cursor.execute("""
                INSERT INTO eventos_audio (
                    subscriber_id, texto_original, provider,
                    duracao_segundos, status, criado_em
                ) VALUES (?, ?, ?, ?, 'enviado', CURRENT_TIMESTAMP)
            """, (subscriber_id, texto[:500], provider, len(texto) // 15))  # estimativa de duração
        else:
            cursor.execute("""
                INSERT INTO public.eventos_audio (
                    subscriber_id, texto_original, provider,
                    duracao_segundos, status, criado_em
                ) VALUES (%s, %s, %s, %s, 'enviado', NOW())
            """, (subscriber_id, texto[:500], provider, len(texto) // 15))
        
        conn.commit()
        conn.close()

        # 5. Log e retorno
        logger.info(f"Áudio enviado para subscriber {subscriber_id} via {provider}: {len(texto)} chars")
        
        return JSONResponse({
            "status": "ok",
            "provider_used": provider,
            "audio_duration_seconds": len(texto) // 15,
            "botconversa_message_id": message_result.get("message_id", "ok"),
        })

    except Exception as exc:
        logger.error(f"Erro ao gerar/enviar áudio: {exc}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)
```

---

## 6. Tabela no banco

### SQLite

```sql
CREATE TABLE IF NOT EXISTS eventos_audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER,
    texto_original TEXT,
    provider TEXT DEFAULT 'elevenlabs',
    duracao_segundos INTEGER,
    status TEXT DEFAULT 'pendente',
    erro TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eventos_audio_subscriber ON eventos_audio(subscriber_id);
CREATE INDEX idx_eventos_audio_status ON eventos_audio(status);
```

### Postgres (Supabase)

```sql
CREATE TABLE IF NOT EXISTS public.eventos_audio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id INTEGER,
    texto_original TEXT,
    provider TEXT DEFAULT 'elevenlabs',
    duracao_segundos INTEGER,
    status TEXT DEFAULT 'pendente',
    erro TEXT,
    criado_em TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Configuração no .env

```env
# ElevenLabs (recomendado)
ELEVENLABS_API_KEY=sua_chave_aqui
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# OpenAI TTS (fallback)
OPENAI_API_KEY=sua_chave_aqui
```

---

## 8. Dashboard (métricas)

| Métrica | Fonte |
|---|---|
| Total de áudios enviados/dia | eventos_audio.criado_em |
| Provider mais usado (elevenlabs vs openai) | eventos_audio.provider |
| Caracteres por áudio (média) | LEN(eventos_audio.texto_original) |
| Taxa de erro | eventos_audio.status = 'erro' |
| Custo estimado (ElevenLabs: centavos/caractere) | Calculado |

---

## 9. Considerações de custo

**ElevenLabs (plano Creator - $22/mês):**
- 100.000 caracteres/mês inclusos
- ~6.600 respostas de áudio curtas (15 chars cada)
- ~330 respostas longas (300 chars cada)
- Para uso pastoral moderado, deve atender

**OpenAI TTS (pay-as-you-go):**
- $0.015 por 1.000 caracteres
- 100.000 caracteres = $1.50
- Muito mais barato, qualidade ligeiramente inferior

**Estratégia recomendada:**
- Usar ElevenLabs como padrão (qualidade pastoral)
- Fallback para OpenAI TTS se ElevenLabs exceder cota mensal
- Registrar métricas para decidir upgrade de plano