# database.py
import sqlite3
import os

# Define o caminho para o arquivo do banco de dados.
# No Render, este arquivo precisará estar em um "Disk" (volume persistente).
# Usaremos '/mnt/data/producao.db' como o caminho no Render.
# Para desenvolvimento local, ele criará 'producao.db' na pasta do backend.
DB_PATH = '/mnt/data/producao.db' if os.environ.get('RENDER') else 'producao.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Isso permite acessar colunas como dicionários (ex: row['data'])
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Cria a tabela 'producoes' se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS producoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE NOT NULL,
            producao INTEGER NOT NULL,
            is_excecao INTEGER NOT NULL,
            operadores_no_dia INTEGER NOT NULL
        )
    ''')

    # Cria a tabela 'configuracoes' se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY NOT NULL,
            valor TEXT NOT NULL
        )
    ''')

    # Insere as configurações padrão se elas ainda não existirem
    # Usamos INSERT OR IGNORE para não dar erro se já existirem
    cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)", ('num_operadores_padrao', '13'))
    cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)", ('pacotes_por_operador_dia_meta', '450'))

    conn.commit()
    conn.close()
    print("Banco de dados inicializado e tabelas criadas/verificadas.")

if __name__ == '__main__':
    # Se este script for executado diretamente, ele inicializa o DB
    init_db()