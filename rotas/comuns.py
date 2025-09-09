from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from rotas.paleta_medicos import CORES_MEDICOS as cores_por_medico

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
        # Converter data de nascimento do formato brasileiro para formato do banco
        data_nascimento_input = request.form['data_nascimento']
        try:
            # Tentar converter de dd/mm/aaaa para aaaa-mm-dd
            data_obj = datetime.strptime(data_nascimento_input, '%d/%m/%Y')
            data_nascimento_db = data_obj.strftime('%Y-%m-%d')
        except ValueError:
            # Se falhar, tentar formato original (aaaa-mm-dd)
            try:
                data_obj = datetime.strptime(data_nascimento_input, '%Y-%m-%d')
                data_nascimento_db = data_nascimento_input
            except ValueError:
                flash('Formato de data inválido. Use dd/mm/aaaa', 'danger')
                return redirect(url_for('comuns.cadastro_recado'))
        
        dados = (
            request.form['medico'],
            request.form['prioridade'],
            request.form['nome_paciente'],
            data_nascimento_db,
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
        from collections import OrderedDict

        status = request.args.get('status', 'respondido')
        busca = (request.args.get('busca') or '').strip()
        perfil = session.get('perfil', '') 

        # ordem fixa e rótulos
        status_ordem = [
            'pendente', 'imprimir', 'solicitado_ao_medico', 'respondido',
            'passar_cartao', 'so_entregar', 'alto_custo', 'entregue'
        ]
        labels = {
            'pendente': 'Pendente',
            'imprimir': 'Imprimir',
            'solicitado_ao_medico': 'Solicitado ao médico',
            'respondido': 'Respondido',
            'passar_cartao': 'Passar cartão',
            'so_entregar': 'Só entregar',
            'alto_custo': 'Alto custo',
            'entregue': 'Entregue',
        }

        resultados_por_status = {s: [] for s in status_ordem}
        contagem_por_status   = {s: 0  for s in status_ordem}

        conn = conectar_banco()
        try:
            cur = conn.cursor()

            if not busca:
                # Sem busca: apenas contagens para as abas
                for s in status_ordem:
                    cur.execute("SELECT COUNT(*) FROM recados WHERE status = ?", (s,))
                    contagem_por_status[s] = cur.fetchone()[0]
            else:
                # Com busca: traz todos os recados que batem e agrupa por status
                like = f'%{busca}%'
                cur.execute("""
                    SELECT id, nome_paciente, telefone, data_cadastro, descricao, status, medico, usuario
                    FROM recados
                    WHERE nome_paciente LIKE ?
                    ORDER BY CASE status
                        WHEN 'pendente' THEN 1
                        WHEN 'imprimir' THEN 2
                        WHEN 'solicitado_ao_medico' THEN 3
                        WHEN 'respondido' THEN 4
                        WHEN 'passar_cartao' THEN 5
                        WHEN 'so_entregar' THEN 6
                        WHEN 'alto_custo' THEN 7
                        WHEN 'entregue' THEN 8
                        ELSE 99 END,
                        medico COLLATE NOCASE ASC,
                        datetime(data_cadastro) DESC
                """, (like,))
                cols = ['id','nome_paciente','telefone','data_cadastro','descricao','status','medico','usuario']
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                for r in rows:
                    st = r['status']
                    if st in resultados_por_status:
                        resultados_por_status[st].append(r)

                contagem_por_status = {s: len(resultados_por_status[s]) for s in status_ordem}
        finally:
            conn.close()

        # Agrupa por médico dentro de cada status (sem acordeão; só cabeçalhos coloridos)
        agrupado_por_status_medico = {}
        for st in status_ordem:
            grupos = OrderedDict()
            for r in resultados_por_status[st]:
                med = r.get('medico') or '---'
                grupos.setdefault(med, []).append(r)
            agrupado_por_status_medico[st] = grupos

        # Flag confiável calculada no backend
        tem_algum = any(len(resultados_por_status[s]) > 0 for s in status_ordem)
        cores_lower = {k.strip().lower(): v for k, v in cores_por_medico.items()}

        return render_template(
            'entregar_recado.html',
            perfil=session.get('perfil'),
            status=status,
            busca=busca,
            status_ordem=status_ordem,
            labels=labels,
            resultados_por_status=resultados_por_status,
            contagem_por_status=contagem_por_status,
            tem_algum=tem_algum,
            cores_lower=cores_lower,
              
        )

   
    @comuns.route('/atualizar_status/<int:id>/<string:novo_status>')
    def atualizar_status(id, novo_status):
        # 1) Atualiza o status (e trata finalizado_por)
        conexao = conectar_banco()
        try:
            cursor = conexao.cursor()

            if novo_status == 'entregue':
                # indo para ENTREGUE => grava quem entregou
                finalizador = session.get('usuario', '---')
                cursor.execute(
                    'UPDATE recados SET status = ?, finalizado_por = ? WHERE id = ?',
                    (novo_status, finalizador, id)
                )
            else:
                # saindo de ENTREGUE (ou qualquer outra transição que não seja ENTREGUE)
                # zera o finalizado_por
                cursor.execute(
                    'UPDATE recados SET status = ?, finalizado_por = NULL WHERE id = ?',
                    (novo_status, id)
                )

            conexao.commit()
        finally:
            conexao.close()

        flash(f'Recado atualizado para o status "{novo_status.replace("_"," ")}" com sucesso!', 'success')

        # 2) Decide para onde voltar com segurança (SEMPRE retorna algo)
        ref = request.headers.get('Referer', '')
        try:
            p = urlparse(ref)
            qs = parse_qs(p.query or '')

            prev_status = (qs.get('status', [''])[0] or '').strip() or None
            busca = (qs.get('busca', [''])[0] or '').strip() or None

            # veio da tela ENTREGAR?
            if '/entregar' in p.path:
                return redirect(url_for('comuns.entregar_recado', status=prev_status, busca=busca))

            # veio da LISTAGEM?
            if '/listar' in p.path:
                # se não houver status na URL anterior, volta para o status atual do item
                return redirect(url_for('responsavel.listar', status=prev_status or novo_status, busca=busca))

        except Exception:
            # falha ao interpretar o referer? Sem crise, temos fallback
            pass

        # Fallback definitivo
        return redirect(url_for('responsavel.listar', status=novo_status))

    return comuns
