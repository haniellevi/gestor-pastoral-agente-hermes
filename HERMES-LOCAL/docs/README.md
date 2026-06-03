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
| `PROJETO_VISUAL_CHATBOT_BOTCONVERSA_IA.md` | Visao do chatbot com IA no BotConversa: fluxos, campos, etiquetas, webhooks e logica | Visual principal do chatbot |

---

## Apoio BotConversa

Pasta: `_apoio_botconversa/`

| Documento | Funcao | Status |
|---|---|---|
| `_apoio_botconversa/planejamento_completo_fluxos_botconversa_hermes.md` | Roteiro detalhado dos fluxos BotConversa + Hermes | Apoio tecnico |
| `_apoio_botconversa/botconversa_arquitetura_fluxos_rute.md` | Arquitetura detalhada da Rute, inventario de fluxos, etiquetas e campos | Apoio tecnico |
| `_apoio_botconversa/botconversa_agente_ia_prompt.md` | Prompt mestre da Rute no BotConversa | Material operacional |
| `_apoio_botconversa/botconversa_assistente_atualizacao_cadastral.md` | Prompt e logica da Rute Cadastro | Material operacional |

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

## Arquivo Historico

Pasta: `_arquivo/`

| Item | Motivo |
|---|---|
| `_arquivo/botconversa_fluxos_pastorais.md` | Versao curta/substituivel dos fluxos pastorais |
| `_arquivo/rute_base_conhecimento.txt` | Base unica em texto, possivelmente duplicada pela base estruturada |
| `_arquivo/base_conhecimento_rute_txt/` | Versao `.txt` da base, mantida apenas para historico ou importacao |

Nada em `_arquivo/` deve ser deletado sem revisao manual.

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
├── PROJETO_VISUAL_CHATBOT_BOTCONVERSA_IA.md
├── base_conhecimento_rute/
├── _apoio_botconversa/
└── _arquivo/
```
