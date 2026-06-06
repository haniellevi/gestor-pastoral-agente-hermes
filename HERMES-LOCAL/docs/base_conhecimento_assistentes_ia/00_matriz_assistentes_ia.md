# Matriz dos Assistentes de IA

## Principio

O BotConversa executa fluxos. A IA interpreta, resume, extrai dados e decide uma saida. Nenhum assistente deve assumir decisao pastoral sensivel nem inventar informacao nao confirmada.

## Assistentes

| Assistente | Funcao | Fluxo principal | Saidas principais |
|---|---|---|---|
| `Rute Geral` | Recepcao e roteamento | `Mensagem Padrão - IA RUTE` | `AtualizaCadastro`, `Visitante`, `PedidoOracao`, `Aconselhamento`, `CelulaG12`, `Ministerio`, `Evento`, `Humano`, `Menu` |
| `Rute Cadastro` | Atualizacao cadastral | `Atualização Cadastral`, `Recadastro Anual` | `Sucesso`, `CadastroIncompleto`, `Humano`, `Inatividade` |
| `Caleb Visitantes` | Visitantes e acompanhamento 24h | `VISITANTE / Consolidação 24h` | `Sucesso`, `PrecisaAcompanhamento`, `CelulaG12`, `Humano` |
| `Caleb Celulas G12` | Celulas, G12 e trilhas | `G12 e Celulas` | `InteresseCelula`, `Lider`, `RelatorioCelula`, `Humano` |
| `Intercessao Oracao` | Pedido de oracao | `Pedido de Oracao` | `Sucesso`, `Crise`, `Humano` |
| `Triagem Aconselhamento` | Acolhimento seguro | `Pedido de Aconselhamento` | `Humano`, `Crise`, `Resumo` |
| `Ministerios Voluntariado` | Interesse em servir | `Ministerios` | `Sucesso`, `RevisaoHumana`, `Humano` |
| `Eventos Agenda` | Eventos confirmados | `Eventos e Agenda` | `Sucesso`, `EventoNaoConfirmado`, `Humano` |
| `Barnabe Comunicacao` | Comunicacao interna | `Comunicacao / Barnabe` | `Ideia`, `Roteiro`, `RevisaoHumana` |
| `Neemias Pastor` | Foco e rotina do Pastor | Fluxo privado | `Metas`, `Procrastinacao`, `ResumoSemanal` |
| `Barnabe Sermoes` | Resumo de sermoes | `Publicar Resumo do Culto` | `MensagemPronta`, `RevisaoHumana` |
| `Caleb Relatorios Celula` | Relatorios de celulas | `Relatorio de Celula` | `RelatorioCompleto`, `DadosFaltando`, `Humano` |
| `Rute Agenda G12` | Agenda para G12 | `Agenda G12` | `MensagemMensal`, `MensagemSemanal`, `ErroAgenda` |

## Campos compartilhados

- `Resumo_Atend_IA`
- `Ultima_Intencao`
- `Precisa_Encaminhar`
- `Nivel_Urgencia`
- `Status_Atendiment_IA`
- `Ultimo_Fluxo_Encamin`

## Etiquetas compartilhadas

- `IA - Em Atendimento`
- `Humano Necessario`
- `Atend Humano Ativo`
- `Cadastro Completo`
- `Cadastro_Incompleto`
- `Atualização Pendente`
- `Atualização Cadastral`

## Regras comuns

1. Responder em portugues do Brasil.
2. Usar tom pastoral, respeitoso e objetivo.
3. Fazer uma pergunta por vez.
4. Salvar resumo sempre que o fluxo usar IA.
5. Encaminhar para humano em crise, denuncia, conflito grave, aconselhamento profundo, reclamacao sensivel ou informacao nao confirmada.
6. Nao prometer horario, vaga, inscricao, contato pastoral ou resposta imediata sem confirmacao do fluxo/humano.
