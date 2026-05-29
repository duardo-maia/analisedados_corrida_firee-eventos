"""
criar_banco.py
--------------
Roda UMA VEZ no seu computador para importar a planilha xlsx
e criar/atualizar o banco SQLite usado pelo app Streamlit.

Uso:
    python criar_banco.py                            # usa caminhos padrão
    python criar_banco.py planilha.xlsx banco.db     # caminhos customizados
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date

# ── Caminhos ────────────────────────────────────────────────────────────────
XLSX_PADRAO = "TreinoOficial.xlsx"
DB_PADRAO   = "corrida.db"

xlsx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(XLSX_PADRAO)
db_path   = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(DB_PADRAO)

# ── Validação ────────────────────────────────────────────────────────────────
if not xlsx_path.exists():
    print(f"❌  Arquivo não encontrado: {xlsx_path}")
    sys.exit(1)

# ── Leitura da planilha ──────────────────────────────────────────────────────
print(f"📂  Lendo: {xlsx_path}")
df = pd.read_excel(xlsx_path)
df.columns = ["timestamp", "nome", "nascimento", "autoriza_imagem"]

df["nascimento"] = pd.to_datetime(df["nascimento"], errors="coerce")

# ── Calcula idade e grupo etário ─────────────────────────────────────────────
hoje = date.today()

def calcular_idade(dt):
    if pd.isnull(dt):
        return None
    return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))

def grupo_etario(dt):
    if pd.isnull(dt):
        return "Sem informação"
    idade = calcular_idade(dt)
    if   16 <= idade <= 19: return "16 a 19 anos"
    elif 20 <= idade <= 29: return "20 a 29 anos"
    elif 30 <= idade <= 39: return "30 a 39 anos"
    elif 40 <= idade <= 49: return "40 a 49 anos"
    elif 50 <= idade <= 59: return "50 a 59 anos"
    elif idade >= 60:       return "60 anos ou mais"
    else:                   return "Sem informação"

df["idade"]        = df["nascimento"].apply(calcular_idade)
df["grupo_etario"] = df["nascimento"].apply(grupo_etario)

# Formata nascimento como string para guardar no SQLite
df["nascimento_fmt"] = df["nascimento"].dt.strftime("%d/%m/%Y").fillna("—")
df["nascimento"]     = df["nascimento"].dt.strftime("%Y-%m-%d").fillna("")

# ── Grava no SQLite ──────────────────────────────────────────────────────────
print(f"💾  Gravando em: {db_path}")
con = sqlite3.connect(db_path)

con.execute("""
    CREATE TABLE IF NOT EXISTS participantes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT,
        nome            TEXT,
        nascimento      TEXT,
        nascimento_fmt  TEXT,
        idade           INTEGER,
        grupo_etario    TEXT,
        autoriza_imagem TEXT
    )
""")

# Apaga dados antigos antes de reimportar (idempotente)
con.execute("DELETE FROM participantes")

df.to_sql("participantes", con, if_exists="append", index=False)
con.commit()

# ── Resumo ───────────────────────────────────────────────────────────────────
total = con.execute("SELECT COUNT(*) FROM participantes").fetchone()[0]
print(f"\n✅  {total} participantes importados com sucesso!\n")

print("Distribuição por grupo etário:")
for row in con.execute("""
    SELECT grupo_etario, COUNT(*) as qtd
    FROM participantes
    GROUP BY grupo_etario
    ORDER BY grupo_etario
"""):
    print(f"   {row[0]:<20} {row[1]} pessoas")

con.close()
print(f"\n📦  Banco salvo em: {db_path.resolve()}")
print("     Copie este arquivo para a pasta do seu app Streamlit.")