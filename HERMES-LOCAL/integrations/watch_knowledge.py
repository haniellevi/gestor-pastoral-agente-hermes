import os
import time
import subprocess
import logging
import shutil
from pathlib import Path

# Caminho absoluto da pasta HERMES-LOCAL para garantir funcionamento em background
BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)

LOG_FILE = BASE_DIR / "knowledge_sync.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TARGET_DIR = BASE_DIR / "conhecimento"
DEBOUNCE_TIME = 5.0  # Tempo de espera em segundos para evitar múltiplos commits rápidos enquanto digita
IGNORED_DIRS = {".git", ".obsidian", ".trash", "__pycache__"}


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def get_source_dir():
    load_env_file()
    configured = os.getenv("HERMES_KNOWLEDGE_SOURCE_DIR", "").strip().strip('"')
    if configured:
        return Path(configured).expanduser()
    return TARGET_DIR


SOURCE_DIR = get_source_dir()


def is_same_path(left, right):
    try:
        return Path(left).resolve().samefile(Path(right).resolve())
    except FileNotFoundError:
        return Path(left).resolve() == Path(right).resolve()

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


def mirror_source_to_target():
    if is_same_path(SOURCE_DIR, TARGET_DIR):
        return

    if not SOURCE_DIR.exists():
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"Pasta fonte criada: {SOURCE_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    for source_file in SOURCE_DIR.rglob("*"):
        if any(part in IGNORED_DIRS for part in source_file.parts):
            continue
        if not source_file.is_file():
            continue

        relative_path = source_file.relative_to(SOURCE_DIR)
        target_file = TARGET_DIR / relative_path
        should_copy = (
            not target_file.exists()
            or source_file.stat().st_mtime > target_file.stat().st_mtime
            or source_file.stat().st_size != target_file.stat().st_size
        )
        if should_copy:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            copied += 1

    if copied:
        logging.info(f"{copied} arquivo(s) copiado(s) de '{SOURCE_DIR}' para '{TARGET_DIR}'.")


def git_sync(branch):
    try:
        mirror_source_to_target()

        # Verifica se realmente há modificações na pasta de conhecimento
        status = subprocess.run(
            ["git", "status", "--porcelain", str(TARGET_DIR.relative_to(BASE_DIR))],
            capture_output=True,
            text=True,
            check=True
        )
        if not status.stdout.strip():
            # Nenhuma alteração pendente
            return

        logging.info("Alterações detectadas na pasta de conhecimento. Sincronizando com o GitHub...")
        
        # Git Add
        subprocess.run(["git", "add", str(TARGET_DIR.relative_to(BASE_DIR))], check=True)
        
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
    path = Path(path)
    if not path.exists():
        return state
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            filepath = Path(root) / file
            try:
                state[str(filepath)] = filepath.stat().st_mtime
            except OSError:
                pass
    return state

def main():
    logging.info(f"Iniciando monitoramento da base de conhecimento: {SOURCE_DIR}")
    mirror_source_to_target()
    last_state = get_directory_state(SOURCE_DIR)
    last_change_time = 0
    pending_sync = False
    
    while True:
        try:
            time.sleep(2)
            current_state = get_directory_state(SOURCE_DIR)
            
            # Compara o estado atual dos arquivos com o estado anterior
            if current_state != last_state:
                logging.info(f"Detecção de modificações físicas em '{SOURCE_DIR}'.")
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
