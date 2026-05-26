"""
Migração: adiciona a tabela 'delegacoes' ao banco pastoral.db
Responsável: Rute (supervisão de tarefas delegadas pelo Pastor)

A tabela rastreia tudo que o Pastor passou para alguém da equipe e
precisa supervisionar — ex: "Joaquim ficou de fazer a arte do culto".

Rode uma vez:  python database/add_delegacoes.py
É seguro rodar de novo (usa CREATE TABLE IF NOT EXISTS).
"""

import sqlite3
import os
from datetime import datetime, timedelta


def migrar():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "pastoral.db")

    print(f"Adicionando tabela 'delegacoes' em: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabela de Delegações (Rute supervisiona)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delegacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarefa TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        area TEXT CHECK (area IN ('Louvor', 'Midia', 'Obreiros', 'Jovens', 'Kids',
                                  'Consolidacao', 'Tecnologia', 'Financeiro', 'Cafe',
                                  'Artes', 'Celulas', 'Geral', 'Outros')) DEFAULT 'Geral',
        data_delegacao TEXT NOT NULL,
        prazo TEXT,
        status TEXT CHECK (status IN ('Pendente', 'Em andamento', 'Concluida', 'Atrasada'))
                 DEFAULT 'Pendente',
        prioridade TEXT CHECK (prioridade IN ('Alta', 'Media', 'Baixa')) DEFAULT 'Media',
        observacoes TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed inicial — exemplos para o painel não nascer vazio
    cursor.execute("SELECT COUNT(*) FROM delegacoes")
    if cursor.fetchone()[0] == 0:
        hoje = datetime.now()
        amanha = hoje + timedelta(days=1)
        dados = [
            ('Criar a arte de divulgação do culto de domingo', 'Joaquim', 'Midia',
             hoje.strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d'),
             'Pendente', 'Alta', 'Postar no @filadelfiacorrente'),
            ('Fazer contato de consolidacao com Lucas Nogueira', 'Luciane', 'Consolidacao',
             hoje.strftime('%Y-%m-%d'), amanha.strftime('%Y-%m-%d'),
             'Pendente', 'Alta', 'Contato em ate 24h apos a visita'),
            ('Organizar escala de louvor da Rede Jovem', 'Ramon', 'Louvor',
             hoje.strftime('%Y-%m-%d'), (hoje + timedelta(days=3)).strftime('%Y-%m-%d'),
             'Em andamento', 'Media', 'Confirmar musicos ate quinta'),
        ]
        cursor.executemany("""
        INSERT INTO delegacoes (tarefa, responsavel, area, data_delegacao, prazo, status, prioridade, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, dados)
        print("Dados iniciais de delegacoes inseridos.")

    conn.commit()
    conn.close()
    print("Tabela 'delegacoes' criada com sucesso!")


if __name__ == "__main__":
    migrar()
