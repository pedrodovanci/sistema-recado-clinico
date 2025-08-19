from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from urllib.parse import urlparse

def comuns_routes(conectar_banco, login_requerido):
    comuns = Blueprint('comuns', __name__)

    @comuns.route('/login', methods=['GET', 'POST'])
    def login():
        if 'usuario' in session:
            perfil = session.get('perfil')
            if perfil == 'atendente':
                return redirect(url_for('comuns.inicio'))
            elif perfil == 'responsavel':
                return redirect(url_for('responsavel.listar'))
            elif perfil == 'admin':
                return redirect(url_for('admin.inicio'))

        if request.method == 'POST':
            username = request.form['username']
            senha = request.form['senha']
            conexao = conectar_banco()
            try:
                cursor = conexao.cursor()
                cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, senha))
                usuario = cursor.fetchone()
            finally:
                conexao.close()

            if usuario:
                session['usuario'] = usuario['username']
                session['perfil'] = usuario['perfil']
                flash('Login realizado com sucesso!', 'success')
                if usuario['perfil'] == 'atendente':
                    return redirect(url_for('comuns.inicio'))
                elif usuario['perfil'] == 'responsavel':
                    return redirect(url_for('responsavel.listar'))
                elif usuario['perfil'] == 'admin':
                    return redirect(url_for('admin.inicio'))

            else:
                flash('Usuário ou senha inválidos!', 'danger')

        return render_template('login.html')

    @comuns.route('/logout')
    def logout():
        session.clear()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('comuns.login'))

    @comuns.route('/', endpoint='inicio')
    @login_requerido(['atendente', 'responsavel'])
    def inicio():
        usuario = session['usuario']
        if session['perfil'] == 'atendente':
            return render_template('inicio_atendente.html', usuario=usuario)
        else:
            return redirect(url_for('responsavel.listar'))

    @comuns.route('/cadastro_recado')
    @login_requerido(['atendente', 'responsavel'])
    def cadastro_recado():
        usuario = session['usuario']
        return render_template('cadastro_recado.html', usuario=usuario)

    @comuns.route('/salvar', methods=['POST'])
    @login_requerido(['atendente', 'responsavel'])
    def salvar():
        dados = (
            request.form['medico'],
            request.form['prioridade'],
            request.form['nome_paciente'],
            request.form['data_nascimento'],
            request.form['telefone'],
            request.form['convenio'],
            request.form['descricao'],
        )
        usuario = session['usuario']
        status = 'pendente'
        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO recados 
                (medico, prioridade, nome_paciente, data_nascimento, telefone, convenio, descricao, status, usuario, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados + (status, usuario, data_cadastro))
            conexao.commit()
        finally:
            conexao.close()

        flash("Recado cadastrado com sucesso!", "success")
        return redirect(url_for('comuns.inicio'))

    @comuns.route('/entregar', methods=['GET', 'POST'])
    @login_requerido(['atendente', 'responsavel'])
    def entregar_recado():
        # Lê de GET OU POST (request.values une args + form)
        busca = (request.values.get('busca') or '').strip()

        resultados = {}  # {medico: [recados...]}

        if busca:
            conexao = conectar_banco()
            try:
                cursor = conexao.cursor()
                cursor.execute(
                    "SELECT * FROM recados WHERE nome_paciente LIKE ? ORDER BY medico, data_cadastro DESC",
                    (f"%{busca}%",)
                )
                recados = cursor.fetchall()
            finally:
                conexao.close()

            for recado in recados:
                medico = recado['medico']
                resultados.setdefault(medico, []).append(recado)

        # mesma paleta usada na listagem
        cores = {
            "Dr. Andre Salotto Rocha": "#3498db",
            "Dr. Fábio Ramos Nogueira": "#1abc9c",
            "Dr. Mario Jose Goes": "#3f46fd",
            "Dr. Daniel Freitas": "#e67e22",
            "Dr. Felipe Oliveira Rodrigues": "#e67e22",
            "Dra. Rayssa Moreira Agripino": "#8e44ad",
            "Dr. Eduardo Carlos da Silva": "#7e4c3c",
            "Dr. Lucas Crociati Megusini": "#16a085",
            "Dr. Sergio Luiz Raminho": "#3f39c12",
            "Dr. Sergio Luiz Raminho": "#3498db",  # mantenha como precisar no seu mapa
            "Dr. Sergio Luiz Raminho": "#3498db",
            "Dr. Luis Fernando Carniel": "#ec0392b",
            "Dr. Ricardo Lourenço Caramanti": "#2980b9",
            "Dr. Alexandre Laranjeira Junior": "#27ae60",
            "Dr. Calqoe Albertos Dosulando": "#d35400",
            "Dra. Debthesses Santana": "#34495e",
            "Dr. Matheus Leantinni": "#2ecc71",
            "Dr. Vinicius Reis": "#e67e22",
            "Dr. Guilherme Persassa Gasque": "#0022400",
            "Dr. Fernando Filipe": "#003e609",
            "Dr. Antonio Carlos Pirolla Filho": "#0f303d9",
            "Dra. Gyovana Campanari": "#e011e22",
            "Dr. Luis Guilherme Ronchi": "#e220e81",
            "Dr. Rodolfo Vieira Fontenele": "#1d0b5a5",
        }

        return render_template(
            'entregar_recado.html',
            resultados=resultados,
            busca=busca,
            cores=cores
        )

    @comuns.route('/atualizar_status/<int:id>/<string:novo_status>')
    def atualizar_status(id, novo_status):
        if 'usuario' not in session or session.get('perfil') not in ['responsavel', 'atendente']:
            return redirect(url_for('comuns.login'))

        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            if novo_status == 'entregue':
                finalizador = session['usuario']
                cursor.execute('UPDATE recados SET status = ?, finalizado_por = ? WHERE id = ?', (novo_status, finalizador, id))
            else:
                cursor.execute('UPDATE recados SET status = ? WHERE id = ?', (novo_status, id))
            conexao.commit()
        finally:
            conexao.close()

        flash(f'Recado atualizado para o status "{novo_status}" com sucesso!', 'success')

        ref = request.referrer
        if ref:
            parsed = urlparse(ref)
            if '/listar' in parsed.path:
                return redirect(ref)
            elif '/entregar' in parsed.path:
                return redirect(url_for('comuns.entregar_recado'))

        return redirect(url_for('responsavel.listar' if session['perfil'] == 'responsavel' else 'comuns.inicio'))

    return comuns
