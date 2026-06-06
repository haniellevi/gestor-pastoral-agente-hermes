# Base de Conhecimento dos Assistentes de IA

Esta pasta organiza o conhecimento operacional de cada assistente de IA do BotConversa/Hermes.

Use estes arquivos como base para:

- montar o campo de contexto de cada assistente no BotConversa;
- revisar o que cada IA pode ou nao pode responder;
- registrar referencias que o Pastor ensinar em cada fase do projeto;
- evitar que um assistente assuma funcao de outro.

Regra central:

```text
Cada assistente deve saber seu papel, seus limites, seus campos, suas etiquetas, suas saidas e quando chamar humano.
```

## Arquivos

| Arquivo | Assistente |
|---|---|
| `00_matriz_assistentes_ia.md` | Visao geral de todos os assistentes |
| `01_rute_geral.md` | Rute Geral |
| `02_rute_cadastro.md` | Rute Cadastro |
| `03_caleb_visitantes.md` | Caleb Visitantes |
| `04_caleb_celulas_g12.md` | Caleb Celulas G12 |
| `05_intercessao_oracao.md` | Intercessao Oracao |
| `06_triagem_aconselhamento.md` | Triagem Aconselhamento |
| `07_ministerios_voluntariado.md` | Ministerios Voluntariado |
| `08_eventos_agenda.md` | Eventos Agenda |
| `09_barnabe_comunicacao.md` | Barnabe Comunicacao |
| `10_neemias_pastor.md` | Neemias Pastor |
| `11_barnabe_sermoes.md` | Barnabe Sermoes |
| `12_caleb_relatorios_celula.md` | Caleb Relatorios Celula |
| `13_rute_agenda_g12.md` | Rute Agenda G12 |

## Como atualizar

Quando o Pastor ensinar uma regra nova, salvar no arquivo do assistente correspondente.

Exemplos:

- regra de consolidacao: `03_caleb_visitantes.md`;
- regra de relatorio de celula: `12_caleb_relatorios_celula.md`;
- regra de agenda G12: `13_rute_agenda_g12.md`;
- regra de sermoes no Spotify: `11_barnabe_sermoes.md`;
- regra geral de roteamento: `01_rute_geral.md`.

## Limite contra deducao

Se uma informacao nao estiver nos documentos oficiais, no banco de dados, na base da Rute ou neste conjunto de arquivos, o assistente deve reconhecer que ainda nao foi ensinado e encaminhar para revisao humana.

