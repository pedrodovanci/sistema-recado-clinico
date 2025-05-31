from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from urllib.parse import urlparse

def comuns_routes(conectar_banco, login_requerido):
    comuns = Blueprint('comuns', __name__)

    @comuns.route('/login', methods=['GET', 'POST'])
    def login():
        if 'usuario' in session:
            perfil = session.get('perfil')
            return redirect(url_for('comuns.inicio' if perfil == 'atendente' else 'responsavel.listar'))

        if request.method == 'POST':
            username = request.form['username']
            senha = request.form['senha']
            conexao = conectar_banco()
            cursor = conexao.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, senha))
            usuario = cursor.fetchone()
            conexao.close()

            if usuario:
                session['usuario'] = usuario['username']
                session['perfil'] = usuario['perfil']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('comuns.inicio' if usuario['perfil'] == 'atendente' else 'responsavel.listar'))
            else:
                flash('Usuário ou senha inválidos!', 'danger')

        return render_template('login.html')
    # Rota para logout (encerra sessão)
    @comuns.route('/logout')
    def logout():
        session.clear()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('comuns.login'))

    # Rota principal que redireciona atendente para dashboard e responsável para listagem
    @comuns.route('/', endpoint='inicio')
    @login_requerido(['atendente', 'responsavel'])
    def inicio():
        usuario = session['usuario']
        if session['perfil'] == 'atendente':
            return render_template('inicio_atendente.html', usuario=usuario)
        else:
            return redirect(url_for('responsavel.listar'))

    # Exibe formulário de cadastro de novo recado    
    @comuns.route('/cadastro_recado')
    @login_requerido(['atendente', 'responsavel'])
    def cadastro_recado():
            usuario = session['usuario']
            return render_template('cadastro_recado.html', usuario=usuario)

    # Salva novo recado enviado pelo formulário de cadastro
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
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO recados 
            (medico, prioridade, nome_paciente, data_nascimento, telefone, convenio, descricao, status, usuario, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados + (status, usuario, data_cadastro))
        conexao.commit()
        conexao.close()
        flash("Recado cadastrado com sucesso!", "success")
            
        return redirect(url_for('comuns.inicio'))

    # Permite busca de recados para entrega e finalização por nome
    @comuns.route('/entregar', methods=['GET', 'POST'])
    @login_requerido(['atendente', 'responsavel'])
    def entregar_recado():
        resultados = {}
        busca = ''
        if request.method == 'POST':
            busca = request.form['busca'].strip()
        if busca:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            cursor.execute('SELECT * FROM recados WHERE nome_paciente LIKE ?', (f'%{busca}%',))
            recados = cursor.fetchall()
            conexao.close()

            for recado in recados:
                status = recado['status']
                medico = recado['medico']  # <- agora sempre definido

                if status not in resultados:
                    resultados[status] = {}

                if medico not in resultados[status]:
                    resultados[status][medico] = []

                resultados[status][medico].append(recado)


        return render_template('entregar_recado.html', resultados=resultados, busca=busca)
    
    # Atualizar status de um recado
    @comuns.route('/atualizar_status/<int:id>/<string:novo_status>')
    def atualizar_status(id, novo_status):
        if 'usuario' not in session or session.get('perfil') not in ['responsavel', 'atendente']:
            return redirect(url_for('comuns.login'))

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if novo_status == 'entregue':
            finalizador = session['usuario']
            cursor.execute('UPDATE recados SET status = ?, finalizado_por = ? WHERE id = ?', (novo_status, finalizador, id))
        else:
            cursor.execute('UPDATE recados SET status = ? WHERE id = ?', (novo_status, id))

            conexao.commit()
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
