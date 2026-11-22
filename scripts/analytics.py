import re
from pathlib import Path

from app.db import connect

text = Path("sql/analytics.sql").read_text()
parts = re.split(r"^-- name: (.+)$", text, flags=re.MULTILINE)  # ['', nome1, sql1, nome2, sql2, ...]

with connect() as conn:
    for name, sql in zip(parts[1::2], parts[2::2]):
        print(f"\n== {name} ==")
        rows = conn.execute(sql).fetchall()
        if not rows:
            print("(nessun risultato)")
            continue
        print(" | ".join(rows[0].keys()))
        for row in rows:
            print(" | ".join(str(v) for v in tuple(row)))
