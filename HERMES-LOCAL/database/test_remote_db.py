import psycopg2
import urllib.parse
import sys

def main():
    senhas = ["Texugo12", "Texugo12!@"]
    success = False
    
    for s in senhas:
        print(f"Testando conexão com senha: {s}")
        try:
            encoded_pass = urllib.parse.quote_plus(s)
            url = f"postgresql://postgres:{encoded_pass}@db.bymrxgwjkbbqfzuuvhyk.supabase.co:5432/postgres"
            conn = psycopg2.connect(url)
            print(f"--> CONECTOU COM SUCESSO! A senha correta é: {s}")
            conn.close()
            success = True
            
            # Retornar a senha encontrada para que o script possa ser usado em automações
            with open("senha_confirmada.txt", "w") as f:
                f.write(s)
            break
        except Exception as e:
            print(f"--> FALHA na senha {s}: {e}")
            
    if not success:
        print("Nenhuma das senhas fornecidas funcionou para conectar ao Supabase.")
        sys.exit(1)

if __name__ == "__main__":
    main()
