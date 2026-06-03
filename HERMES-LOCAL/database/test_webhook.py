import json
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Adiciona o diretório raiz ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Cria uma cópia temporária do banco de dados para os testes
DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"
TEST_DB_PATH = PROJECT_ROOT / "database" / "pastoral_test.db"

# Mock do DB_PATH no modulo webhook_server antes do import
import integrations.webhook_server as ws
ws.DB_PATH = TEST_DB_PATH


class TestWebhookIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # 1. Cria o banco de teste a partir do original (apenas a estrutura ou cópia rápida)
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
            
        conn_orig = sqlite3.connect(DB_PATH)
        conn_test = sqlite3.connect(TEST_DB_PATH)
        
        # Copia esquema e dados
        conn_orig.backup(conn_test)
        conn_orig.close()
        self.conn = conn_test
        
        # Garante que temos um membro de teste
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM membros WHERE telefone = '558999999999'")
        cursor.execute(
            """
            INSERT INTO membros (nome_completo, telefone, botconversa_subscriber_id, status_cadastro)
            VALUES (?, ?, ?, ?)
            """,
            ("Membro de Teste", "558999999999", 999999, "Incompleto")
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    @patch("integrations.webhook_server.BotConversaClient")
    async def test_atualizacao_cadastro_completo(self, mock_client_class):
        # Configura o mock do cliente
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Payload simulando atualização completa e correta via Rute Cadastro
        resumo_ia = (
            "[ATUALIZACAO_CADASTRAL]\n"
            "status=atualizado\n"
            "Bairro=Nova Corrente\n"
            "Tempo_Igreja=Mais de 2 anos\n"
            "Lider_Celula=Joaquim\n"
            "Celula_Atual=Betel\n"
            "G12_Pastoral=Pr. Raniel\n"
            "Fez_Encontro=Sim\n"
            "Universidade_Vida=Sim\n"
            "Capacitacao_Destino=Sim\n"
            "Ministerios=Louvor\n"
            "Interesse_Ministerio=Louvor\n"
            "Feedback_Melhorias=Tudo excelente!\n"
            "Feedback_falta=Nenhuma\n"
            "resumo=Cadastro totalmente preenchido e atualizado com sucesso.\n"
            "[/ATUALIZACAO_CADASTRAL]"
        )
        
        payload = {
            "subscriber_id": 999999,
            "telefone": "558999999999",
            "nome": "Membro de Teste",
            "resumo_ia": resumo_ia
        }
        
        # Executa o processamento do webhook
        resultado = await ws.processar_atualizacao_cadastral(payload)
        
        # Asserções
        self.assertEqual(resultado["status"], "ok")
        
        # Verifica se atualizou o SQLite localmente
        cursor = self.conn.cursor()
        cursor.execute("SELECT status_cadastro, bairro_cidade, lider_celula, celula_atual, fez_encontro FROM membros WHERE id = ?", (resultado["membro_id"],))
        row = cursor.fetchone()
        
        self.assertEqual(row[0], "Completo") # Cadastro deve ficar Completo pois preencheu todas as trilhas
        self.assertEqual(row[1], "Nova Corrente")
        self.assertEqual(row[2], "Joaquim")
        self.assertEqual(row[3], "Betel")
        self.assertEqual(row[4], "Sim")
        
        # Verifica se o cliente da API do BotConversa foi acionado para atualizar campos e tags
        self.assertTrue(mock_client.set_custom_field.called)
        self.assertTrue(mock_client.add_tag.called)

    @patch("integrations.webhook_server.BotConversaClient")
    async def test_cadastro_incompleto(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Faltam campos obrigatórios de trilhas (Universidade da Vida, Capacitação Destino, etc.)
        resumo_ia = (
            "[ATUALIZACAO_CADASTRAL]\n"
            "status=atualizado\n"
            "Bairro=Setor Oeste\n"
            "Tempo_Igreja=Menos de 6 meses\n"
            "Lider_Celula=None\n"
            "Celula_Atual=Nenhuma\n"
            "G12_Pastoral=Nao sei\n"
            "Fez_Encontro=Nao\n"
            "Universidade_Vida=\n" # Vazio
            "Capacitacao_Destino=\n" # Vazio
            "resumo=Membro ainda não iniciou as trilhas.\n"
            "[/ATUALIZACAO_CADASTRAL]"
        )
        
        payload = {
            "subscriber_id": 999999,
            "telefone": "558999999999",
            "nome": "Membro de Teste",
            "resumo_ia": resumo_ia
        }
        
        resultado = await ws.processar_atualizacao_cadastral(payload)
        
        self.assertEqual(resultado["status"], "ok")
        
        # Verifica status local
        cursor = self.conn.cursor()
        cursor.execute("SELECT status_cadastro, bairro_cidade, fez_encontro FROM membros WHERE id = ?", (resultado["membro_id"],))
        row = cursor.fetchone()
        self.assertEqual(row[0], "Incompleto") # Deve permanecer Incompleto
        self.assertEqual(row[1], "Setor Oeste")
        self.assertEqual(row[2], "Nao")

    @patch("integrations.webhook_server.BotConversaClient")
    async def test_confirmacao_sem_alteracao(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Primeiro preenche todos os dados do membro para garantir que está completo
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE membros
            SET bairro_cidade='Centro', tempo_igreja='Mais de 2 anos', lider_celula='Joaquim',
                celula_atual='Betel', g12_pastoral='Pr. Raniel', fez_encontro='Sim',
                universidade_vida='Sim', capacitacao_destino='Sim'
            WHERE telefone = '558999999999'
            """
        )
        self.conn.commit()
        
        # Envia status sem_alteracao
        resumo_ia = (
            "[ATUALIZACAO_CADASTRAL]\n"
            "status=sem_alteracao\n"
            "[/ATUALIZACAO_CADASTRAL]"
        )
        
        payload = {
            "subscriber_id": 999999,
            "telefone": "558999999999",
            "nome": "Membro de Teste",
            "resumo_ia": resumo_ia
        }
        
        resultado = await ws.processar_atualizacao_cadastral(payload)
        
        self.assertEqual(resultado["status"], "ok")
        
        # Verifica no banco local
        cursor = self.conn.cursor()
        cursor.execute("SELECT status_cadastro, ultima_atualizacao_cadastral FROM membros WHERE id = ?", (resultado["membro_id"],))
        row = cursor.fetchone()
        self.assertEqual(row[0], "Completo")
        self.assertIsNotNone(row[1])


if __name__ == "__main__":
    unittest.main()
