import sqlite3
from datetime import datetime

def criar_banco_com_usuarios():
    # Criar banco de dados
    conexao = sqlite3.connect('recados.db')
    cursor = conexao.cursor()
    
    # Criar tabela de recados
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
    
    # Criar tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)
    
    # Inserir usuários de teste
    usuarios_teste = [
        ('Administrador', 'admin', '123', 'admin'),
        ('Atendente Teste', 'atendente', '123', 'atendente'),
        ('Responsável Teste', 'responsavel', '123', 'responsavel')
    ]
    
    for nome, username, senha, perfil in usuarios_teste:
        try:
            cursor.execute(
                'INSERT INTO usuarios (nome, username, senha, perfil) VALUES (?, ?, ?, ?)',
                (nome, username, senha, perfil)
            )
            print(f'Usuário {username} criado com sucesso!')
        except sqlite3.IntegrityError:
            print(f'Usuário {username} já existe.')
    
    # Inserir alguns recados de exemplo
    recados_exemplo = [
        ('Dr. Silva', 'Alto Custo', 'João Santos', '1980-05-15', '11999999999', 'Unimed', 'Consulta cardiológica urgente', 'pendente', 'atendente', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('Dra. Maria', 'Passar Cartão', 'Ana Costa', '1975-08-22', '11888888888', 'Bradesco Saúde', 'Exame de rotina', 'entregue', 'atendente', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('Dr. João', 'Normal', 'Pedro Oliveira', '1990-12-03', '11777777777', 'SulAmérica', 'Consulta dermatológica', 'pendente', 'atendente', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ]
    
    for recado in recados_exemplo:
        cursor.execute(
            'INSERT INTO recados (medico, prioridade, nome_paciente, data_nascimento, telefone, convenio, descricao, status, usuario, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            recado
        )
    
    conexao.commit()
    conexao.close()
    print('Banco de dados inicializado com sucesso!')
    print('Usuários criados:')
    print('- admin/123 (Administrador)')
    print('- atendente/123 (Atendente)')
    print('- responsavel/123 (Responsável)')

if __name__ == '__main__':
    criar_banco_com_usuarios()