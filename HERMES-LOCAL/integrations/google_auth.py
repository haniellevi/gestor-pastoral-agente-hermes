import os
import sys
import glob
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos necessários para integrar Gmail, Calendar, Drive, Sheets, Docs e People API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/contacts.readonly'
]

# Caminhos padrão
INTEGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(INTEGRATIONS_DIR, 'token.json')

def find_client_secrets():
    """Tenta localizar arquivos client_secret*.json em locais comuns."""
    search_dirs = [
        os.path.dirname(INTEGRATIONS_DIR), # Raiz de HERMES-LOCAL/
        os.path.join(os.path.expanduser('~'), 'Downloads'), # Downloads do Usuário
        os.getcwd() # Diretório atual de execução
    ]
    
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
        pattern = os.path.join(directory, 'client_secret*.json')
        files = glob.glob(pattern)
        if files:
            return files[0]
            
        # Tenta também apenas *.json com credenciais no nome
        pattern_cred = os.path.join(directory, '*credentials*.json')
        files_cred = glob.glob(pattern_cred)
        if files_cred:
            return files_cred[0]
            
    return None

def get_credentials(client_secrets_path=None):
    """Obtém credenciais válidas do Google, renovando se necessário ou iniciando fluxo OAuth."""
    creds = None
    
    # 1. Tentar carregar token existente
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            print("Token existente carregado com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar token.json existente: {e}")
            creds = None

    # 2. Se o token não existir ou for inválido
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expirado detectado. Tentando renovar (refresh token)...")
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
                    token_file.write(creds.to_json())
                print("Token renovado e salvo com sucesso.")
                return creds
            except Exception as e:
                print(f"Falha ao renovar token: {e}. Iniciando novo login...")
                creds = None
        
        # 3. Executar o fluxo OAuth se não foi possível carregar/renovar
        if not client_secrets_path:
            client_secrets_path = find_client_secrets()
            
        if not client_secrets_path or not os.path.exists(client_secrets_path):
            raise FileNotFoundError(
                "Arquivo client_secret*.json não encontrado. "
                "Baixe o arquivo de credenciais do Google Cloud Console e passe o caminho ou coloque-o na pasta Downloads."
            )
            
        print(f"Usando arquivo de credenciais: {client_secrets_path}")
        print("Iniciando fluxo OAuth... O navegador será aberto para login.")
        
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Salvar as credenciais para a próxima execução
        with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
            
        print(f"Autenticação realizada com sucesso! Token salvo em: {TOKEN_PATH}")
        
    return creds

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Autenticador Google OAuth para o Hermes")
    parser.add_argument('--secrets', type=str, help="Caminho do arquivo JSON de segredos do cliente Google Cloud")
    args = parser.parse_args()
    
    try:
        get_credentials(args.secrets)
        print("Autenticacao com o Google esta configurada e pronta para uso!")
        sys.exit(0)
    except Exception as e:
        print(f"Erro na autenticacao: {e}", file=sys.stderr)
        sys.exit(1)
