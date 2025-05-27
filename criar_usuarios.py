import sqlite3

con = sqlite3.connect('recados.db')
cur = con.cursor()

# Usuário atendente
cur.execute("INSERT INTO usuarios (nome, username, senha, perfil) VALUES (?, ?, ?, ?)", 
            ('pedro atendente', 'pedroa', '1234', 'atendente'))

# Usuário responsável
cur.execute("INSERT INTO usuarios (nome, username, senha, perfil) VALUES (?, ?, ?, ?)", 
            ('pedro responsavel', 'pedro', '1234', 'responsavel'))

con.commit()
con.close()

print('Usuários criados!')
