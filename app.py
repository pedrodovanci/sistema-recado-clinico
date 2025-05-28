from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse, parse_qs 


def login_requerido(perfis_permitidos):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'usuario' not in session or session.get('perfil') not in perfis_permitidos:
                flash("Faça login para acessar essa página.", "warning")
                return redirect(url_for('login'))
            return func(*args, **kwargs)
        return wrapper
    return decorador

app = Flask(__name__)
app.secret_key = 'chave-secreta'  # Necessário para controle de sessão

#  Função para criar o banco de dados e tabelas
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
            data_cadastro TEXT NOT NULL
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

#  Função para conectar ao banco
def conectar_banco():
    conexao = sqlite3.connect('recados.db')
    conexao.row_factory = sqlite3.Row
    return conexao

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if 'usuario' in session:
        perfil = session.get('perfil')
        return redirect(url_for('inicio' if perfil == 'atendente' else 'listar'))
    
    
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
            if usuario['perfil'] == 'atendente':
                return redirect(url_for('inicio'))
            else:
                return redirect(url_for('listar'))
        else:
            flash('Usuário ou senha inválidos!', 'danger')
    
    return render_template('login.html')

def excluir_recados_antigos():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    limite_data = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        DELETE FROM recados
        WHERE status = 'entregue' AND data_cadastro < ?
    ''', (limite_data,))
    
    print(f"{cursor.rowcount} recado(s) excluído(s).")

    conexao.commit()
    conexao.close()

# 🧹 Exclusão em massa por status (só entregar / alto custo)
@app.route('/excluir_todos/<status>', methods=['POST'])
@login_requerido(['responsavel'])
def excluir_todos(status):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM recados WHERE status = ?', (status,))
    conexao.commit()
    conexao.close()
    flash(f'Todos os recados com status \"{status}\" foram excluídos.', 'success')
    return redirect(url_for('listar', status=status))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Página de cadastro de novo recado (atendente e responsável)
@app.route('/',endpoint = 'inicio')
@login_requerido(['atendente', 'responsavel'])
def cadastro():
    usuario = session['usuario']
    if session['perfil'] == 'atendente':
        return render_template('inicio_atendente.html', usuario=usuario)
    else:
        return redirect(url_for('listar'))

@app.route('/cadastro_recado')
@login_requerido(['atendente', 'responsavel'])
def cadastro_recado():
    usuario = session['usuario']
    return render_template('cadastro_recado.html', usuario=usuario)
    
@app.route('/entregar', methods=['GET', 'POST'])
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
                if status not in resultados:
                    resultados[status] = {}
                medico = recado['medico']
                if medico not in resultados[status]:
                    resultados[status][medico] = []
                resultados[status][medico].append(recado)

    return render_template('entregar_recado.html', resultados=resultados, busca=busca)


# 📋 Página de listagem de recados por status (somente responsável)
@app.route('/listar')
@login_requerido(['responsavel'])
def listar():
    status = request.args.get('status', 'pendente')    

    busca = request.args.get('busca', '').strip()

    conexao = conectar_banco()
    cursor = conexao.cursor()

    if busca:
        cursor.execute(
            'SELECT * FROM recados WHERE status = ? AND nome_paciente LIKE ? ORDER BY medico, prioridade',
            (status, f'%{busca}%')
        )
    else:
        cursor.execute(
            'SELECT * FROM recados WHERE status = ? ORDER BY medico, data_cadastro',
            (status,)
        )
  

    recados = cursor.fetchall()
    conexao.close()
    # 🔥 Organizando os recados por médico
    recados_por_medico = {}
    for recado in recados:
        medico = recado['medico']
        

        if medico not in recados_por_medico:
            recados_por_medico[medico] = []
        recados_por_medico[medico].append(recado)

    quantidades_por_medico = {
    medico: len(recados) for medico, recados in recados_por_medico.items()}

    # 🎨 Cores fixas por médico
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
    "Dr. Sebastiao Silva": "#014217"
}


    return render_template(
        'listar.html',
        recados_por_medico=recados_por_medico,
        status=status,
        cores=cores_por_medico,
        quantidades_por_medico=quantidades_por_medico
    )


    
# ❌ Exclusão individual de recado
@app.route('/recado/<int:id>/excluir', methods=['POST'])
@login_requerido(['responsavel'])
def excluir_recado(id):
    conn = conectar_banco()
    conn.execute('DELETE FROM recados WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar'))

# 🛠 Edição de um recado específico
@app.route('/recado/<int:id>/editar', methods=['GET', 'POST'])
@login_requerido(['responsavel'])
def editar_recado(id):
    conn = conectar_banco()
    cursor = conn.cursor()
    
    recado = conn.execute('SELECT * FROM recados WHERE id = ?', (id,)).fetchone()
    medicos = cursor.execute('SELECT DISTINCT medico FROM recados').fetchall()

    if request.method == 'POST':
        medico = request.form['medico']
        nome_paciente = request.form['nome_paciente']
        telefone = request.form['telefone']
        status = request.form['status']
        prioridade = request.form['prioridade']
        descricao = request.form['mensagem']

        conn.execute('''
            UPDATE recados
            SET medico = ?, nome_paciente = ?, telefone = ?, status = ?, prioridade = ?, descricao = ?
            WHERE id = ?
        ''', (medico, nome_paciente, telefone, status, prioridade, descricao, id))
        conn.commit()
        conn.close()
        return redirect(url_for('detalhar_recado', id=id))

    conn.close()
    return render_template('editar_recado.html', recado=recado, medicos=medicos)

# Visualização detalhada de um recado
@app.route('/recado/<int:id>')
@login_requerido(['responsavel'])
def detalhar_recado(id):
    conn = conectar_banco()
    recado = conn.execute('SELECT * FROM recados WHERE id = ?', (id,)).fetchone()
    conn.close()
    if recado is None:
        return 'Recado não encontrado.', 404
    return render_template('detalhar_recado.html', recado=recado)

# 🔁 Atualizar o status de um recado (via dropdown)
@app.route('/atualizar_status/<int:id>/<string:novo_status>')
def atualizar_status(id, novo_status):
    if 'usuario' not in session or session.get('perfil') not in ['responsavel', 'atendente']:
        return redirect(url_for('login'))

    conexao = conectar_banco()
    cursor = conexao.cursor()

    if novo_status == 'entregue':
        finalizador = session['usuario']
        cursor.execute('UPDATE recados SET status = ?, finalizado_por = ? WHERE id = ?', (novo_status, finalizador, id))
    else:
        cursor.execute('UPDATE recados SET status = ? WHERE id = ?', (novo_status, id))

    conexao.commit()
    conexao.close()

    flash('Recado marcado como entregue com sucesso!', 'success')

    ref = request.referrer
    if ref:
        parsed = urlparse(ref)
        if '/listar' in parsed.path:
            return redirect(ref)
        elif '/entregar' in parsed.path:
            return redirect(url_for('entregar_recado'))

    if session['perfil'] == 'responsavel':
        return redirect(url_for('listar', status='pendente'))
    else:
        return redirect(url_for('inicio'))



# 🖨️ Imprimir todos os recados de um determinado status
@app.route('/imprimir/<status>')
def imprimir(status):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM recados WHERE status = ? ORDER BY medico, prioridade', (status,))
    recados = cursor.fetchall()
    conexao.close()
    return render_template('imprimir_lista.html', recados=recados)
   

# 🖨️ Imprimir recado individual


from datetime import datetime

@app.route('/imprimir_recado/<int:id>', endpoint='imprimir_recado')
@login_requerido(['responsavel'])
def imprimir_recado(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM recados WHERE id = ?', (id,))
    row = cursor.fetchone()
    conexao.close()

    if row:
        recado = dict(row)  # Converte para dicionário mutável

        # ✅ Converte datas do banco para objetos datetime
        try:
            nascimento = datetime.strptime(recado['data_nascimento'], '%Y-%m-%d')
            recado['data_nascimento_formatada'] = nascimento.strftime('%d/%m/%Y')

            cadastro = datetime.strptime(recado['data_cadastro'], '%Y-%m-%d %H:%M:%S')
            recado['data_cadastro_formatada'] = cadastro.strftime('%d/%m/%Y %H:%M')
        except:
            recado['data_nascimento_formatada'] = recado['data_nascimento']
            recado['data_cadastro_formatada'] = recado['data_cadastro']

        return render_template('imprimir_lista.html', recados=[recado])
    else:
        return 'Recado não encontrado.', 404

    
# salvamento de novo recado (POST do formulário de cadastro)
@app.route('/salvar', methods=['POST'])
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

    try:
        cursor.execute('''
            INSERT INTO recados 
            (medico, prioridade, nome_paciente, data_nascimento, telefone, convenio, descricao, status, usuario, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', dados + (status, usuario, data_cadastro))
        conexao.commit()
        print("✅ Recado inserido com sucesso!")
    except Exception as e:
        print("❌ Erro ao inserir no banco:", e)

    conexao.close()
    return redirect(url_for('inicio'))

#filtro de formatacao de data
@app.template_filter('format_data')
def formatar_data_br(data_str):
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
        return data_obj.strftime('%d/%m/%Y')
    except:
        return data_str  # fallback caso a string esteja mal formatada

# 🚀 Rodar o app
if __name__ == "__main__":
    excluir_recados_antigos()  # executa antes de iniciar o app
    app.run(host='0.0.0.0', port=5000, debug=True)

