# Plano de Mídia e Consolidação - Hermes Filadélfia

**Data:** 2026-06-05  
**Autor:** Hermes (Rute)  
**Projeto:** Gestão Conversacional - Igreja Batista Filadélfia Internacional de Corrente-PI  

Este diretório contém o planejamento mestre, as especificações de engenharia e os guias de implementação visual para conectar os fluxos de atendimento do **BotConversa** ao cérebro operacional do **Hermes**, com persistência no banco de dados (SQLite local e Supabase Postgres).

---

## 🗺️ Mapa de Documentos

### 🛠️ Especificação de Mídia Conversacional (Multimodal)
*   **[01. Visão Geral Multimodal](01_VISAO_GERAL_MULTIMODAL.md)**: Abordagem estratégica sobre como o sistema interpreta áudios, imagens, vídeos e documentos sem precisar fazer perguntas desnecessárias ao usuário, integrando-se às políticas da Meta para 2026.
*   **[02. Fluxo de Mídia Completo](02_FLUXO_MIDIA_COMPLETO.md)**: Mapeamento de decisões de estado e controle anti-loops para o fluxo visual `00 - Midia Recebida - Rute`.
*   **[03. Como o BotConversa Entende Mídia](03_COMO_BOTCONVERSA_ENTENDE_MIDIA.md)**: Detalhamento técnico das capacidades de transcrição automática de áudio (Whisper) e visão computacional (GPT-4o Vision) integradas nativamente na plataforma do BotConversa.
*   **[04. Resposta por Áudio no WhatsApp](04_AUDIO_RESPOSTA_ELEVENLABS.md)**: Arquitetura de retorno de voz humanizada ao contato utilizando **ElevenLabs** e **OpenAI TTS**.

### 🔗 Especificações Técnicas de Webhooks e API
*   **[05. Webhook Mídia](05_WEBHOOK_MIDIA.md)**: Endpoint `/webhook_midia` para registro, BI e auditoria de mídias enviadas.
*   **[06. Webhook Audio TTS](06_WEBHOOK_AUDIO_TTS.md)**: Endpoint `/webhook_audio_tts` para geração sob demanda de arquivos MP3 e entrega de áudios realistas.
*   **[07. Processamento de Documentos e Vídeos](07_DOCUMENTO_E_VIDEO.md)**: Endpoint `/webhook_documento` para extração inteligente de textos de PDFs, DOCX e XLSX.

### 🦁 Módulo de Consolidação e Visitantes 24h
*   **[08. Acolhimento de Visitantes](08_ACOLHIMENTO_VISITANTES_24H.md)**: Planejamento estratégico, diretrizes de linguagem quentes e acolhedoras para o acompanhamento rápido e os webhooks de criação (`/webhook_visitante`) e atualização de contatos (`/webhook_consolidacao_contato`).

### 👩💼 Guias Práticos e Passo a Passo
*   **[09. Guia Mestre: Agentes e Fluxos](09_GUIA_MESTRE_AGENTES_E_FLUXOS.md)**: Guia completo clique-por-clique para o senhor criar manualmente os fluxos visuais no BotConversa e configurar as instruções, temperaturas, regras de transição e saídas condicionais de cada um dos **13 assistentes de IA** (como Rute Geral, Rute Cadastro, Caleb Visitantes e Caleb Relatórios) na interface do *GPT Especialista*.

---

## 🎯 Status da Implementação Técnica do Hermes
*   [x] Endpoint `/webhook_midia` adicionado e testado.
*   [x] Endpoint `/webhook_audio_tts` (ElevenLabs + OpenAI fallback) adicionado e testado.
*   [x] Endpoint `/webhook_documento` (PyMuPDF + python-docx + Pandas) adicionado e testado.
*   [x] Endpoint `/webhook_consolidacao_contato` (Caleb update) adicionado e testado.
*   [x] Método de envio de arquivos `send_media` no `BotConversaClient` ativo.
*   [x] Tabelas e índices migrados no SQLite local (`database/pastoral.db`).
*   [x] Tabelas e índices migrados no Supabase Postgres (`database/migrate_supabase_midia.py`).
*   [x] Compilação do servidor de webhooks 100% livre de erros.
*   [x] Suíte de testes (`database/test_webhooks.py`) rodada com 100% de sucesso.
