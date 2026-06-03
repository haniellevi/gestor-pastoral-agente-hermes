import sqlite3
from pathlib import Path

try:
    from integrations.botconversa_client import BotConversaClient
except ImportError:
    from botconversa_client import BotConversaClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"


CONFIG_MATCHES = {
    "tag_filadelfia_corrente": ("tags", "Filadelfia Corrente"),
    "tag_convencao_g12_2026": ("tags", "CONVENÇÃO G12 2026"),
    "tag_g12_pr_raniel": ("tags", "G12 Pastoral - Pr. Raniel"),
    "tag_g12_pastora_vanessa": ("tags", "G12 Pastoral - Pastora Vanessa"),
    "tag_ministerio_louvor": ("tags", "Ministério de Louvor"),
    "tag_membro": ("tags", "Membro"),
    "tag_visitante": ("tags", "Visitante"),
    "tag_atualizacao_cadastral": ("tags", "Atualização Cadastral"),
    "tag_cadastro_completo": ("tags", "Cadastro Completo"),
    "tag_cadastro_incompleto": ("tags", "Cadastro Incompleto"),
    "tag_atualizacao_pendente": ("tags", "Atualização Pendente"),
    "tag_consolidacao_24h": ("tags", "Consolidação 24h"),
    "tag_pedido_oracao": ("tags", "Pedido de Oração"),
    "tag_pedido_aconselhamento": ("tags", "Pedido de Aconselhamento"),
    "tag_humano_necessario": ("tags", "Humano Necessário"),
    "tag_em_atendimento_humano": ("tags", "Em Atendimento Humano"),
    "tag_atualizacao_6m_agendada": ("tags", "Atualização 6M Agendada"),
    "tag_recadastro_anual_agendado": ("tags", "Recadastro Anual Agendado"),
    "tag_atualizacao_recusada": ("tags", "Atualização Recusada"),
    "tag_atualizacao_confirmada_sem_alteracao": ("tags", "Atualização Confirmada Sem Alteração"),
    "flow_boas_vindas": ("flows", "Boas Vindas Filadelfia"),
    "flow_atualizacao_cadastral": ("flows", "Atualização Cadastral"),
    "flow_consolidacao_visitante": ("flows", "VISITANTE"),
    "flow_pedido_oracao": ("flows", "Pedido de Oração"),
    "flow_pedido_aconselhamento": ("flows", "Pedido de Aconselhamento"),
    "flow_g12_celulas": ("flows", "G12 e Células"),
    "flow_ministerios": ("flows", "Ministérios"),
    "flow_confirmacao_cadastral_6m": ("flows", "Confirmação Cadastral 6M"),
    "flow_recadastro_anual": ("flows", "Recadastro Anual"),
    "sequence_revisao_cadastral_6m": ("sequences", "SEQ - Revisao Cadastral 6M"),
    "sequence_recadastro_anual": ("sequences", "SEQ - Recadastro Anual"),
    "sequence_visitante_24h": ("sequences", "SEQ - Follow-up Visitante 24h"),
    "sequence_retomar_atualizacao": ("sequences", "SEQ - Retomar  Atualizacao Cadastral"),
    "sequence_pedido_oracao_followup": ("sequences", "SEQ - Pedido de Oracao Follow-up"),
    "field_data_nascimento": ("custom_fields", "Data Nascimento"),
    "field_bairro": ("custom_fields", "Bairro"),
    "field_tempo_igreja": ("custom_fields", "Tempo_Igreja"),
    "field_lider_celula": ("custom_fields", "Lider_Celula"),
    "field_fez_encontro": ("custom_fields", "Fez_Encontro"),
    "field_universidade_vida": ("custom_fields", "Universidade_Vida"),
    "field_capacitacao_destino": ("custom_fields", "Capacitacao_Destino"),
    "field_interesse_ministerio": ("custom_fields", "Interesse_Ministerio"),
    "field_feedback_melhorias": ("custom_fields", "Feedback_Melhorias"),
    "field_feedback_falta": ("custom_fields", "Feedback_Falta"),
    "field_celula_atual": ("custom_fields", "Celula_Atual"),
    "field_g12_pastoral": ("custom_fields", "G12_Pastoral"),
    "field_ministerios": ("custom_fields", "Ministerios"),
    "field_data_conversao": ("custom_fields", "Data_Conversao"),
    "field_ultima_atualizacao": ("custom_fields", "Ultima_Atualiz_Cadas"),
    "field_status_cadastro": ("custom_fields", "Status_Cadastro"),
    "field_tipo_vinculo": ("custom_fields", "Tipo_Vinculo"),
    "field_resumo_atendimento_ia": ("custom_fields", "Resumo_Atend_IA"),
    "field_ultima_intencao": ("custom_fields", "Ultima_Intencao"),
    "field_encaminhamento_necessario": ("custom_fields", "Encaminhamento_Necessario"),
    "field_nivel_urgencia": ("custom_fields", "Nivel_Urgencia"),
    "field_proxima_atualizacao": ("custom_fields", "Proxima_Atualizacao_Cadastral"),
    "field_proximo_recadastro_anual": ("custom_fields", "Proximo_Recadastro_Anual"),
}


def normalize(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def item_name(item: dict) -> str:
    return item.get("name") or item.get("title") or item.get("label") or item.get("key") or ""


def item_id(item: dict) -> str:
    value = item.get("id") or item.get("pk") or item.get("uuid") or ""
    return str(value)


def build_index(items: list[dict]) -> dict[str, dict]:
    return {normalize(item_name(item)): item for item in items}


def sync_config() -> dict[str, list[tuple]]:
    client = BotConversaClient()
    data = {
        "tags": build_index(client.list_tags()),
        "flows": build_index(client.list_flows()),
        "custom_fields": build_index(client.list_custom_fields()),
        "sequences": build_index(client.list_sequences()),
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated = []
    missing = []

    for config_key, (bucket, expected_name) in CONFIG_MATCHES.items():
        item = data[bucket].get(normalize(expected_name))
        if not item:
            missing.append((config_key, expected_name))
            continue
        value = item_id(item)
        cursor.execute(
            """
            UPDATE botconversa_config
            SET valor = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE chave = ? AND (valor IS NULL OR valor = '')
            """,
            (value, config_key),
        )
        if cursor.rowcount:
            updated.append((config_key, expected_name, value))

    conn.commit()
    conn.close()

    summary = {"updated": updated, "missing": missing}

    print("=== Sincronização BotConversa ===")
    print(f"Atualizados: {len(updated)}")
    for config_key, expected_name, value in updated:
        print(f"  OK {config_key}: {expected_name} -> {value}")
    print(f"Pendentes: {len(missing)}")
    for config_key, expected_name in missing:
        print(f"  - {config_key}: criar/localizar '{expected_name}'")

    return summary


if __name__ == "__main__":
    sync_config()
