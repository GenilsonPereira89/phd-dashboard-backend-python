import os
import psycopg2
from psycopg2 import sql

# Sua função get_db_connection() deve estar ANTES de init_db()
def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não está definida nas variáveis de ambiente.")
    return psycopg2.connect(DATABASE_URL)

# SUBSTITUA SUA FUNÇÃO init_db() INTEIRA POR ESTA:
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Criação da tabela 'producoes' com todas as colunas necessárias
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

        # Bloco ALTER TABLE: Tenta adicionar 'diaristas_no_dia' novamente como um fallback
        # Isso garante que a coluna será adicionada mesmo se a tabela já existia sem ela (e com 'id').
        try:
            cursor.execute('''
                ALTER TABLE producoes
                ADD COLUMN diaristas_no_dia INTEGER DEFAULT 0 NOT NULL;
            ''')
            print("Coluna 'diaristas_no_dia' adicionada à tabela 'producoes'.")
        except psycopg2.ProgrammingError as e:
            if "column \"diaristas_no_dia\" already exists" in str(e):
                print("Coluna 'diaristas_no_dia' já existe. Nenhuma alteração necessária.")
                conn.rollback()
            else:
                raise e
        except Exception as e:
            print(f"Erro ao tentar adicionar coluna 'diaristas_no_dia' (pode ser ignorado se já existe): {e}")
            raise e

        # Criação da tabela 'configuracoes'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id SERIAL PRIMARY KEY,
                chave VARCHAR(50) UNIQUE NOT NULL,
                valor VARCHAR(255) NOT NULL
            );
        ''')
        print("Tabela 'configuracoes' verificada/criada.")

        # Insere configurações padrão se não existirem
        cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('num_operadores_padrao', '13') ON CONFLICT (chave) DO NOTHING;")
        cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('pacotes_por_operador_dia_meta', '450') ON CONFLICT (chave) DO NOTHING;")
        conn.commit()
        print("Configurações padrão verificadas/inseridas.")

    except Exception as e:
        print(f"Erro na inicialização do banco de dados: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()