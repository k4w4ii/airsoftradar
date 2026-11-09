"""Minimális Supabase (PostgREST) kliens – csak stdlib.
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (service role -> RLS megkerülése, csak szerveren!)."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

PAGE = 1000  # Supabase alapértelmezett max-rows


class DB:
    def __init__(self, url: str | None = None, key: str | None = None):
        self.base = (url or os.environ["SUPABASE_URL"]).rstrip("/") + "/rest/v1"
        key = (key or os.environ["SUPABASE_SERVICE_KEY"]).strip()
        self.headers = {"apikey": key, "Content-Type": "application/json"}
        if not key.startswith("sb_"):          # régi JWT service_role kulcs (2026 végéig); az új sb_secret_ csak apikey-ben
            self.headers["Authorization"] = f"Bearer {key}"

    def _req(self, method: str, path: str, params: dict | None = None, body=None, prefer: str | None = None):
        url = f"{self.base}/{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params, safe="(),.*:")
        h = dict(self.headers)
        if prefer:
            h["Prefer"] = prefer
        data = json.dumps(body, default=str).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')[:500]}") from None
        return json.loads(raw) if raw else None

    def select(self, table: str, **params) -> list[dict]:
        """Összes sor lapozva. Pl. select('offers', select='id,url', shop_id='eq.3')"""
        out, offset = [], 0
        while True:
            rows = self._req("GET", table, {**params, "limit": PAGE, "offset": offset})
            out += rows
            if len(rows) < PAGE:
                return out
            offset += PAGE

    def upsert(self, table: str, rows: list[dict], on_conflict: str, returning: bool = True) -> list[dict]:
        out = []
        for i in range(0, len(rows), 500):
            res = self._req("POST", table, {"on_conflict": on_conflict}, rows[i:i + 500],
                            prefer="resolution=merge-duplicates," + ("return=representation" if returning else "return=minimal"))
            out += res or []
        return out

    def insert(self, table: str, rows: list[dict]) -> list[dict]:
        return self._req("POST", table, body=rows, prefer="return=representation") or []

    def update(self, table: str, values: dict, **filters) -> None:
        self._req("PATCH", table, filters, values, prefer="return=minimal")

    def rpc(self, fn: str, args: dict | None = None):
        return self._req("POST", f"rpc/{fn}", body=args or {})


def get_db():
    """A scraper adatbázisa: DB_BACKEND=d1 -> Cloudflare D1 (d1db.D1DB), egyébként Supabase (DB)."""
    if os.environ.get("DB_BACKEND", "").strip().lower() == "d1":
        from d1db import D1DB
        return D1DB()
    return DB()
