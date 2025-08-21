# responsavel.py
# Rotas exclusivas para o perfil "responsável" usando Blueprint

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from urllib.parse import urlparse
from rotas.paleta_medicos import CORES_MEDICOS as cores_por_medico

responsavel_bp = Blueprint('responsavel', __name__)

def responsavel_routes(conectar_banco, login_requerido):

    @responsavel_bp.route('/listar', endpoint='listar')
    @login_requerido(['responsavel'])
    def listar():
        status = request.args.get('status', 'pendente')
        busca  = request.args.get('busca', '').strip()

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if busca:
            like = f"%{busca}%"

            # 1) Resultados da BUSCA (sem filtrar status)
            cursor.execute("""
                SELECT *
                FROM recados
                WHERE nome_paciente LIKE ? COLLATE NOCASE
                ORDER BY medico, data_cadastro DESC
            """, (like,))
            recados = cursor.fetchall()

            # 2) Contagem por status (APENAS dentro do resultado da busca)
            cursor.execute("""
                SELECT status, COUNT(*) AS total
                FROM recados
                WHERE nome_paciente LIKE ? COLLATE NOCASE
                GROUP BY status
            """, (like,))
            contagem_por_status_filtrado = {row['status']: row['total'] for row in cursor.fetchall()}

            # 3) Contagem global (panorama geral — opcional)
            cursor.execute("SELECT status, COUNT(*) AS total FROM recados GROUP BY status")
            contagem_por_status = {row['status']: row['total'] for row in cursor.fetchall()}

        else:
            # Comportamento original (filtra pelo status selecionado)
            cursor.execute("""
                SELECT *
                FROM recados
                WHERE status = ?
                ORDER BY medico, data_cadastro DESC
            """, (status,))
            recados = cursor.fetchall()

            # Contagem global por status
            cursor.execute("SELECT status, COUNT(*) AS total FROM recados GROUP BY status")
            contagem_por_status = {row['status']: row['total'] for row in cursor.fetchall()}

            contagem_por_status_filtrado = None  # não há busca

        # Agrupa por médico
        recados_por_medico = {}
        for recado in recados:
            medico = recado['medico']
            recados_por_medico.setdefault(medico, []).append(recado)

        quantidades_por_medico = {medico: len(lista) for medico, lista in recados_por_medico.items()}
        conexao.close()
        

        return render_template(
            'listar.html',
            recados_por_medico=recados_por_medico,
            status=status,
            cores=cores_por_medico,
            quantidades_por_medico=quantidades_por_medico,
            contagem_por_status=contagem_por_status,
            contagem_por_status_filtrado=contagem_por_status_filtrado,  # <<< NOVO
            busca=busca  # opcional: útil para manter o termo no campo
        )
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
            rows = cursor.fetchall()
        finally:
            conexao.close()

        recados = []
        for row in rows:
            recado = dict(row)
            try:
                nascimento = datetime.strptime(recado['data_nascimento'], '%Y-%m-%d')
                recado['data_nascimento_formatada'] = nascimento.strftime('%d/%m/%Y')
            except:
                recado['data_nascimento_formatada'] = recado['data_nascimento']
            recados.append(recado)

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

    
  
    @responsavel_bp.route('/mover_todos', methods=['POST'])
    @login_requerido(['responsavel'])
    def mover_todos():
        de_status   = (request.form.get('de_status') or 'pendente').strip().lower()
        para_status = (request.form.get('para_status') or '').strip().lower()
        busca       = (request.form.get('busca') or '').strip()

        # Regras claras por origem
        destinos_validos_por_origem = {
            'pendente':   {'imprimir', 'solicitado_ao_medico'},
            'respondido': {'entregue'},   # 👈 só “Entregue” em Respondido
        }

        if de_status not in destinos_validos_por_origem or \
        para_status not in destinos_validos_por_origem[de_status]:
            flash('Escolha um status de destino válido para este status.', 'danger')
            return redirect(url_for('responsavel.listar', status=de_status, busca=busca or None))

        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()

            # WHERE: de qual status e (opcional) busca por paciente
            where = ' WHERE status = ?'
            params_where = [de_status]
            if busca:
                where += ' AND nome_paciente LIKE ?'
                params_where.append(f'%{busca}%')

            if para_status == 'entregue':
                # Preencher "Entregue por"
                finalizador = session.get('usuario', '---')
                sql = f'UPDATE recados SET status = ?, finalizado_por = ?{where}'
                params = [para_status, finalizador] + params_where
            
            elif de_status == 'entregue' and para_status != 'entregue':
                sql = f'UPDATE recados SET status = ?, finalizado_por = NULL{where}'
                params = [para_status] + params_where
            
            else:
                sql = f'UPDATE recados SET status = ?{where}'
                params = [para_status] + params_where

            cursor.execute(sql, params)
            conexao.commit()
            movidos = cursor.rowcount or 0
        finally:
            conexao.close()

        flash(f'{movidos} recado(s) movido(s) para "{para_status.replace("_"," ")}".', 'success')
        return redirect(url_for('responsavel.listar', status=para_status, busca=busca or None))
    
    return responsavel_bp

def excluir_recados_antigos(conectar_banco):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    limite_data = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('DELETE FROM recados WHERE status = "entregue" AND data_cadastro < ?', (limite_data,))
    conexao.commit()
    conexao.close()
