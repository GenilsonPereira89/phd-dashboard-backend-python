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
        # Obtém a URL do banco de dados das variáveis de ambiente
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            # Em ambiente local sem DATABASE_URL definida, você pode querer
            # um fallback para SQLite ou um PostgreSQL local.
            # Para o Render, esta exceção é importante.
            raise ValueError("A variável de ambiente DATABASE_URL não está definida.")

        # Faz o parse da URL do banco de dados para extrair os componentes
        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove a barra inicial '/'
            user=url.username,
            password=url.password,
            sslmode='require' # Recomendado para conexões seguras no Render
        )
        # Configura a conexão para retornar as linhas como dicionários (similar a sqlite3.Row)
        # Isso facilita o uso dos nomes das colunas como chaves
        conn.row_factory = psycopg2.extras.DictCursor
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise # Re-lança a exceção para que a aplicação saiba que algo deu errado

def init_db():
    """
    Inicializa o esquema do banco de dados (cria tabelas se não existirem).
    ATENÇÃO: Em ambientes de produção com PostgreSQL, é mais comum gerenciar
    o esquema do banco de dados usando ferramentas de migração (como Alembic
    para SQLAlchemy ou o sistema de migrações do Django) e executá-las
    separadamente (ex: como um comando de pre-deploy no Render ou via SSH).
    Executar init_db() a cada inicialização da aplicação é para simplicidade
    de teste e pode não ser ideal para ambientes com múltiplas instâncias
    ou deploys frequentes.
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

        conn.commit()
        print("Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
        # Em um aplicativo real, você pode querer registrar este erro de forma mais robusta
    finally:
        if conn:
            conn.close()