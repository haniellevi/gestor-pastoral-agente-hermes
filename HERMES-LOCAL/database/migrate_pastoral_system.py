import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "pastoral.db"


BOTCONVERSA_CONFIG_DEFAULTS = [
    ("tag_membro", "", "Etiqueta BotConversa para membros cadastrados"),
    ("tag_visitante", "", "Etiqueta BotConversa para visitantes"),
    ("tag_atualizacao_cadastral", "", "Etiqueta para quem precisa atualizar cadastro"),
    ("tag_cadastro_completo", "", "Etiqueta para cadastro concluído"),
    ("tag_cadastro_incompleto", "", "Etiqueta para cadastro incompleto"),
    ("tag_atualizacao_pendente", "", "Etiqueta para atualização pendente"),
    ("tag_consolidacao_24h", "", "Etiqueta para visitantes em consolidação 24h"),
    ("tag_pedido_oracao", "", "Etiqueta para pedidos de oração"),
    ("tag_pedido_aconselhamento", "", "Etiqueta para pedidos de aconselhamento"),
    ("tag_humano_necessario", "", "Etiqueta para conversas que precisam de humano"),
    ("tag_em_atendimento_humano", "", "Etiqueta para conversa aberta com humano"),
    ("tag_filadelfia_corrente", "", "Etiqueta geral Filadélfia Corrente"),
    ("tag_convencao_g12_2026", "", "Etiqueta Convenção G12 2026"),
    ("tag_g12_pr_raniel", "", "Etiqueta G12 Pastoral - Pr. Raniel"),
    ("tag_g12_pastora_vanessa", "", "Etiqueta G12 Pastoral - Pastora Vanessa"),
    ("tag_ministerio_louvor", "", "Etiqueta Ministério de Louvor"),
    ("tag_recadastro_anual_agendado", "", "Etiqueta BotConversa para recadastro anual agendado"),
    ("tag_atualizacao_recusada", "", "Etiqueta BotConversa para atualização recusada"),
    ("tag_atualizacao_confirmada_sem_alteracao", "", "Etiqueta BotConversa para atualização confirmada sem alteração"),
    ("flow_boas_vindas", "", "Fluxo BotConversa de boas-vindas"),
    ("flow_midia_recebida", "", "Fluxo BotConversa padrão para mídia recebida"),
    ("flow_pos_atendimento", "", "Fluxo BotConversa pós-atendimento"),
    ("flow_atualizacao_cadastral", "", "Fluxo BotConversa de atualização cadastral"),
    ("flow_consolidacao_visitante", "", "Fluxo BotConversa de consolidação de visitante"),
    ("flow_recadastro_anual", "", "Fluxo BotConversa de recadastro anual"),
    ("flow_pedido_oracao", "", "Fluxo BotConversa de pedido de oração"),
    ("flow_pedido_aconselhamento", "", "Fluxo BotConversa de pedido de aconselhamento"),
    ("flow_g12_celulas", "", "Fluxo BotConversa de G12 e células"),
    ("flow_ministerios", "", "Fluxo BotConversa de ministérios"),
    ("sequence_devocional_diario", "", "Sequência/campanha de devocional diário"),
    ("sequence_recadastro_anual", "", "Sequência de recadastro anual"),
    ("sequence_visitante_24h", "", "Sequência de follow-up visitante 24h"),
    ("sequence_retomar_atualizacao", "", "Sequência para retomar atualização cadastral"),
    ("sequence_pedido_oracao_followup", "", "Sequência de follow-up de pedido de oração"),
    ("field_data_nascimento", "", "Campo personalizado Data_Nascimento"),
    ("field_bairro", "", "Campo personalizado Bairro/Cidade"),
    ("field_tempo_igreja", "", "Campo personalizado Tempo_Igreja"),
    ("field_lider_celula", "", "Campo personalizado Lider_Celula"),
    ("field_fez_encontro", "", "Campo personalizado Fez_Encontro"),
    ("field_universidade_vida", "", "Campo personalizado Universidade_Vida"),
    ("field_capacitacao_destino", "", "Campo personalizado Capacitacao_Destino"),
    ("field_interesse_ministerio", "", "Campo personalizado Interesse_Ministerio"),
    ("field_feedback_melhorias", "", "Campo personalizado Feedback_Melhorias"),
    ("field_feedback_falta", "", "Campo personalizado Feedback_Falta"),
    ("field_celula_atual", "", "Campo personalizado Celula_Atual"),
    ("field_g12_pastoral", "", "Campo personalizado G12_Pastoral"),
    ("field_ministerios", "", "Campo personalizado Ministerios"),
    ("field_data_conversao", "", "Campo personalizado Data_Conversao"),
    ("field_ultima_atualizacao", "", "Campo personalizado Ultima_Atualizacao_Cadastral"),
    ("field_status_cadastro", "", "Campo personalizado Status_Cadastro"),
    ("field_tipo_vinculo", "", "Campo personalizado Tipo_Vinculo"),
    ("field_resumo_atendimento_ia", "", "Campo personalizado Resumo_Atend_IA"),
    ("field_ultima_intencao", "", "Campo personalizado Ultima_Intencao"),
    ("field_encaminhamento_necessario", "", "Campo personalizado Encaminhamento_Necessario"),
    ("field_nivel_urgencia", "", "Campo personalizado Nivel_Urgencia"),
    ("field_proximo_recadastro_anual", "", "Campo personalizado Prox_Recadastro"),
]


