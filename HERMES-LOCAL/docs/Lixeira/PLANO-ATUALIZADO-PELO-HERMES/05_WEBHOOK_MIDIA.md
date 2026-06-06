# 05 - Webhook `/webhook_midia`

**Data:** 2026-06-05  
**Status:** Proposto para implementação

---

## 1. Objetivo

Registrar toda mídia recebida no WhatsApp para:
- BI e dashboard (quantas mídias, de que tipos, que ações geraram)
- Auditoria (quem enviou, quando, o que resultou)
- Métricas de atendimento (quantas foram para humano, quantas resolvidas)
- Identificação de padrões (muitos áudios de oração? muitas imagens de convite?)

---

## 2. Endpoint

```
POST /webhook_midia
```

**Chamado por:** BotConversa (bloco de Integração/Webhook) no final do fluxo `00 - Midia Recebida - Rute`

**Timeout:** responder em < 5 segundos (o BotConversa tem timeout de ~10s)

---

## 3. Payload

### Payload padrão (qualquer ação)

```json
{
  "evento": "midia_recebida",
  "acao": "resolvido|encaminhado|humano|inativo|loop",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "tipo_midia": "imagem|video|audio|documento|sticker",
  "ultima_intencao": "{{Ultima_Intencao}}",
  "ultimo_fluxo_encaminhado": "{{Ultimo_Fluxo_Encaminhado}}",
  "resumo_ia": "{{Resumo_Atend_IA}}",
  "nivel_urgencia": "{{Nivel_Urgencia}}",
  "status_atendimento": "{{Status_Atendimento_IA}}"
}
```

### Se ação = `encaminhado`

```json
{
  "evento": "midia_recebida",
  "acao": "encaminhado",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "tipo_midia": "audio",
  "ultima_intencao": "Pedido_Oracao",
  "ultimo_fluxo_encaminhado": "Pedido de Oracao",
  "resumo_ia": "Pedido de oração recebido por áudio. Pessoa pediu oração pela família.",
  "nivel_urgencia": "Normal",
  "status_atendimento": "Encaminhado"
}
```

### Se ação = `humano`

```json
{
  "evento": "midia_recebida",
  "acao": "humano",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "tipo_midia": "imagem",
  "ultima_intencao": "Aconselhamento",
  "resumo_ia": "Pessoa enviou print de conversa com relato de crise familiar.",
  "nivel_urgencia": "Alta",
  "status_atendimento": "Humano"
}
```

---

## 4. Implementação no servidor

```python
# NOVO ENDPOINT - Midia Recebida

async def midia_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook midia: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = processar_evento_midia(payload)
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro ao processar evento de mídia: {exc}", exc_info=True)
        log_sync_action(
            acao="midia_recebida",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


def processar_evento_midia(payload: dict) -> dict:
    subscriber_id = payload.get("subscriber_id")
    telefone = normalizar_telefone(payload.get("telefone"))
    nome = payload.get("nome") or "Pessoa sem nome"
    acao = payload.get("acao", "resolvido")
    tipo_midia = payload.get("tipo_midia", "desconhecido")
    ultima_intencao = payload.get("ultima_intencao")
    resumo_ia = payload.get("resumo_ia", "")
    nivel_urgencia = normalizar_urgencia(payload.get("nivel_urgencia") or "Normal")
    ultimo_fluxo = payload.get("ultimo_fluxo_encaminhado")

    conn = get_db_connection()
    cursor = conn.cursor()

    is_pg = not isinstance(conn, sqlite3.Connection)

    # SQLite
    if not is_pg:
        cursor.execute("""
            INSERT INTO eventos_midia (
                subscriber_id, telefone, nome, tipo_midia, acao,
                ultima_intencao, ultimo_fluxo_encaminhado, resumo_ia,
                nivel_urgencia, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            int(subscriber_id) if subscriber_id and not str(subscriber_id).startswith("{{") else None,
            telefone or None,
            str(nome).strip(),
            tipo_midia,
            acao,
            ultima_intencao,
            ultimo_fluxo,
            str(resumo_ia).strip(),
            nivel_urgencia,
        ))
    else:
        # Postgres/Supabase
        cursor.execute("""
            INSERT INTO public.eventos_midia (
                subscriber_id, telefone, nome, tipo_midia, acao,
                ultima_intencao, ultimo_fluxo_encaminhado, resumo_ia,
                nivel_urgencia, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            int(subscriber_id) if subscriber_id and not str(subscriber_id).startswith("{{") else None,
            telefone or None,
            str(nome).strip(),
            tipo_midia,
            acao,
            ultima_intencao,
            ultimo_fluxo,
            str(resumo_ia).strip(),
            nivel_urgencia,
        ))

    conn.commit()
    conn.close()

    log_sync_action(
        acao="midia_recebida",
        entidade_tipo="evento_midia",
        entidade_id=str(subscriber_id or "0"),
        payload=payload,
        status="Sucesso",
        resultado=f"Mídia {tipo_midia} / ação {acao} registrada para {nome}"
    )

    logger.info(f"Mídia registrada: {nome} enviou {tipo_midia} -> {acao}")
    return {"status": "ok", "acao": acao, "tipo_midia": tipo_midia}
```

---

## 5. Tabela no banco

### SQLite

```sql
CREATE TABLE IF NOT EXISTS eventos_midia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER,
    telefone TEXT,
    nome TEXT,
    tipo_midia TEXT,
    acao TEXT,
    ultima_intencao TEXT,
    ultimo_fluxo_encaminhado TEXT,
    resumo_ia TEXT,
    nivel_urgencia TEXT DEFAULT 'Normal',
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eventos_midia_subscriber ON eventos_midia(subscriber_id);
CREATE INDEX idx_eventos_midia_data ON eventos_midia(criado_em);
CREATE INDEX idx_eventos_midia_tipo ON eventos_midia(tipo_midia);
```

### Postgres (Supabase)

```sql
CREATE TABLE IF NOT EXISTS public.eventos_midia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id INTEGER,
    telefone TEXT,
    nome TEXT,
    tipo_midia TEXT,
    acao TEXT,
    ultima_intencao TEXT,
    ultimo_fluxo_encaminhado TEXT,
    resumo_ia TEXT,
    nivel_urgencia TEXT DEFAULT 'Normal',
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_eventos_midia_subscriber ON public.eventos_midia(subscriber_id);
CREATE INDEX idx_eventos_midia_data ON public.eventos_midia(criado_em);
CREATE INDEX idx_eventos_midia_tipo ON public.eventos_midia(tipo_midia);
```

---

## 6. Integração no dashboard (BI)

Métricas que este webhook possibilita:

| Métrica | Fonte | Para que serve |
|---|---|---|
| Total de mídias recebidas/dia | eventos_midia | Volume de atendimento |
| % por tipo (áudio, imagem, doc) | eventos_midia.tipo_midia | Padrão de comunicação |
| % resolvido vs humano vs encaminhado | eventos_midia.acao | Eficiência da IA |
| Tipos de mídia que mais viram humano | eventos_midia | O que a IA não consegue resolver |
| Picos de envio por horário | eventos_midia.criado_em | Quando o povo mais envia mídia |
| Contatos que mais enviam mídia | eventos_midia.subscriber_id | Quem precisa de atendimento humano |