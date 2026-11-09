"""
Egyszeri átköltöztetés: Supabase (Postgres) -> Cloudflare D1. Újrafuttatható (INSERT OR REPLACE, ugyanazokkal az id-kkal).
GitHub Actions: migrate-d1 (kézi indítás). Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, D1_API_URL, D1_API_TOKEN.

Lépések: d1/schema.sql alkalmazása -> táblák másolása (csak a D1-ben is létező oszlopok) -> product_summary felépítése.
Átalakítás: igaz/hamis -> 1/0, tömb -> ",a,b,", időpont -> egységes ISO-8601 UTC (a szöveges összehasonlítás miatt).
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from d1db import D1DB, _val
from db import DB

# tábla -> (lapozó oszlop, rendezés, blokkméret a lapozó oszlopon)
TABLES = [
    ("shops", "id", "id", 10**9),
    ("manufacturers", "id", "id", 10**9),
    ("manufacturer_aliases", None, "alias_norm", None),
    ("exchange_rates", None, "currency,rate_date", None),
    ("products", "id", "id", 5000),
    ("product_codes", "product_id", "product_id,code_type,code_norm", 5000),
    ("offers", "id", "id", 3000),
    ("price_history", "offer_id", "offer_id,observed_on", 400),
    ("match_candidates", "offer_id", "offer_id,product_id", 5000),
]
SQL_MAX = 90_000          # D1: egy SQL-utasítás legfeljebb 100 KB
REQ_MAX = 3_000_000       # egy kérés kb. 3 MB
PG_PAGE = 1000            # Supabase max-rows


def lit(v) -> str:
    """SQL-literál (a migrációnál literálokkal sokkal több sor fér egy utasításba, mint 100 paraméterrel)."""
    v = _val(v)
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("\x00", "").replace("'", "''") + "'"


def norm_ts(v):
    if not isinstance(v, str) or "T" not in v:
        return v
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="microseconds")
    except ValueError:
        return v


def apply_schema(d1: D1DB) -> None:
    raw = (Path(__file__).parent.parent / "d1" / "schema.sql").read_text(encoding="utf-8")
    body = "\n".join(line.split("--", 1)[0] for line in raw.splitlines())
    stmts = [(s.strip(), []) for s in body.split(";") if s.strip()]
    d1.execute(stmts)
    print(f"[schema] {len(stmts)} utasítás kész", flush=True)


def pg_rows(pg: DB, table: str, cols: list[str], key: str | None, order: str, step: int | None):
    """Supabase-sorok blokkonként (a nagy OFFSET lassú, ezért a kulcs szerinti tartományokban lapozunk)."""
    sel = ",".join(cols)
    ranges = [None]
    if key:
        top = pg._req("GET", table, {"select": key, "order": f"{key}.desc", "limit": 1})
        if not top:
            return
        hi = int(top[0][key])
        ranges = [(lo, min(lo + step, hi + 1)) for lo in range(0, hi + 1, step)]   # a felső határ ne lépje túl a valós max-ot (smallint id)
    for rg in ranges:
        off = 0
        while True:
            params = {"select": sel, "order": order, "limit": PG_PAGE, "offset": off}
            if rg:
                params["and"] = f"({key}.gte.{rg[0]},{key}.lt.{rg[1]})"
            rows = pg._req("GET", table, params)
            yield from rows
            if len(rows) < PG_PAGE:
                break
            off += PG_PAGE


def copy_table(pg: DB, d1: D1DB, table: str, key, order, step) -> int:
    d1_cols = [r["name"] for r in d1.query(f"SELECT name FROM pragma_table_info('{table}')")]
    sample = pg._req("GET", table, {"select": "*", "limit": 1})
    if not sample:
        print(f"[{table}] üres", flush=True)
        return 0
    cols = [c for c in d1_cols if c in sample[0]]
    head = f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) VALUES "
    stmts, batch, size, req_size, n, t0 = [], [], len(head), 0, 0, time.time()

    def flush_stmt():
        nonlocal batch, size, req_size
        if batch:
            sql = head + ",".join(batch)
            stmts.append((sql, []))
            req_size += len(sql)
            batch, size = [], len(head)

    def flush_req():
        nonlocal stmts, req_size
        flush_stmt()
        if stmts:
            d1.execute(stmts)
            stmts, req_size = [], 0

    for row in pg_rows(pg, table, cols, key, order, step):
        tup = "(" + ",".join(lit(norm_ts(row[c]) if c.endswith("_at") else row[c]) for c in cols) + ")"
        if size + len(tup) + 1 > SQL_MAX:
            flush_stmt()
            if req_size > REQ_MAX or len(stmts) >= 50:
                flush_req()
        batch.append(tup)
        size += len(tup) + 1
        n += 1
        if n % 20000 == 0:
            print(f"[{table}] {n} sor… ({time.time() - t0:.0f} s)", flush=True)
    flush_req()
    got = d1.query(f"SELECT count(*) AS n FROM {table}")[0]["n"]
    print(f"[{table}] {n} sor átmásolva, D1-ben: {got} ({time.time() - t0:.0f} s)", flush=True)
    return n


def main() -> None:
    pg, d1 = DB(), D1DB()
    apply_schema(d1)
    only = set(sys.argv[1:])                       # pl. python migrate_to_d1.py offers price_history
    for table, key, order, step in TABLES:
        if not only or table in only:
            copy_table(pg, d1, table, key, order, step)
    import summary
    summary.rebuild(d1)
    print("KÉSZ – a D1-ben minden adat megvan. Következő lépés: TELEPITES.md 20. pont.", flush=True)


if __name__ == "__main__":
    main()
