import os
import psycopg2
from psycopg2 import sql
# Importa o tipo de erro específico para colunas duplicadas e erros de programação
from psycopg2.errors import DuplicateColumn, ProgrammingError

def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não está definida nas variáveis de ambiente.")
    return psycopg2.connect(DATABASE_URL)

# Esta função init_db() criará as tabelas se elas não existirem
# e não tentará apagar dados.
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Criação da tabela 'producoes' com todas as colunas necessárias
        # Usa 'IF NOT EXISTS' para não gerar erro se a tabela já existir.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS producoes (
                id SERIAL PRIMARY KEY,
                data VARCHAR(10) UNIQUE NOT NULL,
                producao INTEGER NOT NULL,
                is_excecao BOOLEAN DEFAULT FALSE NOT NULL,
                operadores_no_dia INTEGER DEFAULT 13 NOT NULL,
                diaristas_no_dia INTEGER DEFAULT 0 NOT NULL
            );
        ''')
        print("Tabela 'producoes' verificada/criada.")
        conn.commit()

        # Criação da tabela 'configuracoes'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id SERIAL PRIMARY KEY,
                chave VARCHAR(50) UNIQUE NOT NULL,
                valor VARCHAR(255) NOT NULL
            );
        ''')
        print("Tabela 'configuracoes' verificada/criada.")
        conn.commit()

        # Insere configurações padrão se não existirem
        cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('num_operadores_padrao', '13') ON CONFLICT (chave) DO NOTHING;")
        cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('pacotes_por_operador_dia_meta', '450') ON CONFLICT (chave) DO NOTHING;")
        conn.commit()
        print("Configurações padrão verificadas/inseridas.")

    except Exception as e:
        print(f"Erro fatal na inicialização do banco de dados: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()