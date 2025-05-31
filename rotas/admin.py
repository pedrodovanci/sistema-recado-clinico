# rotas/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

def admin_routes(conectar_banco, login_requerido):
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


    @admin_bp.route('/')
    @login_requerido(['admin'])
    def inicio():
        usuario = session['usuario']
        return render_template('admin/admin_inicio.html', usuario=usuario)


    @admin_bp.route('/usuarios')
    @login_requerido(['admin'])
    def listar_usuarios():
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('SELECT * FROM usuarios')
            usuarios = cursor.fetchall()
        finally:
            conexao.close()
        return render_template('admin/listar_usuarios.html', usuarios=usuarios)

    @admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
    @login_requerido(['admin'])
    def novo_usuario():
        if request.method == 'POST':
            nome = request.form['nome']
            username = request.form['username']
            senha = request.form['senha']
            perfil = request.form['perfil']

            conexao = conectar_banco()
            try:
                cursor = conexao.cursor()
                # Verificação de duplicidade
                cursor.execute('SELECT id FROM usuarios WHERE username = ?', (username,))
                if cursor.fetchone():
                    flash('Já existe um usuário com esse login.', 'danger')
                    return render_template('admin/novo_usuario.html')

                cursor.execute('INSERT INTO usuarios (nome, username, senha, perfil) VALUES (?, ?, ?, ?)',(nome, username, senha, perfil))
                conexao.commit() 
            finally:
                conexao.close()

            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('admin.listar_usuarios'))

        return render_template('admin/novo_usuario.html')

    @admin_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
    @login_requerido(['admin'])
    def editar_usuario(id):
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
            usuario = cursor.fetchone()

            if request.method == 'POST':
                nome = request.form['nome']
                username = request.form['username']
                senha = request.form['senha']
                perfil = request.form['perfil']

                if senha:
                    cursor.execute('''
                        UPDATE usuarios SET nome = ?, username = ?, senha = ?, perfil = ? WHERE id = ?
                    ''', (nome, username, senha, perfil, id))
                else:
                    cursor.execute('''
                        UPDATE usuarios SET nome = ?, username = ?, perfil = ? WHERE id = ?
                    ''', (nome, username, perfil, id))
                conexao.commit()
                flash('Usuário atualizado com sucesso!', 'success')
                return redirect(url_for('admin.listar_usuarios'))

        finally:
            conexao.close()

        return render_template('admin/editar_usuario.html', usuario=usuario)

    @admin_bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
    @login_requerido(['admin'])
    def excluir_usuario(id):
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('DELETE FROM usuarios WHERE id = ?', (id,))
            conexao.commit()
        finally:
            conexao.close()
        flash('Usuário excluído com sucesso.', 'success')
        return redirect(url_for('admin.listar_usuarios'))

    return admin_bp

