import sqlite3
import datetime
from pathlib import Path
import os
import sys

# Ajuste do path para imports e acesso correto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"

def verificar_alertas_consolidacao():
    print("=== [Caleb] Verificando Consolidacao de Visitantes (Limite de 24h) ===")
    
    if not DB_PATH.exists():
        print(f"Erro: Banco de dados nao encontrado em {DB_PATH}", file=sys.stderr)
        return []
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Busca visitantes com status 'Pendente' onde o tempo decorrido desde data_visita (YYYY-MM-DD) e maior que 1 dia
    # Usamos julianday('now') e julianday(data_visita)
    cursor.execute("""
        SELECT id, visitante_nome, visitante_whatsapp, data_visita, consolidador_nome, criado_em
        FROM consolidacao_visitantes
        WHERE status = 'Pendente'
          AND (julianday('now') - julianday(data_visita)) > 1.0
    """)
    alertas = cursor.fetchall()
    
    if not alertas:
        print("[OK] Excelente! Nenhum visitante pendente ultrapassou o prazo critico de 24 horas.")
        conn.close()
        return []
        
    print(f"[ALERTA] ATENCAO: Encontrados {len(alertas)} visitantes pendentes com mais de 24h desde a visita:")
    for row in alertas:
        v_id, nome, whatsapp, data_visita, consolidador, criado_em = row
        print(f"  - [Atrasado] ID {v_id}: {nome} | WhatsApp: {whatsapp or 'Nao informado'} | Visita: {data_visita} | Consolidador: {consolidador}")
        
    conn.close()
    return alertas

if __name__ == "__main__":
    # Configura encoding do output se necessario, mas remover os emojis e acentos ja resolve
    verificar_alertas_consolidacao()
