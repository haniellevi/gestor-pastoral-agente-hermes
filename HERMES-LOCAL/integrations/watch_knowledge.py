import os
import time
import subprocess
import logging

# Caminho absoluto da pasta HERMES-LOCAL para garantir funcionamento em background
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

LOG_FILE = os.path.join(BASE_DIR, "knowledge_sync.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

WATCH_DIR = "conhecimento"
DEBOUNCE_TIME = 5.0  # Tempo de espera em segundos para evitar múltiplos commits rápidos enquanto digita

def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        logging.error(f"Erro ao obter branch atual do Git: {e}")
        return "main"

def git_sync(branch):
    try:
        # Verifica se realmente há modificações na pasta de conhecimento
        status = subprocess.run(
            ["git", "status", "--porcelain", WATCH_DIR],
            capture_output=True,
            text=True,
            check=True
        )
        if not status.stdout.strip():
            # Nenhuma alteração pendente
            return

        logging.info("Alterações detectadas na pasta de conhecimento. Sincronizando com o GitHub...")
        
        # Git Add
        subprocess.run(["git", "add", WATCH_DIR], check=True)
        
        # Git Commit
        commit_msg = "auto(conhecimento): atualiza conhecimento do agente via Obsidian/Desktop"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # Git Push
        subprocess.run(["git", "push", "origin", branch], check=True)
        logging.info(f"Sincronização concluída com sucesso na branch '{branch}'!")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao rodar comandos Git: {e.stderr or e}")
    except Exception as e:
        logging.error(f"Erro inesperado durante a sincronização: {e}")

def get_directory_state(path):
    state = {}
    if not os.path.exists(path):
        return state
    for root, dirs, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                state[filepath] = os.path.getmtime(filepath)
            except OSError:
                pass
    return state

def main():
    logging.info("Iniciando monitoramento da pasta de conhecimento...")
    last_state = get_directory_state(WATCH_DIR)
    last_change_time = 0
    pending_sync = False
    
    while True:
        try:
            time.sleep(2)
            current_state = get_directory_state(WATCH_DIR)
            
            # Compara o estado atual dos arquivos com o estado anterior
            if current_state != last_state:
                logging.info("Detecção de modificações físicas na pasta 'conhecimento'.")
                last_state = current_state
                last_change_time = time.time()
                pending_sync = True
                
            # Se houver sincronização pendente e o tempo de debounce passou (usuário terminou de salvar)
            if pending_sync and (time.time() - last_change_time >= DEBOUNCE_TIME):
                branch = get_current_branch()
                git_sync(branch)
                pending_sync = False
                
        except KeyboardInterrupt:
            logging.info("Monitoramento interrompido pelo usuário.")
            break
        except Exception as e:
            logging.error(f"Erro no loop principal do monitor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
