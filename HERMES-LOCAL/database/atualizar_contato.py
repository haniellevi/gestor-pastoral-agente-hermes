import json, urllib.request, urllib.error, sys, re

with open("config/integrations.env") as f:
    KEY = ""
    for line in f:
        if "BOTCONVERSA_API_KEY" in line:
            KEY = line.strip().split("=",1)[1].strip()
            break

BASE = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": KEY}
TAG_FILADELFIA = 17220560

def encontrar_contato(ident):
    """Encontra subscriber por 'contatoX' ou telefone"""
    page = 1
    ident_lower = ident.lower().replace("contato", "").strip()
    
    while True:
        req = urllib.request.Request(f"{BASE}/subscribers/?page={page}", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        for sub in data.get("results", []):
            fn = (sub.get("first_name", "") or "").lower()
            ln = (sub.get("last_name", "") or "").lower()
            phone = re.sub(r"[^\d]", "", sub.get("phone", ""))
            
            # Match by Contato X
            if fn == f"contato {ident_lower}" or fn == f"contato{ident_lower}":
                return sub
            
            # Match by phone
            if phone.endswith(ident_lower[-10:]) or ident_lower[-10:] == phone[-10:]:
                return sub
        
        if not data.get("next"):
            break
        page += 1
    return None

def atualizar_contato(ident, nome_completo):
    """Deleta e recria contato com nome correto + etiqueta"""
    
    parts = nome_completo.strip().split()
    primeiro = parts[0]
    sobrenome = " ".join(parts[1:]) if len(parts) > 1 else primeiro
    
    # Encontrar contato atual
    sub = encontrar_contato(ident)
    if not sub:
        print(f"❌ Contato '{ident}' não encontrado")
        return False
    
    sub_id = sub["id"]
    phone = sub.get("phone", "")
    old_name = f"{sub.get('first_name','')} {sub.get('last_name','')}".strip()
    print(f"🔍 Encontrado: {old_name} (ID:{sub_id})")
    
    # Deletar
    try:
        req = urllib.request.Request(f"{BASE}/subscriber/{sub_id}/delete/", headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"🗑️ Deletado (status {resp.status})")
    except Exception as e:
        print(f"❌ Erro ao deletar: {e}")
        return False
    
    # Recriar
    try:
        payload = {"phone": phone, "first_name": primeiro, "last_name": sobrenome, "has_opt_in_whatsapp": True}
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{BASE}/subscriber/", data=data_bytes, headers={**headers, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            new_id = result.get("id", result.get("subscriber_id"))
            print(f"✅ Recriado: '{primeiro} {sobrenome}' (ID:{new_id})")
    except Exception as e:
        print(f"❌ Erro ao recriar: {e}")
        return False
    
    # Etiquetar
    if new_id:
        try:
            req = urllib.request.Request(f"{BASE}/subscriber/{new_id}/tags/{TAG_FILADELFIA}/", headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"🏷️ Etiqueta 'Filadelfia Corrente' aplicada!")
        except:
            print(f"⚠️ Etiqueta já existia")
    
    print(f"\n✅ Contato atualizado com sucesso!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print('  python database/atualizar_contato.py contato5 "João Pedro Silva"')
        print('  python database/atualizar_contato.py 558999877130 "Maria Souza"')
        sys.exit(1)
    
    ident = sys.argv[1]
    nome = " ".join(sys.argv[2:])
    atualizar_contato(ident, nome)