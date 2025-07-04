import os
import psycopg2
from urllib.parse import urlparse
import psycopg2.extras # Necessário para RealDictCursor

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados PostgreSQL usando a variável
    de ambiente DATABASE_URL.
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("A variável de ambiente DATABASE_URL não está definida.")

        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            sslmode='require'
        )
        # A linha conn.row_factory = psycopg2.extras.DictCursor já foi removida/comentada
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise

def init_db():
    """
    Inicializa o esquema do banco de dados (cria tabelas se não existirem)
    e insere configurações padrão se não existirem.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Cria a tabela 'producoes'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS producoes (
                data TEXT PRIMARY KEY,
                producao INTEGER NOT NULL,
                is_excecao BOOLEAN NOT NULL,
                operadores_no_dia INTEGER NOT NULL
            );
        ''')

        # Cria a tabela 'configuracoes'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
        ''')

        # INSERE VALOR PADRÃO PARA num_operadores_padrao SE NÃO EXISTIR
        # ON CONFLICT DO NOTHING é a forma PostgreSQL de INSERT OR IGNORE
        cursor.execute('''
            INSERT INTO configuracoes (chave, valor)
            VALUES ('num_operadores_padrao', '13')
            ON CONFLICT (chave) DO NOTHING;
        ''')

        # Você pode adicionar outras configurações padrão aqui se tiver:
        # cursor.execute('''
        #     INSERT INTO configuracoes (chave, valor)
        #     VALUES ('pacotes_por_operador_dia_meta', '450')
        #     ON CONFLICT (chave) DO NOTHING;
        # ''')

        conn.commit()
        print("Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()
