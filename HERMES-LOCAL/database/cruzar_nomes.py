import json, re, os, urllib.request, time

# Read API key from env file
with open("config/integrations.env","r") as f:
    for line in f:
        if line.startswith("BOTCONVERSA_API_KEY="):
            API_KEY = line.strip().split("=",1)[1]
            break

BASE_URL = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": API_KEY}
TAG_FILADELFIA = 17220560

with open("database/export_botconversa_completo.json","r",encoding="utf-8") as f:
    export = json.load(f)
all_subs = export["subscribers"]
print(f"Base: {len(all_subs)}")

phone_idx = {}
name_idx = {}
first_idx = {}
for sub in all_subs:
    dig = re.sub(r"[^\d]","",sub.get("phone",""))
    phone_idx[dig] = sub
    full = (sub.get("full_name","") or "").strip().lower()
    first = (sub.get("first_name","") or "").strip().lower()
    if full: name_idx[full] = sub
    fw = first if first else (full.split()[0] if full else "")
    if fw: first_idx.setdefault(fw,[]).append(sub)

nomes = [
    "Adenilde Corrente","Adriano Moura","Adriel Discipulo Corrente",
    "Ana Ariel","Ana Clara Louzeiro Jhenik","Ana Vitoria Louvor Corrente",
    "Arnaldo Teresina","Camila Discipula Corrente","carlosems12 Kadu Discipulo",
    "Charlene CORRENTE igreja","Cleber Corrente","Cintia Corrente",
    "Dagmar Corrente","Dica Discipula","Dona Maria Izalene",
    "Dona Maria Vermelhao","Eriques Corrente","Evelyn Vivas Discipula",
    "Fabiana Do Valmir","Filo G12 Corrente","Gabi Zangadinha",
    "Gabriel De LETICIA","Geovani Eletrobras Discipulos","Gilene Corrente",
    "Hilda Paranagua","Irenalda Baiao","Jamily Neres Corrente",
    "Jenielton Tim","Jhenik Corrente","Joao Victor Corrente",
    "Joaquim Corrente Guimaraes","Joelma Do Eriques","Jucileia Corrente",
    "Kaian Louvor","Kemilly De Camila","Kenia Corrente Filadelfia",
    "Leticia de Gabriel Barreiras","Luciana Discipula Corrente","Luciane Guimaraes",
    "Luzanira Corrente","Livia Do Randel","MARINEIDE BARROS",
    "Maria Amelia Corrente Discipula","Maria Do Nascimento",
    "Marisia Ferreira Lemos","Monick Evans","Naiana Corrente",
    "Nalton Discipulo Pedreiro","Naty Discipla Corrente",
    "Pablo Irmao De Evelin","Paulo Henrique Lemos","Pedro Henrique",
    "Raiffe Corrente","Ramon","Randel Corrente","Rejane De Nielton Tim",
    "Roberio Discipulo Corrente","Roberio Lemos","Sandra Do GILVAN",
    "Thais De RAIFFE","Uelda Corrente","Valmir Corrente",
    "Vytor designs","Wanderson Maciel",
    "Amanda Araujo.","Clara","Clessiane Ribeiro","Eva Maria",
    "Ivana Oliveira","Lohh","Leo","Maria Luiza","Tamires",
    "Valquiria","Leticia Maciel","Patricia & Leo serralheiro"
]

found = []
missing = []
for nome in nomes:
    clean = nome.strip().lower().lstrip("~ ").lstrip('"').rstrip('"').strip()
    sid = None; mt = None
    
    if clean in name_idx:
        sid = name_idx[clean]['id']; mt = 'exato'
    
    if not sid:
        parts = clean.split()
        fw = parts[0]
        if fw in first_idx:
            cands = first_idx[fw]
            if len(cands) == 1:
                sid = cands[0]['id']; mt = 'primeiro_nome'
            elif len(parts) > 1:
                lw = parts[-1]
                for c in cands:
                    cf = (c.get('full_name','') or '').lower()
                    cl = (c.get('last_name','') or '').lower()
                    if lw in cf or lw in cl:
                        sid = c['id']; mt = 'parcial'
                        break
    
    if sid:
        sub_phone = ""
        for s in all_subs:
            if s['id'] == sid:
                sub_phone = re.sub(r"[^\d]","",s.get("phone",""))
                break
        found.append((nome, sid, mt, sub_phone))
        print(f"  OK [{mt}] {str(nome):<45} ID:{sid} Tel:{sub_phone[-10:]}")
    else:
        missing.append((nome, clean))
        print(f"  --- {nome} -> NAO ENCONTRADO")

print(f"\nEncontrados: {len(found)}")
print(f"Faltando: {len(missing)}")

fones = {}
print("\n=== DUPLICATAS ===")
for nome, sid, mt, tel in found:
    if not tel: continue
    if tel in fones:
        print(f"  DUPLICATA: {nome} = {fones[tel]}")
    else:
        fones[tel] = nome

if found:
    print("\n=== ETIQUETANDO ===")
    tagged = 0; errors = 0
    for nome, sid, mt, tel in found:
        try:
            req = urllib.request.Request(f"{BASE_URL}/subscriber/{sid}/tags/{TAG_FILADELFIA}/", headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                tagged += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if 'already' in body.lower():
                tagged += 1
            else:
                errors += 1
        except:
            errors += 1
        time.sleep(0.05)
    print(f"Etiquetados: {tagged}, Erros: {errors}")

if missing:
    print(f"\n=== SUGESTOES FALTANTES ===")
    for nome, clean in missing:
        parts = clean.split()
        best = []
        for sub in all_subs:
            full = (sub.get('full_name','') or '').lower()
            score = sum(1 for p in parts if len(p) > 2 and p in full)
            if score >= max(len(parts)-1, 1):
                best.append((sub['id'], sub.get('full_name',''), re.sub(r"[^\d]","",sub.get('phone',''))[-10:]))
        if best:
            print(f"  Sugestoes para '{nome}':")
            for fid, fn, ft in best[:3]:
                print(f"    -> {fn} (ID:{fid} Tel:{ft})")
        else:
            print(f"  '{nome}' -> sem sugestoes na base")

print(f"\nFIM: {len(found)} encontrados e etiquetados | {len(missing)} faltando")
