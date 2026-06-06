# Inventario BotConversa - Fase 3 Hermes 2.0

Data da verificacao: 2026-06-05  
Fonte: consulta somente leitura via `integrations.botconversa_client.BotConversaClient`

Este documento registra o que ja existe no BotConversa, o que falta criar, o que deve ser mantido e o que nao deve mais guiar a v2.

---

## Resumo executivo

| Tipo | Total encontrado | Diagnostico |
|---|---:|---|
| Etiquetas | 28 | Quase tudo existe; falta `Atualização Recusada`; ha duplicidade de estado `Em Atendimento` / `Em_Atendimento`; itens 6M devem sair da v2. |
| Campos personalizados | 39 | Base suficiente para a v2; manter nomes atuais para nao quebrar fluxos. |
| Fluxos | 19 | Fluxos principais existem; falta padronizar encerramento, Rute Secretaria e nomes duplicados com `5-`. |
| Sequencias | 1 | Existe apenas `SEQ - Revisao Cadastral 6M`; para a v2 faltam sequencias anuais e pastorais. |

Decisao v2: os fluxos devem continuar existindo no BotConversa, mas a persistencia passa a usar `POST /webhook/botconversa` sempre que houver dado pastoral, tarefa ou metrica.

---

## Etiquetas

### Manter como oficiais

| Etiqueta | ID | Uso v2 |
|---|---:|---|
| `Filadelfia Corrente` | 17220560 | Marca geral de contatos da igreja. |
| `Membro` | 17228565 | Identificacao de membro. |
| `Visitante` | 17228566 | Identificacao de visitante. |
| `Atualização Cadastral` | 17228567 | Entrada/estado de cadastro. |
| `Atualização Pendente` | 17229715 | Cadastro iniciado ou pendente. |
| `Cadastro Completo` | 17228568 | Cadastro concluido. |
| `Cadastro_Incompleto` | 17232566 | Cadastro incompleto. |
| `Cadastro Confirmado` | 17232636 | Confirmou dados sem alteracao. |
| `Recadastro Agend` | 17232639 | Recadastro anual agendado. |
| `Consolidacao 24h` | 17232640 | Visitante com acompanhamento 24h aberto. |
| `Pedido de Oracao` | 17232642 | Pedido de oracao registrado. |
| `Pedido Aconselh` | 17232643 | Pedido de aconselhamento registrado. |
| `Humano Necessario` | 17232647 | Precisa de atendimento humano. |
| `Atend Humano Ativo` | 17232648 | Atendimento humano ja aberto. |
| `Célula` | 17228571 | Interesse/assunto de celula. |
| `Ministério` | 17228572 | Interesse/assunto de ministerio. |
| `G12 Pastoral - Pr. Raniel` | 17220557 | Segmentacao G12. |
| `G12 Pastoral - Pastora Vanessa` | 17220559 | Segmentacao G12. |
| `CONVENÇÃO G12 2026` | 17220724 | Campanha/evento especifico. |
| `Ministério de Louvor` | 17220561 | Segmentacao de ministerio. |
| `Outro-Vinculo` | 17229412 | Contato que nao se declarou membro/visitante. |
| `Notif Cultos` | 17232738 | Comunicacao ativa futura. |
| `Celula Sem Relatorio` | 17232740 | Controle operacional de lideranca. |
| `Sem Relatorio 3S` | 17232741 | Escalada de relatorio atrasado. |
| `inativo-30min` | 17236697 | Tratamento de inatividade. |

### Corrigir ou padronizar

| Item | Estado atual | Decisao |
|---|---|---|
| `Em Atendimento` | Existe, ID 17233911 | Usar como etiqueta temporaria de IA em atendimento. |
| `Em_Atendimento` | Existe, ID 17233907 | Nao usar em fluxos novos; manter so por compatibilidade ate revisar fluxos antigos. |
| `Atualização Recusada` | Nao encontrado | Criar no BotConversa. Usar quando a pessoa nao quiser atualizar cadastro. |
| `IA - Em Atendimento` | Nao encontrado | Nao criar agora. A v2 usa `Em Atendimento` para reduzir duplicidade. |

