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

# SUBSTITUA SUA FUNÇÃO init_db() INTEIRA POR ESTA:
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # PRIMEIRA TENTATIVA: Criar a tabela 'producoes' completa se ela NÃO EXISTE.
        # Isso é o ideal para garantir todas as colunas desde o início.
        try:
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
            print("Tabela 'producoes' verificada/criada (CREATE IF NOT EXISTS).")
            conn.commit()
        except Exception as e:
            print(f"Erro ao tentar CREATE TABLE IF NOT EXISTS producoes: {e}")
            conn.rollback() # Reverte em caso de erro

        # SEGUNDA TENTATIVA: Adicionar a coluna 'id' se ela não existir em uma tabela pré-existente malformada
        # Usa information_schema para verificar a existência da coluna de forma segura.
        try:
            cursor.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='producoes' AND column_name='id';")
            id_exists = cursor.fetchone()
            if not id_exists:
                print("Coluna 'id' não encontrada. Tentando adicionar...")
                # Adiciona a coluna 'id' como SERIAL PRIMARY KEY.
                # Se houver dados existentes, o PostgreSQL tentará preencher com valores padrão
                # ou pode exigir um valor padrão para as linhas existentes.
                # Esta é a parte mais delicada com dados existentes.
                cursor.execute('''
                    ALTER TABLE producoes
                    ADD COLUMN id SERIAL PRIMARY KEY;
                ''')
                print("Coluna 'id' adicionada à tabela 'producoes'.")
                conn.commit()
            else:
                print("Coluna 'id' já existe.")
        except ProgrammingError as e:
            # Captura erro se a tabela 'producoes' não existe, mas a esta altura já deveria ter sido criada.
            if "relation \"producoes\" does not exist" in str(e):
                print("Tabela 'producoes' ainda não existe. Ignorando ALTER COLUMN id.")
                conn.rollback()
            else:
                # Re-lança outros erros de programação que não sejam "tabela não existe"
                print(f"Erro de programação ao verificar/adicionar coluna 'id': {e}")
                raise e
        except Exception as e:
            print(f"Erro inesperado ao verificar/adicionar coluna 'id': {e}")
            conn.rollback()
            raise e

        # TERCEIRA TENTATIVA: Adicionar a coluna 'diaristas_no_dia' se ela não existir
        # Este bloco ainda é útil se a tabela já existia sem 'diaristas_no_dia'
        try:
            cursor.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='producoes' AND column_name='diaristas_no_dia';")
            diaristas_exists = cursor.fetchone()
            if not diaristas_exists:
                print("Coluna 'diaristas_no_dia' não encontrada. Tentando adicionar...")
                cursor.execute('''
                    ALTER TABLE producoes
                    ADD COLUMN diaristas_no_dia INTEGER DEFAULT 0 NOT NULL;
                ''')
                print("Coluna 'diaristas_no_dia' adicionada à tabela 'producoes'.")
                conn.commit()
            else:
                print("Coluna 'diaristas_no_dia' já existe.")
        except ProgrammingError as e:
            if "relation \"producoes\" does not exist" in str(e):
                print("Tabela 'producoes' ainda não existe. Ignorando ALTER COLUMN diaristas_no_dia.")
                conn.rollback()
            else:
                print(f"Erro de programação ao verificar/adicionar coluna 'diaristas_no_dia': {e}")
                raise e
        except DuplicateColumn: # Captura especificamente o erro de coluna duplicada
            print("Coluna 'diaristas_no_dia' já existe. Nenhuma alteração necessária.")
            conn.rollback() # Reverte a transação para limpar o estado de erro da conexão
        except Exception as e:
            print(f"Erro inesperado ao verificar/adicionar coluna 'diaristas_no_dia': {e}")
            conn.rollback()
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