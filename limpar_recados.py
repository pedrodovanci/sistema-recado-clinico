from datetime import datetime, timedelta
import sqlite3

def conectar_banco():
    return sqlite3.connect("recados.db")

def excluir_recados_antigos():
    conexao = conectar_banco()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    limite_data = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[INFO] Excluindo recados 'finalizado' com data anterior a {limite_data}")

    cursor.execute('''
        DELETE FROM recados
        WHERE status = 'finalizado' AND data_cadastro < ?
    ''', (limite_data,))

    total = cursor.rowcount
    conexao.commit()
    conexao.close()
    
    print(f"[INFO] {total} recado(s) excluído(s).")

if __name__ == "__main__":
    excluir_recados_antigos()
