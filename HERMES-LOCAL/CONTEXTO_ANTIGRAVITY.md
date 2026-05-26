# Contexto Completo do Projeto — Para o Antigravity 2.0

Este documento descreve tudo que foi construído até agora no ecossistema digital do Pastor Raniel Levi. Use como referência principal antes de qualquer desenvolvimento.

---

## 1. QUEM É O USUÁRIO

**Pastor Raniel Levi**
- Pastor titular da Igreja Batista Filadélfia Internacional de Corrente-PI
- Endereço: Av. Senhora da Conceição, Quadra F, Setor Oeste, nº 13 – Nova Corrente, Corrente-PI, CEP 64.980-000
- CNPJ da igreja: 17.028.114/0001-42
- Co-pastora: Pastora Vanessa
- Instagram da igreja: @filadelfiacorrente
- Também empreendedor digital (agência de sites — Sites Especiais)

**Rotina diária:**
- 05h00 acordar + devocional
- 05h30–06h30 treino físico
- 07h00 levar a filha Sarah na escola
- 08h00 início do trabalho
- Tarde: família + projetos (em casa)
- 22h00 dormir

**Regras inegociáveis de agenda:**
- Segunda = folga pastoral, sem compromissos externos
- Aconselhamentos: terça e quinta, 08h–12h, máximo 4 sessões de 1h/dia
- Nenhum compromisso antes das 08h ou após as 22h

---

## 2. OBSIDIAN VAULT (organizado e limpo)

**Caminho:** `C:\Users\hanie\Searches\OneDrive\Documentos\Obsidian Vault\`

O vault foi reorganizado do zero com estrutura PARA:

```
00 - INBOX/
  └── CAPTURA RAPIDA.md            ← captura rápida de ideias

10 - PROJETOS/
  ├── Hermes - Gestao Pastoral/    ← documentação do sistema Hermes
  │   ├── AGENTS.md                ← fonte de verdade dos agentes
  │   ├── JARVIS - Habilidades Aprovadas.md
  │   ├── Visao Geral e Arquitetura.md
  │   ├── Guia de BI e Modelo de Dados.md
  │   └── Agente 1/2/3/4 (Rute/Caleb/Barnabé/Neemias).md
  ├── SERMOES/
  │   ├── 00 - INDICE DE SERIES.md
  │   ├── 05 - UMA FE QUE TE MOVIMENTA/
  │   └── 06 - O VERDADEIRO DISCIPULO/
  ├── G12 - Líderes/
  │   ├── PAINEL G12.md
  │   └── Template - Ficha de Líder.md
  ├── Ministerio de Casais/
  │   └── PAINEL CASAIS.md
  ├── Sites Especiais/              ← agência (vida empreendedora)
  │   ├── Maquina_Venda_Sites_B2B.md
  │   └── Anaju/ (protótipo de cliente)
  └── Antigravity/
      └── AGENTE_ANTIGRAVITY.md

20 - AREAS/
  ├── ⛪ Igreja e Ministério.md
  ├── 📖 Teologia e Formação.md
  ├── 💼 Sites Especiais.md
  ├── 🚀 Inovação e IA.md
  └── 🏠 Pessoal e Base.md

30 - RECURSOS/
  ├── Mapa de Arquivos Externos.md  ← links para pastas locais do PC
  └── Templates/
      ├── Template - Nova Série.md
      ├── Template - Novo Sermão.md
      └── Novo Projeto.md

40 - ARQUIVO/                       ← projetos encerrados

PAINEL_DIGITAL.md                   ← QG central do vault
```

**Princípio:** Vida pastoral e vida empreendedora são separadas. O vault prioriza a vida pastoral.

---

## 3. GITHUB

**Repositório:** `https://github.com/haniellevi/gestor-pastoral-agente-hermes`

Contém a documentação e os system prompts do Hermes:
```
agents/
  rute.md / caleb.md / barnabe.md / neemias.md
database/
  schema.sql
docs/
  arquitetura.md / bi-modelo-dados.md
.gitignore        ← .env protegido
.env.example      ← modelo de variáveis
README.md
```

