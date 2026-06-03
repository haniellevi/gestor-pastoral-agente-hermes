import json, urllib.request, re

with open("config/integrations.env") as f:
    KEY = ""
    for line in f:
        if "BOTCONVERSA_API_KEY" in line:
            KEY = line.strip().split("=",1)[1].strip()
            break

BASE = "https://backend.botconversa.com.br/api/v1/webhook"
headers = {"API-KEY": KEY}
TAG_CONVENCAO = 17220724

# All 52 convention participants
participants = [
    ("Kemilly Dayane Carvalho de Souza", ""),
    ("Camila Carvalho da Silva Souza", ""),
    ("Letícia Bezerra das Neves Silva", ""),
    ("Ramon dos Santos Ribeiro", ""),
    ("Geovanni da Silva Souza Vivas", ""),
    ("Robério Rodrigues Lemos", ""),
    ("Gabriela Paiva de Carvalho Lemos", ""),
    ("Luzanira Pereira da Silva Barros", ""),
    ("Clebiana de Sena Borges", ""),
    ("João Pedro Sena da Silva", ""),
    ("GIOVANNA LEMOS JACOBINA CORADO", ""),
    ("GABRIEL SOUSA ROSA AMANCIO", ""),
    ("LARISSA SENA DA SILVA", ""),
    ("THIAGO WILHIAN SOUSA LIMA", ""),
    ("Albenita de Castro Pereira", ""),
    ("Wanderson Cleiton do Amaral Maciel", ""),
    ("Lélia Pereira de Miranda", ""),
    ("Mércia Denise Lemos de Neiva Lima", ""),
    ("Clara Beatriz Viana Maciel", ""),
    ("Andreia Vogado da Silva", ""),
    ("Mariana Vogado Fonseca", ""),
    ("Nayla Sena da Silva", ""),
    ("Vinícius de Sousa Carvalho Moura", ""),
    ("Maria Eliza Vogado de Sena Maia", ""),
    ("Erick Kauan Marques do Lago", ""),
    ("Candida de Sena Borges Luz", ""),
    ("Vytor Carvalho de Souza", ""),
    ("Gilene Silva Oliveira Marques", ""),
    ("Cinthya Herley Kochhann Ribeiro", ""),
    ("Natália Silva Ribeiro", ""),
    ("Jonatas Nunes da Costa Maia de Carvalho", ""),
    ("Marcos Augusto Alves de Souza", ""),
    ("Karolina Xavier", ""),
    ("Raiffe Ray", ""),
    ("Diego Rodrigues da Silva", ""),
    ("Clessiane Oliveira Rocha Ribeiro", ""),
    ("Amanda Araujo", ""),
    ("Luciane da Silva Oliveira Guimarães", ""),
    ("Adriano Moura da Silva", ""),
    ("Randel Jeison dos Santos", ""),
    ("Jenielton da Silva Oliveira", ""),
    ("Maria do Livramento Castro dos Santos", ""),
    ("Joelma de Sousa Alves", ""),
    ("Jhenik Teixeira de Brito", ""),
    ("Ana Vitória Alves de Oliveira", ""),
    ("Rejane Pereira Alves Oliveira", ""),
    ("Nalton de Souza Oliveira Filho", ""),
    ("Joaria Moreira Carlos", ""),
    ("Nycole Moreira de Souza", ""),
    ("Marineide Barros Nascimento", ""),
    ("Francineta Teófilo da Silva Oliveira", ""),
    ("João Pedro Sens da Silva", ""),
]

# Get ALL subscribers with the Convenção tag
print("Buscando contatos com tag CONVENÇÃO G12 2026...")
convencao_ids = set()
convencao_subs = []

page = 1
while True:
    req = urllib.request.Request(f"{BASE}/subscribers/?page={page}", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    for sub in data.get("results", []):
        tags = sub.get("tags", [])
        tag_ids = set()
        if tags and isinstance(tags[0], dict):
            tag_ids = {t.get("id") for t in tags}
        else:
            tag_ids = set(tags) if tags else set()
        
        if TAG_CONVENCAO in tag_ids:
            convencao_subs.append(sub)
            convencao_ids.add(sub["id"])
    
    if not data.get("next"):
        break
    page += 1

print(f"Total com tag CONVENÇÃO: {len(convencao_subs)}")

# Build lookup by name parts
print()
print("=" * 100)
print("LISTA DA CARAVANA — STATUS NO BOTCONVERSA")
print("=" * 100)

presentes = []
ausentes = []

for nome, _ in participants:
    nome_lower = nome.lower().strip()
    found = False
    found_info = None
    
    for sub in convencao_subs:
        fn = (sub.get("first_name", "") or "").lower()
        ln = (sub.get("last_name", "") or "").lower()
        full = f"{fn} {ln}".strip()
        phone = sub.get("phone", "")
        
        # Check if any part of the name matches
        nome_parts = set(nome_lower.split())
        full_parts = set(full.split())
        common = nome_parts & full_parts
        
        # If they share 2+ significant words, it's a match
        significant = {p for p in common if len(p) > 2}
        if len(significant) >= 2 or (len(significant) == 1 and len(nome_parts - full_parts) <= 1):
            found = True
            found_info = (sub["id"], fn, ln, phone)
            break
        
        # Also check first name + last initial
        nome_first = nome_parts.pop() if nome_parts else ""
        if nome_first and fn and nome_first in fn:
            found = True
            found_info = (sub["id"], fn, ln, phone)
            break
    
    if found:
        presentes.append((nome, found_info))
        print(f"  ✅ {nome:<45} | {found_info[1].title():<20} {found_info[2].title():<20} | {found_info[3][-10:]}")
    else:
        ausentes.append(nome)
        print(f"  ❌ {nome:<45} | NÃO ENCONTRADO")

print()
print("=" * 100)
print("RESUMO")
print("=" * 100)
print(f"✅ Cadastrados com tag Convenção: {len(presentes)} de 52")
print(f"❌ Faltando: {len(ausentes)} de 52")

if ausentes:
    print()
    print("NÃO ENCONTRADOS:")
    for nome in ausentes:
        print(f"  • {nome}")
