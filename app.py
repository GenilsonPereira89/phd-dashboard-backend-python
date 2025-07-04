# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
# Importa as funções de conexão com o banco de dados do novo arquivo 'database.py'
from database import init_db, get_db_connection
import psycopg2 # Importa psycopg2 para tratamento de erros específicos
import psycopg2.extras # Necessário para RealDictCursor, usado em get_producoes e get_config

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas, permitindo que seu frontend se conecte

# Inicializa o banco de dados quando a aplicação Flask inicia.
# Leia os comentários no arquivo database.py sobre o uso de init_db() em produção.
with app.app_context():
    init_db()

# --- Rotas para Produções ---
@app.route('/api/producoes', methods=['POST'])
def add_producao():
    conn = None
    try:
        data = request.json['data']
        producao = request.json['producao']
        is_excecao = request.json['is_excecao']
        operadores_no_dia = request.json['operadores_no_dia']

        conn = get_db_connection()
        cursor = conn.cursor()

        # CORREÇÃO AQUI: Usa %s para placeholders e ON CONFLICT para upsert no PostgreSQL
        cursor.execute('''
            INSERT INTO producoes (data, producao, is_excecao, operadores_no_dia)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (data) DO UPDATE SET
                producao = EXCLUDED.producao,
                is_excecao = EXCLUDED.is_excecao,
                operadores_no_dia = EXCLUDED.operadores_no_dia
        ''', (data, producao, is_excecao, operadores_no_dia))
        
        conn.commit()
        return jsonify({'message': 'Produção salva/atualizada com sucesso!'}), 201
    except Exception as e:
        print(f"Erro ao salvar produção: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/producoes', methods=['POST'])
def add_or_update_producao():
    data = request.json.get('data')
    producao = request.json.get('producao')
    is_excecao = request.json.get('is_excecao')
    operadores_no_dia = request.json.get('operadores_no_dia')

    # Validação básica dos dados de entrada
    if not all([data, producao is not None, is_excecao is not None, operadores_no_dia is not None]):
        return jsonify({'error': 'Dados incompletos. Forneça data, producao, is_excecao e operadores_no_dia.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Tenta inserir. Se a data já existe (ON CONFLICT), atualiza o registro existente.
        # A sintaxe ON CONFLICT é válida para PostgreSQL.
        # Usa %s para placeholders e RETURNING para obter o 'data' da linha afetada.
        sql = '''
            INSERT INTO producoes (data, producao, is_excecao, operadores_no_dia)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(data) DO UPDATE SET
                producao = EXCLUDED.producao,
                is_excecao = EXCLUDED.is_excecao,
                operadores_no_dia = EXCLUDED.operadores_no_dia
            RETURNING data; -- Retorna a chave primária da linha inserida/atualizada
        '''
        cursor.execute(sql, (data, producao, is_excecao, operadores_no_dia))
        conn.commit() # Confirma as alterações no banco de dados

        # Obtém o resultado do RETURNING
        result = cursor.fetchone()
        return jsonify({'message': 'Produção salva com sucesso!', 'data_id': result[0] if result else None}), 201
    except psycopg2.Error as e: # Captura erros específicos do Psycopg2 (erros de banco de dados)
        conn.rollback() # Desfaz a transação em caso de erro
        return jsonify({'error': str(e)}), 500
    except Exception as e: # Captura outros erros gerais
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/producoes/<string:data>', methods=['DELETE'])
def delete_producao(data):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Usa %s para placeholders no DELETE
        cursor.execute('DELETE FROM producoes WHERE data = %s', (data,))
        conn.commit()

        if cursor.rowcount == 0: # Verifica se alguma linha foi afetada pela exclusão
            return jsonify({'message': 'Registro não encontrado para exclusão.'}), 404

        return jsonify({'message': 'Registro excluído com sucesso!'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# --- Rotas para Configurações ---

@app.route('/api/config', methods=['GET'])
def get_config():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('SELECT chave, valor FROM configuracoes')
        configs = cursor.fetchall()

        config_dict = {row['chave']: row['valor'] for row in configs}
        return jsonify(config_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/config/<string:chave>', methods=['PUT'])
def update_config(chave):
    valor = request.json.get('valor')

    if valor is None:
        return jsonify({'error': 'Valor da configuração não fornecido.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Usa %s para placeholders no UPDATE
        cursor.execute('UPDATE configuracoes SET valor = %s WHERE chave = %s', (valor, chave))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'message': 'Chave de configuração não encontrada para atualização.'}), 404

        return jsonify({'message': f"Configuração '{chave}' atualizada com sucesso!"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Inicia o servidor Flask para desenvolvimento local.
    # No Render, o servidor será iniciado pelo Gunicorn (com o comando 'gunicorn app:app').
    # A porta é obtida da variável de ambiente PORT (usada pelo Render) ou padrão 5000.
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))