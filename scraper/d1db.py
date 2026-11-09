"""
Cloudflare D1 kliens a scrapernek – ugyanaz a felület, mint a db.DB (Supabase/PostgREST), így a scraper többi része
változatlan. A D1-et kívülről a weboldal Workerének titkos végpontján érjük el (web/app/api/db/route.js), mert a
Cloudflare központi D1 API-ja kérésszám-korlátos. Csak stdlib.

Env: D1_API_URL (pl. https://airsofthunter.<fiók>.workers.dev/api/db), D1_API_TOKEN (ugyanaz, mint a Worker INGEST_TOKEN titka).
PostgREST-szűrők, amiket ismer: eq.X, lt.X, in.(a,b), is.null, not.is.null; select="a,b" vagy "*".
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from decimal import Decimal

PAGE = 1000
MAX_PARAMS = 90                 # a D1 egy utasításban legfeljebb 100 paramétert enged
STMTS_PER_REQUEST = 100
VIEWS = {"latest_rates"}        # nézet: nincs rowid, nincs lapozás (kicsi)


def _val(v):
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (list, tuple)):
        if any(isinstance(x, (dict, list, tuple)) for x in v):      # JSON-lista (pl. scrape_runs.errors)
            return json.dumps(v, ensure_ascii=False, default=str)
        return "," + ",".join(map(str, v)) + "," if v else ""      # egyszerű tömb (pl. ships_to)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False, default=str)
    return v


def _lit(s: str):
    return {"true": 1, "false": 0}.get(s, s)


def where(filters: dict) -> tuple[str, list]:
    """PostgREST-stílusú szűrők -> SQL WHERE + paraméterek."""
    parts, params = [], []
    for col, spec in filters.items():
        if col in ("select", "order"):
            continue
        spec = str(spec)
        if spec == "is.null":
            parts.append(f"{col} IS NULL")
        elif spec == "not.is.null":
            parts.append(f"{col} IS NOT NULL")
        elif spec.startswith("in.("):
            vals = [_lit(v) for v in spec[4:-1].split(",") if v != ""]
            if not vals:
                parts.append("0")
            else:
                parts.append(f"{col} IN ({','.join('?' * len(vals))})")
                params += vals
        else:
            op, val = spec.split(".", 1)
            sql_op = {"eq": "=", "lt": "<", "lte": "<=", "gt": ">", "gte": ">=", "neq": "<>"}[op]
            parts.append(f"{col} {sql_op} ?")
            params.append(_lit(val))
    return (" WHERE " + " AND ".join(parts)) if parts else "", params


class D1DB:
    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = (url or os.environ["D1_API_URL"]).rstrip("/")
        self.token = (token or os.environ["D1_API_TOKEN"]).strip()

    # ---- alacsony szint ----------------------------------------------------------------------------------
    def execute(self, statements: list[tuple[str, list]]) -> list[list[dict]]:
        """Utasítások futtatása (100-asával egy kérésben, kérésenként egy tranzakció). Visszaad: sorok utasításonként."""
        out = []
        for i in range(0, len(statements), STMTS_PER_REQUEST):
            chunk = [{"sql": s, "params": [_val(p) for p in ps]} for s, ps in statements[i:i + STMTS_PER_REQUEST]]
            out += [r.get("results", []) for r in self._post({"statements": chunk})]
        return out

    def _post(self, body: dict):
        data = json.dumps(body, default=str).encode()
        for attempt in range(4):
            req = urllib.request.Request(self.url, data=data, method="POST", headers={
                "Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                "User-Agent": "AirsoftHunterBot/1.0 (+https://www.airsofthunter.com/bot)"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:500]
                if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"D1 {e.code}: {msg}") from None
            except urllib.error.URLError:
                if attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        return self.execute([(sql, params or [])])[0]

    # ---- a db.DB-vel azonos felület ----------------------------------------------------------------------
    def select(self, table: str, **params) -> list[dict]:
        cols = params.get("select", "*")
        w, args = where(params)
        if table in VIEWS:
            return self.query(f"SELECT {cols} FROM {table}{w}", args)
        out, last = [], 0                                   # lapozás rowid szerint (OFFSET nélkül: kevesebb olvasott sor)
        while True:
            cond = (w + " AND" if w else " WHERE") + " rowid > ?"
            rows = self.query(f"SELECT rowid AS _rid, {cols} FROM {table}{cond} ORDER BY rowid LIMIT {PAGE}", args + [last])
            for r in rows:
                last = r.pop("_rid")
            out += rows
            if len(rows) < PAGE:
                return out

    def insert(self, table: str, rows: list[dict]) -> list[dict]:
        stmts = []
        for r in rows:
            cols = list(r)
            stmts.append((f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) RETURNING *",
                          [r[c] for c in cols]))
        try:
            return [x for res in self.execute(stmts) for x in res]
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):         # a scraper a Postgres hibakódját figyeli
                raise RuntimeError(f"23505 duplicate key ({e}) slug") from None
            raise

    def upsert(self, table: str, rows: list[dict], on_conflict: str, returning: bool = True) -> list[dict]:
        if not rows:
            return []
        keys = [k.strip() for k in on_conflict.split(",")]
        stmts = []
        for r in rows:
            cols = list(r)
            upd = [c for c in cols if c not in keys]
            sql = (f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) "
                   f"ON CONFLICT({','.join(keys)}) DO " + ("UPDATE SET " + ",".join(f"{c}=excluded.{c}" for c in upd) if upd else "NOTHING")
                   + (" RETURNING *" if returning else ""))
            stmts.append((sql, [r[c] for c in cols]))
        res = self.execute(stmts)
        return [x for rs in res for x in rs] if returning else []

    def update(self, table: str, values: dict, **filters) -> None:
        # a nagy IN-listákat szétvágjuk (D1: max. 100 paraméter / utasítás)
        big = next((k for k, v in filters.items() if str(v).startswith("in.(") and str(v).count(",") >= MAX_PARAMS - len(values)), None)
        if big:
            ids = str(filters[big])[4:-1].split(",")
            step = MAX_PARAMS - len(values) - len(filters)
            stmts = []
            for i in range(0, len(ids), step):
                w, args = where({**filters, big: f"in.({','.join(ids[i:i + step])})"})
                stmts.append((f"UPDATE {table} SET {','.join(f'{c}=?' for c in values)}{w}", list(values.values()) + args))
            self.execute(stmts)
            return
        w, args = where(filters)
        self.execute([(f"UPDATE {table} SET {','.join(f'{c}=?' for c in values)}{w}", list(values.values()) + args)])

    def rpc(self, fn: str, args: dict | None = None):
        # A D1-ben nincs tárolt eljárás: a product_summary-t a napi futás végén a summary.py építi újra (rematch.py).
        if fn == "refresh_product_summary":
            return None
        raise RuntimeError(f"D1: ismeretlen rpc: {fn}")
