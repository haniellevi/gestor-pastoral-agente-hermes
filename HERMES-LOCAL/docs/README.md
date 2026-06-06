# Indice Oficial da Documentacao - Hermes Filadelfia

Este indice define onde cada documento deve ficar para manter o projeto legivel conforme ele crescer.

Regra principal: a raiz de `docs/` deve conter apenas documentos oficiais de consulta frequente. Materiais operacionais, historicos, duplicados ou auxiliares devem ficar em subpastas.

---

## Documentos Principais

| Documento | Quando abrir | Status |
|---|---|---|
| `PLANO_MESTRE_HERMES_FILADELFIA.md` | Visao completa do ecossistema Hermes: BotConversa, Hermes, Supabase, Drive, GitHub, VPS, dashboard e site | Documento mestre |
| `METODO_PLANEJAMENTO_COLABORATIVO.md` | Metodo oficial para planejar cada modulo com o Pastor antes de transformar em tela, fluxo ou automacao | Metodo oficial |
| `MAPA_VISUAL_PROJETO.md` | Mapa simples dos agentes, objetivos, tarefas e beneficios ao Pastor | Visual principal |
| `HERMES_2_0_IMPLEMENTACAO.md` | Implementacao do MVP Hermes 2.0: webhook unico, tabelas, dashboard enxuto e migracao gradual | Documento tecnico atual |
| `PROJETO_VISUAL_CHATBOT_BOTCONVERSA_IA.md` | Visao do chatbot com IA no BotConversa: fluxos, campos, etiquetas, webhooks e logica | Visual principal do chatbot |

---

## Apoio BotConversa

Pasta: `_apoio_botconversa/`

| Documento | Funcao | Status |
|---|---|---|
| `_apoio_botconversa/GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md` | Guia mestre consolidado para logica de chatbot WhatsApp, BotConversa, encerramentos, webhooks, humano e revisao do plano Hermes | Referencia superior para decisoes de arquitetura |
| `_apoio_botconversa/GUIA_EXECUCAO_CHECKLIST_FLUXOS_BOTCONVERSA.md` | Checklist clicavel de execucao fluxo a fluxo, proximas tarefas e controle de pontas soltas | Guia diario de implementacao |
| `_apoio_botconversa/INVENTARIO_BOTCONVERSA_FASE_3_HERMES_2.md` | Inventario real de etiquetas, campos, fluxos e sequencias consultado via API | Inventario Fase 3 |
| `_apoio_botconversa/PASSO_A_PASSO_FLUXOS_BOTCONVERSA_HERMES_2.md` | Passo a passo detalhado de blocos, conteudo, webhooks e finalizacoes dos fluxos v2 | Guia de construcao |
| `_apoio_botconversa/PLANO_RECADASTRO_ANUAL_TODA_BASE.md` | Plano de campanha para rodar recadastro anual em toda a base com ondas, payloads e metricas | Guia de campanha |

---

## Base de Conhecimento da Rute

Pasta: `base_conhecimento_rute/`

Esta pasta permanece separada porque contem conhecimento estruturado em Markdown para consulta e manutencao:

- identidade da igreja;
- endereco e cultos fixos;
- lideres e ministerios;
- visao G12;
- celulas;
- calendario 2026;
- regras de encaminhamento;
- fluxos pastorais do BotConversa.

Se alguma informacao desta base virar conhecimento permanente do sistema, avaliar migracao ou sincronizacao com `conhecimento/`.

---

## Base de Conhecimento dos Assistentes de IA

Pasta: `base_conhecimento_assistentes_ia/`

Esta pasta contem um arquivo para cada assistente de IA do BotConversa:

- Rute Geral;
- Rute Cadastro;
- Caleb Visitantes;
- Caleb Celulas G12;
- Intercessao Oracao;
- Triagem Aconselhamento;
- Ministerios Voluntariado;
- Eventos Agenda;
- Barnabe Comunicacao;
- Neemias Pastor;
- Barnabe Sermoes;
- Caleb Relatorios Celula;
- Rute Agenda G12.

Use esta pasta para lapidar a base de cada assistente conforme o Pastor ensinar os processos reais de cada area.

---

## Arquivo Historico

Pasta: `Lixeira/`

| Item | Motivo |
|---|---|
| `Lixeira/_apoio_botconversa/` | Guias antigos, rascunhos e materiais duplicados substituidos pelo guia mestre |
| `Lixeira/_arquivo/` | Versoes antigas e bases em `.txt`, mantidas apenas para consulta historica |
| `Lixeira/PLANO-ATUALIZADO-PELO-HERMES/` | Documentacao paralela revisada em 2026-06-05; pontos validos migrados para `_apoio_botconversa/` |

Nada em `Lixeira/` deve ser deletado sem revisao manual.

---

## Regra para Novos Documentos

Antes de criar um novo arquivo em `docs/`, classificar em uma destas categorias:

1. **Documento principal:** visao, mapa, decisao oficial ou metodo do projeto.
2. **Apoio tecnico:** implementacao, prompts, integracoes, webhooks, fluxos ou inventarios.
3. **Base de conhecimento:** conteudo que a Rute deve saber e consultar.
4. **Arquivo historico:** versao antiga, rascunho, material duplicado ou substituido.

Se o novo documento repetir algo ja existente, atualizar o documento existente em vez de criar outro.

---

## Estrutura Atual Recomendada

```text
docs/
├── README.md
├── PLANO_MESTRE_HERMES_FILADELFIA.md
├── METODO_PLANEJAMENTO_COLABORATIVO.md
├── MAPA_VISUAL_PROJETO.md
├── HERMES_2_0_IMPLEMENTACAO.md
├── base_conhecimento_rute/
├── base_conhecimento_assistentes_ia/
├── _apoio_botconversa/
└── Lixeira/
```