### Nao usar mais como regra nova

| Item | Estado atual | Motivo |
|---|---|---|
| `Revisao 6M Agend` | Existe, ID 17232637 | A v2 usa recadastro anual, nao revisao semestral. |

---

## Campos personalizados

### Manter como oficiais para v2

| Campo | ID | Uso |
|---|---:|---|
| `Data_Nascimento` | 4964235 | Cadastro. |
| `Bairro` | 4964236 | Cadastro/localizacao. |
| `Tempo_Igreja` | 4964237 | Cadastro. |
| `Lider_Celula` | 4964239 | Cadastro/celulas. |
| `Fez_Encontro` | 4964251 | Trilha G12. |
| `Universidade_Vida` | 4964252 | Trilha G12. |
| `Capacitacao_Destino` | 4964253 | Trilha G12. |
| `Feedback_Melhorias` | 4964254 | Feedback pastoral. |
| `Feedback_falta` | 4964255 | Feedback pastoral. |
| `Celula_Atual` | 4964256 | Celula atual. |
| `G12_Pastoral` | 4964257 | Rede/G12. |
| `Interesse_Ministerio` | 4964258 | Ministerio. |
| `Data_Conversao` | 4964259 | Cadastro espiritual. |
| `Ultima_Atualiza_Cad` | 4964260 | Controle de recadastro. |
| `Status_Cadastro` | 4964391 | Estado do cadastro. |
| `Tipo_Vinculo` | 4964392 | Membro, visitante ou outro. |
| `Resumo_Atend_IA` | 4964393 | Resumo que tambem vai ao Hermes. |
| `Ultima_Intencao` | 4964394 | Roteamento. |
| `Precisa_Encaminhar` | 4964395 | Sinaliza humano/encaminhamento. |
| `Nivel_Urgencia` | 4964396 | Urgencia pastoral. |
| `Proxima_Atualiza_Cad` | 4964398 | Proximo recadastro anual. |
| `Como_Conheceu_Igreja` | 4965414 | Visitante. |
| `Disponibilida_Celula` | 4965415 | Visitante/celulas. |
| `Ministerios` | 4965416 | Ministerio atual/interesse. |
| `Status_Atendiment_IA` | 4965417 | Estado da conversa com IA. |
| `Ultimo_Fluxo_Encamin` | 4965418 | Ultimo fluxo chamado. |
| `Ultima_Resposta_IA` | 4965419 | Auditoria simples de IA. |
| `Resumo_Aconselhament` | 4965420 | Triagem de aconselhamento. |
| `Consolidador_Respons` | 4965421 | Responsavel por consolidacao. |
| `Status_Consolidacao` | 4965422 | Estado da consolidacao. |
| `Origem_Entrada` | 4965544 | Origem do contato/fluxo. |
| `Recebe_Notif_Cultos` | 4965545 | Opt-in comunicacao. |
| `Ult_Relatorio_Cel` | 4965546 | Controle de lideranca. |
| `Data_Celula` | 4965547 | Relatorio de celula. |
| `Presenca_Membros` | 4965548 | Relatorio de celula. |
| `Visitantes_Celula` | 4965570 | Relatorio de celula. |
| `Decisoes_Fe` | 4965572 | Relatorio de celula. |
| `Novos_Nomes` | 4965573 | Relatorio/visitantes. |
| `Obs_Celula` | 4965574 | Observacoes do relatorio. |

### Criar somente se for realmente usado no fluxo

| Campo sugerido | Uso | Decisao |
|---|---|---|
| `Aceita_Acompanhamento` | Visitante aceita contato 24h | Opcional; se nao criar, enviar essa informacao no payload `campos`. |
| `Nome_Celula` | Relatorio de celula | Opcional; se nao criar, usar texto livre no payload `campos.nome_celula`. |
| `Lider_Nome` | Relatorio de celula | Opcional; se nao criar, usar nome do contato ou payload `campos.lider_nome`. |

