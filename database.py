import os
import psycopg2
from psycopg2 import sql
# Importa o tipo de erro específico para colunas duplicadas
from psycopg2.errors import DuplicateColumn

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
        # Este comando usa 'IF NOT EXISTS' para não gerar erro se a tabela já existir.
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

        # Bloco ALTER TABLE: Tenta adicionar 'diaristas_no_dia' novamente como um fallback.
        # Este bloco é importante se a tabela já existia sem essa coluna.
        # A exceção de coluna duplicada será capturada e ignorada de forma mais robusta.
        try:
            cursor.execute('''
                ALTER TABLE producoes
                ADD COLUMN diaristas_no_dia INTEGER DEFAULT 0 NOT NULL;
            ''')
            print("Coluna 'diaristas_no_dia' adicionada à tabela 'producoes'.")
        except DuplicateColumn: # Captura especificamente o erro de coluna duplicada
            print("Coluna 'diaristas_no_dia' já existe. Nenhuma alteração necessária.")
            conn.rollback() # Reverte a transação para limpar o estado de erro da conexão
        except Exception as e:
            # Captura qualquer outro erro inesperado durante o ALTER TABLE
            print(f"Erro inesperado ao tentar adicionar coluna 'diaristas_no_dia': {e}")
            conn.rollback() # Reverte em caso de outros erros
            raise e # Re-lança se não for um erro de coluna duplicada

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
        raise e # Re-lança o erro principal de inicialização
    finally:
        if conn:
            conn.close()