from datetime import datetime, timedelta
import sqlite3
import os
import argparse
import sys

# Caminho absoluto baseado na pasta do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "recados.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")

STATUS_ALVO = ("entregue",)
DIAS_PADRAO = 60  # padrão agora é 60

def conectar_banco():
    return sqlite3.connect(DB_PATH)

def registrar_log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")
    with open(os.path.join(LOG_DIR, f"log_{hoje}.txt"), "a", encoding="utf-8") as f:
        f.write(f"[{hora}] {msg}\n")

def excluir_recados_antigos(dias=DIAS_PADRAO, dry_run=False):
    limite = datetime.now() - timedelta(days=dias)
    limite_str = limite.strftime("%Y-%m-%d %H:%M:%S")

    registrar_log(f"Limite < {limite_str} | Status: {STATUS_ALVO} | Dry-run: {dry_run}")
    registrar_log(f"Banco: {DB_PATH}")

    con = conectar_banco()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Quantos candidatos existem?
    q_select = f"""
        SELECT COUNT(*) as qtd
        FROM recados
        WHERE status IN ({','.join(['?']*len(STATUS_ALVO))})
          AND data_cadastro < ?
    """
    cur.execute(q_select, (*STATUS_ALVO, limite_str))
    qtd = cur.fetchone()["qtd"] or 0
    registrar_log(f"Candidatos (antes): {qtd}")

    if dry_run or qtd == 0:
        con.close()
        return 0

    # Exclusão de fato
    q_delete = f"""
        DELETE FROM recados
        WHERE status IN ({','.join(['?']*len(STATUS_ALVO))})
          AND data_cadastro < ?
    """
    cur.execute(q_delete, (*STATUS_ALVO, limite_str))
    total = cur.rowcount or 0
    con.commit()
    con.close()
    registrar_log(f"✅ {total} recado(s) excluído(s).")
    return total

def main():
    parser = argparse.ArgumentParser(description="Remove recados antigos (status concluído) do SQLite.")
    parser.add_argument("--dias", type=int, default=DIAS_PADRAO, help="Quantidade de dias a manter (padrão: 60).")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem excluir.")
    args = parser.parse_args()
    total = excluir_recados_antigos(dias=args.dias, dry_run=args.dry_run)
    sys.exit(0 if args.dry_run or total >= 0 else 1)

if __name__ == "__main__":
    main()
