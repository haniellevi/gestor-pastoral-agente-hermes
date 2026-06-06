# Hermes v1 Legado

Este diretório registra o congelamento operacional da v1 enquanto a v2 entra em produção por etapas.

## Código legado preservado

- Servidor: `integrations/webhook_server.py`
- Dashboard completo antigo: `dashboard/app.py`
- Scripts SQLite/Supabase existentes: `database/`
- Prompts dos agentes: `agents/`
- Documentação antiga e auxiliar: `docs/Lixeira/` e `docs/_apoio_botconversa/`

## Rotas legadas mantidas

- `/webhook_atualizacao_cadastral`
- `/webhook_atendimento_rute`
- `/webhook_visitante`
- `/webhook_consolidacao_contato`
- `/webhook_g12_celulas`
- `/webhook_midia`
- `/webhook_audio_tts`
- `/webhook_documento`

## Regra de transição

A v1 não deve ser apagada nem reescrita durante a implantação inicial da v2. Primeiro os fluxos reais do BotConversa devem ser migrados para `/webhook/botconversa`, validados em produção e só depois as rotas antigas podem ser desativadas.

