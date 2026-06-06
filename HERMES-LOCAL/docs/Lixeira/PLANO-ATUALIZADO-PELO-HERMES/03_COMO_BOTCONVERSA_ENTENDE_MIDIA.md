# 03 - Como o BotConversa Entende Mídia (Sem Webhook Externo)

**Data:** 2026-06-05  
**Base:** Documentação oficial BotConversa + Pesquisa de campo

---

## 1. A descoberta mais importante

O **bloco Assistente GPT** do BotConversa (chamado de "GPT Especialista" na nova interface) **já entende texto, áudio e imagens nativamente**.

Isso está documentado oficialmente no site de ajuda:

> *"O assistente entende: texto, áudio e imagens."*  
> — Fonte: ajuda.botconversa.com.br, Aula 4 - Criar Assistente com GPT Especialista

**Isso elimina a necessidade de:**
- Webhook externo para transcrição de áudio
- Webhook externo para análise de imagem
- Perguntar "do que se trata?" para midia

---

## 2. Como funciona na prática

### Áudio

1. Pessoa envia áudio no WhatsApp
2. BotConversa recebe o arquivo de áudio
3. Internamente, o BotConversa usa **OpenAI Whisper** (ou tecnologia equivalente) para transcrever o áudio
4. O texto transcrito é enviado ao Assistente GPT como se fosse texto
5. A IA processa e responde

**O que a IA recebe:**
```
[Transcrição do áudio do usuário]:
"Olá, eu gostaria de saber o horário dos cultos e se tem culto hoje"
```

**O que a IA vê:** Apenas o texto, mas ela sabe que veio de um áudio.

### Imagem

1. Pessoa envia imagem (foto, print, arte, sticker)
2. BotConversa recebe o arquivo de imagem
3. Internamente, o BotConversa usa **GPT-4o Vision** (ou equivalente) para analisar a imagem
4. A descrição da imagem é enviada ao Assistente GPT
5. A IA processa e responde

**O que a IA recebe:**
```
[Descrição da imagem enviada pelo usuário]:
"Um cartaz de divulgação com fundo azul, texto em branco dizendo 
'Culto de Celebração - Domingo 19h - Preletor: Pr. Raniel Levi'. 
Tem uma imagem de mãos erguidas ao fundo."
```

**O que a IA vê:** Ela recebe a descrição da imagem e pode agir sobre ela.

### Texto + Mídia

Se a pessoa enviar TEXTO + MÍDIA juntos, o Assistente GPT recebe ambos.

**O que a IA recebe:**
```
[Mensagem de texto do usuário]:
"Pastor, essa é a arte do evento"

[Descrição da imagem]:
"Um cartaz de evento com tema de carnaval, fundo colorido..."
```

---

## 3. O que NÃO funciona nativamente

| Tipo | BotConversa consegue? | Solução |
|---|---|---|
| Áudio | ✅ Sim (transcrição automática) | Nenhuma ação necessária |
| Imagem | ✅ Sim (análise por IA de visão) | Nenhuma ação necessária |
| Sticker | ✅ Sim (tratado como imagem) | Nenhuma ação necessária |
| Vídeo | ❌ Não nativamente | Webhook Hermes para extrair frame + transcrição |
| PDF/DOCX | ❌ Não nativamente | Webhook Hermes para extrair texto |
| Planilha | ❌ Não nativamente | Webhook Hermes para extrair dados |

---

## 4. Configuração no BotConversa

### Não precisa de configuração extra

O bloco Assistente GPT já processa áudio e imagem automaticamente.  
A única coisa que você precisa é:

1. Ter o fluxo `00 - Midia Recebida - Rute` configurado como **Fluxo Padrão para Mídia** nas Configurações do BotConversa
2. Dentro do fluxo, ter um bloco **Assistente GPT** com as instruções corretas
3. Configurar o assistente para SABER que ele consegue ver/ouvir mídia

### O erro comum

Muitos prompts de assistente dizem:

```
"Infelizmente não consigo ver imagens, me explique o que você enviou"
```

Isso faz a IA ignorar a descrição da imagem que o BotConversa já forneceu.  
**O prompt correto deve dizer:**

```
"Você recebeu uma imagem/áudio junto com esta mensagem. 
Analise o conteúdo da mídia e responda adequadamente."
```

---

## 5. Como a Rute Geral deve ser configurada para mídia

As instruções do assistente `Rute Geral` (ou `Rute Midia`, se criar separado) devem incluir:

```
IMPORTANTE - CAPACIDADE MULTIMODAL:
Você CONSEGUE entender o conteúdo de imagens e áudios 
enviados pelo usuário. 

- Se a pessoa enviou uma IMAGEM: você recebeu a descrição 
  do conteúdo visual dela. Analise e responda.
- Se a pessoa enviou um ÁUDIO: você recebeu a transcrição 
  do que foi dito. Analise e responda.
- Se a pessoa enviou TEXTO: leia e responda normalmente.

NUNCA diga que não consegue ver ou ouvir. Você consegue.
```

---

## 6. O que muda no fluxo atual

| Aspecto | Antes (plano original) | Agora (plano atualizado) |
|---|---|---|
| Ao receber mídia | Perguntava "Do que se trata?" | Analisa direto |
| Áudio | Não especificado | Transcrição automática |
| Imagem | Não especificado | Análise por visão computacional |
| Documento | Perguntava e encaminhava | Webhook extrai texto |
| Mensagem inicial | "Recebi sua mídia. Me diga do que se trata" | "Recebi! Deixa eu dar uma olhada" ou pula direto |