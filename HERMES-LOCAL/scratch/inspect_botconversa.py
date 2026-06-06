import json
from integrations.botconversa_client import BotConversaClient

def main():
    client = BotConversaClient()
    
    print("=== BUSCANDO TAGS DO BOTCONVERSA ===")
    tags = client.list_tags()
    for t in tags:
        print(f"Tag ID: {t.get('id')} | Name: '{t.get('name')}'")
        
    print("\n=== BUSCANDO FLOWS DO BOTCONVERSA ===")
    flows = client.list_flows()
    for f in flows:
        print(f"Flow ID: {f.get('id')} | Name: '{f.get('name') or f.get('title')}'")
        
    print("\n=== BUSCANDO CUSTOM FIELDS DO BOTCONVERSA ===")
    fields = client.list_custom_fields()
    for fd in fields:
        print(f"Field ID: {fd.get('id')} | Name: '{fd.get('name') or fd.get('label') or fd.get('key')}'")
        
    print("\n=== BUSCANDO SEQUENCES DO BOTCONVERSA ===")
    seqs = client.list_sequences()
    for s in seqs:
        print(f"Sequence ID: {s.get('id')} | Name: '{s.get('name')}'")

if __name__ == "__main__":
    main()
