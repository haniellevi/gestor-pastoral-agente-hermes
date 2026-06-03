import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:5050"

def enviar_post(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            print(f"Sucesso [{endpoint}]: {body}")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"Erro HTTP [{endpoint}] ({exc.code}): {body}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"Erro de conexão [{endpoint}]: {exc}", file=sys.stderr)
        return None

def testar_atendimento_rute():
    print("\n--- Testando Webhook Atendimento Rute (Oração) ---")
    payload = {
        "subscriber_id": "999999",
        "telefone": "5589988887777",
        "nome": "Membro Teste Oração",
        "tipo_solicitacao": "oracao",
        "nivel_urgencia": "Normal",
        "resumo": "Pedido de oração pela saúde física e familiar."
    }
    enviar_post("/webhook_atendimento_rute", payload)

    print("\n--- Testando Webhook Atendimento Rute (Aconselhamento - Urgente) ---")
    payload = {
        "subscriber_id": "999999",
        "telefone": "5589988887777",
        "nome": "Membro Teste Aconselhamento",
        "tipo_solicitacao": "aconselhamento",
        "nivel_urgencia": "alta",
        "resumo": "Gostaria de agendar um aconselhamento pastoral devido a uma decisão profissional importante."
    }
    enviar_post("/webhook_atendimento_rute", payload)

def testar_atualizacao_cadastral():
    print("\n--- Testando Webhook Atualização Cadastral (IA) ---")
    payload = {
        "subscriber_id": "999999",
        "telefone": "5589988887777",
        "nome": "Membro Teste Cadastral",
        "resumo_ia": "[ATUALIZACAO_CADASTRAL]\nstatus=atualizado\nBairro=Setor Oeste\nTempo_Igreja=3 anos\nLider_Celula=Líder André\nCelula_Atual=Shammah\nG12_Pastoral=Pr. Raniel\nFez_Encontro=Sim\nUniversidade_Vida=Sim\nCapacitacao_Destino=Sim\nMinisterios=Mídia\n[/ATUALIZACAO_CADASTRAL]"
    }
    enviar_post("/webhook_atualizacao_cadastral", payload)

def testar_visitante():
    print("\n--- Testando Webhook Visitante (Caleb) ---")
    payload = {
        "evento": "visitante_registrado",
        "subscriber_id": "888888",
        "nome": "Carlos Visitante Teste",
        "telefone": "5589977776666",
        "bairro": "Nova Corrente",
        "como_conheceu": "Amigo convidou",
        "deseja_contato": "Sim",
        "interesse_celula": "Sim",
        "resumo": "Visitou o culto de domingo e deseja conhecer uma célula no Setor Oeste."
    }
    enviar_post("/webhook_visitante", payload)

def testar_g12_celulas():
    print("\n--- Testando Webhook G12 Células (Relatório Semanal) ---")
    payload = {
        "nome_celula": "Célula Shammah",
        "lider_nome": "Líder André",
        "presenca_membros": 8,
        "visitantes": 2,
        "decisoes_fe": 1,
        "rede": "Jovens",
        "data_relatorio": "2026-06-03"
    }
    enviar_post("/webhook_g12_celulas", payload)

if __name__ == "__main__":
    testar_atendimento_rute()
    testar_atualizacao_cadastral()
    testar_visitante()
    testar_g12_celulas()
