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

        # Criação da tabela 'producoes' com todas as colunas necessárias
        # Este comando usa 'IF NOT EXISTS' para não gerar erro se a tabela já existir.
        # Se a tabela já existe e tem a coluna 'id' como PK, este CREATE TABLE será ignorado.
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

        # REMOVIDO: O BLOCO QUE TENTAVA ADICIONAR A COLUNA 'id' COM ALTER TABLE.
        # Os logs confirmam que 'id' já existe como PRIMARY KEY, então este bloco era o problema.

        # TENTATIVA: Adicionar a coluna 'diaristas_no_dia' se ela não existir
        # Usa information_schema para verificar a existência da coluna de forma segura.
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
            # Este erro pode ocorrer se a tabela 'producoes' não existisse (mas agora ela deveria existir).
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

        # Criação da tabela 'configuracoes' (sempre com IF NOT EXISTS)
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