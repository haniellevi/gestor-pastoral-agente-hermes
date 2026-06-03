import json, urllib.request

with open("config/integrations.env") as f:
    for line in f:
        if line.startswith("BOTCONVERSA_API_KEY="):
            KEY = line.strip().split("=",1)[1]
            break

BASE = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": KEY}

print("=== VERIFICANDO CONTATOS ATUAIS ===")
req = urllib.request.Request(f"{BASE}/subscribers/?page=1", headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    total = data.get("count", 0)
    results = data.get("results", [])
    print(f"Total de contatos agora: {total}\n")
    for r in results:
        tags_raw = r.get("tags", [])
        if isinstance(tags_raw, list) and tags_raw and isinstance(tags_raw[0], dict):
            tags_str = ", ".join(t.get("name","?") for t in tags_raw)
        else:
            tags_str = str(tags_raw)
        print(f"ID:{r['id']} | {r.get('first_name','')} {r.get('last_name','')} | Tel:{r.get('phone','')[-10:]} | Tags:{tags_str}")