import json, urllib.request

with open("config/integrations.env") as f:
    KEY = ""
    for line in f:
        if "BOTCONVERSA_API_KEY" in line:
            KEY = line.strip().split("=",1)[1].strip()
            break

BASE = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": KEY}

print("=== TODOS OS 80 CONTATOS ATUAIS ===")
print()

# Get all pages
all_subs = []
page = 1
while True:
    req = urllib.request.Request(f"{BASE}/subscribers/?page={page}", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    for sub in data.get("results", []):
        tags = sub.get("tags", [])
        if tags and isinstance(tags[0], dict):
            tag_names = [t.get("name","?") for t in tags]
        else:
            tag_names = []
        
        fn = sub.get("first_name","")
        ln = sub.get("last_name","")
        phone = sub.get("phone","")
        all_subs.append((fn, ln, phone, tag_names))
    
    if not data.get("next"):
        break
    page += 1

# Sort: named first, then Contatos
named = [s for s in all_subs if not s[0].lower().startswith("contato")]
contatos = [s for s in all_subs if s[0].lower().startswith("contato")]

print(f"Total: {len(all_subs)}")
print(f"Com nome: {len(named)}")
print(f"Contato X: {len(contatos)}")
print()
print("--- COM NOME ---")
for fn, ln, phone, tags in sorted(named, key=lambda x: x[0].lower()):
    print(f"  ✅ {fn:<30} {ln:<25} | Tel:{phone[-10:]} | Tags:{', '.join(tags) if tags else 'NENHUMA'}")

print()
print("--- CONTATO X (aguardando resposta) ---")
for fn, ln, phone, tags in sorted(contatos, key=lambda x: x[0]):
    print(f"  ⏳ {fn:<30} {ln:<25} | Tel:{phone[-10:]} | Tags:{', '.join(tags) if tags else 'NENHUMA'}")

print()
print("="*60)
print(f"Total: {len(named)} com nome | {len(contatos)} Contato X | {len(named) + len(contatos)} total")