def migrate() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        telefone TEXT UNIQUE,
        data_nascimento TEXT,
        bairro_cidade TEXT,
        tempo_igreja TEXT,
        lider_celula TEXT,
        fez_encontro TEXT,
        universidade_vida TEXT,
        capacitacao_destino TEXT,
        interesse_ministerio TEXT,
        feedback_melhorias TEXT,
        feedback_falta TEXT,
        celula_atual TEXT,
        g12_pastoral TEXT,
        ministerios TEXT,
        data_conversao TEXT,
        status_cadastro TEXT DEFAULT 'Incompleto'
            CHECK (status_cadastro IN ('Incompleto', 'Completo', 'Atualizar', 'Recusou')),
        consentimento_comunicacao INTEGER DEFAULT 0,
        botconversa_subscriber_id INTEGER,
        ultima_atualizacao_cadastral TEXT,
        proxima_atualizacao_cadastral TEXT,
        observacoes TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS botconversa_config (
        chave TEXT PRIMARY KEY,
        valor TEXT,
        descricao TEXT,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS botconversa_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acao TEXT NOT NULL,
        entidade_tipo TEXT,
        entidade_id TEXT,
        payload TEXT,
        status TEXT CHECK (status IN ('Sucesso', 'Erro', 'Pendente')) DEFAULT 'Pendente',
        resultado TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atendimentos_rute (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pessoa_nome TEXT NOT NULL,
        telefone TEXT,
        tipo_solicitacao TEXT CHECK (tipo_solicitacao IN (
            'Atualizacao Cadastro',
            'Informacao Visitante',
            'Pedido Oracao',
            'Pedido Aconselhamento',
            'Entrar Celula',
            'Humano Necessario',
            'Outro'
        )) DEFAULT 'Outro',
        origem TEXT CHECK (origem IN ('BotConversa', 'Dashboard', 'Telegram', 'Manual', 'Outro')) DEFAULT 'Manual',
        nivel_urgencia TEXT CHECK (nivel_urgencia IN ('Baixa', 'Normal', 'Alta', 'Urgente')) DEFAULT 'Normal',
        status TEXT CHECK (status IN ('Novo', 'Em triagem', 'Encaminhado', 'Resolvido', 'Arquivado')) DEFAULT 'Novo',
        responsavel TEXT,
        resumo TEXT,
        membro_id INTEGER,
        botconversa_subscriber_id INTEGER,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (membro_id) REFERENCES membros(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comunicacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        tipo TEXT CHECK (tipo IN (
            'Agenda Semanal',
            'Resumo do Culto',
            'Resumo Reuniao G12',
            'Post Redes Sociais',
            'Post Blog',
            'Video Canal',
            'Devocional Diario',
            'Evento',
            'Outro'
        )) DEFAULT 'Outro',
        canal TEXT CHECK (canal IN ('WhatsApp', 'Instagram', 'Blog', 'YouTube', 'Site', 'Email', 'Outro')) DEFAULT 'WhatsApp',
        publico_alvo TEXT,
        mensagem TEXT,
        status TEXT CHECK (status IN ('Ideia', 'Rascunho', 'Aprovado', 'Enviado', 'Arquivado')) DEFAULT 'Ideia',
        botconversa_flow_id INTEGER,
        botconversa_sequence_id INTEGER,
        botconversa_campaign_id INTEGER,
        data_programada TEXT,
        data_envio TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    for chave, valor, descricao in BOTCONVERSA_CONFIG_DEFAULTS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO botconversa_config (chave, valor, descricao)
            VALUES (?, ?, ?)
            """,
            (chave, valor, descricao),
        )

    conn.commit()
    conn.close()
    print("Migração pastoral/BotConversa aplicada com sucesso.")


if __name__ == "__main__":
    migrate()
