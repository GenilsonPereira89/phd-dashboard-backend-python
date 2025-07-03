# app.py
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, get_db_connection
import os

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas, permitindo que seu frontend se conecte

# Inicializa o banco de dados quando a aplicação Flask inicia
with app.app_context():
    init_db()

# --- Rotas para Produções ---

@app.route('/api/producoes', methods=['GET'])
def get_producoes():
    conn = get_db_connection()
    cursor = conn.cursor()

    ano = request.args.get('ano')
    mes = request.args.get('mes')

    sql = 'SELECT * FROM producoes'
    params = []

    if ano and mes:
        # Filtra por ano e mês (SQLite substr é 1-based index)
        sql += ' WHERE substr(data, 1, 4) = ? AND substr(data, 6, 2) = ?'
        params = [ano, mes.zfill(2)] # zfill(2) garante que o mês tenha 2 dígitos (ex: '7' vira '07')

    sql += ' ORDER BY data ASC'

    cursor.execute(sql, params)
    producoes = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in producoes]) # Converte para lista de dicionários

@app.route('/api/producoes', methods=['POST'])
def add_or_update_producao():
    data = request.json.get('data')
    producao = request.json.get('producao')
    is_excecao = request.json.get('is_excecao')
    operadores_no_dia = request.json.get('operadores_no_dia')

    if not all([data, producao is not None, is_excecao is not None, operadores_no_dia is not None]):
        return jsonify({'error': 'Dados incompletos. Forneça data, producao, is_excecao e operadores_no_dia.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Tenta inserir. Se a data já existe, atualiza.
    sql = '''
        INSERT INTO producoes (data, producao, is_excecao, operadores_no_dia)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(data) DO UPDATE SET
            producao = EXCLUDED.producao,
            is_excecao = EXCLUDED.is_excecao,
            operadores_no_dia = EXCLUDED.operadores_no_dia
    '''
    try:
        cursor.execute(sql, (data, producao, is_excecao, operadores_no_dia))
        conn.commit()
        return jsonify({'message': 'Produção salva com sucesso!', 'id': cursor.lastrowid}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/producoes/<string:data>', methods=['DELETE'])
def delete_producao(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM producoes WHERE data = ?', (data,))
    conn.commit()

    if cursor.rowcount == 0: # Verifica se alguma linha foi afetada
        conn.close()
        return jsonify({'message': 'Registro não encontrado para exclusão.'}), 404

    conn.close()
    return jsonify({'message': 'Registro excluído com sucesso!'}), 200

# --- Rotas para Configurações ---

@app.route('/api/config', methods=['GET'])
def get_config():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT chave, valor FROM configuracoes')
    configs = cursor.fetchall()
    conn.close()

    config_dict = {row['chave']: row['valor'] for row in configs}
    return jsonify(config_dict)

@app.route('/api/config/<string:chave>', methods=['PUT'])
def update_config(chave):
    valor = request.json.get('valor')

    if valor is None:
        return jsonify({'error': 'Valor da configuração não fornecido.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE configuracoes SET valor = ? WHERE chave = ?', (valor, chave))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'message': 'Chave de configuração não encontrada para atualização.'}), 404

    conn.close()
    return jsonify({'message': f"Configuração '{chave}' atualizada com sucesso!"}), 200

if __name__ == '__main__':
    # Inicia o servidor Flask.
    # No Render, o servidor será iniciado de outra forma (gunicorn),
    # mas para testes locais, este é o comando.
    app.run(debug=True, port=os.environ.get('PORT', 5000)) # Porta padrão 5000 para Flask