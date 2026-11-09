"""
Egy d1/*.sql fájl lefuttatása a Cloudflare D1-en (a /api/db végponton át). Actions → d1-sql.
Használat: python scraper/run_sql.py d1/uj_markak_2026-11-09.sql
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*(?:\n|$)", body) if s.strip()]


def main(name: str) -> int:
    if not re.fullmatch(r"d1/[a-z0-9_.\-]+\.sql", name) or name in ("d1/schema.sql",):
        print(f"Hibás fájlnév: {name!r} (minta: d1/valami.sql)")
        return 1
    path = ROOT / name
    if not path.is_file():
        print(f"Nincs ilyen fájl: {name}")
        return 1
    from db import get_db
    db = get_db()
    stmts = statements(path.read_text(encoding="utf-8"))
    print(f"[sql] {name}: {len(stmts)} utasítás", flush=True)
    for start in range(0, len(stmts), 50):                 # 50 utasítás / kérés (kérésenként egy tranzakció)
        chunk = stmts[start:start + 50]
        results = db.execute([(s, []) for s in chunk])
        for i, (s, rows) in enumerate(zip(chunk, results), start + 1):
            if rows or i == len(stmts) or i <= 5:
                head = " ".join(s.split())[:90]
                print(f"[sql] {i}/{len(stmts)} kész: {head}{' → ' + str(rows[:5]) if rows else ''}", flush=True)
        print(f"[sql] {min(start + 50, len(stmts))}/{len(stmts)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