---

## Fluxos

### Oficiais para construir ou revisar agora

| Fluxo | ID | Status | Decisao v2 |
|---|---:|---|---|
| `0- Boas Vindas Filadelfia` | 8973507 | Existe | Porta de entrada oficial. |
| `1-  RUTE SECRETARIA` | 8889256 | Existe com nome irregular | Manter por enquanto; ideal renomear para `1- RUTE SECRETARIA`. |
| `0000 - Encerrar Conversa` | 8973552 | Existe | Encerramento oficial da v2. |
| `13 - Atendimento Humano` | 8978964 | Existe | Caminho humano padrao. |
| `00 - Midia Recebida - Rute` | 8978802 | Existe | Tratamento de midia fora de contexto. |
| `000- Pos-atendimento - Feedback` | 8978803 | Existe | Feedback depois de atendimento humano/resolucao. |
| `3- Atualização Cadastral` | 8974014 | Existe | Cadastro/atualizacao. |
| `4- Recadastro Anual` | 8973680 | Existe | Substitui regra 6M. |
| `5- Visitante` | 8973554 | Existe | Entrada de visitante; deve chamar webhook v2. |
| `6- Consolidação 24h` | 8978956 | Existe | Pode ser subfluxo ou sequencia de acompanhamento. |
| `7- Pedido de Oração` | 8976964 | Existe | Deve chamar webhook v2. |
| `8- Aconselhamento` | 8978960 | Existe | Sempre termina em humano. |
| `9- Central de Células` | 8976799 | Existe | Entrada para interesse ou lideranca. |
| `CALEB CELULAS LIDERANÇA` | 8979649 | Existe | Relatorio de celula; deve chamar webhook v2. |
| `10 - Ministérios` | 8978961 | Existe | Pode ficar como fase posterior. |
| `11 - Eventos` | 8978962 | Existe | Pode ficar como fase posterior. |
| `12 - Calendário Igreja` | 8978963 | Existe | Pode ficar como fase posterior. |

### Duplicados ou conflitantes

| Fluxo | ID | Decisao |
|---|---:|---|
| `2- Encerrar Conversa` | 8977385 | Nao usar em fluxos novos; substituir conexoes por `0000 - Encerrar Conversa`. |
| `5- RUTE TRIAGEM ACONSELHAMENTO` | 8979644 | Nome conflita com `5- Visitante`; renomear para `8.1 - Triagem Aconselhamento` ou manter parado ate revisao. |

---

## Sequencias

### Atual

| Sequencia | ID | Decisao |
|---|---:|---|
| `SEQ - Revisao Cadastral 6M` | 577984 | Nao usar na v2; substituir por recadastro anual. |

### Criar para v2

| Sequencia | Finalidade | Prioridade |
|---|---|---:|
| `SEQ - Recadastro Anual` | Relembrar atualizacao cadastral anual. | 1 |
| `SEQ - Follow-up Visitante 24h` | Cobrar contato rapido com visitante. | 1 |
| `SEQ - Retomar Atualizacao Cadastral` | Retomar cadastro pendente. | 2 |
| `SEQ - Pedido de Oracao Follow-up` | Retorno pastoral simples depois do pedido. | 3 |

---

## Ordem de saneamento recomendada

1. Criar etiqueta `Atualização Recusada`.
2. Criar sequencias v2: recadastro anual e visitante 24h primeiro.
3. Padronizar `1-  RUTE SECRETARIA` para `1- RUTE SECRETARIA`, se o BotConversa permitir sem quebrar referencias.
4. Usar `0000 - Encerrar Conversa` como encerramento unico.
5. Substituir conexoes antigas para `2- Encerrar Conversa`.
6. Parar de usar `Revisao 6M Agend` e `SEQ - Revisao Cadastral 6M`.
7. Usar `Em Atendimento` como etiqueta temporaria oficial; deixar `Em_Atendimento` apenas como legado.
8. Configurar os fluxos prioritarios para chamar `POST /webhook/botconversa`.

