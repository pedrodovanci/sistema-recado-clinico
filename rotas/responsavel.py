# responsavel.py
# Rotas exclusivas para o perfil "responsável" usando Blueprint

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from urllib.parse import urlparse

responsavel_bp = Blueprint('responsavel', __name__)

def responsavel_routes(conectar_banco, login_requerido):

    @responsavel_bp.route('/listar', endpoint='listar')
    @login_requerido(['responsavel'])
    def listar():
        status = request.args.get('status', 'pendente')
        busca = request.args.get('busca', '').strip()

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if busca:
            cursor.execute('SELECT * FROM recados WHERE status = ? AND nome_paciente LIKE ? ORDER BY medico, prioridade', (status, f'%{busca}%'))
        else:
            cursor.execute('SELECT * FROM recados WHERE status = ? ORDER BY medico, data_cadastro', (status,))

        recados = cursor.fetchall()
        cursor.execute('SELECT status, COUNT(*) as total FROM recados GROUP BY status')
        contagem_por_status = {row['status']: row['total'] for row in cursor.fetchall()}

        recados_por_medico = {}
        for recado in recados:
            medico = recado['medico']
            recados_por_medico.setdefault(medico, []).append(recado)

        quantidades_por_medico = {
            medico: len(lista) for medico, lista in recados_por_medico.items()
        }

        cores_por_medico = {
            "Dr. Andre Salotto Rocha": "#3498db",
            "Dr. Fabiano Morais Nogueira": "#1abc9c",
            "Dr. Mario Jose Goes": "#3fdf0e",
            "Dr. Dionei Freitas de Morais": "#e67e22",
            "Dr. Felipe Oliveira Rodrigues": "#f546dd",
            "Dra. Raysa Moreira Aprigio": "#8e44ad",
            "Dr. Eduardo Carlos da Silva": "#e74c3c",
            "Dr. Lucas Crociati Meguins": "#16a085",
            "Dr. Sergio Luiz Ramin": "#f39c12",
            "Dr. Carlos Rocha": "#2c3e50",
            "Dr. Luis Fernando": "#141414",
            "Dr. Linoel Curado Valsechi": "#c0392b",
            "Dr. Ricardo Lourenço Caramanti": "#2980b9",
            "Dr. Alexandre Laranjeira Junior": "#27ae60",
            "Dr. Caique Alberto Dosualdo": "#d35400",
            "Dr. Demosthenes Santana": "#34495e",
            "Dr. Matheus Laurenti": "#0ef8c9",
            "Dr. Vinicius Reis": "#0A0124",
            "Dr. Sebastiao Silva":"#410000",
            "Dr. Guilherme Perassa Gasque":"#022400"
        }

        conexao.close()

        return render_template('listar.html',
                               recados_por_medico=recados_por_medico,
                               status=status,
                               cores=cores_por_medico,
                               quantidades_por_medico=quantidades_por_medico,
                               contagem_por_status=contagem_por_status)

    @responsavel_bp.route('/recado/<int:id>', endpoint='detalhar_recado')
    @login_requerido(['responsavel'])
    def detalhar_recado(id):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM recados WHERE id = ?', (id,))
        recado = cursor.fetchone()
        conexao.close()

        if not recado:
            flash('Recado não encontrado.', 'danger')
            return redirect(url_for('responsavel.listar'))

        return render_template('detalhar_recado.html', recado=recado)

    @responsavel_bp.route('/recado/<int:id>/editar', methods=['GET', 'POST'])
    @login_requerido(['responsavel'])
    def editar_recado(id):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM recados WHERE id = ?', (id,))
        recado = cursor.fetchone()

        if request.method == 'POST':
            cursor.execute('''
                UPDATE recados SET medico = ?, nome_paciente = ?, telefone = ?, status = ?, prioridade = ?, descricao = ?
                WHERE id = ?
            ''', (
                request.form['medico'],
                request.form['nome_paciente'],
                request.form['telefone'],
                request.form['status'],
                request.form['prioridade'],
                request.form['mensagem'],
                id
            ))
            conexao.commit()
            conexao.close()
            return redirect(url_for('responsavel.detalhar_recado', id=id))

        conexao.close()
        return render_template('editar_recado.html', recado=recado)

    @responsavel_bp.route('/recado/<int:id>/excluir', methods=['POST'])
    @login_requerido(['responsavel'])
    def excluir_recado(id):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('DELETE FROM recados WHERE id = ?', (id,))
        conexao.commit()
        conexao.close()
        flash('Recado excluído com sucesso!', 'success')
        return redirect(url_for('responsavel.listar'))

    @responsavel_bp.route('/imprimir_recado/<int:id>', endpoint='imprimir_recado')
    @login_requerido(['responsavel'])
    def imprimir_recado(id):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM recados WHERE id = ?', (id,))
        row = cursor.fetchone()
        conexao.close()

        if row:
            recado = dict(row)
            try:
                nascimento = datetime.strptime(recado['data_nascimento'], '%Y-%m-%d')
                recado['data_nascimento_formatada'] = nascimento.strftime('%d/%m/%Y')
                cadastro = datetime.strptime(recado['data_cadastro'], '%Y-%m-%d %H:%M:%S')
                recado['data_cadastro_formatada'] = cadastro.strftime('%d/%m/%Y %H:%M')
            except:
                recado['data_nascimento_formatada'] = recado['data_nascimento']
                recado['data_cadastro_formatada'] = recado['data_cadastro']
            return render_template('imprimir_lista.html', recados=[recado])

        return 'Recado não encontrado.', 404

    @responsavel_bp.route('/imprimir/<status>', endpoint='imprimir')
    @login_requerido(['responsavel'])
    def imprimir(status):
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('SELECT * FROM recados WHERE status = ? ORDER BY medico, prioridade', (status,))
            recados = cursor.fetchall()
        finally:
            conexao.close()
        return render_template('imprimir_lista.html', recados=recados)

    @responsavel_bp.route('/excluir_todos/<status>', methods=['POST'])
    @login_requerido(['responsavel'])
    def excluir_todos(status):
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()
            cursor.execute('DELETE FROM recados WHERE status = ?', (status,))
            conexao.commit()
        finally:
            conexao.close()
        flash(f'Todos os recados com status "{status}" foram excluídos.', 'success')
        return redirect(url_for('responsavel.listar', status=status))

    return responsavel_bp

def excluir_recados_antigos(conectar_banco):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    limite_data = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('DELETE FROM recados WHERE status = "entregue" AND data_cadastro < ?', (limite_data,))
    conexao.commit()
    conexao.close()
