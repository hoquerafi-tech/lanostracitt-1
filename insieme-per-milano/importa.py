"""Crea le tabelle nel database indicato dalle credenziali (es. Aiven).
Uso:  python importa.py
Legge database.sql e aggiornamento.sql, ignora CREATE/DROP DATABASE e USE
(si usa il database scelto in DB_NAME) ed esegue il resto."""
import re
from db import get_conn

def istruzioni(percorso):
    testo = open(percorso, encoding="utf-8").read()
    testo = "\n".join(r for r in testo.splitlines() if not r.strip().startswith("--"))
    for s in testo.split(";"):
        s = s.strip()
        if s:
            yield s

conn = get_conn()
with conn.cursor() as cur:
    for file in ("database.sql", "aggiornamento.sql"):
        for s in istruzioni(file):
            if re.match(r"(DROP|CREATE)\s+DATABASE|USE\s|SHOW\s|SELECT\s", s, re.I):
                continue
            cur.execute(s)
conn.commit()
conn.close()
print("Tabelle create. Fatto!")
