import json, urllib.request, urllib.error, time

BASE_URL = "https://backend.botconversa.com.br/api/v1/webhook"
API_KEY = "2a0c5bf0-9c53-4d15-bc4c-2b673c5991e4"
headers = {"API-KEY": API_KEY}
TAG_FILADELFIA = 17220560

to_create = [
    ("Contato 1", "558999877130"),
    ("Contato 2", "558999279639"),
    ("Contato 5", "558999798473"),
    ("Contato 6", "558988083478"),
    ("Contato 7", "557791866293"),
    ("Contato 8", "558994650373"),
    ("Contato 9", "558999821667"),
    ("Contato 10", "558994271861"),
    ("Contato 11", "558999261097"),
    ("Contato 12", "556295274697"),
    ("Contato 13", "558494016713"),
    ("Contato 14", "558994545882"),
    ("Contato 15", "558999207078"),
    ("Contato 16", "558999059402"),
    ("Contato 17", "558999207166"),
    ("Contato 20", "558999305444"),
    ("Contato 21", "558999793444"),
    ("Contato 22", "558999320787"),
    ("Contato 24", "558999828638"),
    ("Contato 25", "558999287395"),
    ("Contato 27", "558988057690"),
    ("Contato 29", "558988068666"),
    ("Contato 30", "558999283159"),
]

MESSAGE = "🙏 Ola! Aqui e da secretaria da Igreja Batista Filadelfia Internacional de Corrente. Estamos atualizando os contatos do nosso WhatsApp e nao temos seu nome salvo. Voce poderia confirmar seu nome completo por favor?"

print("=== CRIANDO CONTATOS ===")
created_ids = []

for nome_temp, phone in to_create:
    try:
        payload = {"phone": phone, "first_name": nome_temp, "last_name": "(aguardando)", "has_opt_in_whatsapp": True}
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/subscriber/", data=data_bytes, headers={**headers, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            sub_id = result.get('id', result.get('subscriber_id'))
            created_ids.append((nome_temp, phone, sub_id))
            print(f"  OK: {nome_temp} ({phone}) -> ID {sub_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if 'already' in body.lower():
            try:
                cr = urllib.request.Request(f"{BASE_URL}/subscriber/get_by_phone/{phone}/", headers=headers)
                with urllib.request.urlopen(cr, timeout=10) as cr_resp:
                    edata = json.loads(cr_resp.read().decode())
                    if edata.get('id'):
                        created_ids.append((nome_temp, phone, edata['id']))
                        print(f"  JA EXISTE: {nome_temp} ({phone}) -> ID {edata['id']}")
            except:
                print(f"  ERRO {nome_temp}: {e.code}")
        else:
            print(f"  ERRO {nome_temp}: {body[:150]}")
    except Exception as e:
        print(f"  ERRO {nome_temp}: {e}")
    time.sleep(0.1)

print(f"\nTotal: {len(created_ids)}")

# Send messages
print("\n=== ENVIANDO MENSAGENS ===")
sent = 0
for nome_temp, phone, sub_id in created_ids:
    try:
        payload = {"type": "text", "value": MESSAGE}
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/subscriber/{sub_id}/send_message/", data=data_bytes, headers={**headers, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            sent += 1
            print(f"  Msg enviada: {nome_temp}")
    except Exception as e:
        print(f"  ERRO envio {nome_temp}: {str(e)[:60]}")
    time.sleep(0.15)

print(f"\nMensagens enviadas: {sent}")

# Tag
print("\n=== ETIQUETANDO ===")
tagged = 0
for nome_temp, phone, sub_id in created_ids:
    try:
        req = urllib.request.Request(f"{BASE_URL}/subscriber/{sub_id}/tags/{TAG_FILADELFIA}/", headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            tagged += 1
    except:
        pass
    time.sleep(0.05)

print(f"Etiquetados: {tagged}")
print(f"\nFIM: {sent} msgs enviadas + 7 (leva1) = {sent+7}/30 completos")
