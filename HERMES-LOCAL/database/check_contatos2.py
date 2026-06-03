import json, urllib.request

with open("config/integrations.env") as f:
    KEY = ""
    for line in f:
        if "BOTCONVERSA_API_KEY" in line:
            KEY = line.strip().split("=",1)[1].strip()
            break

BASE = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": KEY}

# Check all pages to see full picture
page = 1
total_contacts = 0
contato_count = 0
caravana_count = 0
untagged_count = 0

while True:
    req = urllib.request.Request(f"{BASE}/subscribers/?page={page}", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    
    results = data.get("results", [])
    total_contacts += len(results)
    
    for r in results:
        name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        tags_raw = r.get("tags", [])
        has_tags = bool(tags_raw)
        
        if name.startswith("Contato "):
            contato_count += 1
        
        if not has_tags:
            untagged_count += 1
            print(f"  SEM TAG: ID:{r['id']} | {name} | Tel:{r.get('phone','')[-10:]}")
    
    next_page = data.get("next")
    if not next_page:
        break
    page += 1

print(f"\nTotal de contatos: {total_contacts}")
print(f"Contato 1-30 (do fluxo): {contato_count}")
print(f"Sem nenhuma etiqueta: {untagged_count}")
