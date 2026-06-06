import os
import asyncio
import json
import sqlite3
import tempfile
import unittest


class HermesV2ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "hermes_v2_test.db")
        os.environ["SUPABASE_DB_URL"] = ""
        os.environ["HERMES_SQLITE_DB_PATH"] = self.db_path

        from hermes_v2.processor import process_botconversa_payload

        self.process = process_botconversa_payload

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop("HERMES_SQLITE_DB_PATH", None)

    def rows(self, table):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
        finally:
            conn.close()

    def test_visitante_creates_inbox_task_and_is_idempotent(self):
        payload = {
            "event_id": "evt-visitante-1",
            "subscriber_id": "123",
            "nome": "Carlos Visitante",
            "telefone": "55 (89) 99999-0000",
            "tipo_evento": "visitante",
            "mensagem": "Primeira visita no culto, deseja contato.",
        }

        first = self.process(payload)
        second = self.process(payload)

        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["intencao"], "visitante")
        self.assertEqual(first["papel_responsavel"], "Caleb")
        self.assertEqual(len(first["tarefas_criadas"]), 1)
        self.assertTrue(second["duplicate"])
        self.assertEqual(len(self.rows("inbox_pastoral")), 1)
        self.assertEqual(len(self.rows("tarefas_pastorais")), 1)
        self.assertEqual(len(self.rows("consolidacao_visitantes")), 1)

    def test_relatorio_celula_incompleto_returns_missing_fields(self):
        result = self.process({
            "event_id": "evt-relatorio-incompleto",
            "tipo_evento": "relatorio_celula",
            "nome": "Lider Teste",
            "mensagem": "Relatório de célula com visitantes 2",
            "campos": {"visitantes": 2},
        })

        self.assertEqual(result["intencao"], "relatorio_celula")
        self.assertIn("nome_celula", result["dados_faltando"])
        self.assertIn("presenca_membros", result["dados_faltando"])
        self.assertEqual(len(self.rows("relatorios_celulas")), 0)
        self.assertEqual(len(self.rows("tarefas_pastorais")), 1)

    def test_relatorio_celula_completo_is_recorded(self):
        result = self.process({
            "event_id": "evt-relatorio-completo",
            "tipo_evento": "relatorio_celula",
            "nome": "Lider Teste",
            "campos": {
                "nome_celula": "Shammah",
                "lider_nome": "Andre",
                "presenca_membros": 8,
                "visitantes": 2,
                "decisoes_fe": 1,
                "rede": "Jovens",
            },
        })

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["dados_faltando"], [])
        self.assertEqual(len(self.rows("relatorios_celulas")), 1)

    def test_sensitive_request_goes_to_human(self):
        result = self.process({
            "event_id": "evt-crise",
            "subscriber_id": "456",
            "nome": "Pessoa em crise",
            "telefone": "558988887777",
            "mensagem": "Estou em desespero e preciso falar com um humano.",
        })

        self.assertEqual(result["intencao"], "humano_necessario")
        self.assertEqual(result["nivel_urgencia"], "Urgente")
        self.assertEqual(result["prioridade"], 1)
        self.assertEqual(len(self.rows("tarefas_pastorais")), 1)

    def test_starlette_endpoint_returns_v2_response(self):
        from integrations.webhook_server import botconversa_v2_endpoint

        class Request:
            async def json(self):
                return {
                    "event_id": "evt-endpoint",
                    "subscriber_id": "789",
                    "nome": "Visitante Endpoint",
                    "telefone": "558988887766",
                    "tipo_evento": "visitante",
                    "mensagem": "Visitante deseja acompanhamento.",
                }

        response = asyncio.run(botconversa_v2_endpoint(Request()))
        body = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["version"], "2.0")
        self.assertEqual(body["intencao"], "visitante")


if __name__ == "__main__":
    unittest.main()
