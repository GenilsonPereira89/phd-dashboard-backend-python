from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras # Para RealDictCursor

# Importa as funções de conexão e inicialização do banco de dados
from database import get_db_connection, init_db

app = Flask(__name__)
# Configura o CORS para permitir requisições do seu frontend no Render
# Substitua 'https://phd-dashboard-frontend.onrender.com' pela URL real do seu frontend
CORS(app, resources={r"/api/*": {"origins": "https://phd-dashboard-frontend.onrender.com"}})

# Inicializa o banco de dados na inicialização do aplicativo Flask
# Isso garante que as tabelas sejam criadas e as configurações padrão inseridas
with app.app_context():
    init_db()

# Rota de teste simples para verificar se o backend está no ar
@app.route('/')
def home():
    return "Backend do Dashboard de Produção está online!"

# Rota para obter dados de produção (filtrados por ano e mês)
@app.route('/api/producoes', methods=['GET'])
def get_producoes():
    conn = None
    try:
        conn = get_db_connection()
        # Usa RealDictCursor para retornar linhas como dicionários
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        ano = request.args.get('ano')
        mes = request.args.get('mes')

        sql = 'SELECT * FROM producoes'
        params = []

        if ano and mes:
            # No PostgreSQL, usa SUBSTRING() em vez de substr() do SQLite.
            # Os placeholders para psycopg2 são %s, não ?.
            sql += ' WHERE SUBSTRING(data, 1, 4) = %s AND SUBSTRING(data, 6, 2) = %s'
            params = [ano, mes.zfill(2)] # zfill(2) garante que o mês tenha 2 dígitos (ex: '07')

        sql += ' ORDER BY data ASC'

        cursor.execute(sql, params)
        producoes = cursor.fetchall()
        return jsonify(producoes)
    except Exception as e:
        print(f"Erro ao buscar produções: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota para adicionar ou atualizar uma produção
@app.route('/api/producoes', methods=['POST'])
def add_producao():
    conn = None
    try:
        data = request.json['data']
        producao = request.json['producao']
        # CORREÇÃO AQUI: Converte o valor de is_excecao para booleano
        is_excecao = bool(request.json['is_excecao']) 
        operadores_no_dia = request.json['operadores_no_dia']

        conn = get_db_connection()
        cursor = conn.cursor()

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

# Rota para excluir uma produção
@app.route('/api/producoes/<string:data_producao>', methods=['DELETE'])
def delete_producao(data_producao):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # No PostgreSQL, os placeholders são %s, não ?.
        cursor.execute('DELETE FROM producoes WHERE data = %s', (data_producao,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Produção excluída com sucesso!'}), 200
        else:
            return jsonify({'message': 'Produção não encontrada.'}), 404
    except Exception as e:
        print(f"Erro ao excluir produção: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota para obter todas as configurações
@app.route('/api/config', methods=['GET'])
def get_all_configs():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT chave, valor FROM configuracoes')
        configs_raw = cursor.fetchall()
        configs = {item['chave']: item['valor'] for item in configs_raw}
        return jsonify(configs), 200
    except Exception as e:
        print(f"Erro ao buscar configurações: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota para atualizar uma configuração específica (ex: num_operadores_padrao)
@app.route('/api/config/<string:chave>', methods=['PUT'])
def update_config(chave):
    conn = None
    try:
        valor = request.json['valor']
        conn = get_db_connection()
        cursor = conn.cursor()
        # No PostgreSQL, os placeholders são %s, não ?.
        cursor.execute('UPDATE configuracoes SET valor = %s WHERE chave = %s', (valor, chave))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': f'Configuração {chave} atualizada com sucesso!'}), 200
        else:
            # Se a chave não existe, podemos inserir em vez de retornar 404
            # ou manter 404 se a intenção é só atualizar existentes
            # Por enquanto, vamos manter o comportamento de atualizar apenas.
            return jsonify({'message': f'Configuração {chave} não encontrada para atualização.'}), 404
    except Exception as e:
        print(f"Erro ao atualizar configuração: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)

