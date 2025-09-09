from flask import Flask, session
from datetime import datetime
import sqlite3
import os

from rotas import comuns_routes, responsavel_routes, admin_routes

app = Flask(__name__)
app.secret_key = 'chave-secreta'

# Banco de dados
def conectar_banco():
    # usa var de ambiente RECADOS_DB se existir; senão usa o banco local
    caminho = os.getenv("RECADOS_DB", "recados.db")
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao

def criar_banco():
    conexao = sqlite3.connect('recados.db')
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medico TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            nome_paciente TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            telefone TEXT NOT NULL,
            convenio TEXT,
            descricao TEXT,
            status TEXT DEFAULT 'pendente',
            usuario TEXT NOT NULL,
            data_cadastro TEXT NOT NULL,
            finalizado_por TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)
    conexao.commit()
    conexao.close()

# Login requerido por perfil
def login_requerido(perfis_permitidos):
    from functools import wraps
    from flask import redirect, url_for, flash
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'usuario' not in session or session.get('perfil') not in perfis_permitidos:
                flash("Faça login para acessar essa página.", "warning")
                return redirect(url_for('comuns.login'))
            return func(*args, **kwargs)
        return wrapper
    return decorador


# Filtros de data
@app.template_filter('format_data')
def formatar_data_br(data_str):
    """Formata data para o padrão brasileiro dd/mm/aaaa"""
    if not data_str:
        return ''
    try:
        # Tenta formato completo com hora
        data_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
        return data_obj.strftime('%d/%m/%Y')
    except:
        try:
            # Tenta formato apenas data
            data_obj = datetime.strptime(data_str, '%Y-%m-%d')
            return data_obj.strftime('%d/%m/%Y')
        except:
            return data_str

@app.template_filter('format_data_hora')
def formatar_data_hora_br(data_str):
    """Formata data e hora para o padrão brasileiro dd/mm/aaaa hh:mm"""
    if not data_str:
        return ''
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
        return data_obj.strftime('%d/%m/%Y %H:%M')
    except:
        return data_str

@app.template_filter('strftime')
def strftime_filter(data_str, formato='%d/%m/%Y'):
    """Filtro personalizado para formatação de datas"""
    if not data_str:
        return ''
    try:
        if isinstance(data_str, str):
            # Tenta diferentes formatos de entrada
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
                try:
                    data_obj = datetime.strptime(data_str, fmt)
                    return data_obj.strftime(formato)
                except:
                    continue
        return data_str
    except:
        return data_str

# Registrar os blueprints
app.register_blueprint(comuns_routes(conectar_banco, login_requerido))
app.register_blueprint(responsavel_routes(conectar_banco, login_requerido))
app.register_blueprint(admin_routes(conectar_banco, login_requerido))  

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return "<h1>404 - Página não encontrada</h1>", 404

#  Executar
if __name__ == '__main__':
    criar_banco()
    app.run(host='0.0.0.0', port=5000, debug=True)

