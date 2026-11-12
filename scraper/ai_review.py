"""
AI-ellenőrzés (Gemini 3.1 Flash-Lite): a termékek kategóriáját a projekt szabályrendszere (ai_szabalyok.md) szerint
átnézeti, az eredményt a D1 ai_categories táblájába írja. A summary.py ezt a kézi javítás után, a szabály-alapú
besorolás helyett használja. Minden terméket csak egyszer kérdez meg (újra csak akkor, ha a neve megváltozott).

Futtatás: GitHub → Actions → ai-review → Run workflow   (helyben: python scraper/ai_review.py)
Env:
  GEMINI_API_KEY   a Google AI Studio kulcsa (GitHub Secret). Nélküle a script kihagyja magát.
  AI_DRY_RUN=1     csak becslés: hány termék, hány token, mennyibe kerülne (nem hív API-t, kulcs sem kell)
  AI_MAX_REQUESTS  legfeljebb ennyi kérés egy futásban (alapból 50; egy kérés = AI_BATCH termék)
  AI_BATCH         termék / kérés (alapból 100)
  AI_MODEL         alapból gemini-3.1-flash-lite
  AI_RESET=1       a korábbi AI-döntések törlése (pl. az ai_szabalyok.md módosítása után mindent újranéz)
Csak stdlib.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import classify

MODEL = os.environ.get("AI_MODEL", "gemini-3.1-flash-lite")
PRICE_IN, PRICE_OUT = 0.25, 1.50                 # USD / 1M token (gemini-3.1-flash-lite, standard; ai.google.dev/pricing)
USD_HUF = 360
RULES = Path(__file__).parent / "ai_szabalyok.md"
# A Gemini ezek közül választhat (az „egyedi / tuningolt” csoportot a summary.py dönti el a név alapján)
CHOICES = sorted(classify.ALL_CATEGORIES - classify.CUSTOM)
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PAUSE_S = 4.5                                    # ≤ ~13 kérés / perc (ingyenes keret)
ORDER = {c: 0 for c in classify.WEAPONS} | {c: 0 for c in classify.CUSTOM} | {"other": 1}   # fegyverek elöl


class QuotaExceeded(Exception):
    pass


def ensure_table(db) -> None:
    db.execute([("CREATE TABLE IF NOT EXISTS ai_categories (slug TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, "
                 "model TEXT, reviewed_at TEXT)", [])])


def load(db) -> dict[str, str]:
    """slug -> kategória (a summary.py hívja). Ha a tábla még nincs, üres."""
    try:
        return {r["slug"]: r["category"] for r in db.select("ai_categories", select="slug,category")
                if r["category"] in classify.ALL_CATEGORIES}
    except Exception:
        return {}


def candidates(products: list[dict], done: dict[str, str]) -> list[dict]:
    """Még át nem nézett (vagy azóta átnevezett) termékek, a fegyverek elöl, azon belül a legolcsóbbak elöl."""
    todo = [p for p in products if done.get(p["slug"]) != p["name"]]
    return sorted(todo, key=lambda p: (ORDER.get(p["category"], 2), p.get("price") or 0, p["id"]))


def items_text(batch: list[dict]) -> str:
    return "\n".join(json.dumps({"i": i, "n": p["name"], "m": p.get("manufacturer") or "", "p": round(p.get("price") or 0)},
                                ensure_ascii=False) for i, p in enumerate(batch))


def request_body(batch: list[dict], thinking: bool = True) -> dict:
    body = {
        "systemInstruction": {"parts": [{"text": RULES.read_text(encoding="utf-8")}]},
        "contents": [{"role": "user", "parts": [{"text": "Termékek (i = sorszám, n = név, m = gyártó, p = ár Ft):\n" + items_text(batch)}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": {"type": "ARRAY", "items": {"type": "OBJECT", "required": ["i", "c"], "properties": {
                "i": {"type": "INTEGER"}, "c": {"type": "STRING", "enum": CHOICES}}}},
        },
    }
    if thinking:
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "low"}
    return body


def parse(text: str, batch: list[dict]) -> dict[int, str]:
    """A válasz -> {termék index: kategória}. Hibás / ismeretlen elemeket kihagyja."""
    out = {}
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return out
    for el in data if isinstance(data, list) else []:
        if isinstance(el, dict) and isinstance(el.get("i"), int) and 0 <= el["i"] < len(batch) and el.get("c") in CHOICES:
            out[el["i"]] = el["c"]
    return out


def call(key: str, batch: list[dict], opener=urllib.request.urlopen) -> tuple[dict[int, str], dict]:
    """Egy kérés. Visszaad: (eredmény, usageMetadata). 429-nél egyszer vár, utána QuotaExceeded."""
    thinking = True
    for attempt in range(4):
        req = urllib.request.Request(API.format(model=MODEL), method="POST",
                                     data=json.dumps(request_body(batch, thinking)).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with opener(req, timeout=180) as r:
                resp = json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:400]
            if e.code == 400 and thinking and "think" in msg.lower():
                thinking = False                     # a modell nem ismeri a thinkingLevel-t: nélküle újra
                continue
            if e.code == 429:
                if attempt == 0 and "PerDay" not in msg:
                    time.sleep(65)                   # percenkénti korlát: várunk egyet
                    continue
                raise QuotaExceeded(msg) from None
            if e.code in (500, 502, 503, 504) and attempt < 3:
                time.sleep(20 * (attempt + 1))
                continue
            raise RuntimeError(f"Gemini {e.code}: {msg}") from None
        cand = (resp.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
        return parse(text, batch), resp.get("usageMetadata", {})
    raise RuntimeError("Gemini: sikertelen kérés")


def estimate(todo: list[dict], batch_size: int) -> dict:
    """Becslés API nélkül (~3,5 karakter / token)."""
    rules = len(RULES.read_text(encoding="utf-8"))
    n_req = -(-len(todo) // batch_size)
    chars = rules * n_req + sum(len(items_text(todo[i:i + batch_size])) for i in range(0, len(todo), batch_size))
    tin, tout = chars / 3.5, len(todo) * 14
    usd = tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT
    return {"termek": len(todo), "keres": n_req, "bemenet_token": round(tin), "kimenet_token": round(tout),
            "usd": round(usd, 3), "huf": round(usd * USD_HUF)}


def _summary(lines: list[str]) -> None:
    print("\n".join(lines), flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def main() -> int:
    from db import get_db
    db = get_db()
    dry = os.environ.get("AI_DRY_RUN") == "1"
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not dry and not key:
        _summary(["## AI-ellenőrzés", "Nincs GEMINI_API_KEY titok – kihagyva (lásd TELEPITES.md, 11. pont)."])
        return 0
    batch_size = int(os.environ.get("AI_BATCH", "100"))
    max_req = int(os.environ.get("AI_MAX_REQUESTS", "50"))
    ensure_table(db)
    if os.environ.get("AI_RESET") == "1" and not dry:
        db.execute([("DELETE FROM ai_categories", [])])      # új szabályok: minden termék újra átnézésre kerül
        print("[ai] korábbi AI-döntések törölve (újra átnézés)", flush=True)
    products = db.select("product_summary", select="id,slug,name,manufacturer,category,price")
    done = {r["slug"]: r["name"] for r in db.select("ai_categories", select="slug,name")}
    todo = candidates(products, done)
    est = estimate(todo, batch_size)
    if dry:
        _summary(["## AI-ellenőrzés – becslés (nem küldött semmit)", "",
                  f"| Átnézendő termék | Kérés | Bemenet (token) | Kimenet (token) | Várható ár |", "|---|---|---|---|---|",
                  f"| {est['termek']} | {est['keres']} | {est['bemenet_token']:,} | {est['kimenet_token']:,} | "
                  f"${est['usd']} (~{est['huf']} Ft) |", "",
                  f"Modell: {MODEL}. Egy futás legfeljebb {max_req} kérést küld ({max_req * batch_size} termék)."])
        return 0
    cur = {p["slug"]: p["category"] for p in products}
    used = {"in": 0, "out": 0}
    changes, saved, stop = [], 0, ""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for n, i in enumerate(range(0, min(len(todo), max_req * batch_size), batch_size)):
        batch = todo[i:i + batch_size]
        if n:
            time.sleep(PAUSE_S)
        try:
            res, usage = call(key, batch)
        except QuotaExceeded as e:
            stop = f"elfogyott a keret (holnap folytatja): {str(e)[:160]}"
            break
        used["in"] += usage.get("promptTokenCount", 0)
        used["out"] += usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        rows = []
        for idx, c in res.items():
            p = batch[idx]
            rows.append({"slug": p["slug"], "name": p["name"], "category": c, "model": MODEL, "reviewed_at": now})
            base = cur.get(p["slug"], "")
            if c != base and not (base in classify.CUSTOM and classify.custom_of(c) == base):
                changes.append((p["name"], base, c, p.get("price")))
        if rows:
            db.upsert("ai_categories", rows, on_conflict="slug", returning=False)
            saved += len(rows)
        print(f"[ai] {n + 1}. kérés: {len(res)}/{len(batch)} termék", flush=True)
    usd = used["in"] / 1e6 * PRICE_IN + used["out"] / 1e6 * PRICE_OUT
    lines = ["## AI-ellenőrzés", "", f"Átnézve: **{saved}** termék, ebből **{len(changes)}** kategóriája változik. "
             f"Hátravan: {max(0, len(todo) - saved)}.",
             f"Tokenek: {used['in']:,} be / {used['out']:,} ki → kb. ${usd:.3f} (~{round(usd * USD_HUF)} Ft; ingyenes keretben 0).",
             *( [f"Megállt: {stop}"] if stop else [] ), ""]
    if changes:
        lines += ["| Termék | Eddig | AI szerint | Ár (Ft) |", "|---|---|---|---|"]
        lines += [f"| {nm[:70]} | {a} | {b} | {round(pr or 0)} |" for nm, a, b, pr in changes[:200]]
    _summary(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
