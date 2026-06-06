# Hermes 2.0 - Implementação MVP

Data: 2026-06-05

## Decisão

O Hermes 2.0 nasce como uma camada paralela e limpa dentro do projeto atual. A versão 1 continua funcionando como legado enquanto a v2 recebe tráfego real por etapas.

## Núcleo v2

- Entrada única do BotConversa: `POST /webhook/botconversa`.
- Banco oficial em produção: Supabase/Postgres.
- SQLite fica apenas como fallback local e testes.
- Centro operacional: `inbox_pastoral`.
- Tarefas e prazos: `tarefas_pastorais`.
- Idempotência e auditoria: `event_logs`.

## Payload padrão

```json
{
  "subscriber_id": 123,
  "nome": "Nome da pessoa",
  "telefone": "5589999999999",
  "mensagem": "Texto ou resumo recebido",
  "fluxo_origem": "VISITANTE",
  "tipo_evento": "visitante",
  "campos": {}
}
```

## Intenções iniciais

- `visitante` -> Caleb, tarefa de consolidação 24h.
- `relatorio_celula` -> Caleb, registro em `relatorios_celulas`.
- `pedido_oracao` -> Rute, tarefa pastoral.
- `aconselhamento` -> Rute, prioridade alta.
- `humano_necessario` -> Rute, prazo curto.
- `agenda` -> Rute.
- `conteudo` -> Barnabé.
- `foco` -> Neemias.
- `outro` -> Rute.

## Migração

1. Rodar a migration `supabase/migrations/20260605143000_hermes_v2_mvp.sql`.
2. Configurar no BotConversa um fluxo piloto apontando para `/webhook/botconversa`.
3. Começar por visitantes e consolidação 24h.
4. Migrar relatórios de célula.
5. Migrar oração, aconselhamento e humano.
6. Usar `dashboard/app_v2.py` como painel operacional durante a transição.
7. Só desativar rotas antigas após validação real.

## Legado preservado

As rotas antigas continuam no servidor:

- `/webhook_atualizacao_cadastral`
- `/webhook_atendimento_rute`
- `/webhook_visitante`
- `/webhook_consolidacao_contato`
- `/webhook_g12_celulas`
- `/webhook_midia`
- `/webhook_audio_tts`
- `/webhook_documento`