**Regra de ouro:** Nenhuma chave de API, senha ou dado de membros vai para o GitHub. Apenas código e documentação.

---

## 4. HERMES LOCAL — O SISTEMA DE AGENTES

**Caminho do projeto:**
`C:\Users\hanie\OneDrive\Documentos\WORKSPACE\Projetos Locais\Gestao Pastoral - Pr Raniel Levi\HERMES-LOCAL\`

**Stack:**
- **Hermes Desktop** (Nous Research) — app Electron que roda o agente localmente
- **Gateway:** Telegram (fase atual) → WhatsApp (fase futura)
- **Banco de dados:** SQLite local (`database/pastoral.db`)
- **Dashboard:** Streamlit (a construir)
- **LLM:** via OpenRouter (Hermes 3 / Llama 3)

**Estrutura do projeto:**
```
HERMES-LOCAL/
├── AGENTS.md              ← FONTE DE VERDADE dos agentes (ler antes de tudo)
├── README.md              ← instruções de instalação
├── run_local.bat          ← script de inicialização
├── agents/
│   ├── rute_prompt.txt
│   ├── caleb_prompt.txt
│   ├── barnabe_prompt.txt
│   └── neemias_prompt.txt
├── conhecimento/          ← base de conhecimento da igreja (RAG local)
│   ├── igreja_filadelfia.md
│   ├── agenda_pastoral.md
│   ├── visao_g12.md
│   └── calendario_2026.md
├── database/
│   ├── schema.sql
│   ├── initialize_db.py
│   ├── migrate_db.py
│   └── pastoral.db        ← banco SQLite já criado
└── dashboard/             ← vazio, a construir
```

---

## 5. AGENTS.MD — REGRA MAIS IMPORTANTE

O arquivo `AGENTS.md` define o comportamento de todos os agentes. A regra mais crítica:

> **REGRA ANTI-DEDUÇÃO:** O agente NÃO sabe como a igreja funciona EXCETO se a informação estiver explicitamente nos arquivos da pasta `conhecimento/`. Se não encontrar a resposta lá, responde que ainda não foi ensinado e pede ao Pastor para explicar — e então grava o aprendizado no arquivo `.md` correspondente.

**Como o agente aprende:**
```python
import os

def ler_conhecimento(arquivo):
    filepath = f"conhecimento/{arquivo}"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "Ainda não há informações cadastradas para este tópico."

def gravar_conhecimento(arquivo, novo_dado):
    os.makedirs("conhecimento", exist_ok=True)
    with open(f"conhecimento/{arquivo}", "a", encoding="utf-8") as f:
        f.write(f"\n{novo_dado}")
