from datetime import datetime, timedelta
import sqlite3
import os

def conectar_banco():
    return sqlite3.connect("recados.db")

def registrar_log(mensagem):
    data_log = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")
    linha = f"[{hora}] {mensagem}\n"

    with open(f"logs/log_{data_log}.txt", "a", encoding="utf-8") as f:
        f.write(linha)

def excluir_recados_antigos():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    conexao = conectar_banco()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    limite_data = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
    registrar_log(f"🔍 Verificando recados entregues antes de {limite_data}")

    cursor.execute('''
        DELETE FROM recados
        WHERE status = 'entregue' AND data_cadastro < ?
    ''', (limite_data,))

    total = cursor.rowcount
    conexao.commit()
    conexao.close()

    registrar_log(f"✅ {total} recado(s) excluído(s).")

if __name__ == "__main__":
    excluir_recados_antigos()

