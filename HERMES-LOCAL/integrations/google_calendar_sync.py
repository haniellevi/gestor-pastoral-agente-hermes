import os
import sqlite3
import datetime
import dateutil.parser
from googleapiclient.discovery import build
from google_auth import get_credentials

# Configurações do Banco de Dados
INTEGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(INTEGRATIONS_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'pastoral.db')

# Timezone padrão do Pastor (Piauí/Brasília)
TIMEZONE = 'America/Sao_Paulo'

def clean_iso_datetime(date_str):
    """Converte datas do banco (YYYY-MM-DD HH:MM:SS) para formato ISO-8601 com timezone."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # Caso seja apenas data
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
    # Assumir que as datas no banco estão no horário local do Pastor
    return dt.isoformat()

def parse_to_db_datetime(iso_str):
    """Converte ISO-8601 (do Google) para formato do banco (YYYY-MM-DD HH:MM:SS)."""
    try:
        dt = dateutil.parser.isoparse(iso_str)
        # Converter para local se tiver offset
        if dt.tzinfo:
            dt = dt.astimezone(datetime.timezone(datetime.timedelta(hours=-3))) # Horário de Brasília
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Erro ao converter data ISO {iso_str}: {e}")
        return None

def auto_categorize(title, description=""):
    """Categoriza um compromisso importado da agenda Google com base em palavras-chave."""
    text = (title + " " + (description or "")).lower()
    
    categories = {
        'Aconselhamento': ['aconselhamento', 'aconselhar', 'aconselha', 'conversar com', 'escutar'],
        'Culto': ['culto', 'celebração', 'celebracao', 'pregação', 'pregar', 'mensagem domingo', 'quarta-feira'],
        'Reuniao Lideranca': ['reunião', 'reuniao', 'g12', 'célula', 'celula', 'encontro', 'líderes', 'lideres', 'diretoria', 'conselho'],
        'Estudo/Sermao': ['estudo', 'esboço', 'esboco', 'preparar', 'leitura', 'teologia', 'livro', 'sermão', 'sermao'],
        'Pessoal': ['pessoal', 'treino', 'academia', 'treinar', 'médico', 'medico', 'dentista', 'família', 'familia', 'sarah', 'folga', 'passeio']
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
                
    return 'Outros'

def push_local_to_google(service, conn):
    """Envia novos compromissos do banco de dados local para o Google Calendar."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, titulo, categoria, data_inicio, data_fim, descricao, duracao_minutos
        FROM compromissos
        WHERE google_event_id IS NULL OR google_event_id = ''
    """)
    compromissos = cursor.fetchall()
    
    if not compromissos:
        print("Nenhum compromisso local novo para enviar ao Google Calendar.")
        return 0
        
    print(f"Enviando {len(compromissos)} compromissos para o Google Calendar...")
    count = 0
    
    for row in compromissos:
        db_id, titulo, categoria, data_inicio, data_fim, descricao, duracao = row
        
        # Montar a descrição adicionando metadados do Hermes
        desc_completa = f"{descricao or ''}\n\n---\nSincronizado via Hermes Gestão Pastoral\nCategoria: #{categoria}"
        
        start_iso = clean_iso_datetime(data_inicio)
        end_iso = clean_iso_datetime(data_fim)
        
        event_body = {
            'summary': f"[{categoria}] {titulo}" if categoria != 'Outros' else titulo,
            'description': desc_completa,
            'start': {
                'dateTime': start_iso,
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': TIMEZONE,
            },
            'reminders': {
                'useDefault': True,
            }
        }
        
        try:
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            google_id = event.get('id')
            
            # Atualizar banco local com o ID do Google
            cursor.execute("""
                UPDATE compromissos
                SET google_event_id = ?
                WHERE id = ?
            """, (google_id, db_id))
            conn.commit()
            
            print(f"✅ Evento '{titulo}' enviado. Google Event ID: {google_id}")
            count += 1
        except Exception as e:
            print(f"❌ Erro ao enviar '{titulo}': {e}")
            
    return count

def pull_google_to_local(service, conn):
    """Importa novos eventos do Google Calendar para o banco local."""
    cursor = conn.cursor()
    
    # Definir intervalo: dos últimos 7 dias até 30 dias no futuro
    agora = datetime.datetime.utcnow()
    inicio = (agora - datetime.timedelta(days=7)).isoformat() + 'Z' # Formato UTC esperado pela API
    fim = (agora + datetime.timedelta(days=30)).isoformat() + 'Z'
    
    print(f"Buscando eventos do Google Calendar de {inicio} até {fim}...")
    
    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=inicio,
            timeMax=fim,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
    except Exception as e:
        print(f"Erro ao buscar eventos do Google Calendar: {e}")
        return 0
        
    if not events:
        print("Nenhum evento retornado do Google Calendar.")
        return 0
        
    count = 0
    for event in events:
        google_id = event.get('id')
        titulo = event.get('summary', 'Compromisso Google')
        descricao = event.get('description', '')
        
        # Ignorar se o evento foi criado pelo próprio Hermes (evita loops)
        if "Sincronizado via Hermes" in (descricao or ""):
            continue
            
        # Verificar se já existe no banco local
        cursor.execute("SELECT id FROM compromissos WHERE google_event_id = ?", (google_id,))
        if cursor.fetchone():
            continue  # Já está no banco local
            
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Pegar data/hora do evento
        start_raw = start.get('dateTime', start.get('date'))
        end_raw = end.get('dateTime', end.get('date'))
        
        if not start_raw or not end_raw:
            continue
            
        # Converter para formato do banco local
        data_inicio = parse_to_db_datetime(start_raw)
        data_fim = parse_to_db_datetime(end_raw)
        
        if not data_inicio or not data_fim:
            continue
            
        # Calcular duração
        dt_start = dateutil.parser.isoparse(start_raw)
        dt_end = dateutil.parser.isoparse(end_raw)
        duracao = int((dt_end - dt_start).total_seconds() / 60)
        
        # Categorizar evento baseado em palavras-chave do título/descrição
        categoria = auto_categorize(titulo, descricao)
        
        try:
            cursor.execute("""
                INSERT INTO compromissos (titulo, categoria, data_inicio, data_fim, descricao, duracao_minutos, google_event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (titulo, categoria, data_inicio, data_fim, descricao, duracao, google_id))
            conn.commit()
            print(f"📥 Novo compromisso importado do Google: '{titulo}' ({categoria})")
            count += 1
        except Exception as e:
            print(f"Erro ao inserir evento importado '{titulo}': {e}")
            
    return count

def sync_all():
    """Executa a sincronização completa (push e pull)."""
    print("\n==============================================")
    print(f"Iniciando Sincronização de Agenda: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==============================================")
    
    if not os.path.exists(DB_PATH):
        print(f"Erro: Banco de dados não encontrado em {DB_PATH}. Execute initialize_db.py primeiro.")
        return
        
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Erro de autenticação Google API: {e}")
        print("Certifique-se de que configurou as credenciais via 'google_auth.py' primeiro.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    try:
        sent = push_local_to_google(service, conn)
        received = pull_google_to_local(service, conn)
        print("----------------------------------------------")
        print(f"Sincronização concluída: {sent} enviados | {received} importados.")
        print("==============================================\n")
    finally:
        conn.close()

if __name__ == '__main__':
    sync_all()
