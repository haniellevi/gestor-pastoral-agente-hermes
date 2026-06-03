-- ----------------------------------------------------
-- SCHEMA DO BANCO DE DADOS - GESTÃO PASTORAL & BI
-- ----------------------------------------------------

-- 1. TABELA DE COMPROMISSOS (Rute)
CREATE TABLE IF NOT EXISTS compromissos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    categoria VARCHAR(50) CHECK (categoria IN ('Aconselhamento', 'Culto', 'Reuniao Lideranca', 'Estudo/Sermao', 'Pessoal', 'Outros')),
    data_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    data_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    descricao TEXT,
    duracao_minutos INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (data_fim - data_inicio))/60) STORED,
    google_event_id VARCHAR(255) UNIQUE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABELA DE RELATÓRIOS DE CÉLULAS G12 (Caleb)
CREATE TABLE IF NOT EXISTS relatorios_celulas (
    id SERIAL PRIMARY KEY,
    data_relatorio DATE NOT NULL,
    nome_celula VARCHAR(100) NOT NULL,
    lider_nome VARCHAR(100) NOT NULL,
    presenca_membros INTEGER DEFAULT 0,
    visitantes INTEGER DEFAULT 0,
    decisoes_fe INTEGER DEFAULT 0,
    rede VARCHAR(50) CHECK (rede IN ('Jovens', 'Casais', 'Homens', 'Mulheres')),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABELA DE CONTROLE DE FOCO E PRODUTIVIDADE (Neemias)
CREATE TABLE IF NOT EXISTS metas_diarias (
    id SERIAL PRIMARY KEY,
    data DATE DEFAULT CURRENT_DATE,
    vitoria_1 TEXT NOT NULL,
    vitoria_1_concluida BOOLEAN DEFAULT FALSE,
    vitoria_2 TEXT NOT NULL,
    vitoria_2_concluida BOOLEAN DEFAULT FALSE,
    vitoria_3 TEXT NOT NULL,
    vitoria_3_concluida BOOLEAN DEFAULT FALSE,
    pontuacao_dia INTEGER DEFAULT 0,
    anotacoes TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. TABELA DE CADASTRO DE CONTEÚDO E MARKETING (Barnabé)
CREATE TABLE IF NOT EXISTS posts_conteudo (
    id SERIAL PRIMARY KEY,
    tema VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) CHECK (tipo IN ('Reels', 'Shorts', 'Carrossel', 'Mensagem Interna', 'Outro')),
    roteiro TEXT,
    status VARCHAR(50) CHECK (status IN ('Ideia', 'Roteirizado', 'Gravado', 'Postado')) DEFAULT 'Ideia',
    views INTEGER DEFAULT 0,
    engajamento INTEGER DEFAULT 0,
    data_publicacao DATE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. TABELA DE PROSPECÇÕES E SUGESTÕES DE MÉTRICAS (Hermes Orquestrador)
CREATE TABLE IF NOT EXISTS sugestoes_bi (
    id SERIAL PRIMARY KEY,
    origem_conversa TEXT NOT NULL,
    metrica_sugerida VARCHAR(100) NOT NULL,
    justificativa TEXT NOT NULL,
    status VARCHAR(50) CHECK (status IN ('Pendente', 'Implementado', 'Rejeitado')) DEFAULT 'Pendente',
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. TABELA DE REGISTRO DE PROCRASTINAÇÃO (Neemias)
CREATE TABLE IF NOT EXISTS registro_procrastinacao (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    tarefa_adiada TEXT NOT NULL,
    distracao TEXT NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. TABELA DE CONSOLIDAÇÃO DE VISITANTES (Caleb)
CREATE TABLE IF NOT EXISTS consolidacao_visitantes (
    id SERIAL PRIMARY KEY,
    data_visita DATE NOT NULL,
    visitante_nome VARCHAR(100) NOT NULL,
    visitante_whatsapp VARCHAR(20),
    consolidador_nome VARCHAR(100) NOT NULL,
    contato_24h BOOLEAN DEFAULT FALSE,
    data_contato DATE,
    feedback TEXT,
    status VARCHAR(50) CHECK (status IN ('Pendente', 'Contatado', 'Integrado', 'Desistiu')) DEFAULT 'Pendente',
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. CENTRAL HERMES DE MEMBROS E ATENDIMENTO (Rute)
CREATE TABLE IF NOT EXISTS atendimentos_rute (
    id SERIAL PRIMARY KEY,
    pessoa_nome VARCHAR(150) NOT NULL,
    telefone VARCHAR(30),
    tipo_solicitacao VARCHAR(50) CHECK (tipo_solicitacao IN (
        'Atualizacao Cadastro',
        'Informacao Visitante',
        'Pedido Oracao',
        'Pedido Aconselhamento',
        'Entrar Celula',
        'Humano Necessario',
        'Outro'
    )) DEFAULT 'Outro',
    origem VARCHAR(30) CHECK (origem IN ('BotConversa', 'Dashboard', 'Telegram', 'Manual', 'Outro')) DEFAULT 'Manual',
    nivel_urgencia VARCHAR(20) CHECK (nivel_urgencia IN ('Baixa', 'Normal', 'Alta', 'Urgente')) DEFAULT 'Normal',
    status VARCHAR(30) CHECK (status IN ('Novo', 'Em triagem', 'Encaminhado', 'Resolvido', 'Arquivado')) DEFAULT 'Novo',
    responsavel VARCHAR(100),
    resumo TEXT,
    membro_id INTEGER REFERENCES membros(id),
    botconversa_subscriber_id INTEGER,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