```

---

## 6. OS QUATRO AGENTES

Todos os prompts estão em `agents/` e já incorporam:
- Referência à pasta `conhecimento/`
- Scripts Python para leitura e escrita no SQLite
- Dados reais da Filadélfia
- Tom direto, sem linguagem evangélica forçada

### RUTE — Secretaria Executiva
**Arquivo:** `agents/rute_prompt.txt`
**Função:** Agenda, lembretes, planejamento semanal/mensal
**Tabela principal:** `compromissos`
**Rotinas:** Check-in noturno 21h, planejamento semanal domingo 16h, alerta dia 28, alerta em novembro para calendário do próximo ano

### CALEB — G12 e Consolidação
**Arquivo:** `agents/caleb_prompt.txt`
**Função:** Relatórios de célula, funil de consolidação, O3M, CVS
**Tabelas principais:** `relatorios_celulas`, `consolidacao_visitantes`
**Regra crítica:** Contato de consolidação em até 24h. Responsável: Luciane
**Rotinas:** Coleta de relatório sáb/dom/seg, alerta de pendências segunda à noite

### BARNABÉ — Conteúdo e Marketing
**Arquivo:** `agents/barnabe_prompt.txt`
**Função:** Roteiros de vídeo, plano de conteúdo, dica diária de liderança, divulgação
**Tabela principal:** `posts_conteudo`
**Rotinas:** Dica de liderança 07h30 (seg–sex), plano mensal no início do mês, divulgação toda quinta
**Canal:** @filadelfiacorrente (Instagram), Spotify (Joaquim)

### NEEMIAS — Foco e Produtividade
**Arquivo:** `agents/neemias_prompt.txt`
**Função:** 3 Vitórias do Dia, bloco de estudo 1h, combate à procrastinação
**Tabelas:** `metas_diarias`, `registro_procrastinacao`
**Rotinas:** 08h00, 14h00, 18h00, 20h00 (cron), revisão semanal domingo
**Pontuação:** 3 vitórias=100pts, 2=60pts, 1=30pts, 0=0pts

---

## 7. BANCO DE DADOS SQLite

**Arquivo:** `database/pastoral.db` (já criado e inicializado)
**Schema:** `database/schema.sql`

**Tabelas:**
| Tabela | Agente | Finalidade |
|--------|--------|------------|
| `compromissos` | Rute | Agenda e distribuição de tempo |
| `relatorios_celulas` | Caleb | Dados semanais das células |
| `consolidacao_visitantes` | Caleb | Funil de consolidação 24h |
| `metas_diarias` | Neemias | 3 vitórias do dia e pontuação |
| `registro_procrastinacao` | Neemias | Padrões de distração |
| `posts_conteudo` | Barnabé | Editorial de conteúdo |
| `sugestoes_bi` | Hermes | BI autoadaptativo |

**Atenção:** O `schema.sql` usa sintaxe PostgreSQL. O `initialize_db.py` já faz as adaptações para SQLite. Use sempre o `initialize_db.py` para criar/recriar o banco.

---

## 8. PASTA CONHECIMENTO (RAG LOCAL)

Quatro arquivos que são a memória da igreja para os agentes:

| Arquivo | Conteúdo |
|---------|----------|
| `igreja_filadelfia.md` | Identidade, endereço, cultos, organograma, equipes dos 12, ministérios, grupos de WhatsApp |
| `agenda_pastoral.md` | Rotina diária, regras de agenda, estrutura semanal, horários de aconselhamento |
| `visao_g12.md` | O3M, CVS, processo AAA, trilha de formação, estrutura de célula, DPI, glossário completo |
| `calendario_2026.md` | Todos os eventos mês a mês, campanhas, datas especiais |

---

## 9. PRÓXIMOS PASSOS PLANEJADOS

**Fase atual (Fase 1):** Neemias + Rute funcionando no Telegram
- Banco já criado
- Prompts prontos
- Conhecimento carregado
- **Falta:** conectar os prompts ao Hermes Desktop e testar os crons

**Fase 2:** Caleb + Barnabé
- Ativar quando Fase 1 virar hábito estável

**Fase 3:** Dashboard Streamlit (BI)
- Ler os dados do `pastoral.db` e exibir KPIs:
  - Eficiência do Pastor (pontuação Neemias)
  - Crescimento de células (Caleb)
  - Distribuição de tempo pastoral (Rute)
  - Funil de consolidação (Caleb)
  - Alcance de conteúdo (Barnabé)
- Hermes orquestrador sugere novas métricas conforme padrões das conversas

---

## 10. SEPARAÇÃO VIDA PASTORAL × EMPREENDEDOR

**Regra do projeto:** As duas vidas são completamente separadas.

**Vida pastoral** (prioridade):
- Hermes Local
- Obsidian: 10-PROJETOS/SERMOES, G12, Casais, Hermes
- GitHub: `gestor-pastoral-agente-hermes`

**Vida empreendedora** (fase futura):
- Sites Especiais (agência de sites)
- Obsidian: 10-PROJETOS/Sites Especiais, Antigravity
- Antigravity 2.0 (desenvolvimento)

---

## 11. CONVENÇÕES DO PROJETO

- **Banco:** SQLite local, path sempre relativo: `database/pastoral.db`
- **Encoding:** UTF-8 em todos os arquivos
- **Conhecimento:** Nunca deduzir — sempre ler `conhecimento/` ou perguntar ao Pastor
- **Secrets:** Nunca hardcodar chaves. Usar `.env` (já no `.gitignore`)
- **Linguagem:** Português brasileiro em tudo — prompts, código, comentários, documentação
- **Tom dos agentes:** Direto e humano, sem linguagem evangélica forçada
